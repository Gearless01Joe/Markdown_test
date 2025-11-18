# -*- coding: utf-8 -*-
"""
RCSB PDB All API Pipeline

负责将 RcsbAllApiItem 写入 MongoDB（或其他存储，依据项目 Pipeline 基类实现）
"""
from src.items.other.rcsb_pdb_item import RcsbAllApiItem
from src.pipelines.raw_storage_pipeline import MongoDBRawStoragePipeline


class RcsbPdbPipeline(MongoDBRawStoragePipeline):
    """
    All API 数据入库 Pipeline。

    属性:
        connect_key: Mongo 连接配置 key。
        collection_name: 写入的集合名称。
        item_class: 期望的 Item 类型。
    """

    connect_key = "default"
    collection_name = "rcsb_pdb_structures_all"
    item_class = RcsbAllApiItem


