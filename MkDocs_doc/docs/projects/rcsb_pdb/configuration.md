# 配置说明

本页汇总 Scrapy、数据库以及运行参数的配置方式，便于快速对齐环境。

---

## 1. Scrapy 设置（`src/settings.py`）

### 并发与重试

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `CONCURRENT_REQUESTS` | 32 | 全局并发数，建议根据 IP/代理能力调节 |
| `DOWNLOAD_DELAY` | 1 | 请求间隔（秒） |
| `RANDOMIZE_DOWNLOAD_DELAY` | True | 在 `[0.5x, 1.5x]` 范围内抖动 |
| `RETRY_TIMES` | 30 | 失败重试次数 |
| `RETRY_HTTP_CODES` | `[500,502,503,504,522,524,408,429,440]` | 需要重试的状态码 |
| `DOWNLOAD_TIMEOUT` | 60 | 请求超时时间（秒） |

### 中间件

```python
DOWNLOADER_MIDDLEWARES = {
    'src.middlewares.captcha_middleware.CaptchaMiddleware': 540,
    'src.middlewares.custom_retry_middleware.CustomRetryMiddleware': 550,
    'src.middlewares.proxy_middleware.BaseProxyMiddleware': 400,
    'src.middlewares.history_data_middleware.HistoryDataMiddleware': 300,
}
```

可根据部署环境启用/禁用代理、验证码或 Playwright 相关中间件。

---

## 2. 数据库配置

### MySQL

```python
MYSQL_DATABASES = {
    "default": {
        "host": "192.168.1.245",
        "port": 3306,
        "user": "medpeer",
        "password": "medpeer",
        "database": "raw_data",
        "charset": "utf8mb4",
    }
}
```

> 仅在少量辅助脚本中使用，可按需改为环境变量 `MYSQL_PASSWORD`。

### MongoDB

```python
MONGODB_DATABASES = {
    "default": {
        "host": "192.168.1.245",
        "port": 27017,
        "user": "medpeer",
        "password": "medpeer",
        "auth_source": "admin",
        "database": "raw_data",
    }
}
```

### Redis

```python
REDIS_DATABASES = {
    "default": {
        "host": "101.200.62.36",
        "port": 6379,
        "password": "medpeer",
        "database": 1,
    }
}
```

Redis 用于记录 `rcsb_all_api:revision`，请保证 TTL ≥ 60 天。

---

## 3. 运行参数

| 参数 | 说明 |
| --- | --- |
| `mode` | `full` / `incremental` |
| `max_targets` | 一次运行的最大结构数 |
| `batch_size` | Search API 的分页条数 |
| `pdb_id` | 手动指定单条结构 |
| `field_filter_config` | 指定字段过滤 JSON |
| `overlap_days` | 增量运行时的回溯天数 |
| `output_filename` | 手动模式下的 JSON 文件名 |

示例：

```bash
scrapy crawl rcsb_all_api \
  -a mode=incremental \
  -a max_targets=1000 \
  -a overlap_days=2 \
  -a field_filter_config=field_filter_config.json
```

---

## 4. 日志与文件

| 配置 | 说明 |
| --- | --- |
| `LOG_ENABLED = True` | 启用日志 |
| `LOG_LEVEL = "INFO"` | 可通过命令行 `-s LOG_LEVEL=DEBUG` 覆盖 |
| `LOG_FILE` | 默认 `None`，由 `firing.py` 决定命名 |
| `FILES_STORE` / `IMAGES_STORE` | 依赖 `UPLOAD_PATH`，需指向可写路径 |

建议在服务器上将日志输出目录挂载为共享存储，方便排查。

---

## 5. Playwright / 代理（可选）

- `PLAYWRIGHT_PROCESS_REQUEST_HEADERS`：自定义请求头（若启用了 Playwright 中间件）
- `BaseProxyMiddleware`：在 `settings.py` 中设置默认代理地址
- `TwistedSemaphoreMiddleware`：如需更精细的并发控制，可开启并配置 `SEMAPHORE_CONFIGS`

---

## 6. 推荐的环境变量

```bash
set RCSB_MONGO_URI=mongodb://user:pwd@host:27017/raw_data
set RCSB_REDIS_URI=redis://:pwd@host:6379/1
set RCSB_FILES_STORE=D:\data\rcsb
```

