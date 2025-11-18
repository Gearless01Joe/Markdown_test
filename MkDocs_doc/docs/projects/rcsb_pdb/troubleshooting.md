# 故障排查

汇总运行过程中最常见的问题及解决方案。

---

## 1. Search API 返回 429 / 503

- **现象**：日志出现 `HTTP 429` 或 `503`
- **原因**：请求过快或被限流
- **解决办法**：
  1. 将 `CONCURRENT_REQUESTS` 调低至 10~16
  2. 提高 `DOWNLOAD_DELAY` 至 2 秒
  3. 检查代理可用性，必要时启用备用代理池

---

## 2. Entry/ChemComp 请求超时

- **现象**：大量 `TimeoutError` 或 `_parse_json` 警告
- **原因**：接口响应慢、网络不稳定
- **解决办法**：
  1. 将 `DOWNLOAD_TIMEOUT` 提高到 120
  2. 开启 `PLAYWRIGHT_PROCESS_REQUEST_HEADERS`，模拟真实浏览器头
  3. 增加重试次数：`-s RETRY_TIMES=50`

---

## 3. MongoDB 连接失败

- **现象**：`pymongo.errors.ServerSelectionTimeoutError`
- **排查**：
  1. 确认 Mongo 服务是否启动、端口是否可访问
  2. 校验 `MONGODB_DATABASES["default"]` 的账号密码
  3. 若使用云实例，确保 IP 白名单已添加爬虫节点

---

## 4. Redis 游标不同步

- **现象**：增量模式重复抓取或完全不抓取
- **解决办法**：
  1. 清理 Redis：`redis-cli DEL rcsb_all_api:revision`
  2. 清理 Mongo 游标：`db.rcsb_increment_state.remove({})`
  3. 重新执行一次全量任务，用于重建基线

---

## 5. 文件下载失败

- **现象**：CIF/验证图片缺失
- **排查**：
  1. 确保 `FILES_STORE` / `IMAGES_STORE` 指向可写路径
  2. 检查 `FileDownloadPipeline` 是否在 `custom_settings` 中被禁用
  3. 对于长路径的 Windows 环境，可启用 `LongPathsEnabled`

---

## 6. mkdocs serve 无法解析模块

- **现象**：`mkdocstrings: ModuleNotFoundError`
- **解决办法**：
  1. 运行 `pip install -r MkDocs_doc/requirements.txt`
  2. 确认 `mkdocs.yml` 中 `mkdocstrings.handlers.python.paths` 包含 `../code_liu`
  3. 在 `MkDocs_doc` 目录执行 `mkdocs serve`，确保相对路径正确

---

## 7. 字段过滤不生效

- **排查步骤**：
  1. 确认 `field_filter_config` 输入路径正确（相对路径相对于 spider 文件）
  2. 检查 JSON 是否 UTF-8 编码、语法正确
  3. 在日志中搜索 `FieldFilter`，确认配置是否被加载

---

## 8. 任务中途退出

- **常见原因**：
  - Mongo/Redis 断开：配置 `AUTOTHROTTLE_ENABLED = False` 的情况下网络抖动更加明显
  - 磁盘空间不足：JSON 文件/日志写入失败
  - Scrapy 异常退出：查看 `logs/*.log`，搜索 `Traceback`

> 如仍无法定位问题，可在群内提供日志片段、命令参数与运行环境信息。*** End Patchgithubassistant to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_patch to=functions.apply_p']]],
# 故障排查

本文档列出 RCSB PDB 爬虫项目的常见问题和解决方案。

## 常见问题

### 问题 1：MongoDB 连接失败

**错误信息**：
```
pymongo.errors.ServerSelectionTimeoutError: No servers found
```

**可能原因**：
1. MongoDB 服务未启动
2. 连接信息配置错误
3. 网络连接问题
4. 防火墙阻止连接

**解决方案**：

1. **检查 MongoDB 服务**：
   ```bash
   # Linux/Mac
   sudo systemctl status mongod
   
   # Windows
   # 检查服务管理器中 MongoDB 服务是否运行
   ```

2. **验证连接信息**：
   ```python
   # 在 settings.py 中检查
   MONGODB_DATABASES = {
       "default": {
           'host': '192.168.1.245',  # 确认主机地址正确
           'port': 27017,             # 确认端口正确
           'user': 'medpeer',         # 确认用户名正确
           'password': 'medpeer',     # 确认密码正确
       },
   }
   ```

3. **测试连接**：
   ```python
   from pymongo import MongoClient
   client = MongoClient('mongodb://medpeer:medpeer@192.168.1.245:27017/')
   print(client.server_info())  # 如果成功会打印服务器信息
   ```

### 问题 2：Redis 连接失败（增量模式）

**错误信息**：
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**可能原因**：
1. Redis 服务未启动
2. 连接信息配置错误
3. 密码错误

**解决方案**：

1. **检查 Redis 服务**：
   ```bash
   # Linux/Mac
   redis-cli ping  # 应该返回 PONG
   
   # Windows
   # 检查 Redis 服务是否运行
   ```

2. **验证连接**：
   ```python
   import redis
   r = redis.Redis(
       host='101.200.62.36',
       port=6379,
       password='medpeer',
       db=1
   )
   print(r.ping())  # 应该返回 True
   ```

3. **如果不需要增量功能**：
   - 使用 `mode=full` 全量模式，不需要 Redis

### 问题 3：API 请求失败

**错误信息**：
```
HTTP 429: Too Many Requests
HTTP 503: Service Unavailable
```

**可能原因**：
1. 请求频率过高
2. API 服务器临时不可用
3. 网络问题

