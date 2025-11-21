# -*- coding: utf-8 -*-

"""
# @Time    : 2025/11/20 18:46
# @User  : 刘子都
# @Descriotion  : Service layer：解析、下载、状态管理、上下文模型。
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

import requests

from src.items.rcsb_pdb_item import RcsbAllApiItem
from src.spiders.rcsb_pdb.constants import FIELD_SCHEMAS, HTTP_STATUS

from concurrent.futures import ThreadPoolExecutor


class DataParser:
    """
    负责解析 JSON 响应 并 执行字段规范化。
    """

    def parse(self, response, logger, default=None):
        """
        解析 Scrapy Response 为字典。

        :param response: Scrapy 响应对象
        :type response: scrapy.http.Response
        :param logger: 日志记录器
        :type logger: logging.Logger
        :param default: 解析失败时的默认返回
        :return: JSON 字典
        :rtype: dict
        """

        # 尝试解析 JSON，失败时记录警告并返回默认值

        try:
            return response.json()
        except Exception as exc:
            logger.warning("%s 解析 JSON 失败: %s", response.url, exc)
            return default if default is not None else {}

    def normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        按 `FIELD_SCHEMAS` 规则补齐字段。

        :param dict data: 原始数据
        :return: 规范化后的数据
        :rtype: dict
        """

        # 如果不是字典，直接返回；否则创建副本。

        if not isinstance(data, dict):
            return data
        result = dict(data)

        # 遍历 Schema，对列表和字典类型的字段进行规范化。

        for field_name, schema in FIELD_SCHEMAS.items():
            if field_name not in result:
                continue
            value = result[field_name]
            if isinstance(value, list):

                # 对单个字典项进行规范化，缺失字段用 `None` 填充

                result[field_name] = [self._normalize_item(item, schema) for item in value]
            elif isinstance(value, dict):

                # 对单个字典项进行规范化，缺失字段用 `None` 填充

                result[field_name] = self._normalize_item(value, schema)
        return result

    @staticmethod
    def _normalize_item(item: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """
            对单个字典项进行规范化。

            :param dict item: 原始字典
            :param dict schema: 字段规范
            :return: 规范化后的字典
            :rtype: dict
        """
        normalized = dict(item)
        for field_name, default_value in schema.items():
            normalized.setdefault(field_name, default_value)
        return normalized


@dataclass
class EntryContext:
    """
    管理单个 PDB Entry 的运行期上下文数据。

    :param str pdb_id: 结构 ID
    :param list file_urls: 已确认可下载的文件 URL 列表
    :param dict file_audit: 文件审计信息
    :param str validation_url: 验证图片 URL
    :param str validation_pdf_url: 验证 PDF URL
    """

    # 定义 Entry 的基本信息字段。

    pdb_id: str
    file_urls: List[str]
    file_audit: Dict[str, Dict[str, Any]]
    validation_url: Optional[str]
    validation_pdf_url: Optional[str]

    # 使用 `default_factory` 确保每个实例都有独立的字典。

    result: Dict[str, Any] = field(
        default_factory=lambda: {
            "rcsb_id": None,
            "properties": {},
            "polymer_entities": [],
            "nonpolymer_entities": [],
            "branched_entities": [],
            "chemcomp": [],
            "drugbank": [],
        }
    )
    pending: Dict[str, int] = field(
        default_factory=lambda: {"entity": 0, "comp": 0, "drugbank": 0, "assembly": 0}
    )
    comp_ids: Set[str] = field(default_factory=set)
    drugbank_ids: Set[str] = field(default_factory=set)
    comp_data: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    drugbank_data: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    assembly_data: Optional[Dict[str, Any]] = None
    revision_date: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    stats: Dict[str, int] = field(
        default_factory=lambda: {"entity_total": 0, "comp_total": 0, "drugbank_total": 0}
    )


    # 代码中大量使用了字典式访问，所以添加 __getitem__ 、 __setitem__  和 get方法

    def __getitem__(self, item):
        """
        支持字典式读取。

        :param str item: 属性名
        :return: 属性值
        """
        return getattr(self, item)

    def __setitem__(self, key, value):
        """
        支持字典式写入。

        :param str key: 属性名
        :param value: 新值
        """
        setattr(self, key, value)

    def get(self, key, default=None):
        """
        仿照 dict.get 获取属性。

        :param str key: 属性名
        :param default: 默认值
        :return: 属性值或默认
        """
        return getattr(self, key, default)

    @classmethod
    def from_bundle(cls, pdb_id: str, bundle: Dict[str, Any]) -> "EntryContext":
        """
        阶段二：将PDB ID和字典转换为EntryContext对象。
        1. 从字典中提取数据
        2. 字段名映射（字典键名 → 对象属性名）
        3. 提供默认值处

        :param str pdb_id: 结构 ID
        :param dict bundle: 包含文件 URL 与审计信息的字典
        :return: 包含文件 URL 与审计信息的上下文实例
        :rtype: EntryContext
        """
        return cls(
            pdb_id=pdb_id,
            file_urls=bundle.get("file_urls", []),
            file_audit=bundle.get("audit", {}),
            validation_url=bundle.get("validation_image_url"),
            validation_pdf_url=bundle.get("validation_pdf_url"),
        )

    def to_item(self) -> RcsbAllApiItem:
        """
        阶段四：将 EntryContext 对转换为 Scrapy Item，用于最终输出给 Pipeline。

        :return: 转换后的 Item
        :rtype: RcsbAllApiItem
        """

        # 将字典格式转换为列表格式。

        result = self.result
        result["chemcomp"] = list(self.comp_data.values())
        result["drugbank"] = list(self.drugbank_data.values())

        # 将 Assembly 数据合并到 properties 中

        if self.assembly_data:
            result.setdefault("properties", {})
            if isinstance(self.assembly_data, dict):
                result["properties"].update(self.assembly_data)
            else:
                result["properties"]["assembly"] = self.assembly_data

        # 创建 Scrapy Item 并填充所有字段

        item = RcsbAllApiItem()
        item["pdb_id"] = self.pdb_id
        item["rcsb_id"] = result.get("rcsb_id")
        item["properties"] = result.get("properties")
        item["polymer_entities"] = result.get("polymer_entities")
        item["nonpolymer_entities"] = result.get("nonpolymer_entities")
        item["branched_entities"] = result.get("branched_entities")
        item["chemcomp"] = result.get("chemcomp")
        item["drugbank"] = result.get("drugbank")
        item["max_revision_date"] = self.revision_date
        item["created_at"] = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
        item["file_urls"] = list(self.file_urls)
        
        # 根据 URL 模式识别文件类型并填充到对应的 Item 字段

        for url in self.file_urls:
            if url.endswith(".cif"):
                item["cif_file"] = url
            elif "_assembly-1.jpeg" in url or "_model-1.jpeg" in url:
                item["structure_image"] = url
            elif "_multipercentile_validation.png" in url:
                item["validation_image"] = url
            elif "_full_validation.pdf" in url:
                item["validation_pdf"] = url
        
        return item


class FileDownloader:
    """
    管理文件 URL 探测与审计
    """

    def __init__(self, logger, timeout: int = 5, max_retries: int = 5):
        """
        初始化文件下载器，设置超时和重试次数。

        :param logger: 日志实例
        :type logger: logging.Logger
        :param timeout: 单次请求超时
        :type timeout: int
        :param max_retries: 探测最大重试次数
        :type max_retries: int
        """

        self.logger = logger
        self.timeout = timeout
        self.max_retries = max_retries

    def build_initial_bundle(self, pdb_id: str) -> Dict[str, Any]:
        """
        阶段一：PDB ID 转字典。
        1. 构造所有可能的文件 URL（CIF、结构图片、验证文件等）
        2. 并行探测文件可用性（使用 ThreadPoolExecutor）
        3. 收集可用的文件 URL 和审计信息

        :param str pdb_id: 结构 ID
        :return: 包含 file_urls 与 audit 信息的字典
        :rtype: dict
        """

        # 根据 PDB ID 构造所有可能的文件 URL

        pdb_id_lower = pdb_id.lower()
        cif_url = f"https://files.rcsb.org/download/{pdb_id}.cif"
        assembly_url = f"https://cdn.rcsb.org/images/structures/{pdb_id_lower}_assembly-1.jpeg"
        model_url = f"https://cdn.rcsb.org/images/structures/{pdb_id_lower}_model-1.jpeg"
        validation_url = (
            f"https://files.rcsb.org/validation/view/{pdb_id_lower}_multipercentile_validation.png"
        )
        validation_pdf_url = (
            f"https://files.rcsb.org/validation/view/{pdb_id_lower}_full_validation.pdf"
        )

        audit_entry: Dict[str, Dict[str, Any]] = {}
        file_urls: List[str] = []

        # 并行检查 CIF 和结构图片候选
        urls_to_check = [cif_url, assembly_url, model_url]
        results = self._parallel_check(urls_to_check)

        # 处理 CIF 文件结果，如果可用则加入 URL 列表

        cif_result = results[0]
        audit_entry["cif_file"] = cif_result
        if cif_result.get("available"):
            file_urls.append(cif_url)

        # 挑选结构图片（从 assembly/model 结果中选）
        structure_results = results[1:]
        structure_result = self._pick_structure_from_results(structure_results, [assembly_url, model_url])
        audit_entry["structure_image"] = structure_result
        if structure_result.get("selected"):
            file_urls.append(structure_result["selected"])

        audit_entry["validation_image"] = {"pending_check": True, "available": False, "missing": False}
        audit_entry["validation_pdf"] = {"pending_check": True, "available": False, "missing": False}

        return {
            "file_urls": file_urls,
            "audit": audit_entry,
            "validation_image_url": validation_url,
            "validation_pdf_url": validation_pdf_url,
        }

    def handle_validation_assets(self, entry: EntryContext, has_validation_report: bool) -> None:
        """
        针对 validation 图片/PDF 做延迟探测。需要先获取 Entry 数据，检查是否有 pdbx_vrpt_summary 字段
        如果有验证报告，才探测验证图片；如果没有，直接标记为缺失
        避免对没有验证报告的结构发送无效 HTTP 请求，节约时间

        :param EntryContext entry: 目标上下文
        :param bool has_validation_report: 是否存在验证报告元数据
        """

        # 根据是否有验证报告决定是否检查验证图片

        urls_to_check = []
        if has_validation_report:
            urls_to_check.append(entry.validation_url)
        urls_to_check.append(entry.validation_pdf_url)  # PDF 不需 report 判断

        if not urls_to_check:
            return

        # 并行检查验证文件

        results = self._parallel_check(urls_to_check)

        # 处理 validation_image
        if has_validation_report:
            validation_image_result = results.pop(0)
            entry.file_audit["validation_image"] = validation_image_result
            if validation_image_result.get("available"):
                entry.file_urls.append(entry.validation_url)
        else:
            entry.file_audit["validation_image"] = {
                "selected": None,
                "available": False,
                "missing": True,
                "reason": "Entry 数据中无 pdbx_vrpt_summary 字段",
                "status": None,
            }

        # 处理 validation_pdf
        validation_pdf_result = results[0] if results else {}
        entry.file_audit["validation_pdf"] = validation_pdf_result
        if validation_pdf_result.get("available"):
            entry.file_urls.append(entry.validation_pdf_url)

    def _parallel_check(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        用线程池并行检查多个 URL，最多 4 个并发

        :param list urls: URL 列表
        :return: 结果列表
        :rtype: list
        """
        with ThreadPoolExecutor(max_workers=4) as executor:
            return list(executor.map(self._check_url, urls))

    def _pick_structure_from_results(self, results: List[Dict[str, Any]], candidates: List[str]) -> Dict[str, Any]:
        """
        从并行结果中挑选第一个可用结构图。

        :param list results: 探测结果列表
        :param list candidates: 对应 URL 列表
        :return: 挑选结果
        :rtype: dict
        """
        # 初始化结果字典，默认所有字段为不可用状态。

        info = {
            "selected": None,
            "reason": "无候选 URL",
            "missing": False,
            "available": False,
            "status": None,
        }

        # 遍历探测结果，找到第一个可用的图片。

        for result, url in zip(results, candidates):
            info["status"] = result["status"]
            info["reason"] = result["reason"]
            info["missing"] = result["missing"]
            if result["available"]:
                info["selected"] = url
                info["available"] = True
                info["reason"] = None
                return info
        return info

    def _check_url(self, url: Optional[str]) -> Dict[str, Any]:
        """
        对指定 URL 执行 HEAD/GET 探测。

        :param str url: 目标 URL
        :return: 包含状态的字典
        :rtype: dict
        """
        result = {
            "selected": url,
            "status": None,
            "reason": None,
            "missing": False,
            "available": False,
        }
        if not url:
            result["reason"] = "URL 未提供"
            return result

        # 尝试 HEAD 请求，获取状态码后关闭连接。

        for attempt in range(1, self.max_retries + 1):
            start_ts = time.perf_counter()
            try:
                resp = requests.head(url, allow_redirects=True, timeout=self.timeout)
                status = resp.status_code
                resp.close()

                # 如果服务器不支持 HEAD（405），改用 GET 请求。

                if status == HTTP_STATUS["method_not_allowed"]:
                    resp = requests.get(url, allow_redirects=True, timeout=self.timeout, stream=True)
                    status = resp.status_code
                    resp.close()

                # 200 状态码表示文件可用，立即返回。

                result["status"] = status
                if status == HTTP_STATUS["success"]:
                    elapsed = time.perf_counter() - start_ts
                    if elapsed > 1:
                        self.logger.debug("⏱️ Probe %s success in %.2fs", url, elapsed)
                    result["available"] = True
                    return result

                # 404 表示文件不存在，不重试，立即返回。

                if status == HTTP_STATUS["not_found"]:
                    result["missing"] = True
                    result["reason"] = "HTTP 404"
                    return result

                # 其他 HTTP 错误：记录但不重试
                result["reason"] = f"HTTP {status}"
                return result

            # 超时异常，达到最大重试次数后返回。

            except requests.Timeout as exc:
                if attempt == self.max_retries:
                    result["reason"] = str(exc)
                    elapsed = time.perf_counter() - start_ts
                    if elapsed > 1:
                        self.logger.debug("⏱️ Probe timeout %s took %.2fs (%s)", url, elapsed, result["reason"])
                    return result

            # 其他异常不重试

            except requests.RequestException as exc:
                result["reason"] = str(exc)
                return result

        return result


class RevisionState:
    """
    负责增量游标读取、去重判定以及游标持久化。
    """

    def __init__(
        self,
        collection,
        redis_conn,
        doc_id: str,
        redis_hash: str,
        ttl_seconds: int,
        overlap_days: int,
    ):
        self.collection = collection
        self.redis_conn = redis_conn
        self.doc_id = doc_id
        self.redis_hash = redis_hash
        self.ttl_seconds = ttl_seconds
        self.overlap_days = overlap_days

        # 从 MongoDB 加载上次的游标，计算增量起始日期（向前推 `overlap_days` 天）。
        record = self.collection.find_one({"_id": self.doc_id})
        self.run_max_revision = record.get("last_revision") if record else None

        if self.run_max_revision:
            cursor_dt = self._to_datetime(self.run_max_revision)
            if cursor_dt:
                start_dt = cursor_dt - timedelta(days=self.overlap_days)
                formatted = (
                    start_dt.replace(microsecond=0)
                    .isoformat()
                    .replace("+00:00", "Z")
                )
                self.increment_start = formatted
            else:
                self.increment_start = None
        else:
            self.increment_start = None

    def update_run_max(self, revision: Optional[str]) -> None:
        """
        记录当前运行周期内遇到的最大 revision 日期，供最终写回 MongoDB。只有当新 revision 更大时才更新，保证游标单调递增。

        :param str revision: 当前 Entry 的 revision
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

    def is_duplicate(self, pdb_id: str, revision: Optional[str]) -> bool:
        """
        判断当前 revision 是否已处理。

        :param str pdb_id: 结构 ID
        :param str revision: revision 字段
        :return: 是否重复
        :rtype: bool
        """
        if not revision:
            return False

        # 从 Redis 读取已存储的 revision，如果当前 revision 小于等于已存储的，则判定为重复。

        stored = self.redis_conn.hget(self.redis_hash, pdb_id)
        if not stored:
            return False
        stored_dt = self._to_datetime(stored)
        incoming = self._to_datetime(revision)
        return bool(stored_dt and incoming and incoming <= stored_dt)

    def persist_revision(self, pdb_id: str, revision: Optional[str]) -> None:
        """
        将最新 revision 写入 Redis。

        :param str pdb_id: 结构 ID
        :param str revision: revision 字符串
        """
        if not revision:
            return
        self.redis_conn.hset(self.redis_hash, pdb_id, revision)
        self.redis_conn.expire(self.redis_hash, self.ttl_seconds)

    def flush(self) -> None:
        """
        将运行期的最大 revision 写回 MongoDB 游标。
        """
        if self.run_max_revision:
            self.collection.update_one(
                {"_id": self.doc_id},
                {"$set": {"last_revision": self.run_max_revision}},
                upsert=True,
            )

    @staticmethod
    def _to_datetime(value: Optional[str]) -> Optional[datetime]:
        """
        将字符串转换成 datetime。

        :param str value: 输入字符串
        :return: 转换后的 datetime
        :rtype: datetime
        """
        if not value:
            return None
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

