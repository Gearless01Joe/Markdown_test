# 使用示例

以下示例展示常见的运行与扩展场景，可直接复制命令行执行。

---

## 1. 全量同步（分批）

```bash
scrapy crawl rcsb_all_api \
  -a mode=full \
  -a max_targets=500 \
  -a batch_size=50 \
  -s LOG_LEVEL=INFO
```

**说明**
- Search API 会按照 revision_date 升序分页
- `max_targets` 控制本次运行的规模，防止任务过长
- 建议结合定时任务分段执行

---

## 2. 增量同步（带回溯）

```bash
scrapy crawl rcsb_all_api \
  -a mode=incremental \
  -a overlap_days=2 \
  -a max_targets=2000
```

**要点**
- Mongo `rcsb_increment_state` 保存上次最大 revision
- `overlap_days` 可防止 revision 回写失败导致的缺失
- Redis `rcsb_all_api:revision` 可以 `DEL` 以强制刷新

---

## 3. 单条调试（输出 JSON）

```bash
scrapy crawl rcsb_all_api \
  -a pdb_id=1A1A \
  -a output_filename=1A1A.debug.json \
  -a mode=full
```

**场景**
- 调试字段过滤结果
- 校验文件下载是否成功
- 不依赖 Mongo/Redis

JSON 文件位于 `src/spider/rcsb_pdb/inhance/1A1A.debug.json`。

---

## 4. 自定义字段过滤

`field_filter_config.json` 示例：

```json
{
  "mode": "whitelist",
  "CoreEntry": {
    "include_all": false,
    "include_fields": [
      "rcsb_id",
      "struct",
      "rcsb_accession_info.revision_date"
    ]
  },
  "CorePolymerEntity": {
    "include_all": true,
    "exclude_fields": ["entity_poly_seq"]
  }
}
```

运行：

```bash
scrapy crawl rcsb_all_api \
  -a field_filter_config=field_filter_config.json
```

---

## 5. 仅写入 Mongo（跳过文件）

```bash
scrapy crawl rcsb_all_api \
  -s ITEM_PIPELINES="{'src.pipelines.storage.rcsb_pdb_pipeline.RcsbPdbPipeline': 400}"
```

> 在 `custom_settings` 里覆盖 `ITEM_PIPELINES`，即可按需开启/关闭文件下载 Pipeline。

---

## 6. 结合 MkDocs 查看 API

1. 更新代码后运行：

   ```bash
   mkdocs serve
   ```

2. 打开 `http://127.0.0.1:8000/projects/ntrt/api/`，即可查看 mkdocstrings 生成的 API 文档。

---

更多命令行参数可通过 `scrapy crawl rcsb_all_api -h` 查看。如需自动化部署，可参考项目根目录的 GitHub Actions 工作流。*** End Patch
# 使用示例

本文档提供 RCSB PDB 爬虫项目的常见使用场景和代码示例。

## 基础示例

### 示例 1：单条数据拉取（调试）

获取单个 PDB 结构数据，用于测试和调试：

```bash
# 方式 1：使用 firing.py
python firing.py

# 方式 2：直接使用 Scrapy 命令
scrapy crawl rcsb_all_api -a pdb_id=1ABC -a output_filename=test.json
```

**输出**：
- 数据保存到 `src/spider/rcsb_pdb/inhance/test.json`
- 不写入数据库

**适用场景**：
- 测试 API 连接
- 调试字段过滤规则
- 验证数据格式

### 示例 2：批量全量采集

采集指定数量的蛋白质结构数据：

```bash
scrapy crawl rcsb_all_api -a mode=full -a max_targets=100 -a batch_size=50
```

**参数说明**：
- `mode=full`：全量模式
- `max_targets=100`：最多采集 100 个结构
- `batch_size=50`：每批请求 50 个

**输出**：
- 数据写入 MongoDB 集合 `rcsb_pdb_structures_all`
- 文件下载到配置的存储路径

**适用场景**：
- 首次数据采集
- 重建数据库
- 采集特定数量的数据

### 示例 3：增量更新

基于上次采集的 revision_date 进行增量更新：

```bash
scrapy crawl rcsb_all_api -a mode=incremental -a overlap_days=1
```

**参数说明**：
- `mode=incremental`：增量模式
- `overlap_days=1`：向前重叠 1 天（避免遗漏）

**输出**：
- 只采集更新或新增的数据
- 更新增量游标到 Redis

**适用场景**：
- 日常数据更新
- 定时任务
- 保持数据同步

## 高级示例

### 示例 4：使用字段过滤

只采集需要的字段，减少数据量：

```bash
scrapy crawl rcsb_all_api \
  -a mode=full \
  -a max_targets=50 \
  -a field_filter_config=field_filter_config.json
```

**配置文件示例**（`field_filter_config.json`）：

```json
{
  "entry_properties": {
    "include": [
      "rcsb_id",
      "struct.title",
      "struct.keywords",
      "rcsb_entry_info.deposited_atom_count"
    ]
  },
  "polymer_entities": {
    "include": [
      "entity_id",
      "rcsb_polymer_entity.entity_poly.rcsb_entity_polymer_type"
    ]
  }
}
```

