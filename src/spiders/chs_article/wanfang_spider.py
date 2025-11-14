import json
import re
import os
import time
import html
from collections import deque


import scrapy
from playwright.async_api import Page
from scrapy.http import Request, Response
from scrapy_playwright.page import PageMethod
from src.items.other.chi_article_item import CnJournalItem, CnArticleItem, JOURNAL_UNIT_RELATION_TYPE, \
    JOURNAL_PLATFORM_CODE, JOURNAL_OPEN_ACCESS, JOURNAL_IS_SUSPENDED, CO_FIRST_AUTHOR, CORRESPONDING_AUTHOR, \
    AUTHOR_IS_DISPLAY, AUTHOR_TYPE, ARTICLE_PUBLISHED_TIME_PRECISION, ARTICLE_ABSTRACT_SECTION_ATTR
from src.spiders.base_spider import BaseSpider
from src.component.base_selector_component import BaseSelectorComponent
from src.utils.utils import en_cn_correction
from src.utils.base_logger import BaseLog
from src.constant import TEMP_PATH

custom_logger = BaseLog()


class WanfangSpider(BaseSpider):
    name = 'wanfang'
    allowed_domains = ["wanfangdata.com.cn", "c.wanfangdata.com.cn", "sns.wanfangdata.com.cn", "d.wanfangdata.com.cn"]
    platform_code = "wanfang"  # 平台标识
    base_url = "https://w.wanfangdata.com.cn"
    """
    自定义配置
    """
    custom_settings = {
        "CONCURRENT_REQUESTS": 10,  # 增加并发量
        "MONGO_DATABASE": "raw_cn_article_list",
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "DEFAULT_REQUEST_HEADERS": {
            'Referer': 'https://c.wanfangdata.com.cn/',
            'Origin': 'https://c.wanfangdata.com.cn',
        },
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
        },
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 180 * 1000,  # Playwright 请求页面时使用的超时时间
        "PLAYWRIGHT_MAX_PAGES_PER_CONTEXT": 3,  # 限制每个浏览器上下文中的最大并发页面数
        'ITEM_PIPELINES': {
            'src.pipelines.data_cleaning_pipeline.DataCleaningPipeline': 99,
            'src.pipelines.file_download_pipeline.FileDownloadPipeline': 100,
            'src.pipelines.file_replacement_pipeline.FileReplacementPipeline': 200,
            # 'src.pipelines.storage.chi_article_pipeline.CNArticleInterfacePipeline': 300,
            'src.pipelines.storage.chi_article_pipeline.CNArticlePipeline': 301,
            # 'src.pipelines.storage.chi_journal_pipeline.CNJournalInterfacePipeline': 302,
            'src.pipelines.storage.chi_journal_pipeline.CNJournalPipeline': 303,
        },
        "DOWNLOADER_MIDDLEWARES": {
            'src.middlewares.proxy_middleware.BaseProxyMiddleware': 400,  # 代理请求中间件
            # 'src.middlewares.custom_retry_middleware.CustomRetryMiddleware': 500,  # 使用自定义重试中间件
        },
        'RETRY_TIMES': 3,  # 请求重试次数
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 522, 524, 408, 429, 403, 404],  # 重试的HTTP状态码
        "EXTENSIONS": {
            'scrapy.extensions.logstats.LogStats': None,
            'src.extensions.verbose_log_stats.VerboseLogStats': 500,  # 510是优先级
        },
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        # 控制最大并发请求数，避免请求堆积
        "CONCURRENT_REQUESTS_PER_DOMAIN": 6,  # 对同一域名的并发请求数
        "CONCURRENT_REQUESTS_PER_IP": 0,
        # 专门针对Playwright请求的设置
        "PLAYWRIGHT_MAX_CONTEXTS": 2,  # 限制浏览器上下文数量
    }

    def __init__(self, **kwargs):
        """
        初始化当前类
        :param kwargs:
        """
        super().__init__(**kwargs)
        self.base_url = "https://c.wanfangdata.com.cn"
        self.sns_base_url = "https://sns.wanfangdata.com.cn"
        self.detail_base_url = "https://d.wanfangdata.com.cn"

        # 初始化断点续爬相关变量
        self.TEMP_DIR = os.path.join(TEMP_PATH, 'Wanfang')
        os.makedirs(self.TEMP_DIR, exist_ok=True)
        self.journal_ids_file = os.path.join(self.TEMP_DIR, 'journal_ids.txt')
        self.article_ids_file = os.path.join(self.TEMP_DIR, 'article_ids.txt')
        self.progress_file = os.path.join(self.TEMP_DIR, 'progress.json')  # 进度文件

        # 已处理的期刊和文献ID集合
        self.processed_journals = set()
        self.processed_articles = set()

        # 使用缓冲队列批量写入文件
        self.journal_id_buffer = deque()
        self.article_id_buffer = deque()
        self.buffer_size = 100  # 缓冲区大小

        # 当前处理进度
        self.current_progress = {
            "category_field": None,
            "category_name": None,
            "subcategory_name": None,
            "journal_index": 0,
            "article_list_url": None,
            "article_page": 0,
            "issue_index": 0
        }
        self._load_progress()

        # 加载已处理的ID
        self._load_processed_ids()

    def _load_progress(self):
        """
        从文件加载处理进度
        """
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    self.current_progress = json.load(f)
                custom_logger.info(f"已加载处理进度: {self.current_progress}")
            except Exception as e:
                custom_logger.warning(f"加载处理进度失败: {e}")

    def _save_progress(self):
        """
        保存处理进度到文件
        """
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            custom_logger.warning(f"保存处理进度失败: {e}")

    def _clear_progress(self):
        """
        清除处理进度
        """
        self.current_progress = {
            "category_field": None,
            "category_name": None,
            "subcategory_name": None,
            "journal_index": 0,
            "article_list_url": None,
            "article_page": 0,
            "issue_index": 0
        }
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)

    def _load_processed_ids(self):
        """
        从文件加载已处理的期刊ID和文献ID
        """
        # 加载已处理的期刊ID
        if os.path.exists(self.journal_ids_file):
            try:
                with open(self.journal_ids_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        journal_id = line.strip()
                        if journal_id:
                            self.processed_journals.add(journal_id)
                custom_logger.info(f"已加载 {len(self.processed_journals)} 个已处理的期刊ID")
            except Exception as e:
                custom_logger.warning(f"加载已处理期刊ID失败: {e}")

        # 加载已处理的文献ID
        if os.path.exists(self.article_ids_file):
            try:
                with open(self.article_ids_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        article_id = line.strip()
                        if article_id:
                            self.processed_articles.add(article_id)
                custom_logger.info(f"已加载 {len(self.processed_articles)} 个已处理的文献ID")
            except Exception as e:
                custom_logger.warning(f"加载已处理文献ID失败: {e}")

    def closed(self, reason):
        """
        爬虫关闭时的清理工作
        """
        # 确保所有缓冲区数据都被写入
        self._flush_journal_ids()
        self._flush_article_ids()
        self._save_progress()
        custom_logger.info(f"爬虫关闭，原因: {reason}")

    def _save_processed_journal_id(self, journal_id):
        """
        保存已处理的期刊ID到文件（使用缓冲机制）
        :param journal_id: 期刊ID
        """
        # 避免重复添加
        if journal_id not in self.processed_journals:
            self.journal_id_buffer.append(journal_id)
            self.processed_journals.add(journal_id)

            if len(self.journal_id_buffer) >= self.buffer_size:
                self._flush_journal_ids()

    def _save_processed_article_id(self, article_id):
        """
        保存已处理的文献ID到文件（使用缓冲机制）
        :param article_id: 文献ID
        """
        # 避免重复添加
        if article_id not in self.processed_articles:
            self.article_id_buffer.append(article_id)
            self.processed_articles.add(article_id)

            if len(self.article_id_buffer) >= self.buffer_size:
                self._flush_article_ids()

    def _flush_journal_ids(self):
        """
        将缓冲的期刊ID写入文件
        """
        if not self.journal_id_buffer:
            return

        try:
            with open(self.journal_ids_file, 'a', encoding='utf-8') as f:
                while self.journal_id_buffer:
                    journal_id = self.journal_id_buffer.popleft()
                    f.write(f"{journal_id}\n")
            custom_logger.info(f"已批量写入 {len(self.journal_id_buffer)} 个期刊ID到文件")
        except Exception as e:
            custom_logger.warning(f"批量保存期刊ID失败: {e}")

    def _flush_article_ids(self):
        """
        将缓冲的文献ID写入文件
        """
        if not self.article_id_buffer:
            return

        try:
            with open(self.article_ids_file, 'a', encoding='utf-8') as f:
                while self.article_id_buffer:
                    article_id = self.article_id_buffer.popleft()
                    f.write(f"{article_id}\n")
            custom_logger.info(f"已批量写入 {len(self.article_id_buffer)} 个文献ID到文件")
        except Exception as e:
            custom_logger.warning(f"批量保存文献ID失败: {e}")


    def start_requests(self):
        """
        开始请求，获取期刊分类
        """
        start_time = time.time()
        custom_logger.info(f"[时间记录] 开始执行 start_requests")
        # 第一次请求获取大类分类
        payload = {
            "cluster_field": [
                {
                    "field": "ClassCode",
                    "prefix": "0/"
                }
            ]
        }

        yield scrapy.Request(
            url="https://c.wanfangdata.com.cn/Category/Facet/Magazine",
            method="POST",
            body=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            callback=self.parse_categories,
            meta={
                "is_first_level": True,
                "start_time": start_time,
                "request_type": "start_requests"
            },


        )

    def parse_categories(self, response: Response):
        """
        解析期刊分类
        """
        start_time = response.meta.get("start_time")
        request_type = response.meta.get("request_type")
        if start_time:
            elapsed_time = time.time() - start_time
            custom_logger.info(f"[时间记录] {request_type} 执行完成，耗时: {elapsed_time:.2f}秒")

        process_start_time = time.time()  # 记录处理开始时间
        custom_logger.info(f"[时间记录] 开始执行 parse_categories")

        data = json.loads(response.text)
        cluster_field = data.get("clusterField", {})
        class_code_clusters = cluster_field.get("ClassCode", {}).get("cluster", [])

        is_first_level = response.meta.get("is_first_level", False)

        if is_first_level:
            # 处理大类，按顺序处理
            if class_code_clusters:
                # 先处理第一个大类
                first_category = class_code_clusters[0]
                remaining_categories = class_code_clusters[1:]

                field = first_category.get("field")
                name = first_category.get("name")  # 如 "0/B"
                number = first_category.get("number")

                # 构造小类请求参数，将0改为1
                prefix_parts = name.split("/")
                prefix_parts[0] = "1"
                new_prefix = "/".join(prefix_parts)  # 如 "1/B"

                payload = {
                    "cluster_field": [
                        {
                            "field": "ClassCode",
                            "prefix": new_prefix
                        }
                    ]
                }

                yield scrapy.Request(
                    url="https://c.wanfangdata.com.cn/Category/Facet/Magazine",
                    method="POST",
                    body=json.dumps(payload),
                    headers={"Content-Type": "application/json"},
                    callback=self.parse_categories,
                    meta={
                        "is_first_level": False,
                        "category_field": field,  # 大类名称，如"哲学政法"
                        "category_name": new_prefix,  # 小类前缀，如"1/B"
                        "remaining_categories": remaining_categories,  # 剩余的大类
                        "start_time": time.time(),  # 记录请求开始时间
                        "request_type": "parse_categories_first_level"
                    },

                )
        else:
            # 处理小类，请求具体期刊列表
            category_field = response.meta.get("category_field")
            category_name = response.meta.get("category_name")
            remaining_categories = response.meta.get("remaining_categories", [])

            # 处理当前大类下的所有小类
            if class_code_clusters:
                # 处理第一个小类
                first_sub_category = class_code_clusters[0]
                remaining_sub_categories = class_code_clusters[1:]

                field = first_sub_category.get("field")  # 小类名称，如"哲学"
                name = first_sub_category.get("name")  # 小类编码，如"1/B/B0"
                number = int(first_sub_category.get("number", 0))

                # 计算总页数，每页50条数据
                total_pages = (number + 49) // 50  # 向上取整

                # 请求每个小类下的期刊列表（第一页）
                start = 0
                payload = {
                    "query": [],
                    "start": start,
                    "rows": 50,
                    "sort_field": {
                        "sort_field": "LastYear;HasFulltext;CoreScore"
                    },
                    "highlight_field": "",
                    "pinyin_title": [],
                    "class_code": name,
                    "core_periodical": [],
                    "sponsor_region": [],
                    "publishing_period": [],
                    "publish_status": "",
                    "return_fields": [
                        "Title", "Id", "CorePeriodical", "CorePeriodicalYear", "Award",
                        "IsPrePublished"
                    ]
                }

                yield scrapy.Request(
                    url="https://c.wanfangdata.com.cn/Category/Magazine/search",
                    method="POST",
                    body=json.dumps(payload),
                    headers={"Content-Type": "application/json"},
                    callback=self.parse_journal_list,
                    meta={
                        "category_info": {
                            "major_category": category_field,
                            "minor_category": field
                        },
                        "subcategory_name": name,
                        "total_pages": total_pages,
                        "current_page": 0,
                        "remaining_sub_categories": remaining_sub_categories,
                        "remaining_categories": remaining_categories,
                        "major_category_field": category_field,
                        "major_category_name": category_name,
                        "start_time": time.time(),  # 记录请求开始时间
                        "request_type": "parse_categories_sub_level"
                    },

                )
        # 记录处理耗时
        if process_start_time:
            elapsed_time = time.time() - process_start_time
            custom_logger.info(f"[时间记录] parse_categories 处理完成，耗时: {elapsed_time:.2f}秒")

    def parse_journal_list(self, response: Response):
        """
        解析期刊列表，串行处理每个期刊
        """
        start_time = response.meta.get("start_time")
        request_type = response.meta.get("request_type")
        if start_time:
            elapsed_time = time.time() - start_time
            custom_logger.info(f"[时间记录] {request_type} 请求完成，耗时: {elapsed_time:.2f}秒")

        process_start_time = time.time()  # 记录处理开始时间
        custom_logger.info(f"[时间记录] 开始执行 parse_journal_list")

        data = json.loads(response.text)
        journals = data.get("value", [])
        category_info = response.meta.get("category_info")
        subcategory_name = response.meta.get("subcategory_name")
        total_pages = response.meta.get("total_pages", 1)
        current_page = response.meta.get("current_page", 0)
        remaining_sub_categories = response.meta.get("remaining_sub_categories", [])
        remaining_categories = response.meta.get("remaining_categories", [])
        major_category_field = response.meta.get("major_category_field")
        major_category_name = response.meta.get("major_category_name")
        journal_index = response.meta.get("journal_index", 0)  # 当前处理的期刊索引

        # 更新进度信息
        self.current_progress.update({
            "subcategory_name": subcategory_name,
            "journal_index": journal_index
        })
        self._save_progress()

        # 检查是否所有期刊都已处理
        if journal_index >= len(journals):
            # 如果还有更多页面，继续请求下一页
            if current_page + 1 < total_pages:
                next_page = current_page + 1
                start = next_page * 50
                payload = {
                    "query": [],
                    "start": start,
                    "rows": 50,
                    "sort_field": {
                        "sort_field": "LastYear;HasFulltext;CoreScore"
                    },
                    "highlight_field": "",
                    "pinyin_title": [],
                    "class_code": subcategory_name,
                    "core_periodical": [],
                    "sponsor_region": [],
                    "publishing_period": [],
                    "publish_status": "",
                    "return_fields": [
                        "Title", "Id", "CorePeriodical", "CorePeriodicalYear", "Award",
                        "IsPrePublished"
                    ]
                }

                yield scrapy.Request(
                    url="https://c.wanfangdata.com.cn/Category/Magazine/search",
                    method="POST",
                    body=json.dumps(payload),
                    headers={"Content-Type": "application/json"},
                    callback=self.parse_journal_list,
                    meta={
                        "category_info": category_info,
                        "subcategory_name": subcategory_name,
                        "total_pages": total_pages,
                        "current_page": next_page,
                        "remaining_sub_categories": remaining_sub_categories,
                        "remaining_categories": remaining_categories,
                        "major_category_field": major_category_field,
                        "major_category_name": major_category_name,
                        "start_time": time.time(),  # 记录请求开始时间
                        "request_type": "parse_journal_list_next_page",
                        "journal_index": 0  # 重置期刊索引
                    },
                )
            else:
                # 当前小类的所有页面都处理完了，处理下一个小类
                if remaining_sub_categories:
                    next_sub_category = remaining_sub_categories[0]
                    new_remaining_sub_categories = remaining_sub_categories[1:]

                    field = next_sub_category.get("field")
                    name = next_sub_category.get("name")
                    number = int(next_sub_category.get("number", 0))

                    # 计算总页数
                    total_pages = (number + 49) // 50

                    # 请求第一个页面
                    start = 0
                    payload = {
                        "query": [],
                        "start": start,
                        "rows": 50,
                        "sort_field": {
                            "sort_field": "LastYear;HasFulltext;CoreScore"
                        },
                        "highlight_field": "",
                        "pinyin_title": [],
                        "class_code": name,
                        "core_periodical": [],
                        "sponsor_region": [],
                        "publishing_period": [],
                        "publish_status": "",
                        "return_fields": [
                            "Title", "Id", "CorePeriodical", "CorePeriodicalYear", "Award",
                            "IsPrePublished"
                        ]
                    }

                    # 更新进度信息
                    self.current_progress.update({
                        "subcategory_name": name,
                        "journal_index": 0
                    })
                    self._save_progress()

                    yield scrapy.Request(
                        url="https://c.wanfangdata.com.cn/Category/Magazine/search",
                        method="POST",
                        body=json.dumps(payload),
                        headers={"Content-Type": "application/json"},
                        callback=self.parse_journal_list,
                        meta={
                            "category_info": {
                                "major_category": major_category_field,
                                "minor_category": field
                            },
                            "subcategory_name": name,
                            "total_pages": total_pages,
                            "current_page": 0,
                            "remaining_sub_categories": new_remaining_sub_categories,
                            "remaining_categories": remaining_categories,
                            "major_category_field": major_category_field,
                            "major_category_name": major_category_name,
                            "start_time": time.time(),  # 记录请求开始时间
                            "request_type": "parse_journal_list_next_subcategory",
                            "journal_index": 0  # 重置期刊索引
                        },
                    )
                else:
                    # 当前大类下的所有小类都处理完了，处理下一个大类
                    if remaining_categories:
                        # 构造下一个大类的小类请求参数
                        next_category = remaining_categories[0]
                        new_remaining_categories = remaining_categories[1:]

                        field = next_category.get("field")
                        name = next_category.get("name")  # 如 "0/B"
                        number = next_category.get("number")

                        # 构造小类请求参数，将0改为1
                        prefix_parts = name.split("/")
                        prefix_parts[0] = "1"
                        new_prefix = "/".join(prefix_parts)  # 如 "1/B"

                        payload = {
                            "cluster_field": [
                                {
                                    "field": "ClassCode",
                                    "prefix": new_prefix
                                }
                            ]
                        }

                        # 更新进度信息
                        self.current_progress.update({
                            "category_field": field,
                            "category_name": new_prefix,
                            "subcategory_name": None,
                            "journal_index": 0
                        })
                        self._save_progress()

                        yield scrapy.Request(
                            url="https://c.wanfangdata.com.cn/Category/Facet/Magazine",
                            method="POST",
                            body=json.dumps(payload),
                            headers={"Content-Type": "application/json"},
                            callback=self.parse_categories,
                            meta={
                                "is_first_level": False,
                                "category_field": field,  # 大类名称，如"哲学政法"
                                "category_name": new_prefix,  # 小类前缀，如"1/B"
                                "remaining_categories": new_remaining_categories,  # 剩余的大类
                                "start_time": time.time(),  # 记录请求开始时间
                                "request_type": "parse_categories_next_major_category"
                            },
                        )
                    else:
                        # 所有分类处理完成
                        custom_logger.info("所有期刊分类处理完成")
                        self._clear_progress()

            # 记录处理耗时
            if process_start_time:
                elapsed_time = time.time() - process_start_time
                custom_logger.info(f"[时间记录] parse_journal_list 处理完成，耗时: {elapsed_time:.2f}秒")
            return

        # 处理当前期刊
        if journal_index < len(journals):
            journal = journals[journal_index]
            journal_id = journal.get("Id")
            journal_title = journal.get("Title", [""])[0] if journal.get("Title") else ""

            # 构造期刊详情页链接
            journal_url = f"https://sns.wanfangdata.com.cn/perio/{journal_id}"

            # 更新进度信息
            self.current_progress["journal_index"] = journal_index
            self._save_progress()

            yield scrapy.Request(
                url=journal_url,
                callback=self.parse_journal_detail,
                meta={
                    "journal_id": journal_id,
                    "journal_title": journal_title,
                    "category_info": category_info,
                    "start_time": time.time(),
                    "request_type": "parse_journal_detail",
                    # 传递继续处理所需的信息
                    "journals": journals,
                    "subcategory_name": subcategory_name,
                    "total_pages": total_pages,
                    "current_page": current_page,
                    "remaining_sub_categories": remaining_sub_categories,
                    "remaining_categories": remaining_categories,
                    "major_category_field": major_category_field,
                    "major_category_name": major_category_name,
                    "journal_index": journal_index,
                },
            )

        # 记录处理耗时
        if process_start_time:
            elapsed_time = time.time() - process_start_time
            custom_logger.info(f"[时间记录] parse_journal_list 处理完成，耗时: {elapsed_time:.2f}秒")

    def parse_journal_detail(self, response: Response):
        """
        解析期刊详情页
        """
        start_time = response.meta.get("start_time")
        request_type = response.meta.get("request_type")
        if start_time:
            elapsed_time = time.time() - start_time
            custom_logger.info(f"[时间记录] {request_type} 请求完成，耗时: {elapsed_time:.2f}秒")

        process_start_time = time.time()  # 记录处理开始时间
        custom_logger.info(f"[时间记录] 开始执行 parse_journal_detail")

        journal_id = response.meta["journal_id"]
        journal_title = response.meta["journal_title"]
        category_info = response.meta["category_info"]

        # 传递继续处理所需的信息
        journals = response.meta["journals"]
        subcategory_name = response.meta["subcategory_name"]
        total_pages = response.meta["total_pages"]
        current_page = response.meta["current_page"]
        remaining_sub_categories = response.meta["remaining_sub_categories"]
        remaining_categories = response.meta["remaining_categories"]
        major_category_field = response.meta["major_category_field"]
        major_category_name = response.meta["major_category_name"]
        journal_index = response.meta["journal_index"]

        # 检查是否已处理过该期刊
        is_journal_processed = journal_id in self.processed_journals
        custom_logger.info(f"期刊 {journal_id} 处理状态: {'已处理' if is_journal_processed else '未处理'}")

        # 提取期刊基本信息
        selector_model = BaseSelectorComponent()

        # 期刊标题和英文标题
        selector_model.add_field(
            selector='.perio_title',
            field_name='journal_name',
            selector_type='css',
            field_type='html'
        )

        # 期刊英文名（在journal_name的子元素中）
        selector_model.add_field(
            selector='.perio_title wf-block',
            field_name='journal_en_name',
            selector_type='css',
            field_type='text'
        )

        # 期刊封面图片链接
        selector_model.add_field(
            selector='wf-place-holder img::attr(src)',
            field_name='journal_image',
            selector_type='css',
            field_type='href'
        )

        # 期刊收录情况
        selector_model.add_field(
            selector='wf-core-perio',
            field_name='index_list',
            selector_type='css',
            field_type='list'
        )

        # 期刊简介
        selector_model.add_field(
            selector='wf-ellipsis-content',
            field_name='journal_intro',
            selector_type='css',
            field_type='text'
        )

        # 曾用名
        selector_model.add_field(
            selector='wf-field-lable:contains("曾用名：") + wf-field-value',
            field_name='former_title',
            selector_type='css',
            field_type='text'
        )

        # 主办单位
        selector_model.add_field(
            selector='wf-field-lable:contains("主办单位：") + wf-field-value',
            field_name='sponsor',
            selector_type='css',
            field_type='text'
        )

        # 主编
        selector_model.add_field(
            selector='wf-field-lable:contains("主编：") + wf-field-value',
            field_name='chief_editor',
            selector_type='css',
            field_type='text'
        )

        # 出版周期
        selector_model.add_field(
            selector='wf-field-lable:contains("出版周期：") + wf-field-value',
            field_name='publish_cycle',
            selector_type='css',
            field_type='text'
        )

        # 语种
        selector_model.add_field(
            selector='wf-field-lable:contains("语种：") + wf-field-value',
            field_name='language',
            selector_type='css',
            field_type='text'
        )

        # 国际刊号(ISSN)
        selector_model.add_field(
            selector='wf-field-lable:contains("国际刊号：") + wf-field-value',
            field_name='issn',
            selector_type='css',
            field_type='text'
        )

        # 国内刊号(CN)
        selector_model.add_field(
            selector='wf-field-lable:contains("国内刊号：") + wf-field-value',
            field_name='cn',
            selector_type='css',
            field_type='text'
        )

        # 电话
        selector_model.add_field(
            selector='wf-field-lable:contains("电话：") + wf-field-value',
            field_name='phone',
            selector_type='css',
            field_type='text'
        )

        # 邮政编码
        selector_model.add_field(
            selector='wf-field-lable:contains("邮政编码：") + wf-field-value',
            field_name='postcode',
            selector_type='css',
            field_type='text'
        )

        # 地址
        selector_model.add_field(
            selector='wf-field-lable:contains("地址：") + wf-field-value',
            field_name='address',
            selector_type='css',
            field_type='text'
        )

        # 执行提取
        extract_result = selector_model.execute_non_yield(response=response)
        if not extract_result["result"]:
            custom_logger.error(f"提取期刊信息失败: {extract_result['msg']}")
            # 继续处理下一个期刊
            yield from self._continue_to_next_journal(
                journals, journal_index, category_info, subcategory_name,
                total_pages, current_page, remaining_sub_categories,
                remaining_categories, major_category_field, major_category_name
            )
            return

        journal_data = extract_result["data"]

        # 处理期刊收录信息
        index_list = []
        index_elements = response.css('wf-core-perio')
        for element in index_elements:
            index_text = element.css('::text').get()
            if index_text:
                index_list.append({
                    "index_name": index_text.strip(),
                    "index_intro": ""  # 万方没有提供详细的索引介绍
                })

        # 处理期刊标题，分离中英文名
        journal_full_name_html = journal_data.get("journal_name", "")  # 包含HTML标签的完整标题
        journal_en_name = journal_data.get("journal_en_name", "")
        journal_image = journal_data.get("journal_image", "")  # 获取期刊封面图片链接

        # 从HTML中提取中文标题（h1标签内的第一部分文本）
        journal_cn_name = ""
        if journal_full_name_html:
            # 提取h1标签内的文本，排除子元素
            soup_match = re.search(r'<h1[^>]*>(.*?)<wf-', journal_full_name_html, re.DOTALL)
            if soup_match:
                journal_cn_name = re.sub(r'<[^>]+>', '', soup_match.group(1)).strip()
            else:
                # 备选方案：直接提取h1标签内容并清理
                journal_cn_name = re.sub(r'<[^>]+>', '', journal_full_name_html).strip()
                # 如果还有英文内容，只取第一部分
                if journal_cn_name:
                    parts = journal_cn_name.split()
                    if parts:
                        journal_cn_name = parts[0]

        # 处理英文名，移除韩文等非英文内容
        if journal_en_name:
            # 移除韩文部分（或其他非英文内容）
            # 只保留英文和空格
            journal_en_name = re.sub(r'[^\x00-\x7F\s]+', '', journal_en_name).strip()
            # 清理多余的空格
            journal_en_name = re.sub(r'\s+', ' ', journal_en_name).strip()

        # 获取投稿信息
        submission_url = f"https://sns.wanfangdata.com.cn/third-web/per/perio/information?perioId={journal_id}"
        yield scrapy.Request(
            url=submission_url,
            callback=self.parse_submission_info,
            meta={
                "journal_data": journal_data,
                "journal_id": journal_id,
                "journal_cn_name": journal_cn_name,
                "journal_en_name": journal_en_name,
                "index_list": index_list,
                "category_info": category_info,
                # 传递期刊详情页的HTML内容
                "journal_detail_html": response.text,
                "journal_image": journal_image,
                "is_journal_processed": is_journal_processed,  # 传递期刊是否已处理的标记
                "start_time": time.time(),  # 记录请求开始时间
                "request_type": "parse_submission_info",
                # 传递继续处理所需的信息
                "journals": journals,
                "subcategory_name": subcategory_name,
                "total_pages": total_pages,
                "current_page": current_page,
                "remaining_sub_categories": remaining_sub_categories,
                "remaining_categories": remaining_categories,
                "major_category_field": major_category_field,
                "major_category_name": major_category_name,
                "journal_index": journal_index,
            },
        )

        # 记录处理耗时
        if process_start_time:
            elapsed_time = time.time() - process_start_time
            custom_logger.info(f"[时间记录] parse_journal_detail 处理完成，耗时: {elapsed_time:.2f}秒")

    def parse_submission_info(self, response: Response):
        """
        解析投稿信息
        """
        start_time = response.meta.get("start_time")
        request_type = response.meta.get("request_type")
        if start_time:
            elapsed_time = time.time() - start_time
            custom_logger.info(f"[时间记录] {request_type} 执行完成，耗时: {elapsed_time:.2f}秒")

        process_start_time = time.time()
        custom_logger.info(f"[时间记录] 开始执行 parse_submission_info")


        journal_data = response.meta["journal_data"]
        journal_id = response.meta["journal_id"]
        journal_cn_name = response.meta["journal_cn_name"]
        journal_en_name = response.meta["journal_en_name"]
        index_list = response.meta["index_list"]
        category_info = response.meta["category_info"]
        # 获取期刊详情页的HTML内容
        journal_detail_html = response.meta.get("journal_detail_html")
        is_journal_processed = response.meta.get("is_journal_processed")

        # 提取投稿方式信息
        submission_methods = {}
        response_text = response.text

        # E-mail投稿
        email_match = re.search(r'投稿地址：([^\s<]+)', response_text)
        if email_match:
            submission_methods['email'] = email_match.group(1)

        # 邮寄投稿信息
        mail_info = {}
        address_match = re.search(r'邮寄地址：([^<\s]+)', response_text)
        if address_match:
            mail_info['address'] = address_match.group(1)

        postcode_match = re.search(r'邮编：([^<\s]+)', response_text)
        if postcode_match:
            mail_info['postcode'] = postcode_match.group(1)

        recipient_match = re.search(r'收件人：([^<\s]+)', response_text)
        if recipient_match:
            mail_info['recipient'] = recipient_match.group(1)

        if mail_info:
            submission_methods['mail'] = mail_info

        # 在线投稿
        online_match = re.search(r"window\.open\('([^']+)'\)", response_text)
        if online_match:
            submission_methods['online'] = online_match.group(1)

        # 获取主管单位和电子邮箱信息
        synopsis_url = f"https://sns.wanfangdata.com.cn/third-web/per/perio/synopsis?perioId={journal_id}"
        yield scrapy.Request(
            url=synopsis_url,
            callback=self.parse_synopsis_info,
            meta={
                "journal_data": journal_data,
                "journal_id": journal_id,
                "journal_cn_name": journal_cn_name,
                "journal_en_name": journal_en_name,
                "index_list": index_list,
                "category_info": category_info,
                "submission_methods": submission_methods,
                # 传递期刊详情页的响应对象
                "journal_detail_html": journal_detail_html,
                "is_journal_processed": is_journal_processed,
                "start_time": time.time(),  # 记录请求开始时
                "request_type": "parse_synopsis_info"
            },

        )
        # 记录处理耗时
        if process_start_time:
            elapsed_time = time.time() - process_start_time
            custom_logger.info(f"[时间记录] parse_submission_info 处理完成，耗时: {elapsed_time:.2f}秒")
    def parse_synopsis_info(self, response: Response):
        """
        解析期刊概要信息（主管单位等）
        """

        start_time = response.meta.get("start_time")
        request_type = response.meta.get("request_type")
        if start_time:
            elapsed_time = time.time() - start_time
            custom_logger.info(f"[时间记录] {request_type} 执行完成，耗时: {elapsed_time:.2f}秒")

        process_start_time = time.time()
        custom_logger.info(f"[时间记录] 开始执行 parse_synopsis_info")

        journal_data = response.meta["journal_data"]
        journal_id = response.meta["journal_id"]
        journal_cn_name = response.meta["journal_cn_name"]
        journal_en_name = response.meta["journal_en_name"]
        index_list = response.meta["index_list"]
        category_info = response.meta["category_info"]
        submission_methods = response.meta["submission_methods"]
        # 获取期刊详情页的HTML内容
        journal_detail_html = response.meta.get("journal_detail_html")
        is_journal_processed = response.meta.get("is_journal_processed")

        # 提取主管单位
        competent_department = ""
        competent_match = re.search(r'主管单位：.*?<span[^>]*>([^<]+)</span>', response.text, re.DOTALL)
        if competent_match:
            competent_department = competent_match.group(1).strip()

        # 提取电子邮箱
        email_list = []
        email_match = re.search(r'电子邮箱：.*?<span[^>]*>([^<]+)</span>', response.text, re.DOTALL)
        if email_match:
            email_text = email_match.group(1)
            # 分割多个邮箱
            emails = re.split(r'[；\s]+', email_text)
            email_list = [email.strip() for email in emails if email.strip()]

        # 获取通知信息（审稿周期等）
        notices_url = f"https://sns.wanfangdata.com.cn/third-web/per/perio/notices?perioId={journal_id}&currentUser="
        yield scrapy.Request(
            url=notices_url,
            callback=self.parse_notices_info,
            meta={
                "journal_data": journal_data,
                "journal_id": journal_id,
                "journal_cn_name": journal_cn_name,
                "journal_en_name": journal_en_name,
                "index_list": index_list,
                "category_info": category_info,
                "submission_methods": submission_methods,
                "competent_department": competent_department,
                "email_list": email_list,
                # 传递期刊详情页的响应对象
                "journal_detail_html": journal_detail_html,
                "is_journal_processed": is_journal_processed,
                "start_time": time.time(),
                "request_type": "parse_notices_info"
            },
        )
        # 记录处理耗时
        if process_start_time:
            elapsed_time = time.time() - process_start_time
            custom_logger.info(f"[时间记录] parse_synopsis_info 处理完成，耗时: {elapsed_time:.2f}秒")

    def parse_notices_info(self, response: Response):
        """
        解析期刊通知信息（审稿周期等）
        """
        start_time = response.meta.get("start_time")
        request_type = response.meta.get("request_type")
        if start_time:
            elapsed_time = time.time() - start_time
            custom_logger.info(f"[时间记录] {request_type} 执行完成，耗时: {elapsed_time:.2f}秒")

        process_start_time = time.time()
        custom_logger.info(f"[时间记录] 开始执行 parse_notices_info")

        journal_data = response.meta["journal_data"]
        journal_id = response.meta["journal_id"]
        journal_cn_name = response.meta["journal_cn_name"]
        journal_en_name = response.meta["journal_en_name"]
        index_list = response.meta["index_list"]
        category_info = response.meta["category_info"]
        submission_methods = response.meta["submission_methods"]
        competent_department = response.meta["competent_department"]
        email_list = response.meta["email_list"]
        # 获取期刊详情页的响应对象
        journal_detail_html = response.meta.get("journal_detail_html")
        is_journal_processed = response.meta.get("is_journal_processed")

        # 传递继续处理所需的信息
        journals = response.meta.get("journals", [])
        subcategory_name = response.meta.get("subcategory_name")
        total_pages = response.meta.get("total_pages")
        current_page = response.meta.get("current_page")
        remaining_sub_categories = response.meta.get("remaining_sub_categories")
        remaining_categories = response.meta.get("remaining_categories")
        major_category_field = response.meta.get("major_category_field")
        major_category_name = response.meta.get("major_category_name")
        journal_index = response.meta.get("journal_index")

        # 提取审稿周期
        review_cycle = ""
        review_match = re.search(r'审稿周期：.*?<span[^>]*[^>]*>(.*?)</span>', response.text, re.DOTALL)
        if review_match:
            review_cycle_text = review_match.group(1)
            # 移除<b>标签，保留文本
            review_cycle = re.sub(r'<b[^>]*>(.*?)</b>', r'\1', review_cycle_text).strip()

        # 提取发稿周期
        publish_cycle = ""
        publish_match = re.search(r'发稿周期：.*?<span[^>]*[^>]*>(.*?)</span>', response.text, re.DOTALL)
        if publish_match:
            publish_cycle_text = publish_match.group(1)
            # 移除<b>标签，保留文本
            publish_cycle = re.sub(r'<b[^>]*>(.*?)</b>', r'\1', publish_cycle_text).strip()

        # 提取出版周期（可能与之前获取的不一样）
        publish_period = ""
        publish_period_match = re.search(r'出版周期：.*?<span[^>]*>(.*?)</span>', response.text, re.DOTALL)
        if publish_period_match:
            publish_period = publish_period_match.group(1).strip()

        # 使用期刊详情页的响应对象来提取文献链接，避免重复请求
        if journal_detail_html:
            custom_logger.info(f"使用已保存的期刊详情页响应来提取文献链接，期刊ID: {journal_id}")
            # 直接处理文献链接
            requests_list = list(self.extract_and_process_article_links(journal_detail_html, journal_id, journal_data, {
                "journal_data": journal_data,
                "journal_id": journal_id,
                "journal_cn_name": journal_cn_name,
                "journal_en_name": journal_en_name,
                "index_list": index_list,
                "category_info": category_info,
                "submission_methods": submission_methods,
                "competent_department": competent_department,
                "email_list": email_list,
                "review_cycle": review_cycle,
                "publish_cycle": publish_cycle,
                "publish_period": publish_period,
                "journal_detail_html": journal_detail_html,
                "is_journal_processed": is_journal_processed,
                # 传递继续处理所需的信息
                "journals": journals,
                "subcategory_name": subcategory_name,
                "total_pages": total_pages,
                "current_page": current_page,
                "remaining_sub_categories": remaining_sub_categories,
                "remaining_categories": remaining_categories,
                "major_category_field": major_category_field,
                "major_category_name": major_category_name,
                "journal_index": journal_index,
            }, start_time=time.time()))

            # 逐个yield请求或item
            for req_or_item in requests_list:
                yield req_or_item

        # 记录处理耗时
        if process_start_time:
            elapsed_time = time.time() - process_start_time
            custom_logger.info(f"[时间记录] parse_notices_info 处理完成，耗时: {elapsed_time:.2f}秒")
        # else:
        #     # 如果没有响应对象，仍然请求期刊详情页
        #     journal_detail_url = f"https://sns.wanfangdata.com.cn/perio/{journal_id}"
        #     custom_logger.info(f"准备请求期刊详情页以获取文献列表: {journal_detail_url}")
        #
        #     yield scrapy.Request(
        #         url=journal_detail_url,
        #         callback=self.parse_journal_issues,
        #         meta={
        #             "journal_id": journal_id,
        #             "journal_data": journal_data
        #         }
        #     )

    def extract_and_process_article_links(self, html_content, journal_id, journal_data, journal_meta, start_time):
        """
        从期刊详情页HTML中提取文献链接并处理，串行化处理每期文献
        """
        request_type = "extract_and_process_article_links"
        if start_time:
            elapsed_time = time.time() - start_time
            custom_logger.info(f"[时间记录] {request_type} 执行完成，耗时: {elapsed_time:.2f}秒")

        process_start_time = time.time()
        custom_logger.info(f"[时间记录] 开始执行 extract_and_process_article_links")

        custom_logger.info(f"开始从期刊详情页HTML中提取文献链接，期刊ID: {journal_id}")

        # 提取年份信息
        year_pattern = re.compile(r'<wf-field-lable[^>]*class="text-left"[^>]*>\s*(\d{4})\s*<')
        year_matches = year_pattern.findall(html_content)

        # 获取最大年份作为end_year
        end_year = None
        if year_matches:
            try:
                years = [int(year) for year in year_matches]
                end_year = max(years)
            except ValueError:
                pass

        # 构造期刊Item
        journal_cn_name = journal_meta["journal_cn_name"]
        journal_en_name = journal_meta["journal_en_name"]
        index_list = journal_meta["index_list"]
        category_info = journal_meta["category_info"]
        submission_methods = journal_meta["submission_methods"]
        competent_department = journal_meta["competent_department"]
        email_list = journal_meta["email_list"]
        review_cycle = journal_meta["review_cycle"]
        publish_cycle_val = journal_meta["publish_cycle"]
        publish_period = journal_meta["publish_period"]
        journal_detail_html = journal_meta["journal_detail_html"]
        is_journal_processed = journal_meta.get("is_journal_processed", False)  # 获取期刊是否已处理的标记

        # 传递继续处理所需的信息
        journals = journal_meta.get("journals", [])
        subcategory_name = journal_meta.get("subcategory_name")
        total_pages = journal_meta.get("total_pages")
        current_page = journal_meta.get("current_page")
        remaining_sub_categories = journal_meta.get("remaining_sub_categories")
        remaining_categories = journal_meta.get("remaining_categories")
        major_category_field = journal_meta.get("major_category_field")
        major_category_name = journal_meta.get("major_category_name")
        journal_index = journal_meta.get("journal_index", 0)

        # 处理期刊封面图片链接
        journal_image = journal_data.get("journal_image", "")

        # 出版商、主办单位和主管单位信息列表
        unit_list = []

        # 添加主管单位
        if competent_department:
            unit_list.append({
                "unit_name": competent_department,
                "relation_type": JOURNAL_UNIT_RELATION_TYPE["authority"]
            })

        # 添加主办单位
        sponsor = journal_data.get("sponsor", "")
        if sponsor:
            unit_list.append({
                "unit_name": sponsor,
                "relation_type": JOURNAL_UNIT_RELATION_TYPE["sponsor"]
            })

        # 期刊平台信息
        platform_list = [
            {
                "platform_id": journal_id,
                "platform_code": JOURNAL_PLATFORM_CODE["wanfang"],
            }
        ]

        # 添加ISSN
        issn = journal_data.get("issn", "")
        if issn:
            platform_list.append({
                "platform_id": issn,
                "platform_code": JOURNAL_PLATFORM_CODE["issn"],
            })

        # 添加CN号
        cn = journal_data.get("cn", "")
        if cn:
            platform_list.append({
                "platform_id": cn,
                "platform_code": JOURNAL_PLATFORM_CODE["cnsn"],
            })

        # 学科信息
        subject_info = []
        if category_info:
            # 一级学科
            tmp_data = {
                "first": category_info.get("major_category"),
                "second": [category_info.get("minor_category")],
            }
            subject_info.append(tmp_data)

        # 期刊额外信息
        extra_info = {
            "chief": journal_data.get("chief_editor"),
            "phone": journal_data.get("phone"),
            "address": journal_data.get("address"),
            "postcode": journal_data.get("postcode"),
            "review_cycle": review_cycle,
            "publish_cycle_info": publish_cycle_val,
            "email": email_list
        }

        # 添加投稿方式到extra_info
        if submission_methods.get("email"):
            extra_info["email_submission"] = submission_methods.get("email")
        if submission_methods.get("mail"):
            extra_info["mail_submission"] = submission_methods.get("mail")
        if submission_methods.get("online"):
            extra_info["online_submission"] = submission_methods.get("online")

        # 清理extra_info中的空值
        extra_info = {k: v for k, v in extra_info.items() if v}

        # 处理语言
        journal_lang = journal_data.get("language", "")
        if journal_lang == "英文":
            journal_lang = "eng"

        # 判断是否停刊
        if end_year:
            is_suspended = JOURNAL_IS_SUSPENDED["not_suspended"]
        else:
            is_suspended = JOURNAL_IS_SUSPENDED["suspended"]

        # 构造期刊Item（仅当期刊未处理时才生成）
        if not is_journal_processed:
            journal_item = CnJournalItem(
                journal_en_name=journal_en_name,
                journal_cn_name=journal_cn_name,
                former_name=[journal_data.get("former_title")] if journal_data.get("former_title") else [],
                journal_cn_intro=journal_data.get("journal_intro", ""),
                journal_en_intro="",  # 万方没有提供英文介绍
                data_source=self.platform_code,
                file_urls=[journal_image],
                journal_image=journal_image,
                journal_lang=journal_lang,
                publish_cycle=publish_period or journal_data.get("publish_cycle", ""),
                extra_info=extra_info,
                start_year=None,  # 万方没有提供创刊年份
                end_year=end_year,  # 设置从文献中提取的最大年份
                is_suspended=is_suspended,
                official_website="",  # 万方没有提供官网地址
                submission_address=submission_methods.get("online", ""),  # 在线投稿地址作为投稿地址
                open_access=JOURNAL_OPEN_ACCESS["not_open"],  # 万方没有明确标识OA期刊
                index_list=index_list,
                unit_list=unit_list,
                platform_list=platform_list,
                subject_info=subject_info,
                original_html=journal_detail_html,
                page_url=f"https://sns.wanfangdata.com.cn/perio/{journal_id}",
            )

            yield journal_item

            # 记录已处理的期刊ID
            self._save_processed_journal_id(journal_id)
            custom_logger.info(f"期刊 {journal_id} 已入库并记录")
        else:
            custom_logger.info(f"期刊 {journal_id} 已处理过，跳过入库")

        # 使用更精确的正则表达式提取年份和期号信息
        # 查找所有包含data-href属性的<span>标签
        issue_pattern = re.compile(r'<span[^>]*data-href="(/sns/perio/[^"]+)"[^>]*>([^<]+)</span>')
        matches = issue_pattern.findall(html_content)

        custom_logger.info(f"在期刊 {journal_id} 的HTML中找到 {len(matches)} 个期号链接")

        # 保存期号链接用于串行处理
        issue_links = []
        for href, issue_text in matches:
            # 解码HTML转义字符
            issue_href = html.unescape(href)

            # 构造完整的文献列表URL
            article_list_url = f"https://sns.wanfangdata.com.cn{issue_href}"
            issue_links.append({
                "url": article_list_url,
                "journal_id": journal_id,
                "journal_data": journal_data,
                "issue_text": issue_text
            })

        # 如果有期号链接，则处理第一个期号
        if issue_links:
            first_issue = issue_links[0]
            remaining_issues = issue_links[1:]

            # 更新进度信息
            self.current_progress.update({
                "article_list_url": first_issue["url"],
                "issue_index": 0
            })
            self._save_progress()

            custom_logger.info(f"准备请求第一期文献列表: {first_issue['url']}")
            yield scrapy.Request(
                url=first_issue["url"],
                callback=self.parse_article_list,
                meta={
                    "journal_id": first_issue["journal_id"],
                    "journal_data": first_issue["journal_data"],
                    "start_time": time.time(),
                    "request_type": "parse_article_list",
                    "article_url": first_issue["url"],
                    "is_first_page": True,
                    "issue_links": issue_links,  # 所有期号链接
                    "current_issue_index": 0,  # 当前期号索引
                }
            )
        else:
            # 没有文献需要处理，继续下一个期刊
            yield from self._continue_to_next_journal(
                journals,
                journal_index + 1,
                category_info,
                subcategory_name,
                total_pages,
                current_page,
                remaining_sub_categories,
                remaining_categories,
                major_category_field,
                major_category_name
            )

        if process_start_time:
            elapsed_time = time.time() - process_start_time
            custom_logger.info(f"[时间记录] extract_and_process_article_links 执行完成，耗时: {elapsed_time:.2f}秒")
    # def parse_journal_issues(self, response: Response):
    #     """
    #     解析期刊年份和期号信息，获取文献列表
    #     """
    #     journal_id = response.meta["journal_id"]
    #     journal_data = response.meta["journal_data"]
    #
    #     custom_logger.info(f"开始解析期刊 {journal_id} 的文献列表，响应状态码: {response.status}")
    #
    #     # 检查响应是否成功
    #     if response.status != 200:
    #         custom_logger.error(f"请求期刊详情页失败，状态码: {response.status}，URL: {response.url}")
    #         return
    #
    #     # 检查响应内容
    #     if not response.text:
    #         custom_logger.error(f"期刊详情页响应内容为空，URL: {response.url}")
    #         return
    #
    #     # 处理文献链接
    #     for request in self.extract_and_process_article_links(response.text, journal_id, journal_data):
    #         yield request

    def parse_article_list(self, response: Response):
        """
        解析文献列表，确保一页文献处理完后再处理下一页，一期文献处理完后再处理下一期
        """
        start_time = response.meta.get("start_time")
        request_type = response.meta.get("request_type")
        article_url = response.meta.get("article_url")
        is_first_page = response.meta.get("is_first_page", False)
        issue_links = response.meta.get("issue_links", [])
        current_issue_index = response.meta.get("current_issue_index", 0)
        if start_time:
            elapsed_time = time.time() - start_time
            custom_logger.info(f"[时间记录] {request_type} 请求完成，耗时: {elapsed_time:.2f}秒,{article_url}")

        process_start_time = time.time()
        custom_logger.info(f"[时间记录] 开始执行 parse_article_list，开始时间: {process_start_time}")

        journal_id = response.meta["journal_id"]
        journal_data = response.meta["journal_data"]

        custom_logger.info(f"开始解析期刊 {journal_id} 的文献列表，响应状态码: {response.status}")
        custom_logger.info(f"当前请求URL: {response.url}")

        # 提取文章信息，包括文章类型
        articles = []

        # 解析文章和类型
        # 先找到所有的文章类型
        category_matches = list(
            re.finditer(r'<wf-article-column[^>]*>(.*?)</wf-article-column>', response.text, re.DOTALL))
        # 再找到所有的文章链接
        article_matches = list(
            re.finditer(r'<a[^>]*href="(https?://d\.wanfangdata\.com\.cn/periodical/[^"]+)"[^>]*title="([^"]*)"[^>]*>',
                        response.text))

        # 添加调试信息
        custom_logger.info(f"找到 {len(category_matches)} 个文章类型")
        custom_logger.info(f"找到 {len(article_matches)} 篇文章")

        # 处理文章链接（如果存在）
        if len(article_matches) > 0:
            # 为每篇文章分配类型
            for article_match in article_matches:
                article_href = article_match.group(1)
                article_title = article_match.group(2)

                # 找到这篇文章对应的文章类型
                article_pos = article_match.start()
                article_type = ""

                # 找到在这篇文章之前最近的文章类型
                for j in range(len(category_matches)):
                    category_match = category_matches[j]
                    if category_match.start() < article_pos:
                        article_type = category_match.group(1).strip()
                    else:
                        break

                articles.append((article_href, article_title, article_type))

            # 并发处理当前页的所有文章
            article_requests = []
            for article_href, article_title, article_type in articles:
                custom_logger.info(
                    f"准备请求文章详情页: {article_href}，文章标题: {article_title}，文章类型: {article_type}")
                article_requests.append(scrapy.Request(
                    url=article_href,
                    callback=self.parse_article_detail,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "playwright_context": "default",  # 明确指定上下文
                        "playwright_page_methods": [
                            PageMethod("wait_for_load_state", state="networkidle")
                        ],
                        "journal_id": journal_id,
                        "journal_data": journal_data,
                        "article_type": article_type,
                        "article_title": article_title,
                        "start_time": time.time(),
                        "request_type": "parse_article_detail",
                        # 传递继续处理所需的信息
                        "issue_links": issue_links,
                        "current_issue_index": current_issue_index,
                    },
                    errback=self.playwright_request_error
                ))

            # 发出所有文章请求
            for request in article_requests:
                yield request

        else:
            custom_logger.warning(f"未提取到文章链接，截取部分HTML内容: {response.text[:2000]}")

        # 处理分页 - 查找下一页链接
        next_page_pattern = re.compile(r'<a[^>]*href="([^"]*)"[^>]*>\s*下一页\s*</a>')
        next_page_match = next_page_pattern.search(response.text)
        if next_page_match:
            next_page_href = next_page_match.group(1)
            if next_page_href:
                # 解码HTML转义字符
                next_page_href = html.unescape(next_page_href)
                next_page_url = f"https://sns.wanfangdata.com.cn{next_page_href}"

                custom_logger.info(f"准备请求下一页: {next_page_url}")
                yield scrapy.Request(
                    url=next_page_url,
                    callback=self.parse_article_list,
                    meta={
                        "journal_id": journal_id,
                        "journal_data": journal_data,
                        "start_time": time.time(),  # 更新开始时间
                        "request_type": "parse_article_list_next_page",
                        "issue_links": issue_links,
                        "current_issue_index": current_issue_index,
                    },
                )
        else:
            custom_logger.info(f"期刊 {journal_id} 的当前期文献列表处理完成，没有更多分页")
            # 当前期号处理完毕，处理下一个期号
            if current_issue_index + 1 < len(issue_links):
                next_issue_index = current_issue_index + 1
                next_issue = issue_links[next_issue_index]

                # 更新进度信息
                self.current_progress.update({
                    "article_list_url": next_issue["url"],
                    "issue_index": next_issue_index
                })
                self._save_progress()

                yield scrapy.Request(
                    url=next_issue["url"],
                    callback=self.parse_article_list,
                    meta={
                        "journal_id": next_issue["journal_id"],
                        "journal_data": next_issue["journal_data"],
                        "start_time": time.time(),
                        "request_type": "parse_article_list",
                        "article_url": next_issue["url"],
                        "is_first_page": True,
                        "issue_links": issue_links,
                        "current_issue_index": next_issue_index,
                    }
                )
            else:
                # 所有期号处理完毕，继续下一个期刊
                custom_logger.info(f"期刊 {journal_id} 的所有期文献处理完成")
                yield from self._continue_to_next_journal_from_meta(response.meta)

        elapsed_time = time.time() - process_start_time
        custom_logger.info(f"[时间记录] parse_article_list 执行完成，结束时间: {time.time()}，耗时: {elapsed_time:.2f}秒")

    def _continue_to_next_journal_from_meta(self, meta):
        """
        从meta信息中获取并继续处理下一个期刊
        """
        journals = meta.get("journals", [])
        journal_index = meta.get("journal_index", 0)
        category_info = meta.get("category_info")
        subcategory_name = meta.get("subcategory_name")
        total_pages = meta.get("total_pages")
        current_page = meta.get("current_page")
        remaining_sub_categories = meta.get("remaining_sub_categories")
        remaining_categories = meta.get("remaining_categories")
        major_category_field = meta.get("major_category_field")
        major_category_name = meta.get("major_category_name")

        yield from self._continue_to_next_journal(
            journals, journal_index + 1, category_info, subcategory_name,
            total_pages, current_page, remaining_sub_categories,
            remaining_categories, major_category_field, major_category_name
        )

    def _continue_to_next_journal(self, journals, journal_index, category_info, subcategory_name,
                                  total_pages, current_page, remaining_sub_categories,
                                  remaining_categories, major_category_field, major_category_name):
        """
        继续处理下一个期刊
        """
        # 更新进度信息
        self.current_progress["journal_index"] = journal_index
        self._save_progress()

        if journal_index < len(journals):
            # 处理下一个期刊
            journal = journals[journal_index]
            journal_id = journal.get("Id")
            journal_title = journal.get("Title", [""])[0] if journal.get("Title") else ""

            # 构造期刊详情页链接
            journal_url = f"https://sns.wanfangdata.com.cn/perio/{journal_id}"

            yield scrapy.Request(
                url=journal_url,
                callback=self.parse_journal_detail,
                meta={
                    "journal_id": journal_id,
                    "journal_title": journal_title,
                    "category_info": category_info,
                    "start_time": time.time(),
                    "request_type": "parse_journal_detail",
                    # 传递继续处理所需的信息
                    "journals": journals,
                    "subcategory_name": subcategory_name,
                    "total_pages": total_pages,
                    "current_page": current_page,
                    "remaining_sub_categories": remaining_sub_categories,
                    "remaining_categories": remaining_categories,
                    "major_category_field": major_category_field,
                    "major_category_name": major_category_name,
                    "journal_index": journal_index,
                },
            )
        else:
            # 当前页面的所有期刊处理完毕，继续处理下一页或下一个分类
            # 构造一个假的响应来调用parse_journal_list继续处理
            fake_request = Request(
                url="",
                meta={
                    "category_info": category_info,
                    "subcategory_name": subcategory_name,
                    "total_pages": total_pages,
                    "current_page": current_page,
                    "remaining_sub_categories": remaining_sub_categories,
                    "remaining_categories": remaining_categories,
                    "major_category_field": major_category_field,
                    "major_category_name": major_category_name,
                    "journal_index": journal_index,  # 这个索引会触发下一页处理
                }
            )
            fake_response = Response(
                url="",
                request=fake_request
            )

            # 手动调用parse_journal_list处理下一页
            for req in self.parse_journal_list(fake_response):
                yield req

    # def _process_next_journal(self):
    #     """
    #     处理下一个期刊
    #     """
    #     if self.journal_queue:
    #         journal_info = self.journal_queue.popleft()
    #         yield scrapy.Request(
    #             url=journal_info["url"],
    #             callback=self.parse_journal_detail,
    #             meta={
    #                 "journal_id": journal_info["journal_id"],
    #                 "journal_title": journal_info["journal_title"],
    #                 "category_info": journal_info["category_info"],
    #                 "start_time": time.time(),
    #                 "request_type": "parse_journal_detail"
    #             },
    #         )
    #     else:
    #         custom_logger.info("所有期刊处理完成")

    async def parse_article_detail(self, response: Response):
        """
        解析文献详情页（使用Playwright）
        """
        start_time = response.meta.get("start_time")
        request_type = response.meta.get("request_type")
        if start_time:
            elapsed_time = time.time() - start_time
            custom_logger.info(f"[时间记录] {request_type} 请求完成，耗时: {elapsed_time:.2f}秒")

        process_start_time = time.time()
        custom_logger.info(f"[时间记录] 开始执行 parse_article_detail，开始时间：{process_start_time}")

        journal_id = response.meta["journal_id"]
        journal_data = response.meta["journal_data"]
        article_type = response.meta["article_type"]
        article_title = response.meta["article_title"]

        # 从页面URL中提取platform_id
        platform_id = ""
        page_url = response.url
        if page_url:
            # 从URL中提取最后的部分作为platform_id
            # 例如：https://d.wanfangdata.com.cn/periodical/fxhx202501001
            # 提取fxhx202501001
            url_parts = page_url.split('/')
            if url_parts:
                platform_id = url_parts[-1]

        # 检查是否已处理过该文献
        if platform_id and platform_id in self.processed_articles:
            custom_logger.info(f"文献 {platform_id} 已处理过，跳过")
            # 关闭页面
            if "playwright_page" in response.meta:
                page: Page = response.meta["playwright_page"]
                try:
                    await page.close()
                except Exception as e:
                    custom_logger.warning(f"Error closing page for {response.url}: {str(e)}")
            return

        # 检查playwright_page是否存在
        if "playwright_page" not in response.meta:
            custom_logger.error(f"Playwright page not found in response meta for {response.url}")
            return

        page: Page = response.meta["playwright_page"]

        try:
            # 等待页面加载完成
            await page.wait_for_load_state("networkidle",timeout=30000)

            # 提取DOI
            doi = ""
            doi_element = page.locator('.doiStyle a')
            if await doi_element.count() > 0:
                doi = await doi_element.inner_text()

            # 提取作者信息
            authors = []
            author_elements = await page.locator('.author .test-detail-author').all()
            author_index = 1

            for author_element in author_elements:
                author_name = ""
                name_element = author_element.locator('span.ivu-badge div.author-margin + *')
                if await name_element.count() > 0:
                    author_name = await name_element.inner_text()

                if not author_name:
                    continue

                # 检查是否为第一作者
                is_co_first_author = CO_FIRST_AUTHOR["not_first"]
                first_author_icon = author_element.locator('img[title="第一作者"]')
                if await first_author_icon.count() > 0:
                    is_co_first_author = CO_FIRST_AUTHOR["first"]

                # 检查是否为通讯作者
                is_corresponding_author = CORRESPONDING_AUTHOR["not_corp"]
                corresponding_author_icon = author_element.locator('img[title="通讯作者"]')
                if await corresponding_author_icon.count() > 0:
                    is_corresponding_author = CORRESPONDING_AUTHOR["corp"]

                # 获取作者编号
                author_badge = author_element.locator('sup.ivu-badge-count')
                author_number = ""
                if await author_badge.count() > 0:
                    author_number = await author_badge.inner_text()

                authors.append({
                    "author_name": author_name.strip(),
                    "co_first_author": is_co_first_author,
                    "corresponding_author": is_corresponding_author,
                    "is_display": AUTHOR_IS_DISPLAY["display"],
                    "author_email": [],  # 页面未提供作者邮箱
                    "author_type": AUTHOR_TYPE["person"],
                    "author_number": author_number,
                    "unit_info": []  # 稍后填充单位信息
                })

            # 提取作者单位信息
            units = {}
            unit_elements = await page.locator('.itemUrl span.multi-sep').all()
            for unit_element in unit_elements:
                unit_text = await unit_element.inner_text()
                # 提取编号和单位名称
                match = re.match(r'^(\d+)\.(.*)', unit_text.strip())
                if match:
                    unit_number = match.group(1)
                    unit_name = match.group(2).strip()
                    units[unit_number] = unit_name

            # 将单位信息关联到作者
            for author in authors:
                author_number = author.get("author_number", "")
                if author_number in units:
                    author["unit_info"].append({
                        "unit_name": units[author_number]
                    })

            # 提取摘要
            abstract_text = ""
            abstract_element = page.locator('.summary.list .text-overflow')
            if await abstract_element.count() > 0:
                # 检查是否有展开按钮
                expand_button = abstract_element.locator('.abstractIcon.btn')
                if await expand_button.count() > 0:
                    # 点击展开按钮
                    try:
                        await expand_button.click(timeout=5000)
                        await page.wait_for_timeout(1000)  # 等待内容展开
                    except Exception as e:
                        custom_logger.warning(f"点击摘要展开按钮失败: {e}")

                # 重新获取摘要文本
                abstract_content = abstract_element.locator('span:not(.slot-box)')
                if await abstract_content.count() > 0:
                    abstract_texts = []
                    count = await abstract_content.count()
                    for i in range(count):
                        text = await abstract_content.nth(i).inner_text()
                        abstract_texts.append(text)
                    abstract_text = ''.join(abstract_texts)

            # 提取关键词
            keywords = []
            keyword_elements = await page.locator('.keyword.list .itemKeyword a span').all()
            for keyword_element in keyword_elements:
                keyword = await keyword_element.inner_text()
                keywords.append(keyword.strip())

            # 提取机标分类号
            clc_codes = []
            clc_elements = await page.locator('.classify.list .itemUrl span.multi-sep span').all()
            for clc_element in clc_elements:
                clc_text = await clc_element.inner_text()
                # 只保留括号外的部分
                clc_code = re.sub(r'\(.*?\)', '', clc_text).strip()
                if clc_code:
                    clc_codes.append(clc_code)

            # 提取论文发表日期
            publish_date = ""
            publish_element = page.locator('.publish.list .itemUrl')
            publish_texts = await publish_element.all_inner_texts()
            for text in publish_texts:
                if text.strip() and not "万方平台首次上网日期" in text:
                    publish_date = text.strip()
                    break

            # 如果没有发表日期，尝试获取在线出版日期
            if not publish_date:
                online_element = page.locator('.publish.list .itemUrl span:has-text("万方平台首次上网日期")')
                if await online_element.count() > 0:
                    parent_element = online_element.locator('xpath=..')
                    full_text = await parent_element.inner_text()
                    publish_date = full_text.replace("（万方平台首次上网日期，不代表论文的发表时间）", "").strip()

            # 提取资助基金
            grants = []
            fund_elements = await page.locator('.itemKeyword span.multi-sep').all()
            for idx, fund_element in enumerate(fund_elements, 1):
                # 提取基金名称
                fund_name_elements = await fund_element.locator('a').all()
                fund_name = ""
                if len(fund_name_elements) > 0:
                    fund_names = []
                    for elem in fund_name_elements:
                        name = await elem.inner_text()
                        name = re.sub(r'\s+', ' ', name).strip()
                        if name:
                            fund_names.append(name)
                    fund_name = ' '.join(fund_names)

                # 提取基金编号（可能有多个）
                fund_numbers = []
                fund_number_elements = await fund_element.locator('span.linkKehu span').all()
                for fund_number_element in fund_number_elements:
                    fund_number = await fund_number_element.inner_text()
                    fund_number = fund_number.strip()
                    if fund_number:
                        fund_numbers.append(fund_number)

                # 组合基金信息
                if fund_name and fund_numbers:
                    # 有基金名称和多个基金编号
                    fund_info = f"{fund_name} ( {', '.join(fund_numbers)} )"
                    grants.append({
                        'grant_name': fund_info,
                        'grant_order': str(idx)  # 添加序号
                    })
                elif fund_name:
                    # 只有基金名称
                    grants.append({
                        'grant_name': fund_name,
                        'grant_order': str(idx)  # 添加序号
                    })
                elif fund_numbers:
                    # 只有基金编号（可能多个）
                    fund_info = ', '.join(fund_numbers)
                    grants.append({
                        'grant_name': fund_info,
                        'grant_order': str(idx)  # 添加序号
                    })

            # 提取页码
            page_numbers = ""
            page_element = page.locator('.pages.list .itemUrl .canReadOnline')
            if await page_element.count() > 0:
                page_text = await page_element.inner_text()
                # 提取括号中的内容
                match = re.search(r'\((.*?)\)', page_text)
                if match:
                    page_numbers = match.group(1).strip()

            # 点击"英文信息"按钮展开英文内容
            english_button = page.locator('.moreFlex')
            if await english_button.count() > 0:
                try:
                    await english_button.click(timeout=5000)
                    await page.wait_for_timeout(1000)  # 等待内容展开
                except Exception as e:
                    custom_logger.warning(f"点击英文信息按钮失败: {e}")

            # 提取英文标题
            en_title = ""
            en_title_element = page.locator('.summary .detailTitleEN')
            if await en_title_element.count() > 0:
                en_title = await en_title_element.inner_text()

            # 提取英文摘要
            en_abstract = ""
            en_abstract_element = page.locator('.summary:has(.item:has-text("Abstract：")) .text-overflow')
            if await en_abstract_element.count() > 0:
                # 检查是否有展开按钮
                en_expand_button = en_abstract_element.locator('.abstractIcon.btn')
                if await en_expand_button.count() > 0:
                    # 点击展开按钮
                    await en_expand_button.click()
                    await page.wait_for_timeout(1000)  # 等待内容展开

                # 重新获取摘要文本
                en_abstract_content = en_abstract_element.locator('span:not(.slot-box)')
                if await en_abstract_content.count() > 0:
                    en_abstract_texts = []
                    count = await en_abstract_content.count()
                    for i in range(count):
                        text = await en_abstract_content.nth(i).inner_text()
                        en_abstract_texts.append(text)
                    en_abstract = ''.join(en_abstract_texts)

            # 提取英文关键词
            en_keywords = []
            en_keyword_elements = await page.locator('.keywordEN.list .itemKeyword a span').all()
            for en_keyword_element in en_keyword_elements:
                en_keyword = await en_keyword_element.inner_text()
                en_keywords.append(en_keyword.strip())

            # 提取参考文献
            references = []
            reference_elements = await page.locator('tr[data-v-1c6d046b] td[style*="word-break"]').all()
            for reference_element in reference_elements:
                reference_text = await reference_element.inner_text()
                # 清理参考文献文本
                reference_text = re.sub(r'\s+', ' ', reference_text).strip()
                # 移除多余的符号
                reference_text = re.sub(r'\.\s*\.', '.', reference_text)
                reference_text = re.sub(r'\s*\.\s*$', '.', reference_text)
                if reference_text:
                    references.append(reference_text)

            # 提取年,卷(期)
            publish_info = ""
            publish_info_element = page.locator('.publishData.MCD a')
            if await publish_info_element.count() > 0:
                # 获取a标签内所有span的文本并拼接
                span_elements = await publish_info_element.locator('span').all()
                span_texts = []
                for span_element in span_elements:
                    span_text = await span_element.inner_text()
                    span_texts.append(span_text.strip())
                publish_info = ''.join(span_texts)

            # 提取期刊名和ISSN
            periodical_name = ""
            periodical_name_element = page.locator('.periodicalName a')
            if await periodical_name_element.count() > 0:
                periodical_name = await periodical_name_element.inner_text()
                periodical_name = periodical_name.strip()

            issn = ""
            issn_element = page.locator('.periodicalDataItem.M10')
            if await issn_element.count() > 0:
                issn_text = await issn_element.inner_text()
                match = re.search(r'ISSN：(\d{4}-\d{4})', issn_text)
                if match:
                    issn = match.group(1)

            # 构造文章Item
            # 处理中英文标题
            title_data = en_cn_correction(
                text_list=[article_title, en_title],
                chs_field_name="article_cn_name",
                eng_field_name="article_en_name"
            )

            # 处理中英文摘要
            abstract_data = {
                "chs_info": [],
                "eng_info": []
            }

            if abstract_text or en_abstract:
                abstract_result = en_cn_correction(
                    text_list=[abstract_text, en_abstract],
                    chs_field_name="abstract_chs",
                    eng_field_name="abstract_eng"
                )

                # 根据结果构建abstract_data
                if abstract_result.get("abstract_chs"):
                    abstract_data["chs_info"].append({
                        "section_attr": ARTICLE_ABSTRACT_SECTION_ATTR["abstract"],
                        "section_text": abstract_result["abstract_chs"]
                    })

                if abstract_result.get("abstract_eng"):
                    abstract_data["eng_info"].append({
                        "section_attr": ARTICLE_ABSTRACT_SECTION_ATTR["abstract"],
                        "section_text": abstract_result["abstract_eng"]
                    })

            # 处理关键词
            keyword_data = []
            # 将中英文关键词列表合并传入
            combined_keywords = keywords + en_keywords
            for keyword in combined_keywords:
                keyword_result = en_cn_correction(
                    text_list=[keyword],
                    chs_field_name="keyword_chs",
                    eng_field_name="keyword_eng"
                )
                keyword_data.append(keyword_result)

            # 处理基金信息
            grant_data = []
            for i, grant in enumerate(grants, 1):
                grant_data.append({
                    "grant_name": grant["grant_name"],
                    "grant_order": grant["grant_order"]
                })

            # 确定发表时间精度
            published_time_precision = ARTICLE_PUBLISHED_TIME_PRECISION["D"]  # 默认为日
            if publish_date:
                date_parts = re.findall(r'\d+', publish_date)
                if len(date_parts) == 1:
                    published_time_precision = ARTICLE_PUBLISHED_TIME_PRECISION["Y"]
                elif len(date_parts) == 2:
                    published_time_precision = ARTICLE_PUBLISHED_TIME_PRECISION["M"]
                elif len(date_parts) >= 3:
                    published_time_precision = ARTICLE_PUBLISHED_TIME_PRECISION["D"]

            # 从publish_info中提取卷和期
            volume = ""
            issue = ""
            year = ""
            volume_issue_info = self.extract_volume_issue(publish_info)
            if volume_issue_info:
                volume = volume_issue_info.get("volume", "")
                issue = volume_issue_info.get("issue", "")
                year = volume_issue_info.get("year", "")

            # 构造文章Item
            article_item = CnArticleItem(
                article_en_name=title_data.get("article_en_name", ""),
                article_cn_name=title_data.get("article_cn_name", ""),
                article_doi=doi,
                type_name={"chi": article_type} if article_type else {},
                journal_info={
                    "journal_issn": issn,
                    "journal_name": periodical_name
                },
                article_year=year,
                article_language=title_data.get("article_cn_name", ""),  # 用文章标题判断语言
                published_time=publish_date,
                published_time_precision=published_time_precision,
                volume=volume,
                issue=issue,
                page=page_numbers,
                clc_codes=clc_codes,
                platform_source=self.platform_code,
                platform_id=platform_id,
                article_abstract=abstract_data,
                article_reference=references,
                article_keywords=keyword_data,
                article_grant=grant_data,
                article_author=authors,
                original_html=response.text,
                page_url=response.url,
            )

            yield article_item

            # 记录已处理的文献ID
            if platform_id:
                self._save_processed_article_id(platform_id)
                custom_logger.info(f"文献 {platform_id} 已入库并记录")
        except Exception as e:
            custom_logger.error(f"Error parsing article detail for {response.url}: {str(e)}")
        finally:
            # 确保页面被关闭
            try:
                if not page.is_closed():
                    await page.close()
                    page_closed = True
                    custom_logger.info(f"成功关闭页面: {response.url}")
            except Exception as e:
                custom_logger.warning(f"Error closing page for {response.url}: {str(e)}")


            elapsed_time = time.time() - process_start_time
            custom_logger.info(f"[时间记录] parse_article_detail 执行完成，耗时: {elapsed_time:.2f}秒")

    def handle_request_error(self, failure):
        """
        处理请求错误
        :param failure:错误对象
        :return:
        """
        custom_logger.error(f"请求失败: {failure.request.url}")
        custom_logger.error(f"错误类型: {failure.type}")
        custom_logger.error(f"错误详情: {repr(failure.value)}")

        # 获取当前重试次数
        request = failure.request
        if "retry_times" not in request.meta:
            retry_times = 0
        else:
            retry_times = request.meta["retry_times"]

        # 限制重试次数为3次
        if retry_times < 3:
            custom_logger.info(f"第{retry_times + 1}次重试请求: {request.url}")
            # 增加重试次数
            request.meta["retry_times"] = retry_times + 1
            return request
        else:
            custom_logger.error(f"已达到最大重试次数(3次)，放弃请求: {request.url}")

    def extract_volume_issue(self, text):
        """
        从年,卷(期)信息中提取卷和期
        :param text: 格式如 2025,53(1)
        :return: dict 包含volume和issue
        """
        # 使用正则表达式匹配年,卷(期)格式
        pattern = r'(\d+),(\d+)\((\d+)\)'
        match = re.search(pattern, text)
        if match:
            year = match.group(1)
            volume = match.group(2)
            issue = match.group(3)
            return {
                "year": year,
                "volume": volume,
                "issue": issue
            }
        return None

    async def init_page(self, page, request):
        """
        初始化页面
        """
        await page.set_extra_http_headers({
            'Referer': 'https://c.wanfangdata.com.cn/',
            'Origin': 'https://c.wanfangdata.com.cn'
        })
