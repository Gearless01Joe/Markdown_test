# 配置说明

集中记录「改哪几个文件就能调整环境」以及常见命令行参数，方便部署与排障。

---

## 1. 关键文件

| 文件 | 作用 |
| --- | --- |
| `src/settings.py` | Scrapy 全局配置、数据库连接、中间件、日志默认值 |
| `src/constant.py` | 运行时目录、日志路径、公共域名/接口常量 |
| `firing.py` | 运行入口，按需拼装 Scrapy 命令并设置日志文件 |

> 若需要按环境切换配置，建议把敏感信息放到环境变量，Python 中通过 `os.getenv` 读取。

---

## 2. 数据库与缓存

```python
MONGODB_DATABASES = {
    "default": {
        "host": "192.168.1.245",
        "port": 27017,
        "user": "medpeer",
        "password": "medpeer",
        "auth_source": "admin",
        "database": "raw_data",
        "direct_connection": True,
    }
}

REDIS_DATABASES = {
    "default": {
        "host": "101.200.62.36",
        "port": 6379,
        "password": "medpeer",
        "database": 1,
    }
}
```

- **Mongo**：主数据落地、增量游标，`RcsbPdbPipeline.collection_name = "rcsb_pdb_structures_all"`。
- **Redis**：`rcsb_all_api:revision` Hash，TTL 默认 60 天，可通过 `REDIS_TTL_SECONDS` 调整。
- **MySQL**：可选，没有相关依赖可保持默认。

推荐环境变量示例：

```bash
set RCSB_MONGO_URI=mongodb://user:pwd@host:27017/raw_data
set RCSB_REDIS_URI=redis://:pwd@host:6379/1
set RCSB_FILES_STORE=D:\data\rcsb
```

---

## 3. Scrapy 与并发设置

```python
BOT_NAME = "src"
SPIDER_MODULES = ["src.spiders"]
NEWSPIDER_MODULE = "src.spiders"

CONCURRENT_REQUESTS = 32
DOWNLOAD_DELAY = 1
RANDOMIZE_DOWNLOAD_DELAY = True
RETRY_TIMES = 30
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429, 440]
DOWNLOAD_TIMEOUT = 60
```

- 命令行可通过 `-s` 覆盖，例如 `-s CONCURRENT_REQUESTS=8 -s DOWNLOAD_DELAY=2`。
- Spider 内部可在 `custom_settings` 重写（RCSB 默认延迟 0.3 秒）。

### 中间件

```python
DOWNLOADER_MIDDLEWARES = {
    "src.middlewares.captcha_middleware.CaptchaMiddleware": 540,
    "src.middlewares.custom_retry_middleware.CustomRetryMiddleware": 550,
    "src.middlewares.proxy_middleware.BaseProxyMiddleware": 400,
    "src.middlewares.history_data_middleware.HistoryDataMiddleware": 300,
}
```

- 可在 Spider `custom_settings` 中关闭特定中间件；或在命令行使用 `-s DOWNLOADER_MIDDLEWARES="{}"` 临时禁用。
- 若启用 Playwright，可结合 `PLAYWRIGHT_PROCESS_REQUEST_HEADERS` 注入浏览器头部。

---

## 4. 文件与日志

| 配置 | 说明 |
| --- | --- |
| `LOG_PATH`, `UPLOAD_PATH`, `RUNTIME_PATH` | 在 `constant.py` 中设置，需指向有写权限的共享目录 |
| `LOG_LEVEL` | 默认 `INFO`，调试可改为 `DEBUG`；命令行可使用 `-s LOG_LEVEL=DEBUG` |
| `LOG_FILE` | 由 `firing.py` 决定，命名规则 `爬虫-日期-参数.log` |
| `FILES_STORE` / `IMAGES_STORE` | 与 `UPLOAD_PATH` 保持一致，Pipeline 会自动写入 |
| `MEDIA_ALLOW_REDIRECTS` | 已启用，保证 CIF/图片重定向可下载 |

需要输出到其它日志系统时，可在 `src/utils/base_logger.py` 中扩展 Handler。

---

## 5. 命令行参数（Scrapy `-a`）

| 参数 | 描述 | 默认 |
| --- | --- | --- |
| `mode` | `full` / `incremental` | `full` |
| `pdb_id` | 指定单个结构 ID | `None` |
| `max_targets` | 本次任务最多采集多少条 | 100 |
| `batch_size` | Search API 每批条数 | `min(100, max_targets)` |
| `start_from` | Search API 起始偏移 | 0 |
| `overlap_days` | 增量回溯天数 | 1 |
| `output_filename` | 单条模式输出 JSON 名称 | `rcsb_all_api.json` |
| `field_filter_config` | 预留给字段过滤 | `None` |

```bash
scrapy crawl rcsb_all_api ^
  -a mode=incremental ^
  -a max_targets=1500 ^
  -a overlap_days=2 ^
  -s LOG_LEVEL=INFO
```

---

## 6. 代理 / Playwright（可选）

- `BaseProxyMiddleware`：在 `settings.py` 或命令行 `-s HTTP_PROXY=...` 注入。
- `TwistedSemaphoreMiddleware`：如果需要精细控制不同域名的并发，可启用并配置 `SEMAPHORE_CONFIGS`。
- `PLAYWRIGHT_PROCESS_REQUEST_HEADERS`：对特定接口要求浏览器头部时开启。

---

## 7. 常见覆盖场景

| 需求 | 命令示例 |
| --- | --- |
| 临时关闭文件下载 | `scrapy crawl ... -s ITEM_PIPELINES="{'src.pipelines.storage.rcsb_pdb_pipeline.RcsbPdbPipeline': 400}"` |
| 调整日志输出 | `scrapy crawl ... -s LOG_FILE=D:/logs/rcsb.log -s LOG_LEVEL=DEBUG` |
| 清空 Redis 游标 | `redis-cli DEL rcsb_all_api:revision` |
| 清空 Mongo 游标 | `mongo raw_data --eval "db.rcsb_increment_state.remove({})"` |

---

更多运行姿势参考 [使用示例](examples.md)，若遇到连接或性能问题可对照 [故障排查](troubleshooting.md)。