**说明**：
- `include`：只保留指定的字段
- `exclude`：排除指定的字段
- 字段路径使用点号分隔，如 `struct.title`

### 示例 5：从指定位置开始采集

从 Search API 的第 100 条开始采集：

```bash
scrapy crawl rcsb_all_api \
  -a mode=full \
  -a max_targets=200 \
  -a start_from=100 \
  -a batch_size=50
```

**适用场景**：
- 断点续传
- 跳过已采集的数据
- 分批次采集

### 示例 6：自定义输出文件名

单条模式下指定输出文件名：

```bash
scrapy crawl rcsb_all_api \
  -a pdb_id=1ABC \
  -a output_filename=my_custom_output.json
```

**输出位置**：
- `src/spider/rcsb_pdb/inhance/my_custom_output.json`

## Python 代码示例

### 示例 7：在代码中启动爬虫

```python
from scrapy import cmdline

# 单条模式
cmdline.execute([
    'scrapy', 'crawl', 'rcsb_all_api',
    '-a', 'pdb_id=1ABC',
    '-a', 'output_filename=test.json'
])

# 全量模式
cmdline.execute([
    'scrapy', 'crawl', 'rcsb_all_api',
    '-a', 'mode=full',
    '-a', 'max_targets=100',
    '-a', 'batch_size=50'
])

# 增量模式
cmdline.execute([
    'scrapy', 'crawl', 'rcsb_all_api',
    '-a', 'mode=incremental',
    '-a', 'overlap_days=1'
])
```

### 示例 8：使用 firing.py 启动

```python
# 编辑 firing.py
from firing import start_spider

# 单条模式
start_spider(
    spider_name="rcsb_all_api",
    pdb_id="1ABC",
    output_filename="test.json"
)

# 全量模式
start_spider(
    spider_name="rcsb_all_api",
    mode="full",
    max_targets=100,
    batch_size=50
)

# 增量模式
start_spider(
    spider_name="rcsb_all_api",
    mode="incremental",
    overlap_days=1
)
```

## 实际应用场景

### 场景 1：首次数据采集

```bash
# 采集前 1000 个结构
scrapy crawl rcsb_all_api \
  -a mode=full \
  -a max_targets=1000 \
  -a batch_size=100
```

### 场景 2：日常增量更新（定时任务）

```bash
# 每天运行一次，更新最新数据
scrapy crawl rcsb_all_api \
  -a mode=incremental \
  -a overlap_days=1
```

**Crontab 配置示例**：

```bash
# 每天凌晨 2 点运行
0 2 * * * cd /path/to/RCSB_PDB && scrapy crawl rcsb_all_api -a mode=incremental
```

### 场景 3：测试特定 PDB ID

```bash
# 测试多个 PDB ID
for pdb_id in 1ABC 2DEF 3GHI; do
  scrapy crawl rcsb_all_api -a pdb_id=$pdb_id -a output_filename=${pdb_id}.json
done
```

### 场景 4：采集特定字段

创建 `field_filter_config.json`：

```json
{
  "entry_properties": {
    "include": [
      "rcsb_id",
      "struct.title",
      "rcsb_entry_info.molecular_weight"
    ]
  }
}
```

运行：

```bash
scrapy crawl rcsb_all_api \
  -a mode=full \
  -a max_targets=100 \
  -a field_filter_config=field_filter_config.json
```

## 数据查询示例

### MongoDB 查询示例

```python
from src.utils.mongodb_manager import MongoDBManager

mongo = MongoDBManager()
collection = mongo.db['rcsb_pdb_structures_all']

# 查询特定 PDB ID
result = collection.find_one({'PDB_ID': '1ABC'})

# 查询所有数据
all_data = collection.find()

# 统计数量
count = collection.count_documents({})

# 查询最近更新的数据
recent = collection.find().sort('max_revision_date', -1).limit(10)
```

### Redis 查询示例

```python
from src.utils.redis_manager import RedisManager

redis = RedisManager().get_connection()

# 获取增量游标
cursor = redis.hget('rcsb_all_api:revision', 'last_revision_date')
print(f"Last revision date: {cursor}")
```

## 错误处理示例

### 示例 9：处理采集错误

```python
# 在爬虫中添加错误处理
def parse(self, response):
    try:
        # 采集逻辑
        yield item
    except Exception as e:
        self.logger.error(f"Error processing {response.url}: {e}")
        # 可以选择重试或跳过
```

## 性能优化示例

### 示例 10：调整并发数

```python
# 在 settings.py 中调整
CONCURRENT_REQUESTS = 64  # 提高并发数

# 或通过命令行参数
scrapy crawl rcsb_all_api -s CONCURRENT_REQUESTS=64 -a mode=full
```

### 示例 11：调整批量大小

```bash
# 根据网络情况调整 batch_size
scrapy crawl rcsb_all_api \
  -a mode=full \
  -a max_targets=1000 \
  -a batch_size=100  # 增大批量大小
```

## 相关文档

- [快速开始](getting-started.md) - 环境配置
- [核心模块](guide.md) - 模块详细说明
- [配置说明](configuration.md) - 配置参数
- [系统全景](api.md) - API 参考

