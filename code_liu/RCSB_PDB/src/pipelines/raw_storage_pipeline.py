# -*- coding: utf-8 -*-

"""
# @Time    : 2025/3/7 16:58
# @User  : Mabin
# @Description  :MongoDB临时数据存储管道（临时数据只作为记录使用，不做复杂操作）
"""
from datetime import datetime
from src.utils.mongodb_manager import MongoDBManager
from src.utils.mysql_manager import MySQLManager


class MongoDBRawStoragePipeline:
    connect_key = "default"  # MongoDB链接标识
    collection_name = "information"  # MongoDB入库集合名
    item_class = None  # 当前管道所接受的item类型（子类需要明确）

    def __init__(self):
        """
        初始化相关属性
        :author Mabin
        """
        self.database_model = None
        self.current_settings = None

    def open_spider(self, spider):
        """
        启动相关数据库链接
        :author Mabin
        :param spider:
        :return:
        """
        # 初始化相关模型
        self.database_model = MongoDBManager(connect_key=self.connect_key)

        # 获取当前模型运行的参数
        tmp_settings = dict(dict(spider.settings), **dict(spider.custom_settings))
        self.current_settings = {
            "CONCURRENT_REQUESTS": tmp_settings.get("CONCURRENT_REQUESTS"),
            "RETRY_TIMES": tmp_settings.get("RETRY_TIMES"),
            "CONCURRENT_REQUESTS_PER_DOMAIN": tmp_settings.get("CONCURRENT_REQUESTS_PER_DOMAIN"),
            "RETRY_HTTP_CODES": tmp_settings.get("RETRY_HTTP_CODES"),
            "ITEM_PIPELINES": tmp_settings.get("ITEM_PIPELINES"),
            "DOWNLOADER_MIDDLEWARES": tmp_settings.get("DOWNLOADER_MIDDLEWARES"),
            "EXTENSIONS": tmp_settings.get("EXTENSIONS"),
        }

    def process_item(self, item, spider):
        """
        记录数据库
        :author Mabin
        :param item:
        :param spider:
        :return:
        """
        if not isinstance(item, self.item_class):
            # 非指定类型的item，直接返回
            return item

        # 组织入库数据
        create_date = dict(
            dict(item),
            **{
                "metadata": {
                    "spider_name": spider.name,
                    "allowed_domains": spider.allowed_domains,
                    "start_urls": spider.start_urls,
                    "spider_settings": self.current_settings,
                },
                "create_time": datetime.now(),
            }
        )

        # 执行数据入库
        self.database_model.db[self.collection_name].insert_one(create_date)

        return item


class MySQLRawStoragePipeline:
    connect_key = "default"  # MySQL链接标识

    def __init__(self):
        """
        初始化相关属性
        :author Mabin
        """
        self.database_model = None

    def open_spider(self, spider):
        """
        启动相关数据库链接
        :author Mabin
        :param spider:
        :return:
        """
        # 初始化相关模型
        self.database_model = MySQLManager(connect_key=self.connect_key)
