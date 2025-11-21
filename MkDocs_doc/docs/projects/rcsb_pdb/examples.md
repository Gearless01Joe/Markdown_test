# 使用示例

覆盖最常用的运行姿势。所有命令均在 `code_liu/RCSB_PDB/` 目录执行，确保虚拟环境已激活。

---

## 1. 快速命令集合

| 场景 | 命令 | 说明 |
| --- | --- | --- |
| 全量导入 1k 条 | `scrapy crawl rcsb_all_api -a mode=full -a max_targets=1000 -a batch_size=100 -s LOG_LEVEL=INFO` | 按 `revision_date` 升序遍历，适合首次建库 |
| 日常增量 | `scrapy crawl rcsb_all_api -a mode=incremental -a overlap_days=2` | Mongo&Redis 持游标，`overlap_days` 防止漏数据 |
| 单条调试 | `scrapy crawl rcsb_all_api -a pdb_id=7PZJ -a output_filename=7PZJ.debug.json` | 不依赖 Mongo/Redis，输出 JSON 便于排障 |
| 降低并发 | `scrapy crawl rcsb_all_api -s CONCURRENT_REQUESTS=8 -s DOWNLOAD_DELAY=2` | 代理或海外网络不稳定时使用 |

> 任何 `-a` 参数后都可以附加 `-s LOG_FILE=runtime/log/manual.log` 以便单独留痕。

---

## 2. 参数搭配建议

### 分批全量（夜间导入）

```bash
scrapy crawl rcsb_all_api \
  -a mode=full \
  -a max_targets=500 \
  -a batch_size=50 \
  -a start_from=2000
```

- `start_from` 可配合调度任务做断点续跑。
- `max_targets` 建议控制在 500~1000，便于重试与回滚。

### 增量 + 回溯

```bash
scrapy crawl rcsb_all_api \
  -a mode=incremental \
  -a overlap_days=3 \
  -a max_targets=2000 \
  -s AUTOTHROTTLE_TARGET_CONCURRENCY=6.0
```

- `overlap_days` 取 2~3 天，即使游标写失败也能自动补齐。
- 可以视情况在命令里直接覆盖自动限流参数。

---

## 3. 维护/排障命令

| 目的 | 命令 |
| --- | --- |
| 清空 Redis 游标 | `redis-cli DEL rcsb_all_api:revision` |
| 重置 Mongo 游标 | `mongo raw_data --eval "db.rcsb_increment_state.remove({})"` |
| 查看最近写入记录 | `mongo raw_data --eval "db.rcsb_pdb_structures_all.find().sort({max_revision_date:-1}).limit(5).pretty()"` |
| 检查附件下载 | `ls runtime/storage/rcsb_pdb_all | tail`（Windows 使用 `Get-ChildItem`） |

> 实际排查时建议配合 `LOG_LEVEL=DEBUG`，查看 `RevisionState` 与 `file_audit` 日志。

---

## 4. 代码/调度示例

### 4.1 `firing.py` 触发

```python
from firing import start_spider

start_spider(
    spider_name="rcsb_all_api",
    mode="incremental",
    overlap_days=2,
    service_object="医学信息支撑服务平台",
)
```

用于 VS Code/PyCharm 调试，可直接打断点。

### 4.2 定时任务（Linux Crontab）

```bash
0 2 * * * source /opt/rcsb/.venv/bin/activate && \
  cd /opt/rcsb/code_liu/RCSB_PDB && \
  scrapy crawl rcsb_all_api -a mode=incremental -a overlap_days=2 \
  >> /opt/rcsb/runtime/log/daily.log 2>&1
```

---

## 5. 常见组合问题

- **只想写入 Mongo，不下载文件**  
  `scrapy crawl ... -s ITEM_PIPELINES="{'src.pipelines.storage.rcsb_pdb_pipeline.RcsbPdbPipeline': 400}"`

- **需要放大超时时间**  
  `scrapy crawl ... -s DOWNLOAD_TIMEOUT=120 -s RETRY_TIMES=50`

- **断点续跑**  
  根据日志中的 `start` 值调整 `-a start_from=`；若 Search API 结果集较大，也可以把 `max_targets` 分多次跑完。

---

更多组合可通过 `scrapy crawl rcsb_all_api -h` 查看；如需自定义流程，建议在 `custom_settings` 或 `firing.py` 中封装，方便团队复用。

