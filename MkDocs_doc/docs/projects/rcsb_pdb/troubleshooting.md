# 故障排查

常见问题按照「症状 → 快速定位 → 修复动作」整理，可直接复制命令执行。

---

## 1. mkdocs serve 报 `ModuleNotFoundError`

**症状**：`mkdocstrings: ModuleNotFoundError: No module named 'src...'`

**定位**：
1. 确认已安装 `pip install -r code_liu/RCSB_PDB/requirements.txt`
2. 检查环境变量：`echo %PYTHONPATH%` 中是否包含 `code_liu/RCSB_PDB`

**处理**：
```bash
set PYTHONPATH=%PYTHONPATH%;D:\Python_project\Markdown\code_liu\RCSB_PDB
mkdocs serve
```

---

## 2. MongoDB 连接失败

**症状**：`pymongo.errors.ServerSelectionTimeoutError`

**定位步骤**：
1. `mongo --host <host> --port <port>` 测试网络连通
2. 检查 `src/settings.py` 的账号密码、库名
3. 查看 Mongo 日志是否有鉴权失败

**处理**：
- 更新 `MONGODB_DATABASES["default"]`，或改为读取 `RCSB_MONGO_URI`
- 若只是临时不可用，可在命令行追加 `-s RETRY_TIMES=60`

---

## 3. Redis 游标不生效 / 重复采集

**症状**：增量模式重复抓取旧数据

**定位**：
1. `redis-cli HLEN rcsb_all_api:revision`
2. `mongo raw_data --eval "db.rcsb_increment_state.find().pretty()"`

**处理**：
```bash
redis-cli DEL rcsb_all_api:revision
mongo raw_data --eval "db.rcsb_increment_state.remove({})"
scrapy crawl rcsb_all_api -a mode=full -a max_targets=100  # 重建基线
```

---

## 4. HTTP 429 / 503 频发

**症状**：日志出现大量 `429 Too Many Requests` 或 `503 Service Unavailable`

**解决方案**：
```bash
scrapy crawl rcsb_all_api \
  -s CONCURRENT_REQUESTS=8 \
  -s DOWNLOAD_DELAY=2 \
  -s AUTOTHROTTLE_TARGET_CONCURRENCY=2.0
```
同时检查代理池是否正常、是否被目标站封锁。

---

## 5. 附件缺失（CIF/验证图）

**症状**：Mongo 记录正常，但 `file_urls` 为空或目录没有生成文件

**检查**：
1. 日志中搜索 `FileDownloader` / `validation_image` 关键字
2. 确认 `UPLOAD_PATH` 是否存在、是否有写权限
3. 看看 `context.file_audit` 中的 `missing` 字段

**处理**：
```bash
scrapy crawl rcsb_all_api \
  -a pdb_id=1A1A \
  -s FILES_STORE=D:/temp/rcsb_files
```
若单条测试成功，说明生产目录权限不足；否则需要检查网络或站点可用性。

---

## 6. 任务中途退出 / 没有日志

**排查清单**：
1. 是否通过 `firing.py` 传入 `LOG_FILE`（无日志大概率没写磁盘）
2. Windows 下路径过长，可开启 `LongPathsEnabled` 或切换更短的根目录
3. Supervisor/Airflow 是否对标准输出做了截断

**推荐做法**：为所有生产任务指定日志文件，例如：
```bash
python firing.py --name rcsb_all_api --service_object prod ^
  -s LOG_FILE=D:/rcsb/logs/%DATE:~0,10%-prod.log
```

---

## 7. 清理/重置脚本合集

```bash
# 清空 Redis 游标
redis-cli DEL rcsb_all_api:revision

# 重建 Mongo 集合索引（可选）
mongo raw_data --eval "db.rcsb_pdb_structures_all.createIndex({'PDB_ID': 1}, {unique: true})"

# 只入库、不下载文件
scrapy crawl rcsb_all_api -s ITEM_PIPELINES="{'src.pipelines.storage.rcsb_pdb_pipeline.RcsbPdbPipeline': 400}"
```

---

仍无法定位问题时，请提供：命令参数、完整日志片段、Mongo/Redis 结果，方便在群内协助分析。需要更系统性的建议，可回看 [配置说明](configuration.md) 与 [架构设计](architecture.md)。

