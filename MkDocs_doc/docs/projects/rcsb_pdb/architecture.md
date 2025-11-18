# 架构设计

---

## 1. 总览

RCSB PDB 项目采用「采集层 + 裁剪层 + 存储层 + 状态层」的分层设计：

```
┌───────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐
│ Scrapy    │ -> │ FieldFilter│ -> │ Pipelines   │ -> │ Mongo/Files│
│ Spider    │    │ (JSON 规则)│    │ (File/Mongo)│    │ + Redis     │
└───────────┘    └────────────┘    └────────────┘    └────────────┘
        ↑                  ↑                 ↑                ↑
        │                  │                 │                │
        └──── Playwright / 中间件 ───┴─── 配置/日志 ─────┴─── 游标/缓存
```

---

## 2. 关键组件

| 模块 | 位置 | 作用 |
| --- | --- | --- |
| `RcsbAllApiSpider` | `src/spider/rcsb_pdb/rcsb_pdb_spider.py` | 调度 Search / Entry / Entity / ChemComp / DrugBank 请求 |
| `FieldFilter` | `src/spider/rcsb_pdb/field_filter.py` | 按 JSON 规则裁剪字段，支持白名单/黑名单 |
| `RcsbAllApiItem` | `src/items/rcsb_pdb_item.py` | 定义结构条目的标准格式 |
| `RcsbPdbPipeline` | `src/pipelines/rcsb_pdb_pipeline.py` | 将 Item 写入 Mongo，并落地附件 |
| `settings.py` | `src/settings.py` | Scrapy、数据库、日志、自定义中间件配置 |
| `MongoDBManager/RedisManager` | `src/utils/` | 管理增量游标、Revision 缓存 |

---

## 3. 数据流

1. **Search 阶段**：构造查询体 `_build_search_body`，按 `revision_date` 升序拉取 PDB ID。
2. **Entry 阶段**：逐个 PDB ID 获取核心属性，同时记录 revision_date 与文件下载 URL。
3. **Entity 阶段**：并发抓取 polymer / nonpolymer / branched 实体，对结果应用 `FieldFilter`。
4. **ChemComp / DrugBank 阶段**：基于实体中出现的化合物 ID 补充化学/药物信息。
5. **存储阶段**：
   - JSON：`spider/rcsb_pdb/inhance/<PDB_ID>.json`
   - Mongo：`raw_data.rcsb_pdb_structures_all`
   - Redis：`rcsb_all_api:revision`，用于增量去重
6. **增量游标**：`MongoDBManager` 在爬虫关闭时更新 `rcsb_increment_state.last_revision`。

---

## 4. 运行模式

| 模式 | 入口参数 | 说明 |
| --- | --- | --- |
| `full` | `scrapy crawl rcsb_all_api -a mode=full` | 按 revision_date 升序全量抓取 |
| `incremental` | `-a mode=incremental -a overlap_days=2` | 基于 Mongo 游标 + Redis 判重，向前重叠 N 天 |
| `manual` | `-a pdb_id=1A1A` | 仅抓取指定 PDB ID，常用于调试 |

---

## 5. 中间件与扩展

- `CaptchaMiddleware`：全局验证码拦截
- `CustomRetryMiddleware`：替换默认 Retry，支持代理异常码
- `BaseProxyMiddleware`：统一注入代理
- `HistoryDataMiddleware`：过滤历史重复请求
- Playwright（可选）：通过 `PLAYWRIGHT_PROCESS_REQUEST_HEADERS` 注入自定义头部

---

## 6. 部署拓扑

| 层级 | 建议部署方式 |
| --- | --- |
| 爬虫节点 | Windows/Linux 主机，支持多进程 Scrapy |
| MongoDB | 独立实例或共享集群，需开启鉴权 |
| Redis | 小型单节点即可，重点保证持久化 |
| 日志/文件 | 网络共享目录或 OSS |

> 若部署到服务器，可通过 `systemd` / `Supervisor` 守护 Scrapy 任务，或迁移至 Airflow/Scheduler。
# 架构设计

本文档介绍 RCSB PDB 爬虫项目的整体架构设计、模块关系和数据流程。

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                    RCSB PDB 爬虫系统                      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────┐  │
│  │  启动脚本     │───▶│  爬虫引擎     │───▶│ 数据管道  │  │
│  │  firing.py   │    │ RcsbAllApi  │    │ Pipeline │  │
│  └──────────────┘    └──────────────┘    └──────────┘  │
│         │                     │                  │       │
│         │                     │                  │       │
│         ▼                     ▼                  ▼       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────┐  │
│  │  参数解析     │    │  API 请求     │    │ 数据存储  │  │
│  │  模式选择     │    │  字段过滤     │    │ MongoDB  │  │
│  └──────────────┘    └──────────────┘    └──────────┘  │
│                                                           │
└─────────────────────────────────────────────────────────┘
         │                     │                  │
         ▼                     ▼                  ▼
  ┌──────────┐          ┌──────────┐      ┌──────────┐
  │  Redis   │          │  MongoDB │      │  文件系统  │
  │  (游标)  │          │ (主存储) │      │ (CIF/图片)│
  └──────────┘          └──────────┘      └──────────┘
