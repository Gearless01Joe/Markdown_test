# -*- coding: utf-8 -*-

"""
# @Time    : 2025/11/20 18:46
# @User  : 刘子都
# @Descriotion  : RCSB PDB 爬虫 - 支持批量全量与增量更新。
"""
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, Generator, List, Optional

import scrapy

from src.constant import BASE_DIR
from src.items.rcsb_pdb_item import RcsbAllApiItem
from src.utils.mongodb_manager import MongoDBManager
from src.utils.redis_manager import RedisManager

from .constants import (
    API_BASE as CONST_API_BASE,
    API_ENDPOINTS,
    DEFAULT_ASSEMBLY_ID,
    REDIS_REVISION_HASH as CONST_REDIS_HASH,
    REDIS_TTL_SECONDS as CONST_REDIS_TTL,
    SEARCH_API as CONST_SEARCH_API,
)
from .request_builder import RequestBuilder
from .services import DataParser, EntryContext, FileDownloader, RevisionState


class RcsbAllApiSpider(scrapy.Spider):
    """
    RCSB CoreEntry 全量/增量爬虫。

    作用:
        拉取 RCSB PDB Entry 及其实体、ChemComp、DrugBank 数据。
    """

    name = "rcsb_all_api"

    # 允许的域名列表 以及 起始 URL 列表（空，因为使用 `start_requests` 方法）

    allowed_domains = ["data.rcsb.org", "search.rcsb.org", "rcsb.org"]
    start_urls = []

    # ========== 配置区域 ==========
    DEFAULT_MAX_TARGETS = 100
    DEFAULT_BATCH_SIZE = 100
    INCREMENT_COLLECTION = "rcsb_increment_state"
    INCREMENT_DOC_ID = "rcsb_all_api"
    REDIS_REVISION_HASH = CONST_REDIS_HASH
    REDIS_TTL_SECONDS = CONST_REDIS_TTL
    # =============================

    SEARCH_API = CONST_SEARCH_API
    API_BASE = CONST_API_BASE
    API_ENDPOINTS = API_ENDPOINTS

    SECTION_MAP = {
        "polymer_entity": "CorePolymerEntity",
        "nonpolymer_entity": "CoreNonpolymerEntity",
        "branched_entity": "CoreBranchedEntity",
        "chemcomp": "CoreChemComp",
        "drugbank": "CoreDrugbank",
        "assembly": "CoreAssembly",
    }

    handle_httpstatus_list = [400]

    # 并发控制：64 总并发，16 每域名并发
    # - 下载延迟：0.3 秒，随机化
    # - 超时和重试：30 秒超时，3 次重试
    # - 自动限流：启用，目标并发 4.0
    # - Pipeline：文件下载 → 文件替换（OSS上传） → 数据存储（MongoDB）

    custom_settings = {
        # ========== 并发与速率 ==========
        "CONCURRENT_REQUESTS": 64,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 16,
        "DOWNLOAD_DELAY": 0.3,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        # ========== 超时与重试 ==========
        "DOWNLOAD_TIMEOUT": 30 ,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 3,
        # ========== 自动限流 ==========
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 0.3,
        "AUTOTHROTTLE_MAX_DELAY": 2.0,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 4.0,
        # ========== 其他 ==========
        "LOG_LEVEL": "INFO",
        "DOWNLOADER_MIDDLEWARES": {
            "src.middlewares.proxy_middleware.BaseProxyMiddleware": None,
        },
        "ITEM_PIPELINES": {
            "src.pipelines.file_download_pipeline.FileDownloadPipeline": 200,
            "src.pipelines.file_replacement_pipeline.FileReplacementPipeline": 300,
            "src.pipelines.storage.rcsb_pdb_pipeline.RcsbPdbPipeline": 400,
        },
    }

    def __init__(
        self,
        pdb_id=None,
        output_filename=None,
        field_filter_config=None,
        mode=None,
        max_targets=None,
        start_from=None,
        batch_size=None,
        overlap_days=None,
        *args,
        **kwargs,
    ):
        """
        初始化爬虫并加载依赖。

        :param pdb_id: 指定单个结构 ID
        :type pdb_id: str or None
        :param output_filename: 自定义输出文件名
        :type output_filename: str or None
        :param field_filter_config: 字段过滤配置路径
        :type field_filter_config: str or None
        :param mode: 运行模式，full 或 incremental
        :type mode: str or None
        :param max_targets: 最大结构数量
        :type max_targets: int or None
        :param start_from: Search API 起始偏移
        :type start_from: int or None
        :param batch_size: Search API 每批数量
        :type batch_size: int or None
        :param overlap_days: 增量模式向前重叠天数
        :type overlap_days: int or None
        """
        super().__init__(*args, **kwargs)

        # 设置运行模式，当前为 "full"

        self.mode = (mode or "full").lower()
        if self.mode not in {"full", "incremental"}:
            self.mode = "full"

        # - `max_targets`：最大结构数量
        # - `batch_size`：每批数量
        # - `start_from`：起始偏移
        # - `overlap_days`：增量模式重叠天数

        self.max_targets = (
            int(max_targets) if max_targets else self.DEFAULT_MAX_TARGETS
        )
        self.batch_size = (
            int(batch_size)
            if batch_size
            else min(self.DEFAULT_BATCH_SIZE, self.max_targets)
        )
        self.start_from = int(start_from) if start_from else 0
        self.overlap_days = int(overlap_days) if overlap_days else 1

        # 初始化数据库连接

        self.mongo_manager = MongoDBManager()
        self.increment_collection = self.mongo_manager.db[self.INCREMENT_COLLECTION]
        self.redis_conn = RedisManager().get_connection()

        # 初始化各个服务模块

        self.request_builder = RequestBuilder(self.SEARCH_API, self.API_ENDPOINTS)
        self.data_parser = DataParser()
        self.file_downloader = FileDownloader(self.logger, timeout=5, max_retries=5)
        self.revision_state = RevisionState(
            collection=self.increment_collection,
            redis_conn=self.redis_conn,
            doc_id=self.INCREMENT_DOC_ID,
            redis_hash=self.REDIS_REVISION_HASH,
            ttl_seconds=self.REDIS_TTL_SECONDS,
            overlap_days=self.overlap_days,
        )

        # 获取增量模式的起始日期

        self.increment_start_date = self.revision_state.increment_start

        # 初始化运行状态变量

        self.search_finished = False
        self.total_enqueued = 0
        self.entry_queue: deque[str] = deque()
        self.entry_contexts: Dict[str, Dict[str, Any]] = {}
        self.saved_count = 0
        self.duplicate_skipped = 0
        self.file_audit: Dict[str, Dict[str, Any]] = {}

    def start_requests(self):
        """
        Scrapy 入口：调度 Search API 请求。

        :return: Search 请求序列
        :rtype: Generator[scrapy.Request, None, None]
        """
        # 构造 Search API 请求，返回 scrapy.Request
        yield from self._request_search(self.start_from)

    def parse(self, response):
        """
        框架入口占位，复用 start_requests 逻辑。

        :param response: 框架虚拟响应
        :type response: scrapy.http.Response
        """
        # 复用 start_requests，再次返回 Search Request

        yield from self.start_requests()

    def _request_search(self, start):
        """
        构造 Search API 请求。

        :param start: 分页起点
        :type start: int
        :return: Search 请求
        :rtype: Generator[scrapy.Request, None, None]
        """
        remaining = max(self.max_targets - self.total_enqueued, 0)
        if remaining <= 0:
            return

        rows = min(self.batch_size, remaining)

        # 构造 Search API 请求，返回 scrapy.Request

        yield self.request_builder.build_search_request(
            start=start,
            rows=rows,
            mode=self.mode,
            increment_start=self.increment_start_date,
            logger=self.logger,
            callback=self.parse_search,
        )

    def parse_search(self, response):
        """
        解析 Search API 结果并调度 Entry。

        :param response: Search 响应
        :type response: scrapy.http.Response
        :return: None（通过 yield 产生请求）
        :rtype: None
        """

        # 检查响应状态码。

        if response.status != 200:
            self.logger.error("Search API 返回异常 %s, body=%s", response.status, response.text)
            return None

        # 解析 JSON，如果没有结果则标记完成。

        data = self.data_parser.parse(response, self.logger)
        result_set = data.get("result_set", [])
        if not result_set:
            self.search_finished = True
            return None

        # 解析结果集，注册 Entry 上下文并发起请求。

        for entry in result_set:
            if self.total_enqueued >= self.max_targets:
                break
            pdb_id = entry.get("identifier")
            if not pdb_id:
                continue
            self.total_enqueued += 1
            yield from self._schedule_entry(pdb_id)

        # 如果未达到上限，继续请求下一页。

        if self.total_enqueued < self.max_targets:
            next_start = response.meta.get("start", 0) + len(result_set)
            yield from self._request_search(next_start)
        else:
            self.search_finished = True

    def _schedule_entry(self, pdb_id):
        """
        注册 Entry 上下文并发起请求。

        :param pdb_id: 结构 ID
        :type pdb_id: str
        :return: Entry/资源预探测请求
        :rtype: Generator[scrapy.Request, None, None]
        """

        # 标准化 PDB ID，检查是否已处理。

        pdb_id = pdb_id.upper()
        if pdb_id in self.entry_contexts:
            return None

        # 构建文件列表，创建 Entry 上下文并缓存。

        bundle = self.file_downloader.build_initial_bundle(pdb_id)
        context = EntryContext.from_bundle(pdb_id, bundle)
        self.entry_contexts[pdb_id] = context

        # 构造 Entry API 请求，返回 scrapy.Request

        yield self.request_builder.build_api_request(
            "entry",
            pdb_id,
            callback=self.parse_entry,
            errback=self._entry_errback,
            meta={"pdb_id": pdb_id},
        )


    def parse_entry(self, response):
        """
        解析 Entry 数据并调度实体。

        :param response: Entry 响应
        :type response: scrapy.http.Response
        :return: None（通过 yield 产生请求）
        :rtype: None
        """

        # 获取上下文，如果不存在则返回

        pdb_id = response.meta["pdb_id"]
        context = self.entry_contexts.get(pdb_id)
        if not context:
            return None

        # 解析 JSON，失败则清理上下文。

        data = self.data_parser.parse(response, self.logger)
        if not data:
            self._cleanup_entry(pdb_id)
            return None

        # 提取 rcsb_id 和 properties，进行字段规范化。

        context["result"]["rcsb_id"] = data.get("rcsb_id")
        properties = {k: v for k, v in data.items() if k != "rcsb_id"}
        properties = self.data_parser.normalize(properties)
        context["result"]["properties"] = properties

        # 提取 revision_date，更新运行期最大 revision。

        revision_date = (data.get("rcsb_accession_info") or {}).get("revision_date")
        context["revision_date"] = revision_date
        self.revision_state.update_run_max(revision_date)

        # 检查是否有验证报告，处理验证文件。
        has_validation_report = "pdbx_vrpt_summary" in data
        self.file_downloader.handle_validation_assets(context, has_validation_report)

        # 增量模式下检查是否重复，如果重复则跳过。

        if self.mode == "incremental" and self.revision_state.is_duplicate(pdb_id, revision_date):
            self.duplicate_skipped += 1
            self.logger.info(
                "⏭️ 跳过未更新结构 (revision: %s, total_skipped=%d)",
                revision_date,
                self.duplicate_skipped,
            )
            self._cleanup_entry(pdb_id)
            return None

        # 提取实体 ID 列表，设置待处理计数器。

        container = data.get("rcsb_entry_container_identifiers", {})
        entity_ids = {
            "polymer_entity": container.get("polymer_entity_ids", []) or [],
            "nonpolymer_entity": container.get("nonpolymer_entity_ids", []) or [],
            "branched_entity": container.get("branched_entity_ids", []) or [],
        }

        context["pending"]["entity"] = sum(len(ids) for ids in entity_ids.values())

        # 调度 Assembly API 请求。
        context["pending"]["assembly"] = 1
        yield self.request_builder.build_api_request(
            "assembly",
            pdb_id,
            DEFAULT_ASSEMBLY_ID,
            callback=self._parse_assembly,
            errback=self._assembly_errback,
            meta={"pdb_id": pdb_id},
        )

        # 如果没有实体，直接进入后续阶段。

        if context["pending"]["entity"] == 0:
            followups = self._after_entities_complete(pdb_id)
            if followups:
                yield from followups
            return None

        # 调度所有实体 API 请求。

        for entity_type, ids in entity_ids.items():
            for entity_id in ids:
                # 构造实体 API 请求，返回 scrapy.Request
                yield self.request_builder.build_api_request(
                    entity_type,
                    pdb_id,
                    entity_id,
                    callback=self._parse_entity,
                    errback=self._entity_errback,
                    meta={"pdb_id": pdb_id, "entity_type": entity_type},
                )

    def _parse_entity(self, response):
        """
        解析实体数据并写入结果，检查实体阶段是否完成。

        :param response: 实体响应
        :type response: scrapy.http.Response
        :return: None（通过 yield 产生请求）
        :rtype: None
        """

        # 获取上下文和实体类型。

        pdb_id = response.meta["pdb_id"]
        entity_type = response.meta["entity_type"]
        context = self.entry_contexts.get(pdb_id)
        if not context:
            return None

        # 解析并规范化实体数据，追加到对应列表。

        data = self.data_parser.parse(response, self.logger)
        if data:
            normalized = self.data_parser.normalize(data)
            alias = self._entity_alias(entity_type)
            context["result"][alias].append(normalized)

        # 递减计数器，如果还有未完成的实体则返回。

        context["pending"]["entity"] -= 1
        if context["pending"]["entity"] > 0:
            return None

        # 所有实体完成，调度 ChemComp/DrugBank

        followups = self._after_entities_complete(pdb_id)
        if followups:
            yield from followups
        return None

    def _parse_assembly(self, response):
        """
        解析 Assembly 数据并写入结果，检查 Assembly 阶段是否完成。

        :param response: Assembly 响应
        :type response: scrapy.http.Response
        :return: None（通过 yield 产生请求）
        :rtype: None
        """
        pdb_id = response.meta["pdb_id"]
        context = self.entry_contexts.get(pdb_id)
        if not context:
            return None

        # 解析并规范化 Assembly 数据。

        data = self.data_parser.parse(response, self.logger)
        if data:
            normalized = self.data_parser.normalize(data)
            context["assembly_data"] = normalized

        # 递减计数器，检查是否可以保存。

        context["pending"]["assembly"] = max(0, context["pending"]["assembly"] - 1)
        followups = self._maybe_finalize(pdb_id)
        if followups:
            yield from followups
        return None

    def _after_entities_complete(self, pdb_id):
        """
        实体阶段完结 → 整理出要批量补的 ID（comp_id/drugbank_id） → 一次性发 ChemComp/DrugBank 请求 → 如果没有要补的，直接进入收尾

        :param pdb_id: 结构 ID
        :type pdb_id: str
        :return: 后续请求
        :rtype: Generator[scrapy.Request, None, None] or None
        """
        context = self.entry_contexts.get(pdb_id)
        if not context:
            return None

        # 从实体中收集 comp_id 与 drugbank_id
        comp_ids = set()
        drugbank_ids = set()

        for entity in context["result"]["polymer_entities"]:
            for seq in entity.get("entity_poly_seq") or []:
                mon_id = seq.get("mon_id")
                if mon_id:
                    comp_ids.add(mon_id)

        # 从 nonpolymer_entities 中收集 comp_id 和 drugbank_id。

        for entity in context["result"]["nonpolymer_entities"]:
            container = entity.get(
                "rcsb_nonpolymer_entity_container_identifier"
            ) or {}
            comp_id = container.get("comp_id")
            if comp_id:
                comp_ids.add(comp_id)
            db_id = container.get("drugbank_id")
            if isinstance(db_id, list):
                drugbank_ids.update(filter(None, db_id))
            elif db_id:
                drugbank_ids.add(db_id)

        for entity in context["result"]["branched_entities"]:
            for scheme in entity.get("pdbx_branch_scheme") or []:
                mon_id = scheme.get("mon_id")
                if mon_id:
                    comp_ids.add(mon_id)

        # 排序并设置待处理计数器。

        comp_ids = sorted(comp_ids)
        drugbank_ids = sorted(drugbank_ids)

        context["comp_ids"] = comp_ids
        context["drugbank_ids"] = drugbank_ids
        context["pending"]["comp"] = 1 if comp_ids else 0
        context["pending"]["drugbank"] = 1 if drugbank_ids else 0

        # 批量调度 ChemComp 请求

        if comp_ids:
            yield self.request_builder.build_api_request(
                "chemcomp",
                ids=comp_ids,
                callback=self._parse_comp,
                errback=self._comp_errback,
                meta={"pdb_id": pdb_id, "comp_ids": comp_ids},
            )

        # 批量调度 DrugBank 请求

        if drugbank_ids:
            yield self.request_builder.build_api_request(
                "drugbank",
                ids=drugbank_ids,
                callback=self._parse_drugbank,
                errback=self._drugbank_errback,
                meta={"pdb_id": pdb_id, "drugbank_ids": drugbank_ids},
            )

        # 如果没有 comp 和 drugbank，直接检查是否可以保存

        followups = self._maybe_finalize(pdb_id)
        if followups:
            yield from followups

    def _maybe_finalize(self, pdb_id):
        """
        检查所有阶段是否完成，若完成则保存。

        :param pdb_id: 结构 ID
        :type pdb_id: str
        :return: 保存结果的迭代器
        :rtype: Generator or None
        """
        context = self.entry_contexts.get(pdb_id)
        if not context:
            return None

        # 检查所有计数器是否归零，如果都完成则保存结果。

        pending = context.get("pending", {})
        if (
            pending.get("entity", 0) == 0
            and pending.get("comp", 0) == 0
            and pending.get("drugbank", 0) == 0
            and pending.get("assembly", 0) == 0
        ):
            return self._save_result(context)
        return None

    def _parse_comp(self, response):
        """
        解析 ChemComp 数据，检查阶段是否完成。

        :param response: ChemComp 响应
        :type response: scrapy.http.Response
        :return: None（通过 yield 产生请求）
        :rtype: None
        """
        pdb_id = response.meta["pdb_id"]
        context = self.entry_contexts.get(pdb_id)
        if not context:
            return None

        data = self.data_parser.parse(response, self.logger)

        # 处理批量响应，提取每个 comp_id 对应的数据。

        comp_ids = response.meta.get("comp_ids")
        if comp_ids:
            items = data if isinstance(data, list) else ([data] if data else [])
            remaining = list(comp_ids)
            for item in items:
                if not item:
                    continue
                comp_id = (
                    item.get("rcsb_id")
                    or item.get("chem_comp", {}).get("id")
                    or (remaining.pop(0) if remaining else None)
                )
                if not comp_id:
                    continue
                normalized = self.data_parser.normalize(item)
                normalized["comp_id"] = comp_id
                context["comp_data"][comp_id] = normalized
                if comp_id in remaining:
                    remaining.remove(comp_id)
            if remaining:
                self.logger.warning("ChemComp 批量响应缺少 ID：%s", ",".join(remaining))

            # 递减计数器，检查是否可以保存。

            context["pending"]["comp"] = max(0, context["pending"]["comp"] - 1)
        else:
            comp_id = response.meta["comp_id"]
            if data:
                normalized = self.data_parser.normalize(data)
                normalized["comp_id"] = comp_id
                context["comp_data"][comp_id] = normalized
            context["pending"]["comp"] -= 1

        followups = self._maybe_finalize(pdb_id)
        if followups:
            yield from followups
        return None

    def _parse_drugbank(self, response):
        """
        解析 DrugBank 数据，检查阶段是否完成。

        :param response: DrugBank 响应
        :type response: scrapy.http.Response
        :return: None（通过 yield 产生请求）
        :rtype: None
        """
        pdb_id = response.meta["pdb_id"]
        context = self.entry_contexts.get(pdb_id)
        if not context:
            return None

        data = self.data_parser.parse(response, self.logger)
        drugbank_ids = response.meta.get("drugbank_ids")
        if drugbank_ids:
            items = data if isinstance(data, list) else ([data] if data else [])
            remaining = list(drugbank_ids)
            for item in items:
                if not item:
                    continue
                drugbank_id = (
                    item.get("rcsb_id")
                    or item.get("identifier")
                    or (remaining.pop(0) if remaining else None)
                )
                if not drugbank_id:
                    continue
                normalized = self.data_parser.normalize(item)
                normalized["comp_id"] = drugbank_id
                context["drugbank_data"][drugbank_id] = normalized
                if drugbank_id in remaining:
                    remaining.remove(drugbank_id)
            if remaining:
                self.logger.warning("DrugBank 批量响应缺少 ID：%s", ",".join(remaining))
            context["pending"]["drugbank"] = max(0, context["pending"]["drugbank"] - 1)
        else:
            drugbank_id = response.meta["drugbank_id"]
            if data:
                normalized = self.data_parser.normalize(data)
                normalized["comp_id"] = drugbank_id
                context["drugbank_data"][drugbank_id] = normalized
            context["pending"]["drugbank"] -= 1

        followups = self._maybe_finalize(pdb_id)
        if followups:
            yield from followups
        return None

    def _save_result(self, context):
        """
        序列化结果、产出 Item 并更新增量标记。

        :param context: Entry 上下文
        :type context: EntryContext
        :return: Item 迭代器
        :rtype: Generator[RcsbAllApiItem, None, None]
        """

        # 如果前面流程没有拿到 `rcsb_id`，视为失败直接清理；

        if not context["result"].get("rcsb_id"):
            self._cleanup_entry(context["pdb_id"])
            return None

        # 使用 EntryContext.to_item() 方法转换，避免重复代码

        item = context.to_item()

        # 把文件探测结果记录下来，后面 `closed()` 里会集中输出哪些文件缺失或失败。

        audit_entry = context.get("file_audit", {})
        self.file_audit[item["pdb_id"]] = audit_entry
        labels = {
            "cif_file": "CIF 文件",
            "structure_image": "结构图片",
            "validation_image": "报告图片",
            "validation_pdf": "报告 PDF",
        }
        for field, label in labels.items():
            data = audit_entry.get(field, {})
            if not data or data.get("available"):
                continue
            reason = data.get("reason") or "未知原因"
            if data.get("missing") and field != "cif_file":
                self.logger.info("ℹ️ %s %s 不存在：%s", item["pdb_id"], label, reason)
            else:
                self.logger.error("❌ %s %s 获取失败：%s", item["pdb_id"], label, reason)

        # 把当前结构的 revision 写入 Redis，用于增量模式的重复判断。

        revision = context.get("revision_date")
        if revision:
            self.revision_state.persist_revision(context["pdb_id"], revision)

        # 更新统计、日志提示、清理上下文，并把最终的 Item 交给 Pipeline。

        self.saved_count += 1
        self.logger.info("✅ 已保存 %d 条结构 (revision: %s)", self.saved_count, revision)
        self._cleanup_entry(context["pdb_id"])
        yield item

    def _cleanup_entry(self, pdb_id):
        """
        清理缓存的 Entry 上下文。

        :param pdb_id: 结构 ID
        :type pdb_id: str
        :return: None
        :rtype: None
        """
        self.entry_contexts.pop(pdb_id, None)
        return None

    def closed(self, reason):
        """
        Scrapy 关闭钩子，写回增量游标。

        :param reason: 退出原因
        :type reason: str
        :return: None
        :rtype: None
        """

        # 增量模式下，将最大 revision 写回 MongoDB。

        if self.mode == "incremental":
            self.revision_state.flush()

        # 记录运行统计信息。

        self.logger.info(
            "📊 本次运行保存 %d 条，判重跳过 %d 条 (mode=%s)",
            self.saved_count,
            self.duplicate_skipped,
            self.mode,
        )

        # 统计并输出文件获取失败的情况。

        if self.file_audit:
            buckets = {
                "结构图片缺失": [],
                "结构图片获取失败": [],
                "报告图片缺失": [],
                "报告图片获取失败": [],
                "报告 PDF 缺失": [],
                "报告 PDF 获取失败": [],
                "CIF 下载失败": [],
            }
            for pdb_id, entry in self.file_audit.items():
                struct = entry.get("structure_image", {})
                if struct.get("missing"):
                    buckets["结构图片缺失"].append(f"{pdb_id}({struct.get('reason')})")
                elif struct and not struct.get("available"):
                    buckets["结构图片获取失败"].append(f"{pdb_id}({struct.get('reason')})")

                validation = entry.get("validation_image", {})
                if validation.get("missing"):
                    buckets["报告图片缺失"].append(f"{pdb_id}({validation.get('reason')})")
                elif validation and not validation.get("available"):
                    buckets["报告图片获取失败"].append(f"{pdb_id}({validation.get('reason')})")

                validation_pdf = entry.get("validation_pdf", {})
                if validation_pdf.get("missing"):
                    buckets["报告 PDF 缺失"].append(f"{pdb_id}({validation_pdf.get('reason')})")
                elif validation_pdf and not validation_pdf.get("available"):
                    buckets["报告 PDF 获取失败"].append(f"{pdb_id}({validation_pdf.get('reason')})")

                cif_result = entry.get("cif_file", {})
                if cif_result and not cif_result.get("available"):
                    buckets["CIF 下载失败"].append(f"{pdb_id}({cif_result.get('reason')})")

            for title, items in buckets.items():
                if items:
                    self.logger.info("📊 %s %d 条：%s", title, len(items), ", ".join(items))
        return None

    def _entity_alias(self, entity_type):
        """
        实体类型与结果键映射。

        :param entity_type: 实体类型
        :type entity_type: str
        :return: 结果字段名
        :rtype: str
        """

        # 将实体 API 的类型字符串转换成 `context["result"]` 里对应的列表键名。避免在 `_parse_entity` 中写一堆 if/else，后续如果新增实体类型也能集中维护。

        return {
            "polymer_entity": "polymer_entities",
            "nonpolymer_entity": "nonpolymer_entities",
            "branched_entity": "branched_entities",
        }[entity_type]


    def _entry_errback(self, failure):
        """
        Entry API 失败时直接清理上下文并结束，防止卡死在半流程。

        :param failure: 失败对象
        :type failure: scrapy.Failure
        :return: None
        :rtype: None
        """
        pdb_id = failure.request.meta.get("pdb_id")
        self.logger.error("Entry 请求失败: %s", failure.value)
        self._cleanup_entry(pdb_id)
        return None

    def _entity_errback(self, failure):
        """
        实体请求失败时，同样递减计数器，如果所有实体都已结束（成功或失败），就继续走 ChemComp/DrugBank 的阶段，保证流程不中断。

        :param failure: 失败对象
        :type failure: scrapy.Failure
        :return: None（通过 yield 产生请求）
        :rtype: None
        """
        pdb_id = failure.request.meta.get("pdb_id")
        entity_type = failure.request.meta.get("entity_type")
        self.logger.error("Entity 请求失败 (%s): %s", entity_type, failure.value)
        context = self.entry_contexts.get(pdb_id)
        if not context:
            return None
        # 实体阶段计数器递减
        context["pending"]["entity"] -= 1
        if context["pending"]["entity"] > 0:
            return None
        # 所有实体完成，调度 ChemComp/DrugBank
        followups = self._after_entities_complete(pdb_id)
        if followups:
            for req in followups:
                yield req
        return None

    def _comp_errback(self, failure):
        """
        某个 ChemComp/DrugBank 批量请求失败时，记录日志、递减计数，并调用 `_maybe_finalize` 检查是否还能继续保存结果。这样即便一个批次失败，也能让其他阶段正常结束。

        :param failure: 失败对象
        :type failure: scrapy.Failure
        :return: None（通过 yield 产生请求）
        :rtype: None
        """
        pdb_id = failure.request.meta.get("pdb_id")
        comp_ids = failure.request.meta.get("comp_ids")
        if comp_ids:
            label = ",".join(comp_ids)
        else:
            label = failure.request.meta.get("comp_id")
        self.logger.error("ChemComp 请求失败 (%s): %s", label, failure.value)
        context = self.entry_contexts.get(pdb_id)
        if not context:
            return None
        # ChemComp 阶段计数器递减
        context["pending"]["comp"] = max(0, context["pending"]["comp"] - 1)
        followups = self._maybe_finalize(pdb_id)
        if followups:
            for req in followups:
                yield req
        return None

    def _drugbank_errback(self, failure):
        """
        DrugBank 请求错误处理。具体同上

        :param failure: 失败对象
        :type failure: scrapy.Failure
        :return: None（通过 yield 产生请求）
        :rtype: None
        """
        pdb_id = failure.request.meta.get("pdb_id")
        drugbank_ids = failure.request.meta.get("drugbank_ids")
        if drugbank_ids:
            label = ",".join(drugbank_ids)
        else:
            label = failure.request.meta.get("drugbank_id")
        self.logger.error("DrugBank 请求失败 (%s): %s", label, failure.value)
        context = self.entry_contexts.get(pdb_id)
        if not context:
            return None
        # DrugBank 阶段计数器递减
        context["pending"]["drugbank"] = max(
            0, context["pending"]["drugbank"] - 1
        )
        followups = self._maybe_finalize(pdb_id)
        if followups:
            for req in followups:
                yield req
        return None

    def _assembly_errback(self, failure):
        """
        把 assembly 数据记为 None，依旧让后续流程能继续。因为没有 assembly 不影响其它数据保存，只是在最终 Item 中缺少这一块。

        :param failure: 失败对象
        :type failure: scrapy.Failure
        :return: None（通过 yield 产生请求）
        :rtype: None
        """
        pdb_id = failure.request.meta.get("pdb_id")
        self.logger.info("Assembly 请求失败: %s，写入空值继续", failure.value)
        context = self.entry_contexts.get(pdb_id)
        if not context:
            return None
        context["assembly_data"] = None
        # Assembly 阶段计数器递减
        context["pending"]["assembly"] -= 1
        followups = self._maybe_finalize(pdb_id)
        if followups:
            for req in followups:
                yield req
        return None