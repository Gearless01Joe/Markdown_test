# -*- coding: utf-8 -*-

"""
# @Time    : 2025/11/20 18:46
# @User  : 刘子都
# @Descriotion  : RCSB PDB spider 常量定义。
"""

# 定义两个API基础路径，分别用于取PDB ID和取基础数据

SEARCH_API = "https://search.rcsb.org/rcsbsearch/v2/query"
API_BASE = "https://data.rcsb.org/rest/v1/core"

# 定义所有字段的映射

API_ENDPOINTS = {
    "entry": f"{API_BASE}/entry",
    "polymer_entity": f"{API_BASE}/polymer_entity",
    "nonpolymer_entity": f"{API_BASE}/nonpolymer_entity",
    "branched_entity": f"{API_BASE}/branched_entity",
    "chemcomp": f"{API_BASE}/chemcomp",
    "drugbank": f"{API_BASE}/drugbank",
    "assembly": f"{API_BASE}/assembly",
}
# 定义常用的 HTTP 状态码

HTTP_STATUS = {
    "success": 200,
    "not_found": 404,
    "method_not_allowed": 405,
}
# 定义 Redis Hash 的键名，用于存储每个 PDB ID 的最新 revision 日期，实现增量去重

REDIS_REVISION_HASH = "rcsb_all_api:revision"

# 定义 Redis 数据的过期时间（60天），避免内存无限增长。

REDIS_TTL_SECONDS = 60 * 60 * 24 * 60  # 60 天

# 默认的 Assembly ID，通常 assembly-1 就是代表全链，但有些 PDB 可能没有这个 ID

DEFAULT_ASSEMBLY_ID = "1"


# 定义字段规范化规则，确保所有 Schema 中定义的字段都存在，缺失时填充 `None`。

FIELD_SCHEMAS = {
    "exptl": {
        "crystals_number": None,
        "details": None,
        "method": None,
        "method_details": None,
    },
    "audit_author": {
        "identifier_ORCID": None,
        "name": None,
        "pdbx_ordinal": None,
    },
    "citation": {
        "book_id_ISBN": None,
        "book_publisher": None,
        "book_publisher_city": None,
        "book_title": None,
        "coordinate_linkage": None,
        "country": None,
        "id": None,
        "journal_abbrev": None,
        "journal_full": None,
        "journal_id_ASTM": None,
        "journal_id_CSD": None,
        "journal_id_ISSN": None,
        "journal_issue": None,
        "journal_volume": None,
        "language": None,
        "page_first": None,
        "page_last": None,
        "pdbx_database_id_DOI": None,
        "pdbx_database_id_PubMed": None,
        "title": None,
        "year": None,
    },
    "cell": {
        "Z_PDB": None,
        "angle_alpha": None,
        "angle_beta": None,
        "angle_gamma": None,
        "formula_units_Z": None,
        "length_a": None,
        "length_b": None,
        "length_c": None,
        "pdbx_unique_axis": None,
        "volume": None,
    },
}

