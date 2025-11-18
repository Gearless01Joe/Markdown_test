# 核心模块指南

本文从工程视角梳理 RCSB PDB 项目的关键模块，帮助你快速定位「该改哪里、该看哪里」。

---

## 1. 项目配置 `src/settings.py`

| 区域 | 说明 | 关键字段 |
| --- | --- | --- |
| 数据库 | 定义 MySQL / MongoDB / Redis 连接 | `MYSQL_DATABASES`, `MONGODB_DATABASES`, `REDIS_DATABASES` |
| Scrapy 基础 | BOT、Spider 模块、并发、下载设置 | `BOT_NAME`, `CONCURRENT_REQUESTS`, `DOWNLOAD_DELAY` |
| 中间件 | 统一加载验证码、代理、历史数据控制 | `DOWNLOADER_MIDDLEWARES`, `SPIDER_MIDDLEWARES` |
| Playwright | 如需浏览器，可在此启用 | `PLAYWRIGHT_PROCESS_REQUEST_HEADERS` |
| 日志 | 分级、格式、文件落地 | `LOG_*` 系列 |

> 建议通过环境变量覆盖生产配置，避免直接改动仓库。

---

## 2. 数据模型 `src/items/rcsb_pdb_item.py`

`RcsbAllApiItem` 代表一条结构化的蛋白质记录，包含：

- 结构标识：`PDB_ID`, `rcsb_id`, `max_revision_date`
- Entry 属性：`entry_properties`
- 各类实体：`polymer_entities`, `nonpolymer_entities`, `branched_entities`
- 化合物/药物：`chemcomp`, `drugbank`
- 附件：`cif_file`, `validation_image`

字段类型沿用 Scrapy `Field`/自定义 `StringField|FileOSSField`，方便 Pipeline 与下载器识别。

---

## 3. Pipeline `src/pipelines/rcsb_pdb_pipeline.py`

`RcsbPdbPipeline` 继承 `MongoDBRawStoragePipeline`，核心配置：

- `connect_key = "default"`：引用 `settings.py` 中的 Mongo 连接
- `collection_name = "rcsb_pdb_structures_all"`：入库集合
- `item_class = RcsbAllApiItem`：只接受规范化 Item

若需写入其他库，可通过继承覆盖 `collection_name` 或实现额外的 Pipeline。

---

## 4. 字段过滤 `src/spider/rcsb_pdb/field_filter.py`

`FieldFilter` 基于 JSON 配置裁剪数据，常见用途：

- 控制 Entry/Entity 中的字段保留与剔除
- 对嵌套字段设置 include/exclude 规则
- 指定白名单或黑名单模式

示例规则（详见 `field_filter_config.json`）：

```json
{
  "mode": "whitelist",
  "CoreEntry": {
    "include_all": false,
    "include_fields": ["rcsb_id", "struct", "rcsb_accession_info"]
  }
}
```

---

## 5. 主爬虫 `src/spider/rcsb_pdb/rcsb_pdb_spider.py`

### 入口参数
- `mode`: `full` / `incremental`
- `max_targets`, `batch_size`, `start_from`
- `pdb_id`: 单条调试
- `field_filter_config`: 自定义过滤文件

### 核心流程
1. `_request_search`：调用 Search API 分页获取 PDB ID
2. `_schedule_entry` & `parse_entry`：拉取 Entry，记录 revision_date
3. `_parse_entity`：抓取 polymer / nonpolymer / branched
4. `_parse_comp` / `_parse_drugbank`：补充化合物/药物详情
5. `_save_result`：写 JSON、构建 Item、更新 Redis/Mongo 游标

### 增量机制
- `RedisManager`：`rcsb_all_api:revision` 哈希记录各 PDB 近期 revision
- `MongoDBManager`：`rcsb_increment_state.last_revision` 记录全局游标
- `_compute_increment_start`：根据 `overlap_days` 回溯

---

## 6. 依赖工具

| 模块 | 作用 |
| --- | --- |
| `src.utils.mongodb_manager.MongoDBManager` | 统一 Mongo 连接 |
| `src.utils.redis_manager.RedisManager` | 提供 Redis 连接池 |
| `src.pipelines.file_download_pipeline` | 下载 CIF/图片并保存 |
| `src.middlewares.*` | 代理、重试、历史数据拦截 |

---

## 7. 修改建议

1. **新需求**：在 Spider 中新增 API 调用 → 更新 Item 字段 → 扩展 Pipeline 入库逻辑。
2. **字段策略**：通过 JSON 配置控制输出，不建议直接修改代码。
3. **部署优化**：可在 `custom_settings` 中调整并发、日志、Pipeline 顺序。

更多实操示例见 [使用示例](examples.md)。
