# -*- coding: utf-8 -*-

"""
# @Time    : 2025/2/25 11:16
# @User  : Mabin
# @Description  :静态常量
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # 根路径
RUNTIME_PATH = os.path.join(BASE_DIR, 'runtime')  # 运行环境目录
LOG_PATH = os.path.join(RUNTIME_PATH, 'log')  # 日志目录
CACHE_PATH = os.path.join(RUNTIME_PATH, 'cache')  # 缓存文件目录
TEMP_PATH = os.path.join(RUNTIME_PATH, 'temp')  # 临时文件路径
UPLOAD_PATH = os.path.join(RUNTIME_PATH, 'upload')  # 上传文件路径
STORAGE_PATH = os.path.join(RUNTIME_PATH, 'storage')  # 文件存储路径
EXTEND_PATH = os.path.join(BASE_DIR, 'extend')  # 依赖文件路径
PROMPT_PATH = os.path.join(EXTEND_PATH, 'prompt')  # Prompt的JSON结构存储根路径

# 配置相关
LOG_STDOUT = False  # 是否将print等标准输出重定向至日志
MEDPEER_PUBLIC_KEY = "MedPeer"  # 定义用于passport加解密的公共密钥

# 网站相关
CURRENT_PROTOCOL = "http://"  # 定义协议类型
CURRENT_TOP_DOMAIN = "com"  # 顶级域
CURRENT_SECOND_DOMAIN = "xishanyigu"  # 二级级域
CURRENT_DOMAIN = CURRENT_SECOND_DOMAIN + "." + CURRENT_TOP_DOMAIN  # 定义域名

# 域名相关
AI_PUBLIC_DOMAIN = "http://101.200.62.36:8001"  # 定义AI服务域名
CONFIG_PUBLIC_DOMAIN = CURRENT_PROTOCOL + 'user.' + CURRENT_DOMAIN  # 定义系统参数服务域名
DATA_ENTER_DOMAIN = CURRENT_PROTOCOL + 'task-scheduling.' + CURRENT_DOMAIN  # 定义资源采集入库域名
ARTICLE_KEEPER_PUBLIC_DOMAIN = CURRENT_PROTOCOL + 'article-keeper.' + CURRENT_DOMAIN  # 定义文献库服务局域网域名

# 接口相关
FREE_LLM_INTERFACE = AI_PUBLIC_DOMAIN + "/ai_platfrom/free_service/streamFreeModel"  # 免费模型接口（流式）
CONFIG_PUBLIC_INTERFACE = CONFIG_PUBLIC_DOMAIN + "/config/index/getConfig"  # 系统配置相关接口

# 入库接口
ENTER_INFORMATION_API = DATA_ENTER_DOMAIN + "/data_capture/enter_database/enterInformationAPI"  # 资讯入库接口
ENTER_DOCUMENT_API = DATA_ENTER_DOMAIN + "/data_capture/enter_database/enterDocumentAPI"  # 文档入库接口
ENTER_VIDEO_API = DATA_ENTER_DOMAIN + "/data_capture/enter_database/enterVideoAPI"  # 视频入库接口
ENTER_UNIT_API = DATA_ENTER_DOMAIN + "/data_capture/enter_database/enterUnitAPI"  # 机构入库接口
ENTER_PERSONAGE_API = DATA_ENTER_DOMAIN + "/data_capture/enter_database/enterPersonageAPI"  # 人物入库接口
ENTER_PATENT_API = DATA_ENTER_DOMAIN + "/data_capture/enter_database/enterPatentAPI"  # 专利入库接口

CN_JOURNAL_INTERFACE = ARTICLE_KEEPER_PUBLIC_DOMAIN + "/cn_enter/cn_data_enter/enterCnJournal"  # 中文期刊入库接口
CN_ARTICLE_INTERFACE = ARTICLE_KEEPER_PUBLIC_DOMAIN + "/cn_enter/cn_data_enter/enterCnArticle"  # 中文文献入库接口

# 缓存相关
CACHE_SUMMARY = {
    # 上次爬取时间缓存前缀
    "CACHE_LAST_DATE_PREFIX": "scrapy:last_date:",
    # 爬虫单例运行缓存
    "CACHE_SINGLE_PREFIX": "scrapy:single:",
    # 历史数据缓存
    "CACHE_SEEN_KEYS_PREFIX": "scrapy:seen_keys:",
}
# 段落语言类型，包括：chi，eng等
MARC_CODE = {
    "chi": "chi",
    "eng": "eng"
}
# 资源类型
RESOURCE_TYPE = {
    "document": "document",  # 文档
    "information": "information",  # 资讯
    "video": "video",  # 视频
    "unit": "unit",  # 机构
    "personage": "personage",  # 人物
    "patent": "patent",  # 专利
    "article": "article",  # 文献
}

# 资源标签，例如：新闻发布/文章资讯/科普信息/设备介绍/训练培训/研究计划/合作项目
RESOURCE_LABEL = {
    "news": {
        "label": "新闻发布",
        "type": RESOURCE_TYPE['information'],
    },
    "article": {
        "label": "文章资讯",
        "type": RESOURCE_TYPE['information'],
    },
    "science": {
        "label": "科普信息",
        "type": RESOURCE_TYPE['information'],
    },
    "equipment": {
        "label": "设备介绍",
        "type": RESOURCE_TYPE['information'],
    },
    "training": {
        "label": "训练培训",
        "type": RESOURCE_TYPE['information'],
    },
    "research": {
        "label": "研究计划",
        "type": RESOURCE_TYPE['information'],
    },
    "cooperate": {
        "label": "合作项目",
        "type": RESOURCE_TYPE['information'],
    },
    "document": {
        "label": "研究报告",
        "type": RESOURCE_TYPE['document'],
    },
    "manuals": {
        "label": "手册书籍",
        "type": RESOURCE_TYPE['document'],
    },
    "video": {
        "label": "视频资料",
        "type": RESOURCE_TYPE['video'],
    },
    "figure": {
        "label": "图片信息",
        "type": RESOURCE_TYPE['document'],
    },
}

# 服务对象
SERVICE_OBJECT = {
    "MED_INFO_SERVICE_PLATFORM": "医学信息支撑服务平台"
}
