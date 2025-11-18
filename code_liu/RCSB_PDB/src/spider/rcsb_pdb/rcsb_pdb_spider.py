# -*- coding: utf-8 -*-
"""
RCSB PDB 爬虫 - 支持单条拉取、批量全量、增量更新
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import scrapy

from .field_filter import FieldFilter
from src.items.other.rcsb_pdb_item import RcsbAllApiItem
from src.utils.mongodb_manager import MongoDBManager
from src.utils.redis_manager import RedisManager


class RcsbAllApiSpider(scrapy.Spider):
    """提取完整 CoreEntry 数据的爬虫"""

    name = "rcsb_all_api"
    allowed_domains = ["data.rcsb.org", "search.rcsb.org", "rcsb.org"]
    start_urls = ["https://www.rcsb.org/"]

    # ========== 配置区域 ==========
    OUTPUT_FILENAME = "data_real_all.json"
    FIELD_FILTER_CONFIG = None  # 字段过滤配置文件路径
    DEFAULT_MAX_TARGETS = 200
    DEFAULT_BATCH_SIZE = 50
    INCREMENT_COLLECTION = "rcsb_increment_state"
    INCREMENT_DOC_ID = "rcsb_all_api"
    REDIS_REVISION_HASH = "rcsb_all_api:revision"
    REDIS_TTL_SECONDS = 60 * 60 * 24 * 60  # 60 天
    # =============================

    SEARCH_API = "https://search.rcsb.org/rcsbsearch/v2/query"
    API_BASE = "https://data.rcsb.org/rest/v1/core"
    API_ENDPOINTS = {
        "entry": f"{API_BASE}/entry",
        "polymer_entity": f"{API_BASE}/polymer_entity",
        "nonpolymer_entity": f"{API_BASE}/nonpolymer_entity",
        "branched_entity": f"{API_BASE}/branched_entity",
        "chemcomp": f"{API_BASE}/chemcomp",
        "drugbank": f"{API_BASE}/drugbank",
    }

    SECTION_MAP = {
        "polymer_entity": "CorePolymerEntity",
        "nonpolymer_entity": "CoreNonpolymerEntity",
        "branched_entity": "CoreBranchedEntity",
        "chemcomp": "CoreChemComp",
        "drugbank": "CoreDrugbank",
    }

    custom_settings = {
        "ITEM_PIPELINES": {
            "src.pipelines.file_download_pipeline.FileDownloadPipeline": 200,
            "src.pipelines.file_replacement_pipeline.FileReplacementPipeline": 300,
            "src.pipelines.storage.rcsb_pdb_pipeline.RcsbPdbPipeline": 400,
        },
        "LOG_LEVEL": "INFO",
    }

    def __init__(
        self,
        pdb_id: Optional[str] = None,
        output_filename: Optional[str] = None,
        field_filter_config: Optional[str] = None,
        mode: Optional[str] = None,
        max_targets: Optional[int] = None,
        start_from: Optional[int] = None,
        batch_size: Optional[int] = None,
        overlap_days: Optional[int] = None,
        *args,
        **kwargs,
    ):
        """
        初始化 RCSB 全量爬虫。

        参数:
            pdb_id (Optional[str]): 手动指定的 PDB ID（单条调试使用）。
            output_filename (Optional[str]): 单条调试模式下的输出文件名。
            field_filter_config (Optional[str]): 字段过滤配置文件路径。
            mode (Optional[str]): 运行模式，支持 full 与 incremental。
            max_targets (Optional[int]): 本次任务抓取的最大结构数。
            start_from (Optional[int]): Search API 分页起点。
            batch_size (Optional[int]): Search API 每批请求的条数。
            overlap_days (Optional[int]): 增量模式向前重叠的天数。
            args: 透传给基类的其余位置参数。
            kwargs: 透传给基类的其余关键字参数。
        """
        super().__init__(*args, **kwargs)

        # ====== 运行模式 ======
        self.manual_ids: List[str] = [pdb_id.upper()] if pdb_id else []
        self.manual_run = bool(self.manual_ids)

        self.mode = (mode or "full").lower()
        if self.mode not in {"full", "incremental"}:
            self.mode = "full"

        self.max_targets = int(max_targets) if max_targets else self.DEFAULT_MAX_TARGETS
        self.batch_size = int(batch_size) if batch_size else min(self.DEFAULT_BATCH_SIZE, self.max_targets)
        self.start_from = int(start_from) if start_from else 0
        self.overlap_days = int(overlap_days) if overlap_days else 1

        # ====== 输出路径 ======
        self.output_dir = Path(__file__).resolve().parent / "inhance"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.user_output_filename = output_filename or self.OUTPUT_FILENAME

        # ====== 字段过滤器 ======
        config_path = field_filter_config if field_filter_config is not None else self.FIELD_FILTER_CONFIG
        if config_path:
            cfg_path = Path(config_path)
            if not cfg_path.is_absolute():
                cfg_path = Path(__file__).resolve().parent / cfg_path
            config_path = str(cfg_path)
        self.field_filter = FieldFilter(config_path)

        # ====== Mongo / Redis 依赖 ======
        self.mongo_manager = MongoDBManager()
        self.increment_collection = self.mongo_manager.db[self.INCREMENT_COLLECTION]
        self.redis_conn = RedisManager().get_connection()

        # ====== 增量游标 ======
        if self.mode == "incremental" and not self.manual_run:
            self.last_revision_cursor = self._load_increment_cursor()
            self.increment_start_date = self._compute_increment_start(self.last_revision_cursor)
            self.run_max_revision = self.last_revision_cursor
        else:
            self.last_revision_cursor = None
            self.increment_start_date = None
            self.run_max_revision = None

        # ====== 运行状态 ======
        self.search_finished = False
        self.total_enqueued = 0
        self.entry_contexts: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------ #
    # 入口函数
    # ------------------------------------------------------------------ #
    def parse(self, response):
        """
        Scrapy 默认入口。

        参数:
            response (Response): 占位响应（来源于 start_urls）。
        返回:
            Generator[scrapy.Request, None, None]: 后续将要调度的请求。
        """
        if self.manual_run:
            for pdb_id in self.manual_ids:
                yield from self._schedule_entry(pdb_id, manual=True)
            return

        yield from self._request_search(self.start_from)

    # ------------------------------------------------------------------ #
    # Search API
    # ------------------------------------------------------------------ #
    def _request_search(self, start: int) -> Generator[scrapy.Request, None, None]:
        """
        构造 Search API 请求并分页拉取 PDB ID。

        参数:
            start (int): Search API 的分页起始位置。
        返回:
            Generator[scrapy.Request, None, None]: Search API 请求生成器。
        """
        remaining = max(self.max_targets - self.total_enqueued, 0)
        if remaining <= 0:
            return

        rows = min(self.batch_size, remaining)
        body = self._build_search_body(start=start, rows=rows)
        yield scrapy.Request(
            url=self.SEARCH_API,
            method="POST",
            body=json.dumps(body),
            headers={"Content-Type": "application/json"},
            callback=self.parse_search,
            meta={"start": start, "rows": rows},
        )

    def parse_search(self, response):
        """
        解析 Search API 响应并调度 Entry 请求。

        参数:
            response (Response): Search API 的响应对象。
        返回:
            Generator[scrapy.Request, None, None]: 后续 Entry 请求。
        """
        data = self._parse_json(response)
        result_set = data.get("result_set", [])
        if not result_set:
            self.search_finished = True
            return

        for entry in result_set:
            if self.total_enqueued >= self.max_targets:
                break
            pdb_id = entry.get("identifier")
            if not pdb_id:
                continue
            self.total_enqueued += 1
            yield from self._schedule_entry(pdb_id)

        if self.total_enqueued < self.max_targets:
            next_start = response.meta.get("start", 0) + len(result_set)
            yield from self._request_search(next_start)
        else:
            self.search_finished = True

    def _build_search_body(self, start: int, rows: int) -> Dict[str, Any]:
        """
        生成 Search API 的请求体。

        参数:
            start (int): 分页起点。
            rows (int): 单批请求条数。
        返回:
            Dict[str, Any]: 可直接用于 POST 的 JSON 结构。
        """
        query = {
            "type": "terminal",
            "service": "text",
            "parameters": {"attribute": "rcsb_id", "operator": "exists"},
        }

        request_options: Dict[str, Any] = {
            "paginate": {"start": start, "rows": rows},
            "scoring_strategy": "combined",
            "sort": [{"sort_by": "rcsb_accession_info.revision_date", "direction": "asc"}],
        }

        if self.increment_start_date:
            request_options["filters"] = [
                {
                    "type": "date",
                    "service": "text",
                    "parameters": {
                        "attribute": "rcsb_accession_info.revision_date",
                        "operator": "greater_or_equal",
                        "value": self.increment_start_date,
                    },
                }
            ]

        return {"query": query, "return_type": "entry", "request_options": request_options}

    # ------------------------------------------------------------------ #
    # Entry 处理
    # ------------------------------------------------------------------ #
    def _schedule_entry(self, pdb_id: str, manual: bool = False) -> Generator[scrapy.Request, None, None]:
        """
        注册单个 PDB ID 的 Entry 请求与上下文。

        参数:
            pdb_id (str): 结构 ID。
            manual (bool): 是否来自手动模式。
        返回:
            Generator[scrapy.Request, None, None]: Entry API 请求。
        """
        pdb_id = pdb_id.upper()
        if pdb_id in self.entry_contexts:
            return

        context = self._create_entry_context(pdb_id, manual=manual)
        self.entry_contexts[pdb_id] = context

        url = f"{self.API_ENDPOINTS['entry']}/{pdb_id}"
        yield scrapy.Request(
            url=url,
            callback=self.parse_entry,
            meta={"pdb_id": pdb_id},
            errback=self._entry_errback,
        )

    def _create_entry_context(self, pdb_id: str, manual: bool = False) -> Dict[str, Any]:
        """
        初始化单个 PDB ID 的上下文信息。

        参数:
            pdb_id (str): 结构 ID。
            manual (bool): 是否来自手动模式。
        返回:
            Dict[str, Any]: 该结构的运行状态容器。
        """
        cif_url = f"https://files.rcsb.org/download/{pdb_id}.cif"
        validation_url = f"https://files.rcsb.org/validation/view/{pdb_id.lower()}_multipercentile_validation.png"
        return {
            "pdb_id": pdb_id,
            "result": {
                "rcsb_id": None,
                "properties": {},
                "polymer_entities": [],
                "nonpolymer_entities": [],
                "branched_entities": [],
                "chemcomp": [],
                "drugbank": [],
            },
            "pending": {"entity": 0, "comp": 0, "drugbank": 0},
            "comp_ids": set(),
            "drugbank_ids": set(),
            "comp_data": {},
            "drugbank_data": {},
            "revision_date": None,
            "output_path": self._resolve_output_path(pdb_id, manual=manual),
            "file_urls": [cif_url, validation_url],
        }

    def parse_entry(self, response):
        """
        解析 Entry API 响应并分发实体请求。

        参数:
            response (Response): Entry API 的响应对象。
        返回:
            Generator[scrapy.Request, None, None]: 后续实体或化合物请求。
        """
        pdb_id = response.meta["pdb_id"]
        context = self.entry_contexts.get(pdb_id)
        if not context:
            return

        data = self._parse_json(response)
        if not data:
            self._cleanup_entry(pdb_id)
            return

        context["result"]["rcsb_id"] = data.get("rcsb_id")

        properties = {k: v for k, v in data.items() if k != "rcsb_id"}
        context["result"]["properties"] = self.field_filter.filter_data(
            {"properties": properties},
            "CoreEntry",
        ).get("properties", properties)

        revision_date = (data.get("rcsb_accession_info") or {}).get("revision_date")
        context["revision_date"] = revision_date
        self._update_run_max_revision(revision_date)

        if self.mode == "incremental" and self._is_duplicate_revision(pdb_id, revision_date):
            self.logger.info("⏭️ 跳过未更新结构 %s (revision: %s)", pdb_id, revision_date)
            self._cleanup_entry(pdb_id)
            return

        container = data.get("rcsb_entry_container_identifiers", {})
        entity_ids = {
            "polymer_entity": container.get("polymer_entity_ids", []) or [],
            "nonpolymer_entity": container.get("nonpolymer_entity_ids", []) or [],
            "branched_entity": container.get("branched_entity_ids", []) or [],
        }

        context["pending"]["entity"] = sum(len(ids) for ids in entity_ids.values())

        if context["pending"]["entity"] == 0:
            followups = self._after_entities_complete(pdb_id)
            if followups:
                yield from followups
            return

        for entity_type, ids in entity_ids.items():
            for entity_id in ids:
                url = f"{self.API_ENDPOINTS[entity_type]}/{pdb_id}/{entity_id}"
                yield scrapy.Request(
                    url=url,
                    callback=self._parse_entity,
                    meta={"pdb_id": pdb_id, "entity_type": entity_type},
                    errback=self._entity_errback,
                )

    def _parse_entity(self, response):
        """
        解析实体接口响应并写入上下文。

        参数:
            response (Response): Polymer/Nonpolymer/Branched API 响应。
        返回:
            Generator[scrapy.Request, None, None]: 后续请求（若完成实体阶段）。
        """
        pdb_id = response.meta["pdb_id"]
        entity_type = response.meta["entity_type"]
        context = self.entry_contexts.get(pdb_id)
        if not context:
            return

        data = self._parse_json(response)
        if data:
            filtered = self.field_filter.filter_data(data, self.SECTION_MAP[entity_type])
            alias = self._entity_alias(entity_type)
            context["result"][alias].append(filtered)

        followups = self._check_entity_complete(pdb_id)
        if followups:
            yield from followups

    # ------------------------------------------------------------------ #
    # Entity -> ChemComp / DrugBank
    # ------------------------------------------------------------------ #
    def _check_entity_complete(self, pdb_id: str):
        """
        判断当前结构的实体请求是否全部返回。

        参数:
            pdb_id (str): 结构 ID。
        返回:
            Optional[Generator[scrapy.Request, None, None]]: 需要继续调度的请求。
        """
        context = self.entry_contexts.get(pdb_id)
        if not context:
            return None

        context["pending"]["entity"] -= 1
        if context["pending"]["entity"] > 0:
            return None
        return self._after_entities_complete(pdb_id)

    def _after_entities_complete(self, pdb_id: str):
        """
        实体阶段结束后的调度逻辑。

        参数:
            pdb_id (str): 结构 ID。
        返回:
            Optional[Generator[scrapy.Request, None, None]]: ChemComp/DrugBank 请求或保存动作。
        """
        context = self.entry_contexts.get(pdb_id)
        if not context:
            return None

        self._collect_comp_ids(context)
        if context["pending"]["comp"] == 0 and context["pending"]["drugbank"] == 0:
            return self._save_result(context)

        for comp_id in context["comp_ids"]:
            url = f"{self.API_ENDPOINTS['chemcomp']}/{comp_id}"
            yield scrapy.Request(
                url=url,
                callback=self._parse_comp,
                meta={"pdb_id": pdb_id, "comp_id": comp_id},
                errback=self._comp_errback,
            )

        for drugbank_id in context["drugbank_ids"]:
            url = f"{self.API_ENDPOINTS['drugbank']}/{drugbank_id}"
            yield scrapy.Request(
                url=url,
                callback=self._parse_drugbank,
                meta={"pdb_id": pdb_id, "drugbank_id": drugbank_id},
                errback=self._drugbank_errback,
            )

    def _collect_comp_ids(self, context: Dict[str, Any]):
        """
        从实体结果中收集 ChemComp 与 DrugBank 的 comp_id。

        参数:
            context (Dict[str, Any]): 结构运行上下文。
        """
        comp_ids = set()
        drugbank_ids = set()

        for entity in context["result"]["polymer_entities"]:
            for seq in entity.get("entity_poly_seq") or []:
                mon_id = seq.get("mon_id")
                if mon_id:
                    comp_ids.add(mon_id)

        for entity in context["result"]["nonpolymer_entities"]:
            container = entity.get("rcsb_nonpolymer_entity_container_identifier") or {}
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

        context["comp_ids"] = comp_ids
        context["drugbank_ids"] = drugbank_ids
        context["pending"]["comp"] = len(comp_ids)
        context["pending"]["drugbank"] = len(drugbank_ids)

    def _parse_comp(self, response):
        """
        解析 ChemComp 响应并记录结果。

        参数:
            response (Response): ChemComp API 响应。
        返回:
            Generator[scrapy.Request, None, None]: 当 ChemComp 队列完成时的后续操作。
        """
        pdb_id = response.meta["pdb_id"]
        comp_id = response.meta["comp_id"]
        context = self.entry_contexts.get(pdb_id)
        if not context:
            return

        data = self._parse_json(response)
        if data:
            filtered = self.field_filter.filter_data(data, "CoreChemComp")
            filtered["comp_id"] = comp_id
            context["comp_data"][comp_id] = filtered

        followups = self._check_comp_complete(pdb_id)
        if followups:
            yield from followups

    def _parse_drugbank(self, response):
        """
        解析 DrugBank 响应并记录结果。

        参数:
            response (Response): DrugBank API 响应。
        返回:
            Generator[scrapy.Request, None, None]: 当 DrugBank 队列完成时的后续操作。
        """
        pdb_id = response.meta["pdb_id"]
        drugbank_id = response.meta["drugbank_id"]
        context = self.entry_contexts.get(pdb_id)
        if not context:
            return

        data = self._parse_json(response)
        if data:
            filtered = self.field_filter.filter_data(data, "CoreDrugbank")
            filtered["comp_id"] = drugbank_id
            context["drugbank_data"][drugbank_id] = filtered

        followups = self._check_drugbank_complete(pdb_id)
        if followups:
            yield from followups

    def _check_comp_complete(self, pdb_id: str):
        """
        ChemComp 请求完成度检查。

        参数:
            pdb_id (str): 结构 ID。
        返回:
            Optional[Generator[scrapy.Request, None, None]]: 队列完成时触发的保存动作。
        """
        context = self.entry_contexts.get(pdb_id)
        if not context:
            return None

        context["pending"]["comp"] -= 1
        if context["pending"]["comp"] == 0 and context["pending"]["drugbank"] == 0:
            return self._save_result(context)
        return None

    def _check_drugbank_complete(self, pdb_id: str):
        """
        DrugBank 请求完成度检查。

        参数:
            pdb_id (str): 结构 ID。
        返回:
            Optional[Generator[scrapy.Request, None, None]]: 队列完成时触发的保存动作。
        """
        context = self.entry_contexts.get(pdb_id)
        if not context:
            return None

        context["pending"]["drugbank"] -= 1
        if context["pending"]["comp"] == 0 and context["pending"]["drugbank"] == 0:
            return self._save_result(context)
        return None

    # ------------------------------------------------------------------ #
    # 保存结果
    # ------------------------------------------------------------------ #
    def _save_result(self, context: Dict[str, Any]):
        """
        将当前结构的汇总结果落盘并生成 Scrapy Item。

        参数:
            context (Dict[str, Any]): 结构上下文。
        返回:
            Generator[RcsbAllApiItem, None, None]: Scrapy Item 产出。
        """
        result = context["result"]
        result["chemcomp"] = list(context["comp_data"].values())
        result["drugbank"] = list(context["drugbank_data"].values())

        if not result.get("rcsb_id"):
            self._cleanup_entry(context["pdb_id"])
            return

        try:
            with context["output_path"].open("w", encoding="utf-8") as fp:
                json.dump(result, fp, ensure_ascii=False, indent=2)
            self.logger.info("✅ %s 保存到 %s", context["pdb_id"], context["output_path"].name)
        except Exception as exc:
            self.logger.error("⚠️ 保存 %s 失败: %s", context["pdb_id"], exc)

        item = RcsbAllApiItem()
        item["PDB_ID"] = context["pdb_id"]
        item["rcsb_id"] = result.get("rcsb_id")
        item["entry_properties"] = result.get("properties")
        item["polymer_entities"] = result.get("polymer_entities")
        item["nonpolymer_entities"] = result.get("nonpolymer_entities")
        item["branched_entities"] = result.get("branched_entities")
        item["chemcomp"] = result.get("chemcomp")
        item["drugbank"] = result.get("drugbank")
        item["max_revision_date"] = context.get("revision_date")
        item["file_urls"] = context["file_urls"]
        if context["file_urls"]:
            item["cif_file"] = context["file_urls"][0]
            if len(context["file_urls"]) > 1:
                item["validation_image"] = context["file_urls"][1]

        revision = context.get("revision_date")
        if revision:
            self.redis_conn.hset(self.REDIS_REVISION_HASH, context["pdb_id"], revision)
            self.redis_conn.expire(self.REDIS_REVISION_HASH, self.REDIS_TTL_SECONDS)

        self._cleanup_entry(context["pdb_id"])
        yield item

    def _cleanup_entry(self, pdb_id: str):
        """
        清理结构上下文，释放内存。

        参数:
            pdb_id (str): 结构 ID。
        """
        self.entry_contexts.pop(pdb_id, None)

    # ------------------------------------------------------------------ #
    # 增量游标 & 去重
    # ------------------------------------------------------------------ #
    def _load_increment_cursor(self) -> Optional[str]:
        """
        从 Mongo 中读取上次增量游标。

        返回:
            Optional[str]: 最近一次的 revision_date。
        """
        record = self.increment_collection.find_one({"_id": self.INCREMENT_DOC_ID})
        return record.get("last_revision") if record else None

    def _compute_increment_start(self, cursor: Optional[str]) -> Optional[str]:
        """
        根据游标计算增量模式的起始日期。

        参数:
            cursor (Optional[str]): Mongo 中记录的 revision_date。
        返回:
            Optional[str]: 向前重叠 overlap_days 后的 ISO 字符串。
        """
        if not cursor:
            return None
        cursor_dt = self._to_datetime(cursor)
        if not cursor_dt:
            return None
        start_dt = cursor_dt - timedelta(days=self.overlap_days)
        return self._format_datetime(start_dt)

    def _update_run_max_revision(self, revision: Optional[str]):
        """
        记录本次运行中遇到的最大 revision 值。

        参数:
            revision (Optional[str]): 当前结构的 revision_date。
        """
        if not revision:
            return
        if not self.run_max_revision:
            self.run_max_revision = revision
            return
        current = self._to_datetime(self.run_max_revision)
        incoming = self._to_datetime(revision)
        if current and incoming and incoming > current:
            self.run_max_revision = revision

    def _is_duplicate_revision(self, pdb_id: str, revision: Optional[str]) -> bool:
        """
        基于 Redis 保存的 revision_date 判断是否重复。

        参数:
            pdb_id (str): 结构 ID。
            revision (Optional[str]): 当前 revision_date。
        返回:
            bool: True 表示无需再次处理。
        """
        if not revision:
            return False
        stored = self.redis_conn.hget(self.REDIS_REVISION_HASH, pdb_id)
        if not stored:
            return False
        stored_dt = self._to_datetime(stored)
        incoming = self._to_datetime(revision)
        return bool(stored_dt and incoming and incoming <= stored_dt)

    def closed(self, reason):
        """
        爬虫关闭时更新 Mongo 中的增量游标。

        参数:
            reason (str): Scrapy 关闭原因。
        """
        if self.mode == "incremental" and self.run_max_revision:
            self.increment_collection.update_one(
                {"_id": self.INCREMENT_DOC_ID},
                {"$set": {"last_revision": self.run_max_revision}},
                upsert=True,
            )

    # ------------------------------------------------------------------ #
    # 工具函数
    # ------------------------------------------------------------------ #
    def _entity_alias(self, entity_type: str) -> str:
        """
        将 entity 类型映射为结果中的字段名。

        参数:
            entity_type (str): API 中的实体类型。
        返回:
            str: result 字典中的 key。
        """
        return {
            "polymer_entity": "polymer_entities",
            "nonpolymer_entity": "nonpolymer_entities",
            "branched_entity": "branched_entities",
        }[entity_type]

    def _resolve_output_path(self, pdb_id: str, manual: bool = False) -> Path:
        """
        计算当前结构的输出文件路径。

        参数:
            pdb_id (str): 结构 ID。
            manual (bool): 是否来自手动模式。
        返回:
            Path: JSON 文件的目标路径。
        """
        if manual and len(self.manual_ids) == 1:
            return self.output_dir / self.user_output_filename
        return self.output_dir / f"{pdb_id}.json"

    def _parse_json(self, response, default=None):
        """
        安全解析 JSON 响应。

        参数:
            response (Response): Scrapy Response。
            default (Any): 解析失败时的返回值。
        返回:
            Any: 解析后的数据。
        """
        try:
            return response.json()
        except Exception as exc:
            self.logger.warning("%s 解析 JSON 失败: %s", response.url, exc)
            return default if default is not None else {}

    @staticmethod
    def _to_datetime(value: Optional[str]) -> Optional[datetime]:
        """
        将 ISO 字符串转换为 datetime。

        参数:
            value (Optional[str]): 原始时间字符串。
        返回:
            Optional[datetime]: datetime 对象。
        """
        if not value:
            return None
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    @staticmethod
    def _format_datetime(dt: datetime) -> str:
        """
        将 datetime 转换为 ISO 字符串。

        参数:
            dt (datetime): datetime 对象。
        返回:
            str: ISO 格式字符串。
        """
        return dt.replace(microsecond=0).isoformat()

    # ------------------------------------------------------------------ #
    # Errbacks
    # ------------------------------------------------------------------ #
    def _entry_errback(self, failure):
        """
        Entry API 请求失败回调。

        参数:
            failure (Failure): Scrapy Failure 对象。
        """
        pdb_id = failure.request.meta.get("pdb_id")
        self.logger.error("Entry 请求失败 %s: %s", pdb_id, failure.value)
        self._cleanup_entry(pdb_id)

    def _entity_errback(self, failure):
        """
        实体 API 请求失败回调。

        参数:
            failure (Failure): Scrapy Failure 对象。
        返回:
            Generator[scrapy.Request, None, None]: 继续调度的请求。
        """
        pdb_id = failure.request.meta.get("pdb_id")
        entity_type = failure.request.meta.get("entity_type")
        self.logger.error("Entity 请求失败 %s (%s): %s", pdb_id, entity_type, failure.value)
        followups = self._check_entity_complete(pdb_id)
        if followups:
            for req in followups:
                yield req

    def _comp_errback(self, failure):
        """
        ChemComp 请求失败回调。

        参数:
            failure (Failure): Scrapy Failure 对象。
        返回:
            Generator[scrapy.Request, None, None]: 继续调度的请求。
        """
        pdb_id = failure.request.meta.get("pdb_id")
        comp_id = failure.request.meta.get("comp_id")
        self.logger.error("ChemComp 请求失败 %s (%s): %s", pdb_id, comp_id, failure.value)
        followups = self._check_comp_complete(pdb_id)
        if followups:
            for req in followups:
                yield req

    def _drugbank_errback(self, failure):
        """
        DrugBank 请求失败回调。

        参数:
            failure (Failure): Scrapy Failure 对象。
        返回:
            Generator[scrapy.Request, None, None]: 继续调度的请求。
        """
        pdb_id = failure.request.meta.get("pdb_id")
        drugbank_id = failure.request.meta.get("drugbank_id")
        self.logger.error("DrugBank 请求失败 %s (%s): %s", pdb_id, drugbank_id, failure.value)
        followups = self._check_drugbank_complete(pdb_id)
        if followups:
            for req in followups:
                yield req
