# 快速开始

面向需要落地 RCSB PDB 采集任务的同学，下面的步骤可以在 ~10 分钟内完成环境准备、拉起爬虫并验证结果。

---

## 1. 环境要求

| 组件 | 版本建议 | 用途 |
| --- | --- | --- |
| Python | 3.10+ | 运行 Scrapy 与业务脚本 |
| MongoDB | 4.4+ | 存放结构化结果、增量游标 |
| Redis | 5.0+ | 缓存 revision_date，去重与回溯 |
| Git / pip | 最新 | 获取代码与依赖 |

> 建议为 RCSB_PDB 单独创建虚拟环境，避免与其他项目的 Scrapy 版本冲突。

---

## 2. 克隆与安装

```bash
git clone git@github.com:Gearless01Joe/Markdown_test.git
cd Markdown_test

python -m venv .venv
.venv\Scripts\activate              # macOS / Linux 使用 source .venv/bin/activate

pip install -r code_liu/RCSB_PDB/requirements.txt
pip install -r MkDocs_doc/requirements.txt
```

常用依赖包含 `scrapy`, `pymongo`, `redis`, `structlog` 等；如果公司出网受限，可切换到内部 PyPI 镜像。

---

## 3. 配置环境

1. **数据库与缓存**

   - 编辑 `code_liu/RCSB_PDB/src/settings.py`，将 `MONGODB_DATABASES`、`REDIS_DATABASES`、`MYSQL_DATABASES` 改为自己的地址/账号。
   - 生产环境推荐改为读取环境变量，例如：
     ```bash
     set RCSB_MONGO_URI=mongodb://user:pwd@host:27017/raw_data
     set RCSB_REDIS_URI=redis://:pwd@host:6379/1
     ```

2. **日志与文件路径**

   - 在 `code_liu/RCSB_PDB/src/constant.py` 设置 `LOG_PATH`、`UPLOAD_PATH`、`RUNTIME_PATH`。
   - 确保对应目录存在且具有写权限（尤其是服务器挂载盘）。

3. **PYTHONPATH（运行爬虫与 mkdocstrings 都会用到）**

   ```bash
   set PYTHONPATH=%PYTHONPATH%;D:\Python_project\Markdown\code_liu\RCSB_PDB
   ```

   > 如果使用 VS Code / PyCharm，可在项目解释器设置中添加上述路径，避免 `ModuleNotFoundError: src...`。

---

## 4. 运行首个任务

在 `code_liu/RCSB_PDB` 目录可以选择两种入口：

### 4.1 `firing.py`（适合调试）

```bash
cd code_liu/RCSB_PDB
python firing.py --name rcsb_all_api --service_object "医学信息支撑服务平台"
```

### 4.2 Scrapy 命令行

```bash
# 单条调试
scrapy crawl rcsb_all_api -a pdb_id=1A1A -a output_filename=1A1A.json

# 全量批量
scrapy crawl rcsb_all_api -a mode=full -a max_targets=800 -a batch_size=100

# 增量更新
scrapy crawl rcsb_all_api -a mode=incremental -a overlap_days=2
```

> 运行过程中的日志会根据 `LOG_FILE` 设置写入 `runtime/log/` 或控制台，可通过 `-s LOG_LEVEL=DEBUG` 临时提高日志级别。

---

## 5. 运行参数速查

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `mode` | `full / incremental`，决定 Search 策略 | `full` |
| `pdb_id` | 指定单个结构，常用于调试 | `None` |
| `max_targets` | 本次任务最多采集多少条 | 100 |
| `batch_size` | Search API 每批数量 | `min(100, max_targets)` |
| `start_from` | Search API 起始偏移 | 0 |
| `overlap_days` | 增量回溯天数，防止遗漏 | 1 |
| `output_filename` | 单条模式输出 JSON 名称 | `rcsb_all_api.json` |
| `field_filter_config` | 预留字段过滤配置（仍在实现中） | `None` |

**推荐组合**

- 首次导入：`mode=full + max_targets=2000 + batch_size=200`
- 日常增量：`mode=incremental + overlap_days=2`
- 线上排查：`pdb_id=<结构ID> + output_filename=xxx.debug.json`

---

## 6. 验证结果

| 位置 | 期望内容 |
| --- | --- |
| `runtime/storage/rcsb_pdb_all/*.cif` | 下载的结构文件 |
| `MongoDB raw_data.rcsb_pdb_structures_all` | 每个 PDB 的标准化文档 |
| `MongoDB raw_data.rcsb_increment_state` | `rcsb_all_api` 的增量游标 |
| `Redis rcsb_all_api:revision` | `pdb_id -> last_revision` 哈希 |

命令行自检示例：

```bash
# Mongo
mongo raw_data --eval "db.rcsb_pdb_structures_all.countDocuments()"

# Redis
redis-cli HLEN rcsb_all_api:revision
```

---

## 7. 文档与开发辅助

1. **本地文档**
   ```bash
   cd MkDocs_doc
   mkdocs serve
   # 访问 http://127.0.0.1:8000/projects/rcsb_pdb/
   ```

2. **mkdocstrings 引用源码**
   - 确保 `PYTHONPATH` 中包含 `code_liu/RCSB_PDB`
   - 运行 `mkdocs build` 之前先安装 `Scrapy`、`pymongo` 等依赖（已在步骤 2 完成）

3. **下一步**
   - 阅读 [架构设计](architecture.md) 了解整体数据流
   - 查看 [配置说明](configuration.md) 对齐环境变量
   - 参考 [使用示例](examples.md) 扩展更多运行姿势
   - 如遇异常，跳转至 [故障排查](troubleshooting.md)

---

完成以上步骤后，即可将任务纳入调度系统或继续补充字段过滤、管道逻辑。祝爬取顺利 🎉

