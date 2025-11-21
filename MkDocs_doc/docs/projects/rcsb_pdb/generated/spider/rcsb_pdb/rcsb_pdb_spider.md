# rcsb_pdb_spider

RCSB PDB 爬虫 - 支持单条拉取、批量全量、增量更新

**模块路径**: `code_liu.RCSB_PDB.src.spiders.rcsb_pdb.rcsb_pdb_spider`

## 导入

- `datetime.datetime`
- `datetime.timedelta`
- `field_filter.FieldFilter`
- `json`
- `pathlib.Path`
- `scrapy`
- `src.items.other.rcsb_pdb_item.RcsbAllApiItem`
- `src.utils.mongodb_manager.MongoDBManager`
- `src.utils.redis_manager.RedisManager`
- `typing.Any`

## 类

### RcsbAllApiSpider

提取完整 CoreEntry 数据的爬虫

**继承自**: `scrapy.Spider`

#### 属性

- `name` (`str`)
- `allowed_domains`
- `start_urls`
- `OUTPUT_FILENAME` (`str`)
- `FIELD_FILTER_CONFIG` (`NoneType`)
- `DEFAULT_MAX_TARGETS` (`int`)
- `DEFAULT_BATCH_SIZE` (`int`)
- `INCREMENT_COLLECTION` (`str`)
- `INCREMENT_DOC_ID` (`str`)
- `REDIS_REVISION_HASH` (`str`)
- `REDIS_TTL_SECONDS`
- `SEARCH_API` (`str`)
- `API_BASE` (`str`)
- `API_ENDPOINTS`
- `SECTION_MAP`
- `custom_settings`

#### 方法

##### parse

```python
def parse( self, response )
```

Scrapy 默认入口。

参数:
    response (Response): 占位响应（来源于 start_urls）。
返回:
    Generator[scrapy.Request, None, None]: 后续将要调度的请求。

##### parse_search

```python
def parse_search( self, response )
```

解析 Search API 响应并调度 Entry 请求。

参数:
    response (Response): Search API 的响应对象。
返回:
    Generator[scrapy.Request, None, None]: 后续 Entry 请求。

##### parse_entry

```python
def parse_entry( self, response )
```

解析 Entry API 响应并分发实体请求。

参数:
    response (Response): Entry API 的响应对象。
返回:
    Generator[scrapy.Request, None, None]: 后续实体或化合物请求。

##### closed

```python
def closed( self, reason )
```

爬虫关闭时更新 Mongo 中的增量游标。

参数:
    reason (str): Scrapy 关闭原因。

## 函数

### parse

```python
def parse( self, response )
```

Scrapy 默认入口。

参数:
    response (Response): 占位响应（来源于 start_urls）。
返回:
    Generator[scrapy.Request, None, None]: 后续将要调度的请求。

### parse_search

```python
def parse_search( self, response )
```

解析 Search API 响应并调度 Entry 请求。

参数:
    response (Response): Search API 的响应对象。
返回:
    Generator[scrapy.Request, None, None]: 后续 Entry 请求。

### parse_entry

```python
def parse_entry( self, response )
```

解析 Entry API 响应并分发实体请求。

参数:
    response (Response): Entry API 的响应对象。
返回:
    Generator[scrapy.Request, None, None]: 后续实体或化合物请求。

### closed

```python
def closed( self, reason )
```

爬虫关闭时更新 Mongo 中的增量游标。

参数:
    reason (str): Scrapy 关闭原因。