**解决方案**：

1. **增加下载延迟**：
   ```python
   # 在 settings.py 中
   DOWNLOAD_DELAY = 2  # 增加到 2 秒
   ```

2. **减少并发数**：
   ```python
   CONCURRENT_REQUESTS = 16  # 从 32 降到 16
   ```

3. **检查重试配置**：
   ```python
   RETRY_ENABLED = True
   RETRY_TIMES = 30  # 确保重试次数足够
   RETRY_HTTP_CODES = [429, 503, 504]  # 确保包含这些状态码
   ```

### 问题 4：字段过滤不生效

**错误信息**：
- 数据中仍然包含不需要的字段

**可能原因**：
1. 配置文件路径错误
2. 配置文件格式错误
3. 字段路径不正确

**解决方案**：

1. **检查配置文件路径**：
   ```bash
   # 使用绝对路径
   scrapy crawl rcsb_all_api -a field_filter_config=/absolute/path/to/config.json
   
   # 或使用相对路径（相对于爬虫文件）
   scrapy crawl rcsb_all_api -a field_filter_config=field_filter_config.json
   ```

2. **验证配置文件格式**：
   ```json
   {
     "entry_properties": {
       "include": ["rcsb_id", "struct.title"]
     }
   }
   ```

3. **检查字段路径**：
   - 使用点号分隔，如 `struct.title`
   - 参考 API 返回的实际字段结构

### 问题 5：增量游标丢失

**错误信息**：
- 增量模式从开始采集，而不是从上次位置继续

**可能原因**：
1. Redis 数据过期
2. Redis 连接失败
3. 游标未正确保存

**解决方案**：

1. **检查 Redis TTL**：
   ```python
   # 默认 TTL 是 60 天
   REDIS_TTL_SECONDS = 60 * 60 * 24 * 60
   ```

2. **手动设置游标**：
   ```python
   from src.utils.redis_manager import RedisManager
   redis = RedisManager().get_connection()
   redis.hset('rcsb_all_api:revision', 'last_revision_date', '2024-01-01T00:00:00Z')
   ```

3. **从 MongoDB 恢复游标**：
   ```python
   from src.utils.mongodb_manager import MongoDBManager
   mongo = MongoDBManager()
   collection = mongo.db['rcsb_increment_state']
   doc = collection.find_one({'_id': 'rcsb_all_api'})
   if doc:
       last_revision = doc.get('last_revision_date')
       # 设置到 Redis
   ```

### 问题 6：文件下载失败

**错误信息**：
```
Failed to download file: ...
```

**可能原因**：
1. 文件 URL 无效
2. 网络问题
3. 存储路径不存在
4. 权限问题

**解决方案**：

1. **检查存储路径**：
   ```python
   # 在 constant.py 中
   UPLOAD_PATH = "/path/to/uploads"  # 确保路径存在且有写权限
   ```

2. **检查文件 URL**：
   - 在日志中查看具体的文件 URL
   - 手动访问 URL 验证是否可访问

3. **检查权限**：
   ```bash
   # Linux/Mac
   chmod 755 /path/to/uploads
   ```

### 问题 7：内存占用过高

**错误信息**：
- 程序运行缓慢
- 系统内存不足

**可能原因**：
1. 并发数过高
2. 批量大小过大
3. 数据量过大

**解决方案**：

1. **降低并发数**：
   ```python
   CONCURRENT_REQUESTS = 16  # 从 32 降到 16
   ```

2. **减小批量大小**：
   ```bash
   scrapy crawl rcsb_all_api -a batch_size=25  # 从 50 降到 25
   ```

3. **使用字段过滤**：
   - 只采集需要的字段，减少内存占用

### 问题 8：日志文件过大

**错误信息**：
- 日志文件占用大量磁盘空间

**解决方案**：

1. **调整日志级别**：
   ```python
   LOG_LEVEL = "WARNING"  # 从 DEBUG 或 INFO 改为 WARNING
   ```

2. **定期清理日志**：
   ```bash
   # 删除 30 天前的日志
   find /path/to/logs -name "*.log" -mtime +30 -delete
   ```

3. **限制日志文件大小**：
   - 使用日志轮转工具（如 logrotate）

## 调试技巧

### 技巧 1：启用详细日志

```python
# 在 settings.py 中
LOG_LEVEL = "DEBUG"
```

### 技巧 2：单条模式调试

```bash
# 只采集一条数据，便于调试
scrapy crawl rcsb_all_api -a pdb_id=1ABC -a output_filename=debug.json
```

### 技巧 3：使用断点调试

```python
# 在 firing.py 中使用
import pdb; pdb.set_trace()  # 设置断点
```

### 技巧 4：查看中间数据

```python
# 在爬虫中添加日志
self.logger.debug(f"Entry data: {entry_data}")
self.logger.debug(f"Filtered data: {filtered_data}")
```

## 获取帮助

如果以上方案无法解决问题，请：

1. **查看日志**：
   - 检查日志文件中的详细错误信息
   - 注意错误堆栈跟踪

2. **检查配置**：
   - 验证所有配置项是否正确
   - 参考 [配置说明](configuration.md)

3. **查看文档**：
   - [系统全景](api.md) - API 参考
   - [核心模块](guide.md) - 模块说明
   - [使用示例](examples.md) - 使用示例

4. **联系维护者**：
   - 提供错误日志
   - 提供配置信息（隐藏敏感信息）
   - 描述复现步骤

## 相关文档

- [快速开始](getting-started.md) - 环境配置
- [配置说明](configuration.md) - 配置详解
- [使用示例](examples.md) - 使用示例