```

## 核心模块

### 1. 爬虫模块（Spider）

**位置**：`src/spider/rcsb_pdb/rcsb_pdb_spider.py`

**职责**：
- 管理爬虫运行模式（单条/全量/增量）
- 调用 RCSB PDB API 获取数据
- 处理数据解析和字段过滤
- 管理增量游标

**关键类**：
- `RcsbAllApiSpider`：主爬虫类

### 2. 数据项模块（Items）

**位置**：`src/items/other/rcsb_pdb_item.py`

**职责**：
- 定义数据结构
- 标准化数据输出
- 字段类型验证

**关键类**：
- `RcsbAllApiItem`：RCSB PDB 数据项

### 3. 管道模块（Pipelines）

**位置**：`src/pipelines/storage/rcsb_pdb_pipeline.py`

**职责**：
- 文件下载（CIF、验证图片）
- 文件路径替换
- 数据入库（MongoDB）

**关键类**：
- `RcsbPdbPipeline`：数据入库管道

### 4. 字段过滤模块（Field Filter）

**位置**：`src/spider/rcsb_pdb/field_filter.py`

**职责**：
- 根据配置文件过滤字段
- 减少数据量
- 提高采集效率

**关键类**：
- `FieldFilter`：字段过滤器

## 数据流程

### 全量模式流程

```
1. 启动爬虫
   ↓
2. 调用 Search API 获取 PDB ID 列表
   ↓
3. 批量请求 Entry API 获取基础信息
   ↓
4. 并行请求相关 API（polymer_entity, chemcomp 等）
   ↓
5. 字段过滤（如果配置了过滤规则）
   ↓
6. 下载文件（CIF、验证图片）
   ↓
7. 数据入库（MongoDB）
```

### 增量模式流程

```
1. 启动爬虫（incremental 模式）
   ↓
2. 从 MongoDB 读取上次的 revision_date 游标
   ↓
3. 计算增量起始日期（考虑 overlap_days）
   ↓
4. 调用 Search API 查询更新数据
   ↓
5. 后续流程与全量模式相同
   ↓
6. 更新 revision_date 游标到 Redis
```

### 单条模式流程

```
1. 启动爬虫（指定 pdb_id）
   ↓
2. 直接请求 Entry API 获取数据
   ↓
3. 请求相关 API
   ↓
4. 字段过滤
   ↓
5. 下载文件
   ↓
6. 输出到本地 JSON 文件（不入库）
```

## 模块关系

### 依赖关系

```
RcsbAllApiSpider
    ├── FieldFilter (字段过滤)
    ├── RcsbAllApiItem (数据项)
    ├── MongoDBManager (数据库操作)
    └── RedisManager (游标管理)
         │
         └── RcsbPdbPipeline (数据入库)
              └── MongoDBRawStoragePipeline (基类)
```

### 数据流向

```
API 响应 → Spider 解析 → Item 封装 → Pipeline 处理 → MongoDB 存储
                                    ↓
                              文件下载 → 文件系统
```

## 设计决策

### 1. 为什么使用 MongoDB？

- **文档型数据库**：适合存储 JSON 格式的蛋白质结构数据
- **灵活的数据结构**：不同 PDB 结构可能有不同的字段
- **高性能**：适合大量数据的写入和查询

### 2. 为什么使用 Redis 存储游标？

- **高性能**：增量游标需要频繁读写
- **持久化**：支持数据持久化，避免游标丢失
- **TTL 支持**：可以设置过期时间

### 3. 为什么支持字段过滤？

- **减少数据量**：RCSB PDB 数据量巨大，全量采集可能不需要所有字段
- **提高效率**：减少网络传输和存储空间
- **灵活性**：通过配置文件控制，无需修改代码

### 4. 为什么支持三种运行模式？

- **单条模式**：便于调试和测试
- **全量模式**：首次采集或重建数据
- **增量模式**：日常更新，避免重复采集

## 扩展性

### 添加新的 API 端点

1. 在 `API_ENDPOINTS` 中添加新端点
2. 在 `SECTION_MAP` 中添加映射关系
3. 在 `_fetch_related_data` 中添加请求逻辑

### 添加新的数据存储

1. 继承 `MongoDBRawStoragePipeline`
2. 实现自定义存储逻辑
3. 在 `custom_settings` 中配置 Pipeline

### 添加新的字段过滤规则

1. 编辑 `field_filter_config.json`
2. 定义需要保留的字段路径
3. 重启爬虫应用新规则

## 性能优化

### 并发控制

- 使用 Scrapy 的 `CONCURRENT_REQUESTS` 控制并发数
- 默认并发数为 32，可根据网络情况调整

### 批量请求

- 使用 `batch_size` 参数控制每批请求数量
- 默认批量大小为 50，可根据 API 限制调整

### 增量更新

- 使用 `overlap_days` 参数避免遗漏数据
- 默认重叠 1 天，可根据更新频率调整

## 相关文档

- [系统全景](api.md) - 查看完整的 API 文档
- [核心模块](guide.md) - 了解各模块的详细说明
- [配置说明](configuration.md) - 了解配置参数

