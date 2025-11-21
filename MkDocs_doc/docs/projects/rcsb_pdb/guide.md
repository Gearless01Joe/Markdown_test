# 核心模块指南

本文聚焦于开发/维护时最常接触的代码，按照「入口 → 服务 → 数据 → 管道 → 管理」逐一说明。文中提到的路径均以 `code_liu/RCSB_PDB/` 为根。

---

## 1. 运行入口

### `firing.py`

- 封装 Scrapy 命令执行，支持 `--name rcsb_all_api` 与任意自定义参数。
- 根据 `LOG_FILE` 设置自动创建日志目录与文件名，便于控制台 / 文件双写。
- 推荐在 IDE 中通过 `start_spider(spider_name="rcsb_all_api", mode="full")` 方式调试，可直接打断点。

### Scrapy 设置 `src/settings.py`

| 区域 | 关键字段 | 说明 |
| --- | --- | --- |
| 基础 | `BOT_NAME`, `SPIDER_MODULES`, `NEWSPIDER_MODULE` | Scrapy 识别爬虫的入口 |
| 并发/重试 | `CONCURRENT_REQUESTS`, `DOWNLOAD_DELAY`, `RETRY_TIMES` 等 | 全局默认，Spider 内部可通过 `custom_settings` 覆盖 |
| 中间件 | `DOWNLOADER_MIDDLEWARES`, `SPIDER_MIDDLEWARES` | 启用验证码拦截、代理、历史数据过滤 |
| 日志/文件 | `LOG_*`, `FILES_STORE`, `IMAGES_STORE` | 依赖 `constant.py` 中的目录配置 |
| 数据库 | `MONGODB_DATABASES`, `REDIS_DATABASES`, `MYSQL_DATABASES` | 统一管理连接信息（可结合环境变量读取） |

---

## 2. 爬虫与服务层

### `RcsbAllApiSpider`（`src/spiders/rcsb_pdb/rcsb_pdb_spider.py`）

- **入口参数**：`mode`, `pdb_id`, `max_targets`, `batch_size`, `start_from`, `overlap_days`, `output_filename` 等。
- **自定义设置**：在 `custom_settings` 内覆盖并发、日志等级、Pipeline 顺序，避免污染全局配置。
- **关键方法**：
  - `_request_search`：根据当前偏移构建搜索请求。
  - `parse_entry` / `_parse_entity_*`：解析 Entry 与实体结构，累积到 `EntryContext`。
  - `_after_entities_complete`：当实体全部处理完毕后生成 Item 并调度附件下载。
  - `_cleanup_entry`：释放上下文、统计成功/跳过数量。

### 服务类 `src/spiders/rcsb_pdb/services.py`

| 类 | 职责 |
| --- | --- |
| `DataParser` | 包装 `response.json()`，结合 `FIELD_SCHEMAS` 补齐缺失字段，统一日志输出 |
| `EntryContext` | 在单个 PDB 生命周期内缓存所有中间结果，并在 `to_item()` 时一次性产出 Item |
| `FileDownloader` | 负责 CIF / 结构图 / 验证文件的 URL 生成、并行可用性探测以及审计信息记录 |
| `RevisionState` | 读写 Mongo&Redis 游标，计算增量起始日期、去重、统计跳过数量 |

> 如果需要新增 API 采集流程，优先在 `EntryContext` 中补充字段，然后在 Spider 的 `pending` 计数中注册，避免漏掉收尾逻辑。

### 请求构造器 `src/spiders/rcsb_pdb/request_builder.py`

- 只负责拼接 URL 和请求体，不持有状态，可直接在其他项目复用。
- Search API 紧耦合 `revision_date` 排序与分页逻辑；如需切换排序字段，请同步修改 `_build_search_body`。

---

## 3. 数据与管道

### Item 定义 `src/items/rcsb_pdb_item.py`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `PDB_ID`, `rcsb_id`, `max_revision_date` | `StringField` | 唯一标识、增量游标 |
| `entry_properties` | `Field` | 标准化后的 Entry JSON |
| `polymer_entities` / `nonpolymer_entities` / `branched_entities` | `Field` | 各实体列表 |
| `chemcomp`, `drugbank` | `Field` | 化合物与药物信息 |
| `cif_file`, `validation_image`, `validation_pdf` | `FileOSSField` | 与 `FileDownloadPipeline` 协同上传 |

> 若需要额外的字段（例如结构评分），直接在 Item 中新增 `Field` 并在 `EntryContext.to_item()` 赋值。

### Pipeline 组合

1. **`FileDownloadPipeline`**：下载 `item["file_urls"]`，保存到 `UPLOAD_PATH` 并记录结果。
2. **`FileReplacementPipeline`**：将本地路径替换为 OSS/共享存储路径，保证最终数据可被解析层直接使用。
3. **`RcsbPdbPipeline`**（`src/pipelines/storage/rcsb_pdb_pipeline.py`）：继承 `MongoDBRawStoragePipeline`，把 `RcsbAllApiItem` 写入 `raw_data.rcsb_pdb_structures_all`，并附加 metadata。

如需对接其他存储（例如 Kafka、接口推送），建议新建 Pipeline 并插入到 400 之后，以免影响原有落库。

---

## 4. 管理工具

| 模块 | 作用 |
| --- | --- |
| `src/utils/mongodb_manager.py` | 基于连接池的 Mongo 单例，支持多 `connect_key`。`MongoDBManager(connect_key="default").db[...]` |
| `src/utils/redis_manager.py` | 提供 `get_connection()` 获取 `StrictRedis`，默认开启健康检查与连接池 |
| `src/pipelines/raw_storage_pipeline.py` | Mongo/MySQL Pipeline 基类，封装通用的 metadata、运行参数记录 |
| `src/utils/base_logger.py` | 自定义日志格式化，支持 `LOG_STDOUT` 与按月分目录输出 |

当连接配置调整时，只需更新 `settings.py` 中的参数即可；各模块会在 `open_spider` 时重新读取。

---

## 5. 调整与扩展建议

1. **引入新 API**  
   - 在 `constants.API_ENDPOINTS` 添加 endpoint  
   - 在 Spider 中注册新的 `SECTION_MAP`，实现对应的 `_parse_xxx` 方法  
   - 在 `EntryContext` 中定义缓存结构并在 `to_item()` 中输出

2. **增强字段/附件**  
   - 若只影响 JSON，可通过 `EntryContext` 即可  
   - 若涉及新增文件，则补充 `FileDownloader.build_initial_bundle` 与 Pipeline

3. **裁剪/隔离配置**  
   - 可以把特定任务的自定义设置放到 Spider `custom_settings` 中，例如不同环境的 `ITEM_PIPELINES`、`CONCURRENT_REQUESTS`

4. **排障定位**  
   - 观察 `context.file_audit` 或 `RevisionState` 日志可以快速判断缺失的附件/游标  
   - 结合 [故障排查](troubleshooting.md) 中的命令清理 Mongo/Redis 游标，恢复增量。

---

更多场景与命令示例见 [使用示例](examples.md)，需要了解整体数据流可回到 [架构设计](architecture.md)。
