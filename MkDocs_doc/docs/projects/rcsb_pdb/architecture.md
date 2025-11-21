# 架构设计

RCSB PDB 爬虫由 Scrapy 驱动，按照「采集层 → 服务层 → 管道层 → 状态层」拆分。目标是在可控并发下持续同步 PDB Entry、实体、ChemComp、DrugBank 数据，并在 Mongo/Redis 中维护可追溯的状态。

```
┌────────────┐    ┌───────────────┐    ┌──────────────┐    ┌────────────┐
│ Request    │ -> │ RcsbAllApi    │ -> │ Pipelines     │ -> │ Storage     │
│ Builder    │    │ Spider +Svc   │    │ (File/Mongo)  │    │ Mongo/Redis │
└────────────┘    └───────────────┘    └──────────────┘    └────────────┘
        ↑                    ↑                   ↑                   ↑
        │                    │                   │                   │
        └────── 日志/配置 ───┴── 文件审计 ───────┴── 增量游标 ─────┴── 调度/监控
```

---

## 1. 组件解剖

| 层级 | 文件 | 关键类 / 函数 | 职责 |
| --- | --- | --- | --- |
| **启动层** | `firing.py` | `start_spider` | 解析命令行参数，拼装 Scrapy 命令，附加日志配置 |
| **请求层** | `src/spiders/rcsb_pdb/request_builder.py` | `RequestBuilder` | 构建 Search / Entry / Entity / ChemComp 等 REST 请求 |
| **服务层** | `src/spiders/rcsb_pdb/services.py` | `DataParser`, `EntryContext`, `FileDownloader`, `RevisionState` | 解析 JSON、维护上下文、探测附件、管理增量游标 |
| **爬虫层** | `src/spiders/rcsb_pdb/rcsb_pdb_spider.py` | `RcsbAllApiSpider` | 入口模式控制、调度请求、拼装 `RcsbAllApiItem` |
| **数据层** | `src/items/rcsb_pdb_item.py` | `RcsbAllApiItem` | 统一结构化字段（Entry/Entity/ChemComp/DrugBank/附件） |
| **管道层** | `src/pipelines/file_download_pipeline.py`, `file_replacement_pipeline.py`, `storage/rcsb_pdb_pipeline.py` | `FileDownloadPipeline`, `FileReplacementPipeline`, `RcsbPdbPipeline` | 文件下载与替换、结果入库 Mongo |
| **管理层** | `src/utils/mongodb_manager.py`, `redis_manager.py` | `MongoDBManager`, `RedisManager` | 单例级连接池，提供稳定的 DB/缓存访问 |

> 字段过滤相关参数已预留，最终仍由 `EntryContext` + Pipeline 组合来裁剪与序列化字段。

---

## 2. 数据流程

1. **Search**：`RequestBuilder.build_search_request` 按 `revision_date` 升序分页，默认批次 100 条。
2. **Entry**：`parse_entry` 解析核心属性、revision、验证报告，并初始化 `EntryContext`。
3. **Entity**：对 polymer / nonpolymer / branched 进行并发抓取，累计到 `context.pending`。
4. **ChemComp & DrugBank**：根据实体引用动态拼接请求，结果缓存在 `context.comp_data / drugbank_data`。
5. **Assembly**：请求 `assembly` 端点，补充结构装配信息。
6. **附件探测**：`FileDownloader` 并发探测 CIF、结构图、验证报告，写入 `file_urls` 与审计信息。
7. **生成 Item**：`EntryContext.to_item()` 将收集到的数据整理为 `RcsbAllApiItem`，并标记 `max_revision_date`。
8. **Pipeline**：依次触发文件下载、路径替换、Mongo 入库，最终在 `raw_data.rcsb_pdb_structures_all` 存档。
9. **游标更新**：`RevisionState` 在 `close_spider` 时把本轮最大 revision 写回 Mongo + Redis。

---

## 3. 模式与状态

| 模式 | 描述 | 入口命令 |
| --- | --- | --- |
| `full` | 以 `revision_date` 升序遍历 Search API，常用于首轮导入或重建 | `scrapy crawl rcsb_all_api -a mode=full` |
| `incremental` | 读取 Mongo `rcsb_increment_state` 与 Redis `rcsb_all_api:revision`，只处理更新的数据 | `scrapy crawl rcsb_all_api -a mode=incremental -a overlap_days=2` |
| `manual` | 指定 `pdb_id`，拉取单条数据并输出 JSON，通常用于排障 | `scrapy crawl rcsb_all_api -a pdb_id=1A1A -a output_filename=1A1A.json` |

**状态持久化**

- Mongo：`rcsb_increment_state` 文档保存全局游标、执行时间、最近 revision。
- Redis：`HSET rcsb_all_api:revision <pdb_id> <revision>`，TTL 默认 60 天，用于快速判重。

---

## 4. 并发与容错

| 配置 | 默认 | 说明 |
| --- | --- | --- |
| `CONCURRENT_REQUESTS` | 32 | 全局并发，视代理 / 带宽可调到 64 |
| `CONCURRENT_REQUESTS_PER_DOMAIN` | 16 (Spider 内覆盖) | 避免单域过载 |
| `DOWNLOAD_DELAY` | 0.3s（Spider 自定义） | 搭配 `RANDOMIZE_DOWNLOAD_DELAY=True` |
| `RETRY_TIMES` | 30 | 结合 `CustomRetryMiddleware`，对 429/503/网络抖动友好 |
| `DOWNLOAD_TIMEOUT` | 30 | 可基于网络状况改为 60 |
| `AUTOTHROTTLE_ENABLED` | True | 目标并发 4，平衡 Search/API 速率 |

若部署在代理池或限流环境，可使用 `-s CONCURRENT_REQUESTS=8 -s DOWNLOAD_DELAY=1` 快速降级。

---

## 5. 部署拓扑建议

| 角色 | 建议 |
| --- | --- |
| 爬虫节点 | Windows / Linux 任意，建议 2 核 4G+，定时通过 `Supervisor / systemd / Airflow` 拉起 |
| MongoDB | 与主数据湖共享实例即可，但需开启鉴权并设置备份策略 |
| Redis | 单节点即可，记得开启持久化（AOF/RDB）防止游标丢失 |
| 文件/日志 | 指向 NAS / OSS，便于共享与审计；`LOG_PATH`、`UPLOAD_PATH` 统一指向挂载路径 |

> 线上使用前要确保运行账号对 `runtime/log`、`runtime/storage` 拥有写权限，否则 Pipeline 会直接抛错。

---

## 6. 如何扩展

1. **新增 API 端点**  
   - 在 `src/spiders/rcsb_pdb/constants.py` 的 `API_ENDPOINTS` 增加 URL  
   - 在 `RcsbAllApiSpider.SECTION_MAP`/`_fetch_related_data` 注册新的处理函数

2. **自定义字段或导出格式**  
   - 扩展 `RcsbAllApiItem` 字段  
   - 在 `RcsbPdbPipeline` 或新建 Pipeline 中处理落库逻辑

3. **定制调度策略**  
   - 通过命令行注入新的 `-a` 参数  
   - 在 `firing.py` 中追加 `argparse` 选项即可无缝传递到 Spider

---

掌握以上结构后，可以快速定位性能瓶颈（Search 速率、附件下载）或数据问题（增量游标、Mongo 入库），并沉淀到 [故障排查](troubleshooting.md)。