代码层可通过 `os.getenv` 读取，既避免泄露常量，又方便切换环境。

更多示例见 [使用示例](examples.md) 与 [故障排查](troubleshooting.md)。
# 配置说明

本文档详细说明 RCSB PDB 爬虫项目的所有配置项，包括数据库配置、Scrapy 配置、运行参数等。

## 配置文件位置

主要配置文件：`src/settings.py`

## 数据库配置

### MongoDB 配置

```python
MONGODB_DATABASES = {
    "default": {
        "type": "mongodb",
        'user': 'medpeer',              # 用户名
        'password': 'medpeer',          # 密码
        'auth_source': 'admin',         # 认证数据库
        'host': '192.168.1.245',        # 主机地址
        'port': 27017,                  # 端口
        'database': 'raw_data',         # 数据库名
        "charset": "utf8mb4",
        "direct_connection": True,      # 单节点连接
    },
}
```

**说明**：
- MongoDB 是主存储数据库，所有采集的数据都会写入这里
- 集合名称由 `RcsbPdbPipeline.collection_name` 指定，默认为 `rcsb_pdb_structures_all`
- 增量模式的游标也存储在 MongoDB 的 `rcsb_increment_state` 集合中

### Redis 配置

```python
REDIS_DATABASES = {
    "default": {
        "type": "redis",
        'password': 'medpeer',          # 密码
        'host': '101.200.62.36',       # 主机地址
        'port': 6379,                  # 端口
        'database': 1,                 # 数据库编号
    }
}
```

**说明**：
- Redis 用于存储增量游标（revision_date）
- 增量模式必需，全量模式和单条模式不需要
- 游标存储在 Hash 中，key 为 `rcsb_all_api:revision`，TTL 为 60 天

### MySQL 配置（可选）

```python
MYSQL_DATABASES = {
    "default": {
        "type": "mysql",
        'user': 'medpeer',
        'password': 'medpeer',
        'host': '192.168.1.245',
        'port': 3306,
        'database': 'raw_data',
        "charset": "utf8mb4"
    },
}
```

**说明**：
- MySQL 配置是可选的，当前项目主要使用 MongoDB
- 如果后续需要 MySQL 存储，可以在这里配置

## Scrapy 基础配置

### 项目配置

```python
BOT_NAME = "src"
SPIDER_MODULES = ["src.spiders"]
NEWSPIDER_MODULE = "src.spiders"
```

### 爬虫行为配置

```python
# 不遵循 robots.txt
ROBOTSTXT_OBEY = False

# 下载延迟（秒）
DOWNLOAD_DELAY = 1

# 随机化下载延迟
RANDOMIZE_DOWNLOAD_DELAY = True

# 并发请求数量
CONCURRENT_REQUESTS = 32
```

**说明**：
- `DOWNLOAD_DELAY` 控制相同网站两个请求之间的间隔
- `RANDOMIZE_DOWNLOAD_DELAY` 会在 0.5 * DOWNLOAD_DELAY 到 1.5 * DOWNLOAD_DELAY 之间随机
- `CONCURRENT_REQUESTS` 可以根据网络情况调整，默认 32

### 重试配置

```python
RETRY_ENABLED = True              # 启用重试
RETRY_TIMES = 30                  # 重试次数
DOWNLOAD_TIMEOUT = 60            # 下载超时时间（秒）
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429, 440]
```

**说明**：
- `RETRY_HTTP_CODES` 指定哪些 HTTP 状态码需要重试
- 440 是代理超过带宽的状态码
- 429 是请求频率过高的状态码

## 中间件配置

### 下载中间件

```python
DOWNLOADER_MIDDLEWARES = {
    'src.middlewares.captcha_middleware.CaptchaMiddleware': 540,
    'src.middlewares.custom_retry_middleware.CustomRetryMiddleware': 550,
    'src.middlewares.proxy_middleware.BaseProxyMiddleware': 400,
    'src.middlewares.history_data_middleware.HistoryDataMiddleware': 300,
}
```

**说明**：
- 中间件按数字顺序执行，数字越小越先执行
- `CaptchaMiddleware`：处理验证码
- `CustomRetryMiddleware`：自定义重试逻辑
- `BaseProxyMiddleware`：代理中间件
- `HistoryDataMiddleware`：历史数据中间件

### 爬虫中间件

