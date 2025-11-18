# rcsb_pdb_item

RCSB PDB All API Item

用于 RcsbAllApiSpider 的标准化数据输出，确保后续 Pipeline 能够统一处理。

**模块路径**: `code_liu.RCSB_PDB.src.items.rcsb_pdb_item`

## 导入

- `scrapy.Field`
- `src.items.base_items.BaseItem`
- `src.items.base_items.FileOSSField`
- `src.items.base_items.StringField`

## 类

### RcsbAllApiItem

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

**继承自**: `BaseItem`

#### 属性

- `PDB_ID`
- `rcsb_id`
- `entry_properties`
- `polymer_entities`
- `nonpolymer_entities`
- `branched_entities`
- `chemcomp`
- `drugbank`
- `max_revision_date`
- `cif_file`
- `validation_image`
