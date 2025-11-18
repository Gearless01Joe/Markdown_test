# -*- coding: utf-8 -*-
"""
RCSB PDB All API Item

用于 RcsbAllApiSpider 的标准化数据输出，确保后续 Pipeline 能够统一处理。
"""
from scrapy import Field
from src.items.base_items import BaseItem, StringField, FileOSSField


class RcsbAllApiItem(BaseItem):
    """
    All API 全字段数据项。

    字段:
        PDB_ID: 结构 ID。
        rcsb_id: Entry API 返回的唯一标识。
        entry_properties: Entry API 的 properties 字典。
        polymer_entities: Polymer 实体数组。
        nonpolymer_entities: Nonpolymer 实体数组。
        branched_entities: Branched 实体数组。
        chemcomp: ChemComp 数据列表。
        drugbank: DrugBank 数据列表。
        max_revision_date: revision_date，用于增量游标。
        cif_file: CIF 文件下载结果。
        validation_image: 验证图下载结果。
    """

    PDB_ID = StringField()  # 结构 ID
    rcsb_id = StringField()
    entry_properties = Field()  # Entry API properties (dict)
    polymer_entities = Field()  # Polymer entities (list)
    nonpolymer_entities = Field()  # Nonpolymer entities (list)
    branched_entities = Field()  # Branched entities (list)
    chemcomp = Field()  # ChemComp 数据 (list)
    drugbank = Field()  # DrugBank 数据 (list)
    max_revision_date = StringField()  # 当前结构的 revision_date

    cif_file = FileOSSField(bucket_sign="local", oss_path_sign="rcsb_pdb_all")
    validation_image = FileOSSField(bucket_sign="local", oss_path_sign="rcsb_pdb_all")


