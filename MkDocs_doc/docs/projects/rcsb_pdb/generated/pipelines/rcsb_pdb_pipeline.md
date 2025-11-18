# rcsb_pdb_pipeline

RCSB PDB All API Pipeline

负责将 RcsbAllApiItem 写入 MongoDB（或其他存储，依据项目 Pipeline 基类实现）

**模块路径**: `code_liu.RCSB_PDB.src.pipelines.rcsb_pdb_pipeline`

## 导入

- `src.items.other.rcsb_pdb_item.RcsbAllApiItem`
- `src.pipelines.raw_storage_pipeline.MongoDBRawStoragePipeline`

## 类

### RcsbPdbPipeline

All API 数据入库 Pipeline。

属性:
    connect_key: Mongo 连接配置 key。
    collection_name: 写入的集合名称。
    item_class: 期望的 Item 类型。

**继承自**: `MongoDBRawStoragePipeline`

#### 属性

- `connect_key` (`str`)
- `collection_name` (`str`)
- `item_class` (`RcsbAllApiItem`)
