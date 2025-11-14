# 爬虫模块文档

## 概述

爬虫模块（spiders）包含了各种数据爬取功能，按照入库数据类型或业务领域分组。

## 模块结构

### 基础模块

- **BaseSpider**: 所有爬虫的基类，提供公共功能

### 业务模块

- **NSFC 爬虫**: 国自然相关数据爬取
  - `nsfc/`: 正式版本
  - `nsfc_new/`: 新版本
  - `nsfc_temp/`: 临时版本
- **RCSB PDB 爬虫**: 蛋白质数据库爬取
- **中文文献爬虫**: CNKI、万方等
- **英文期刊爬虫**: Scopus、Scimagojr、LetPub 等

## 快速开始

```python
from spiders.base_spider import BaseSpider

class MySpider(BaseSpider):
    name = 'my_spider'
    base_url = 'https://example.com'
```

## 文档导航

- [基础爬虫类](api.md#basespider) - BaseSpider 的详细文档
- [NSFC 爬虫](api.md#nsfc) - 国自然相关爬虫
- [RCSB PDB 爬虫](api.md#rcsb-pdb) - 蛋白质数据库爬虫
- [中文文献爬虫](api.md#中文文献) - CNKI、万方等
- [英文期刊爬虫](api.md#英文期刊) - Scopus 等