```python
SPIDER_MIDDLEWARES = {
    'src.middlewares.custom_retry_middleware.CustomExceptionMiddleware': 543,
}
```

## Pipeline 配置

在爬虫的 `custom_settings` 中配置：

```python
custom_settings = {
    "ITEM_PIPELINES": {
        "src.pipelines.file_download_pipeline.FileDownloadPipeline": 200,
        "src.pipelines.file_replacement_pipeline.FileReplacementPipeline": 300,
        "src.pipelines.storage.rcsb_pdb_pipeline.RcsbPdbPipeline": 400,
    },
    "LOG_LEVEL": "INFO",
}
```

**Pipeline 执行顺序**：
1. `FileDownloadPipeline` (200) - 下载 CIF 文件和验证图片
2. `FileReplacementPipeline` (300) - 替换文件路径为 OSS 路径
3. `RcsbPdbPipeline` (400) - 数据入库

## 文件存储配置

```python
# 文件存储路径
FILES_STORE = UPLOAD_PATH          # 下载文件存放地址
IMAGES_STORE = UPLOAD_PATH         # 图片文件存放地址

# 允许媒体文件重定向
MEDIA_ALLOW_REDIRECTS = True
```

**说明**：
- `UPLOAD_PATH` 在 `src/constant.py` 中定义
- 下载的文件会先存储到本地，然后上传到 OSS
- Pipeline 会自动处理文件路径替换

## 日志配置

```python
LOG_ENABLED = True
LOG_ENCODING = "utf-8"
LOG_FILE_APPEND = True
LOG_FORMAT = '...'  # 日志格式
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'
LOG_FORMATTER = src.utils.base_logger.BaseSpiderLogFormatter
LOGSTATS_INTERVAL = 60.0
```

**说明**：
- 日志文件路径在 `firing.py` 中动态生成
- 日志格式包含进程ID、线程ID、调用文件等信息
- `LOGSTATS_INTERVAL` 控制统计信息的记录间隔

## 爬虫运行参数

### 命令行参数

```bash
# 单条模式
scrapy crawl rcsb_all_api -a pdb_id=1ABC -a output_filename=test.json

# 全量模式
scrapy crawl rcsb_all_api -a mode=full -a max_targets=100 -a batch_size=50

# 增量模式
scrapy crawl rcsb_all_api -a mode=incremental -a overlap_days=1
```

### 参数说明

| 参数名 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| `pdb_id` | str | PDB ID（单条模式） | None |
| `output_filename` | str | 输出文件名（单条模式） | `data_real_all.json` |
| `field_filter_config` | str | 字段过滤配置文件路径 | None |
| `mode` | str | 运行模式（full/incremental） | `full` |
| `max_targets` | int | 最大采集数量 | 200 |
| `start_from` | int | Search API 分页起点 | 0 |
| `batch_size` | int | 每批请求数量 | 50 |
| `overlap_days` | int | 增量模式向前重叠天数 | 1 |

## 环境变量

### 日志路径

在 `src/constant.py` 中配置：

```python
LOG_PATH = "/path/to/logs"
UPLOAD_PATH = "/path/to/uploads"
```

### 代理配置（可选）

如果需要使用代理，可以在 `firing.py` 中取消注释：

```python
# os.environ['http_proxy'] = 'http://127.0.0.1:10810'
# os.environ['https_proxy'] = 'http://127.0.0.1:10810'
```

## 配置最佳实践

### 1. 开发环境配置

- 降低 `CONCURRENT_REQUESTS` 到 8-16
- 设置 `LOG_LEVEL = "DEBUG"` 查看详细日志
- 使用单条模式进行测试

### 2. 生产环境配置

- 提高 `CONCURRENT_REQUESTS` 到 32-64（根据网络情况）
- 设置 `LOG_LEVEL = "INFO"` 或 `"WARNING"`
- 使用增量模式进行日常更新
- 配置合适的 `max_targets` 和 `batch_size`

### 3. 性能优化

- 根据 API 限制调整 `DOWNLOAD_DELAY` 和 `CONCURRENT_REQUESTS`
- 使用字段过滤减少数据量
- 合理设置 `batch_size` 平衡效率和稳定性

## 相关文档

- [快速开始](getting-started.md) - 环境配置和安装
- [使用示例](examples.md) - 配置使用示例
- [故障排查](troubleshooting.md) - 配置相关问题

