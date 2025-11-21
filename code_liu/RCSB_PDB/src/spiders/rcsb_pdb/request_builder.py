# -*- coding: utf-8 -*-

"""
# @Time    : 2025/11/20 18:46
# @User  : 刘子都
# @Descriotion  : Request builder 封装 Scrapy Request 构造。
"""
from __future__ import annotations

import json
from typing import List, Optional

import scrapy


class RequestBuilder:
    """
    封装所有 RCSB API 请求的构造逻辑，避免在 Spider 中直接构造 URL 和 Request。

    :param str search_api: Search API 基础地址
    :param dict endpoints: 其余 API 的 endpoint 映射
    """

# 初始化时接收 Search API URL 和端点映射，保存为实例变量。

    def __init__(self, search_api: str, endpoints: dict):
        self.search_api = search_api
        self.endpoints = endpoints

    def build_search_request(
        self,
        start: int,
        rows: int,
        mode: str,
        increment_start: Optional[str],
        logger,
        callback,
    ) -> scrapy.Request:
        """
        构造 Search API 的 POST 请求。

        :param int start: 分页起点
        :param int rows: 每批数量
        :param str mode: 运行模式，full 或 incremental
        :param str increment_start: 增量模式的起始 revision 日期
        :param logger: 日志记录器
        :param callback: Scrapy 回调函数
        :return: 已构造的 Search API 请求
        :rtype: scrapy.Request
        """
        #
        body = self._build_search_body(start, rows, mode, increment_start)

        # 记录搜索参数和查询条件，便于调试。

        logger.info("🔍 Search params: start=%s rows=%s mode=%s", start, rows, mode)
        logger.info("🔍 Search query: %s", json.dumps(body.get("query")))

        # 返回 Search API 请求

        return scrapy.Request(
            url=self.search_api,    # Search API URL
            method="POST",          # 使用 POST 方法，向服务器提交查询条件
            body=json.dumps(body),    # 请求体为 JSON 字符串
            headers={"Content-Type": "application/json", "Accept": "application/json"},  # 设置请求头
            callback=callback,       # 响应回调
            meta={"start": start, "rows": rows},     # 传递分页信息
        )

    def build_api_request(
        self,
        endpoint_key: str,
        *path_parts: str,
        ids: Optional[List[str]] = None,
        callback=None,
        errback=None,
        meta: Optional[dict] = None,
    ) -> scrapy.Request:
        """
        构造除 Search API 以外的所有请求。

        :param str endpoint_key: endpoint 名称
        :param path_parts: URL 追加的路径片段
        :param ids: 批量 ID 列表
        :param callback: Scrapy 回调
        :param errback: Scrapy errback
        :param dict meta: 额外 meta 信息
        :return: 已构造的 Request
        :rtype: scrapy.Request
        """
        # 将端点 URL 和路径片段组合成 URL 段列表

        segments = [self.endpoints[endpoint_key], *path_parts]
        if ids:
            segments.append(",".join(ids))

        # 用 `/` 连接所有非空段，构造完整 URL

        url = "/".join(filter(None, segments))
        return scrapy.Request(
            url=url,
            callback=callback,
            errback=errback,
            meta=meta or {}
        )

    def _build_search_body(
        self, start: int, rows: int, mode: str, increment_start: Optional[str]
    ) -> dict:
        """
        生成 Search API 的请求体。

        :param int start: 分页起点
        :param int rows: 每批数量
        :param str mode: full 或 incremental
        :param str increment_start: 增量模式的起始 revision
        :return: Search API 请求体
        :rtype: dict
        """
        # 生成查询条件

        base_node = {
            "type": "terminal",
            "service": "text",
            "parameters": {"attribute": "rcsb_id", "operator": "exists"},
        }

        # 如果是增量模式且有起始日期，添加日期过滤条件

        nodes = [base_node]
        if mode == "incremental" and increment_start:
            nodes.append(
                {
                    "type": "terminal",
                    "service": "text",
                    "parameters": {
                        "attribute": "rcsb_accession_info.revision_date",
                        "operator": "greater_or_equal",
                        "value": increment_start,
                    },
                }
            )

        if len(nodes) == 1:
            query = nodes[0]
        else:
            query = {"type": "group", "logical_operator": "and", "nodes": nodes}

        # 设置分页、评分策略和排序（按 revision_date 升序）。

        request_options = {
            "paginate": {"start": start, "rows": rows},
            "scoring_strategy": "combined",
            "sort": [{"sort_by": "rcsb_accession_info.revision_date", "direction": "asc"}],
        }
        return {"query": query, "return_type": "entry", "request_options": request_options}

