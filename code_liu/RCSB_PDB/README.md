# 采集框架（爬虫部分）

#### 介绍

当前为全新的Scrapy项目组织方案

#### 项目结构

```
├── scrapy.cfg               # Scrapy部署配置文件
├── firing.py                # 当前项目的爬虫启动辅助脚本
├── requirements.txt         # 项目依赖
├── README.md                # 项目文档
│
├── runtime/                 # 运行目录
│   ├── cache                # 缓存文件目录
│   ├── log                  # 日志目录
│   └── temp                 # 下载文件等临时存储目录
│
├── docs/                    # 项目文档目录
│
├── tests/                   # 单元测试（未实装）
│   ├── __init__.py
│   ├── test_spiders.py
│   └── test_pipelines.py
│
└── src/                     # 爬虫主体
    ├── __init__.py
    │
    ├── constant.py          # 常量配置
    │
    ├── settings.py          # 项目设置（继承默认设置并扩展）
    │
    ├── items/               # 数据模型定义（模块化拆分）
    │   ├── __init__.py
    │   ├── base_items.py       # Item基类以及所使用的Field类定义
    │   └── video_item.py       # 视频Item
    │
    ├── spiders/             # 爬虫目录（推荐模块化组织）
    │   ├── __init__.py
    │   ├── base_spider.py   # 基础爬虫类
    │   ├── nsfc/                       # 按网站分组
    │   │   ├── __init__.py
    │   │   ├── base_spider.py          # 当前网站的基础爬虫类（可选）
    │   │   ├── information/            # 资讯类型
    │   │   │   └──xxx_spider.py        # xx爬虫
    │   │   ├── mixed/                  # 混合类型
    │   │   └── document/               # 文档类型
    │   └── xml/                        # 另一网站（只爬取单一类型）
    │       ├── __init__.py
    │       └── xxx_spider.py           # xx爬虫
    │
    ├── middlewares/         # 中间件模块化
    │   ├── __init__.py
    │   ├── proxy_middleware.py       # 代理中间件
    │   ├── user_agents.py            # UA轮转中间件（未实装）
    │   └── retry_middleware.py       # 自定义重试逻辑
    │
    ├── pipelines/                              # 数据处理管道
    │   ├── __init__.py
    │   ├── data_cleaning_pipeline.py           # 数据常规清洗管道
    │   ├── file_download_pipeline.py           # 文件下载管道
    │   ├── file_replacement_pipeline.py        # 文件信息替换管道（主要解决文件路径问题）
    │   ├── raw_data_storage_pipeline.py        # 临时数据存储管道(基类)
    │   ├── rich_text_analysis_pipeline.py      # 富文本格式解析管道
    │   ├── youtube_video_pipeline.py           # YouTube视频下载管道（未实装）
    │   ├── storage
    │   │    └── document_storage_pipeline.py             # 文档数据的临时库入库、接口入库
    │   │    └── video_storage_pipeline.py                # 视频数据的临时库入库、接口入库
    │   │    └── information_storage_pipeline.py          # 资讯数据的临时库入库、接口入库
    │   └── expand                              # 拓展，用于存储特定爬虫的定制管道
    │
    ├── utils/               # 工具函数
    │   ├── __init__.py
    │   ├── base_language_detection.py       # 语言检测
    │   ├── base_logger.py                   # 日志配置
    │   ├── base_oss.py                      # OSS相关文件上传类
    │   ├── base_token.py                    # 身份令牌类
    │   ├── blm_server.py                    # 模型请求类
    │   ├── mongodb_manager.py               # MongoDB数据库操作工具类
    │   ├── redis_manager.py                 # Redis数据库管理类
    │   └── mysql_manager.py                 # MySQL数据库操作工具类
    │
    └── extensions/          # 自定义扩展
        ├── __init__.py
        ├── stats.py         # 统计扩展（未实装）
        └── error_handler.py # 错误处理扩展（未实装）
```

#### 使用须知

* HTML解析库统一使用Scrapy的解析函数，如果需要使用其他库进行解析，则统一使用lxml
* 文件引用减少使用from XX import *
* 管道调用顺序（排序靠前者应当优先调用）
  * data_cleaning_pipeline
  * rich_text_analysis_pipeline
  * file_download_pipeline
  * file_replacement_pipeline
  * storage类管道