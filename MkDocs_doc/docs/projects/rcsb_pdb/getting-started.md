# 快速开始

本指南帮助你在 10 分钟内跑通 RCSB PDB 项目，涵盖环境准备、依赖安装以及常见命令。

---

## 1. 先决条件

| 组件 | 建议版本 | 说明 |
| --- | --- | --- |
| Python | 3.11+ | 需启用 venv |
| MongoDB | 4.4+ | 保存结构化结果与增量游标 |
| Redis | 5.0+ | 缓存 revision_date，做重复判断 |
| Git | 2.30+ | 拉取代码 |

> ⚠️ 若无法访问外网，请提前配置公司制品库 / pip 源。

---

## 2. 克隆与安装

```bash
git clone git@github.com:Gearless01Joe/Markdown_test.git
cd Markdown_test

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
pip install -r MkDocs_doc/requirements.txt
```

---

## 3. 配置本地环境

1. 复制 `code_liu/RCSB_PDB/.env.example`（若存在）或手动创建 `.env`：

```
MONGO_URI=mongodb://medpeer:medpeer@192.168.1.245:27017/raw_data
REDIS_URI=redis://:medpeer@101.200.62.36:6379/1
```

2. 根据需要修改 `src/settings.py` 中的数据库、日志、代理配置。建议将敏感信息提取为环境变量：

```bash
set MYSQL_PASSWORD=***
set REDIS_PASSWORD=***
```

3. 创建数据目录：

```bash
mkdir -p data/rcsb_pdb_all
```

---

## 4. 运行方式

### 方式一：单条调试

```bash
cd code_liu/RCSB_PDB
scrapy crawl rcsb_all_api -a pdb_id=1A1A -a mode=full
```

- `pdb_id`：指定结构 ID
- `output_filename`：自定义 JSON 文件名

### 方式二：批量全量

```bash
scrapy crawl rcsb_all_api -a mode=full -a max_targets=500 -a batch_size=50
```

- `max_targets`：本次任务的数量上限
- `batch_size`：Search API 的分页大小

### 方式三：增量更新

```bash
scrapy crawl rcsb_all_api -a mode=incremental -a overlap_days=2
```

- Redis 保存 revision_date，Mongo `rcsb_increment_state` 保存游标
- `overlap_days` 用于防抖，建议 1~3 天

---

## 5. 验证结果

1. **JSON 文件**：`code_liu/RCSB_PDB/src/spider/rcsb_pdb/inhance/*.json`
2. **MongoDB**：`raw_data.rcsb_pdb_structures_all`
3. **Redis**：`rcsb_all_api:revision` 哈希
4. **MkDocs 文档**：

```bash
cd MkDocs_doc
mkdocs serve
# 浏览 http://127.0.0.1:8000/projects/ntrt/
```

---

## 6. 常见命令速查

| 需求 | 命令 |
| --- | --- |
| 查看支持参数 | `scrapy crawl rcsb_all_api -a help=1` |
| 清空增量游标 | `mongo raw_data --eval 'db.rcsb_increment_state.remove({})'` |
| 清空 Redis revision | `redis-cli DEL rcsb_all_api:revision` |
| 导出日志 | `scrapy crawl ... --logfile logs/rcsb.log` |

如遇问题，可跳转至 [故障排查](troubleshooting.md)。
# 快速开始

本文档将帮助你快速搭建 RCSB PDB 爬虫项目的运行环境并执行第一次数据采集。

## 环境要求

- **Python**：3.8 或更高版本
- **操作系统**：Windows / Linux / macOS
- **数据库**：
  - MongoDB 4.0+（必需）
  - Redis 5.0+（增量模式需要）
  - MySQL 5.7+（可选）

## 安装步骤

### 1. 克隆项目

```bash
cd D:\Python_project\Markdown\code_liu\RCSB_PDB
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖包括：
- `scrapy` - 爬虫框架
- `pymongo` - MongoDB 驱动
- `redis` - Redis 驱动
- `pymysql` - MySQL 驱动（可选）

### 3. 配置数据库

编辑 `src/settings.py`，配置数据库连接信息：

```python
# MongoDB 配置
MONGODB_DATABASES = {
    "default": {
        "type": "mongodb",
        'user': 'your_username',
        'password': 'your_password',
        'host': 'your_host',
        'port': 27017,
        'database': 'raw_data',
    },
}

# Redis 配置（增量模式需要）
REDIS_DATABASES = {
    "default": {
        "type": "redis",
        'password': 'your_password',
        'host': 'your_host',
        'port': 6379,
        'database': 1,
    }
}
```

### 4. 配置日志路径

在 `src/constant.py` 中配置日志和文件存储路径：

```python
LOG_PATH = "/path/to/logs"
UPLOAD_PATH = "/path/to/uploads"
```

## 快速运行示例

### 示例 1：单条数据拉取（调试模式）

获取单个 PDB 结构数据，用于测试和调试：

```bash
python firing.py
```

或者直接使用 Scrapy 命令：

```bash
scrapy crawl rcsb_all_api -a pdb_id=1ABC -a output_filename=test.json
```

**参数说明**：
- `pdb_id`：PDB ID（如 1ABC）
- `output_filename`：输出文件名（可选）

### 示例 2：批量全量采集

采集指定数量的蛋白质结构数据：

```bash
scrapy crawl rcsb_all_api -a mode=full -a max_targets=100 -a batch_size=50
```

**参数说明**：
- `mode=full`：全量模式
- `max_targets`：最大采集数量
- `batch_size`：每批请求数量

### 示例 3：增量更新

基于上次采集的 revision_date 进行增量更新：

```bash
scrapy crawl rcsb_all_api -a mode=incremental -a overlap_days=1
```

**参数说明**：
- `mode=incremental`：增量模式
- `overlap_days`：向前重叠天数（避免遗漏）

## 验证安装

运行单条数据拉取测试：

```bash
scrapy crawl rcsb_all_api -a pdb_id=1ABC
```

如果看到以下输出，说明安装成功：

```
[INFO] 开始处理 PDB ID: 1ABC
[INFO] 数据采集完成
[INFO] 数据已保存到 MongoDB
```

## 常见问题

### 问题 1：MongoDB 连接失败

**解决方案**：
1. 检查 MongoDB 服务是否启动
2. 验证连接信息是否正确
3. 检查网络连接和防火墙设置

### 问题 2：Redis 连接失败（增量模式）

**解决方案**：
1. 增量模式需要 Redis，确保 Redis 服务运行
2. 验证 Redis 连接配置
3. 如果不需要增量功能，可以使用 `mode=full`

### 问题 3：依赖安装失败

**解决方案**：
```bash
# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 下一步

- 查看 [架构设计](architecture.md) 了解系统架构
- 查看 [配置说明](configuration.md) 了解详细配置
- 查看 [使用示例](examples.md) 了解更多使用场景
- 查看 [系统全景](api.md) 了解完整的 API 文档

## 获取帮助

如果遇到问题，请查看：
- [故障排查](troubleshooting.md) - 常见问题解决方案
- [核心模块](guide.md) - 模块详细说明
- [系统全景](api.md) - API 参考文档

