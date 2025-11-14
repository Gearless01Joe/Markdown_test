# -*- coding: utf-8 -*-

"""
# @Time    : 2025/2/25 10:38
# @User  : Mabin
# @Description  :爬虫setting
"""
import os
import time
import random

import src.utils.base_logger
from src.constant import LOG_PATH, UPLOAD_PATH

# *********************以下配置本地与服务器存在差异，禁止随意修改************************
# 日志相关
# LOG_LEVEL = "WARNING"  # 日志记录的最低级别，默认DEBUG
LOG_FILE = None
# 用于记录输出的文件名，默认控制台输出,此处只设置日志存放的目录,剩余部分由各个爬虫项目的firing.py来确定日志文件名称
# LOG_FILE = os.path.join(LOG_PATH, time.strftime('%Y-%m'))

# MySQL数据库连接配置
MYSQL_DATABASES = {
    "default": {
        "type": "mysql",
        'user': 'medpeer',
        'password': 'medpeer',
        'host': '192.168.1.245',
        'port': 3306,
        'database': 'raw_data',
        "charset": "utf8mb4"
    },
}

# MongoDB数据库连接配置
MONGODB_DATABASES = {
    "default": {
        "type": "mongodb",
        'user': 'medpeer',
        'password': 'medpeer',
        'auth_source': 'admin',  # 认证数据库（必须与用户创建库一致）
        'host': '192.168.1.245',
        'port': 27017,
        'database': 'raw_data',
        "charset": "utf8mb4",
        "direct_connection": True,  # 单节点
    },
}

# Redis数据库连接配置
REDIS_DATABASES = {
    "default": {
        "type": "redis",
        'password': 'medpeer',
        'host': '101.200.62.36',
        'port': 6379,
        'database': 1,
    }
}

# ********************************************************************************

# 基础设置
BOT_NAME = "src"
SPIDER_MODULES = ["src.spiders"]
NEWSPIDER_MODULE = "src.spiders"

# 不遵循robots.txt中的爬虫规则
ROBOTSTXT_OBEY = False

# 相同网站两个请求之间的间隔时间
DOWNLOAD_DELAY = 1

# 请求间隔设置为范围随机值
RANDOMIZE_DOWNLOAD_DELAY = True

# 下载中间件设置
DOWNLOADER_MIDDLEWARES = {
    # 'src.middlewares.proxy_middleware.ProxyRetryMiddleware': 543,  # 请求重试中间件
    'src.middlewares.captcha_middleware.CaptchaMiddleware': 540,  # 需要在重试中间件之前
    'src.middlewares.custom_retry_middleware.CustomRetryMiddleware': 550,  # 替换默认的 RetryMiddleware
    # 并发量精准控制，主要使用SEMAPHORE_CONFIGS参数进行配置
    # 'src.middlewares.twisted_semaphore_middleware.TwistedSemaphoreMiddleware': 560,
    'src.middlewares.proxy_middleware.BaseProxyMiddleware': 400,  # 代理请求中间件
    'src.middlewares.history_data_middleware.HistoryDataMiddleware': 300,  # 历史数据中间件
}

# 爬虫中间件
SPIDER_MIDDLEWARES = {
    # 针对部分报错重试、释放meta中的custom_playwright_semaphore信号量、释放meta中的playwright_page的页面
    'src.middlewares.custom_retry_middleware.CustomExceptionMiddleware': 543,
    # 并发量精准控制，主要使用SEMAPHORE_CONFIGS参数进行配置
    # 'src.middlewares.twisted_semaphore_middleware.TwistedSemaphoreMiddleware': 560,
}

# 拓展
EXTENSIONS = {
    # 'scrapy.extensions.logstats.LogStats': None,
    # 'src.extensions.verbose_log_stats.VerboseLogStats': 500,  # 日志
}

# 客户端 user-agent请求头
USER_AGENT = None

# 规定哪些非正常响应码可以进入callback
HTTPERROR_ALLOWED_CODES = []

# 并发请求数量
CONCURRENT_REQUESTS = 32

# 请求重试相关
RETRY_ENABLED = True  # 进行重试
RETRY_TIMES = 30  # 重试次数
DOWNLOAD_TIMEOUT = 60  # 下载超时时间
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429, 440]  # 需要重试的状态码(440为代理超过带宽的状态码)

# 配置请求头
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
    'referer': 'https://cn.bing.com/',
    'Origin': 'https://cn.bing.com/',
}

# 下载相关设置
MEDIA_ALLOW_REDIRECTS = True  # 允许媒体文件重定向
FILES_STORE = UPLOAD_PATH  # 下载文件存放地址（Files Pipeline）
IMAGES_STORE = UPLOAD_PATH  # 图片文件存放地址（Images Pipeline）

# 日志配置
LOG_ENABLED = True  # 启用日志记录
LOG_ENCODING = "utf-8"  # 日志编码
LOG_FILE_APPEND = True  # 追加式记录日志
LOG_FORMAT = '---------------------------------------------------------------\n' \
             '[%(levelname)s] [%(asctime)s] [%(name)s]\n' \
             '[进程ID] %(process)d [线程ID] %(thread)d [调用文件] %(pathname)s\n' \
             '%(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'  # 日期格式
LOG_FORMATTER = src.utils.base_logger.BaseSpiderLogFormatter  # 日志格式化类，可自定义
LOGSTATS_INTERVAL = 60.0  # 统计信息的记录间隔（单位：秒）

# Set settings whose default value is deprecated to a future-proof value
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# *********************Scrapy-Playwright相关配置************************
# PLAYWRIGHT_CONNECT_URL = "ws://192.168.1.17:3004"
PLAYWRIGHT_PROCESS_REQUEST_HEADERS = "src.component.playwright_helper.customize_scrapy_headers"  # Playwright自定义请求头配置
