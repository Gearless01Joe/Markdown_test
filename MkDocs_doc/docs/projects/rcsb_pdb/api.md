# 系统全景 · API 参考

> 本页提供关键模块的索引与说明，方便在 IDE / 搜索中快速定位。若需自动化的 mkdocstrings 输出，请参考文末的「技巧」。

---

## 1. 模块地图

| 文件 | 主要类 / 函数 | 职责 |
| --- | --- | --- |
| `src/spiders/rcsb_pdb/rcsb_pdb_spider.py` | `RcsbAllApiSpider` | 管控运行模式、调度 Search/Entry/Entity/ChemComp/DrugBank 请求 |
| `src/spiders/rcsb_pdb/request_builder.py` | `RequestBuilder` | 拼接所有 REST 请求（Search、Entry、Assembly 等） |
| `src/spiders/rcsb_pdb/services.py` | `DataParser`, `EntryContext`, `FileDownloader`, `RevisionState` | JSON 解析、上下文存储、附件探测、增量游标管理 |
| `src/items/rcsb_pdb_item.py` | `RcsbAllApiItem` | 统一结构 ID、实体、ChemComp/DrugBank 与附件字段 |
| `src/pipelines/file_download_pipeline.py` | `FileDownloadPipeline` | 下载 CIF / 图片文件 |
| `src/pipelines/file_replacement_pipeline.py` | `FileReplacementPipeline` | 将本地路径替换为 OSS / 共享目录 |
| `src/pipelines/storage/rcsb_pdb_pipeline.py` | `RcsbPdbPipeline` | 入库到 Mongo `raw_data.rcsb_pdb_structures_all` |
| `src/utils/mongodb_manager.py` | `MongoDBManager` | Mongo 单例连接池 |
| `src/utils/redis_manager.py` | `RedisManager` | Redis 连接池，供 `RevisionState` 使用 |

---

## 2. 重点模块速览

### 2.1 RcsbAllApiSpider

- 入口参数：`mode`, `pdb_id`, `max_targets`, `batch_size`, `start_from`, `overlap_days`, `output_filename`, `field_filter_config`。
- 覆盖 `custom_settings` 控制并发（64 总并发 / 16 每域名 / 0.3s 延迟 / 自动限流）。
- 核心方法：
  - `_request_search` / `parse_search`：分页调度 Search API
  - `_schedule_entry` / `parse_entry`：拉取 Entry、实体 ID、revision
  - `_after_entities_complete`：组装 `RcsbAllApiItem`，写入 Pipeline

### 2.2 Services（`src/spiders/rcsb_pdb/services.py`）

- `DataParser`：包装 `response.json()`，结合 `FIELD_SCHEMAS` 补齐字段
- `EntryContext`：贯穿单个 PDB 生命周期，`to_item()` 负责最终结构化
- `FileDownloader`：探测 CIF/结构图/验证文件，记录可用性
- `RevisionState`：维护 Mongo/Redis 游标，计算增量起点、判重

### 2.3 RequestBuilder

- `build_search_request`：按 `revision_date` 升序拼接 Search 请求体
- `build_api_request`：对 Entry / Entity / ChemComp / DrugBank / Assembly 统一封装

### 2.4 Item & Pipeline

- `RcsbAllApiItem`：包含 Entry 属性、实体列表、ChemComp/DrugBank、附件 URL、`max_revision_date`
- `FileDownloadPipeline` → `FileReplacementPipeline` → `RcsbPdbPipeline`：负责文件下载、路径替换、Mongo 入库

---

## 3. 常用代码段

```python
# 运行爬虫（firing.py）
from firing import start_spider

start_spider(
    spider_name="rcsb_all_api",
    mode="incremental",
    overlap_days=2,
)
```

```python
# 读取 Mongo 结果
from src.utils.mongodb_manager import MongoDBManager

mongo = MongoDBManager()
doc = mongo.db["rcsb_pdb_structures_all"].find_one({"PDB_ID": "1A1A"})
print(doc["max_revision_date"])
```

```python
# 检查 Redis 游标
from src.utils.redis_manager import RedisManager

r = RedisManager().get_connection()
print(r.hget("rcsb_all_api:revision", "1A1A"))
```

---

## 4. mkdocstrings 小贴士（可选）

1. 确保依赖安装：`pip install -r code_liu/RCSB_PDB/requirements.txt`
2. 设置 Python 路径：
   ```bash
   set PYTHONPATH=%PYTHONPATH%;D:\Python_project\Markdown\code_liu\RCSB_PDB
   ```
3. 在 `docs/projects/rcsb_pdb/api.md` 中按需恢复 `::: src.spiders.rcsb_pdb.request_builder.RequestBuilder` 等语句，即可重新启用自动 API 文档。

> 由于 Scrapy / Redis / pymongo 属于运行时依赖，未安装时会导致 `mkdocs serve` 报错；如只需浏览文档，可先保留当前的文字概览。

---

如需继续深挖，请结合源代码与 [核心模块指南](guide.md)。欢迎在 PR 中补充更多有价值的片段。

