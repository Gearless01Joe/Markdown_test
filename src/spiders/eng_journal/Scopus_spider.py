# -*- coding: utf-8 -*-
"""
# @Time    : 2025/8/22 17:48
# @User  : LGZ
# @Description  : Scopus期刊数据爬虫（结合Scrapy和Playwright）
"""
import time
import random
import json
import os
import re
import math
import scrapy
import html
from bs4 import BeautifulSoup
from src.constant import TEMP_PATH
from src.items.other.eng_journal_item import EngJournalItem, JOURNAL_OPEN_ACCESS
from src.spiders.base_spider import BaseSpider
from src.utils.base_logger import BaseLog


class ScopusSpider(BaseSpider):
    name = 'scopus'
    allowed_domains = ['www.scopus.com']
    base_url = 'https://www.scopus.com/'
    custom_settings = {
        'ITEM_PIPELINES': {
            'src.pipelines.data_cleaning_pipeline.DataCleaningPipeline': 300,  # 数据清洗管道
            'src.pipelines.storage.eng_journal_pipeline.EngJournalPipeline': 500,  # 数据入库管道
        },
        "DOWNLOADER_MIDDLEWARES": {
            'src.middlewares.proxy_middleware.BaseProxyMiddleware': 400,  # 代理请求中间件
            'src.middlewares.custom_retry_middleware.CustomRetryMiddleware': 500, # 使用自定义重试中间件
        },
        # 控制并发请求数量
        'CONCURRENT_REQUESTS': 4,  # 增加并发以提高效率
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,  # 每域名并发
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': 1,
        'RETRY_TIMES': 3,  # 请求重试次数
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 522, 524, 408, 429, 403,404],  # 重试的HTTP状态码
        'CLOSESPIDER_PAGECOUNT': 0,  # 禁用页面计数关闭
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
        },

        "PLAYWRIGHT_CONTEXTS": {
            "default": {
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0"
            }
        },
        # 增加每个上下文的并发页面数
        "PLAYWRIGHT_MAX_PAGES_PER_CONTEXT": 8,
        # 设置Playwright超时
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 120000,
    }
    TEMP_DIR = os.path.join(TEMP_PATH, 'Scopus')
    # 年份范围控制常量
    YEARS_TO_FETCH = 5  # 获取最近5年的数据

    def __init__(self, **kwargs):
        """
        初始化Scopus爬虫实例
        :author LGZ
        :param kwargs: 其他参数
        """
        super().__init__(**kwargs)
        self.base_logger = BaseLog()
        # 本地记录文件路径
        os.makedirs(self.TEMP_DIR, exist_ok=True)  # 确保目录存在
        self.processed_journals_file = os.path.join(self.TEMP_DIR, 'processed_journals.txt')
        self.source_ids_file = os.path.join(self.TEMP_DIR, 'source_ids.txt')
        self.progress_file = os.path.join(self.TEMP_DIR, 'progress.json')  # 进度记录文件
        # 已处理的期刊集合
        self.processed_journals = set()
        # 存储sourceIds用于分页请求
        self.source_ids = []
        # 总数据量和总页数
        self.total_count = 0
        self.total_pages = 0
        self.results_per_page = 20
        # 用于存储cookies
        self.session_cookies = {}
        # 用于跟踪已处理的页面
        self.processed_pages = set()
        # 加载已处理的期刊ID
        self._load_processed_journals()
        # 加载进度信息
        self._load_progress()
        # 加载source_ids（如果存在）
        self._load_source_ids()
        # 添加计数器和队列
        # self.current_page = 1  # 当前处理的列表页
        self.pending_detail_requests = 0  # 当前页待处理的详情请求数量
        self.next_page_data = None  # 存储下一页的请求参数

    def start_requests(self):
        """
        开始请求第一页数据
        :author LGZ
        :return: scrapy请求对象
        """
        self.base_logger.info("开始请求第一页数据")
        # 如果有断点记录，则从断点处恢复
        if self.current_page > 1:
            self.base_logger.info(f"检测到断点，从第 {self.current_page} 页恢复爬取")
            offset = (self.current_page - 1) * self.results_per_page
            # 确保source_ids已加载
            if not self.source_ids:
                self._load_source_ids()
            for request in self._request_page_with_post(offset, self.current_page, self.current_page):
                yield request
            return

        # 先访问列表页获取cookie
        list_url = "https://www.scopus.com/sources.uri"
        list_params = {'zone': 'TopNavBar', 'origin': ''}
        list_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-CN,zh;q=0.9',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
            'referer': 'https://www.scopus.com/'
        }

        # 使用Playwright中间件发送请求，设置高优先级
        yield scrapy.Request(
            url=list_url,
            callback=self.parse_first_page,
            headers=list_headers,
            meta={
                'playwright': True,
                'playwright_include_page': True,
                'download_timeout': 120,  # 增加超时时间
                'priority': 100  # 高优先级
            },
            dont_filter=True
        )

    async def parse_first_page(self, response):
        """
        解析第一页数据并发起后续请求
        :author LGZ
        :param response: 响应对象
        :return: scrapy请求对象
        """
        self.base_logger.info("解析第一页数据")
        try:
            # 获取页面对象
            page = response.meta["playwright_page"]

            # 保存cookies用于后续请求
            cookies = await page.context.cookies()
            for cookie in cookies:
                self.session_cookies[cookie["name"]] = cookie["value"]
            self.base_logger.info(f"已保存会话cookies: {len(self.session_cookies)} 个")
            # 关闭页面释放资源
            await page.close()

            # 解析响应内容
            soup = BeautifulSoup(response.text, 'html.parser')
            # 从HTML中提取JSON数据
            results_json_element = soup.find('pre', {'id': 'resultsJson'})
            if not results_json_element:
                self.base_logger.warning("未找到resultsJson元素")
                return

            # 解码HTML实体
            results_json_text = html.unescape(results_json_element.get_text())
            results_data = json.loads(results_json_text)
            self.total_count = results_data.get('totalResultsCount', 0)
            self.total_pages = math.ceil(self.total_count / self.results_per_page)
            self.base_logger.info(f"总共找到 {self.total_count} 条数据，共 {self.total_pages} 页")

            # 提取第一页的期刊ID
            first_page_ids = []
            results = results_data.get('results', [])
            for result in results:
                journal_id = result.get('id')
                if journal_id:
                    first_page_ids.append(str(journal_id))

            self.base_logger.info(f"第一页包含 {len(first_page_ids)} 个期刊")

            # 保存sourceIds用于后续分页请求
            self.source_ids = first_page_ids
            self._save_source_ids(first_page_ids)
            self.processed_pages.add(1)  # 标记第一页已处理

            # 设置待处理的详情请求计数
            unprocessed_count = 0
            for journal_id in first_page_ids:
                if journal_id not in self.processed_journals:
                    unprocessed_count += 1

            self.pending_detail_requests = unprocessed_count
            self.base_logger.info(f"第一页有 {unprocessed_count} 个期刊需要处理")

            # 如果没有需要处理的详情请求，直接请求下一页
            if self.pending_detail_requests == 0:
                self.base_logger.info("第一页所有期刊已处理过，直接请求下一页")
                if self.total_pages > 1:
                    self.current_page = 2
                    offset = (2 - 1) * self.results_per_page
                    for request in self._request_page_with_post(offset, 2, 2):
                        yield request
                return

            # 请求第一页的期刊详情
            for journal_id in first_page_ids:
                if journal_id in self.processed_journals:
                    self.base_logger.debug(f"期刊 {journal_id} 已处理过，跳过")
                    continue

                for request in self._request_journal_details(journal_id, 1):
                    yield request

            # 预先准备下一页的请求参数，但不立即发送
            if self.total_pages > 1:
                self.next_page_data = {
                    'page': 2,
                    'offset': self.results_per_page
                }
        except Exception as e:
            self.base_logger.error(f"解析第一页数据失败: {e}")

    def _request_page_with_post(self, offset, page, page_number):
        """
        使用POST请求获取页面数据
        :author LGZ
        :param offset: 偏移量
        :param page: 页码
        :param page_number: 页面编号，用于跟踪处理顺序
        :return: scrapy请求对象
        """
        self.base_logger.info(f"生成第 {page_number} 页的请求，优先级: {3000 - page_number}")

        url = "https://www.scopus.com/sources.uri"
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-CN,zh;q=0.9',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
            'referer': 'https://www.scopus.com/sources.uri',
            'content-type': 'application/x-www-form-urlencoded'
        }
        # 构造POST数据
        form_data = {
            'sortField': 'citescore',
            'sortDirection': 'desc',
            'sourceSelectionType': 'all',
            'sourceIds': ','.join(self.source_ids),  # 使用之前保存的sourceIds
            'typeFilter': '',
            'listId': '',
            'resultsListTypeValue': 'Sources',
            'sourcePageDataSource': 'All',
            'clearAllFlag': 'false',
            'field': 'subject',
            'subject': '',
            '_openAccess': 'on',
            'countField': '',
            '_bestPercentile': 'on',
            '_quartile': 'on',
            '_type': 'on',
            '_selectAllCheckBox': 'on',
            '_selectPageCheckBox': 'on',
            'year': '2024',
            'offset': str(offset),
            'resultsPerPage': str(self.results_per_page)
        }

        # 使用Playwright发送POST请求，继续使用之前的会话，设置中等优先级
        yield scrapy.FormRequest(
            url=url,
            formdata=form_data,
            headers=headers,
            callback=self.parse_list_page,
            meta={
                'playwright': True,
                'playwright_include_page': True,
                'page_number': page_number,
                'download_timeout': 120,
                'cookies': self.session_cookies,  # 传递会话cookies
                'priority': 1000 - page_number  # 页码越小，优先级越高
            },
            priority=1000 - page_number,  # 在请求级别也设置优先级
            dont_filter=True
        )

    async def parse_list_page(self, response):
        """
        处理列表页响应内容
        :author LGZ
        :param response: 响应对象
        :return: scrapy请求对象
        """
        page = response.meta.get('page_number', 0)
        self.base_logger.info(f"解析第 {page} 页数据")

        # 检查页面是否已经处理过
        if page in self.processed_pages:
            self.base_logger.debug(f"第 {page} 页已处理过，跳过")
            return

        self.processed_pages.add(page)

        try:
            # 获取页面对象
            playwright_page = response.meta["playwright_page"]

            # 更新cookies用于后续请求
            cookies = await playwright_page.context.cookies()
            for cookie in cookies:
                self.session_cookies[cookie["name"]] = cookie["value"]

            # 关闭页面释放资源
            await playwright_page.close()

            soup = BeautifulSoup(response.text, 'html.parser')
            # 提取resultsJson中的数据
            results_json_element = soup.find('pre', {'id': 'resultsJson'})
            if not results_json_element:
                self.base_logger.warning(f"第 {page} 页未找到resultsJson元素")
                return
            # 解码HTML实体
            results_json_text = html.unescape(results_json_element.get_text())
            results_data = json.loads(results_json_text)
            results = results_data.get('results', [])
            # 提取期刊ID
            page_ids = []
            for result in results:
                journal_id = result.get('id')
                if journal_id:
                    page_ids.append(str(journal_id))
            self.base_logger.info(f"第 {page} 页包含 {len(page_ids)} 个期刊")
            # 保存sourceIds用于后续请求
            self.source_ids = page_ids
            self._save_source_ids(page_ids)

            # 设置待处理的详情请求计数
            unprocessed_count = 0
            for journal_id in page_ids:
                if journal_id not in self.processed_journals:
                    unprocessed_count += 1

            self.pending_detail_requests = unprocessed_count
            self.base_logger.info(f"第 {page} 页有 {unprocessed_count} 个期刊需要处理")

            # 如果没有需要处理的详情请求，直接请求下一页
            if self.pending_detail_requests == 0:
                self.base_logger.info(f"第 {page} 页所有期刊已处理过，直接请求下一页")
                if page < self.total_pages:
                    next_page = page + 1
                    self.current_page = next_page
                    offset = (next_page - 1) * self.results_per_page
                    for request in self._request_page_with_post(offset, next_page, next_page):
                        yield request
                return

            # 请求期刊详情
            for journal_id in page_ids:
                if journal_id in self.processed_journals:
                    self.base_logger.debug(f"期刊 {journal_id} 已处理过，跳过")
                    continue

                for request in self._request_journal_details(journal_id, page):
                    yield request

            # 预先准备下一页的请求参数，但不立即发送
            if page < self.total_pages:
                next_page = page + 1
                self.next_page_data = {
                    'page': next_page,
                    'offset': (next_page - 1) * self.results_per_page
                }
        except Exception as e:
            self.base_logger.error(f"解析第 {page} 页数据失败: {e}")
            # 发生错误时，尝试继续请求下一页
            if page < self.total_pages:
                next_page = page + 1
                self.current_page = next_page
                offset = (next_page - 1) * self.results_per_page
                for request in self._request_page_with_post(offset, next_page, next_page):
                    yield request

    def _request_journal_details(self, journal_id,page_number):
        """
        请求期刊详情数据
        :author LGZ
        :param journal_id: 期刊ID
        :return: scrapy请求对象列表
        """
        time.sleep(random.uniform(0.5, 1.5))
        # 请求基本详情数据
        basic_info_url = f"https://www.scopus.com/api/rest/sources/{journal_id}"
        basic_headers = {
            'accept': 'application/json, text/plain, */*',
            'referer': f'https://www.scopus.com/source/sourceInfo.url?sourceId={journal_id}',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0'
        }

        # 使用Playwright请求基本详情数据，传递页码信息
        yield scrapy.Request(
            url=basic_info_url,
            headers=basic_headers,
            callback=self.parse_basic_info,
            cookies=self.session_cookies,
            meta={
                'playwright': True,
                'journal_id': journal_id,
                'download_timeout': 60,
                'playwright_context': 'default',
                'priority': -100,
                'page_number': page_number  # 添加页码信息
            },
            dont_filter=True
        )

    def parse_basic_info(self, response):
        """
        解析期刊基本信息并请求CiteScore数据
        :author LGZ
        :param response: 响应对象
        :return: scrapy请求对象
        """
        journal_id = response.meta['journal_id']
        page_number = response.meta['page_number']  # 获取页码信息
        try:
            # 检查响应内容是否为JSON
            basic_response_text = response.text
            self.base_logger.debug(f"基本详情响应状态: {response.status}")

            # 清洗数据，只去除JSON数据外的HTML代码
            # 使用正则表达式精确提取HTML中的JSON数据
            # 匹配以{开头，以}结尾的JSON数据，忽略前后的HTML标签
            json_match = re.search(r'({.*})', basic_response_text, re.DOTALL)
            if json_match:
                basic_response_text = json_match.group(1)

            # 尝试解析JSON
            try:
                basic_data = json.loads(basic_response_text)
                # 清理数据，移除request和response字段
                basic_data.pop('request', None)
                basic_data.pop('response', None)
            except json.JSONDecodeError as e:
                self.base_logger.error(f"解析基本详情JSON失败，响应内容: {basic_response_text[:500]}")
                return

            # 请求CiteScore数据，使用相同的会话cookies
            citescore_info_url = f"https://www.scopus.com/source/citescore/{journal_id}.uri"
            citescore_headers = {
                'accept': '*/*',
                'referer': f'https://www.scopus.com/sourceid/{journal_id}',
                'x-requested-with': 'XMLHttpRequest',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0'
            }

            # 请求CiteScore数据时传递页码
            yield scrapy.Request(
                url=citescore_info_url,
                headers=citescore_headers,
                callback=self.parse_citescore_info,
                cookies=self.session_cookies,
                meta={
                    'playwright': True,
                    'journal_id': journal_id,
                    'basic_data': basic_data,
                    'download_timeout': 60,
                    'playwright_context': 'default',
                    'priority': -100,
                    'page_number': page_number  # 传递页码信息
                },
                dont_filter=True
            )
        except Exception as e:
            self.base_logger.error(f"处理期刊 {journal_id} 基本详情数据失败: {e}")
            # 即使失败也要减少计数
            self.pending_detail_requests -= 1
            self._check_and_request_next_page(page_number)
    def parse_citescore_info(self, response):
        """
        解析期刊CiteScore数据并生成Item
        :author LGZ
        :param response: 响应对象
        :return: EngJournalItem对象
        """
        journal_id = response.meta['journal_id']
        basic_data = response.meta['basic_data']
        page_number = response.meta['page_number']  # 获取页码信息

        try:
            # 检查响应内容是否为JSON
            citescore_response_text = response.text
            self.base_logger.debug(f"CiteScore响应状态: {response.status}")

            # 清洗数据，只去除JSON数据外的HTML代码
            # 使用正则表达式精确提取HTML中的JSON数据
            # 匹配以{开头，以}结尾的JSON数据，忽略前后的HTML标签
            json_match = re.search(r'({.*})', citescore_response_text, re.DOTALL)
            if json_match:
                citescore_response_text = json_match.group(1)

            # 尝试解析JSON
            try:
                citescore_data = json.loads(citescore_response_text)
                # 清理数据，移除request和response字段
                citescore_data.pop('request', None)
                citescore_data.pop('response', None)
            except json.JSONDecodeError as e:
                self.base_logger.error(f"解析CiteScore JSON失败，响应内容: {citescore_response_text[:500]}")
                return

            # 解析并生成Item
            item = self.parse_journal_details(
                journal_id,
                basic_data,
                citescore_data
            )
            if item:
                yield item
                # 记录已处理的期刊
                self._save_processed_journal(journal_id)
            # 减少待处理请求计数
            self.pending_detail_requests -= 1
            self.base_logger.debug(f"页面 {page_number} 还剩 {self.pending_detail_requests} 个期刊待处理")

            # 检查是否需要请求下一页
            self._check_and_request_next_page(page_number)

        except Exception as e:
            self.base_logger.error(f"处理期刊 {journal_id} CiteScore数据失败: {e}")
            # 即使失败也要减少计数
            self.pending_detail_requests -= 1
            self._check_and_request_next_page(page_number)

    def parse_journal_details(self, journal_id, basic_data, citescore_data):
        """
        解析期刊详情数据
        :author LGZ
        :param journal_id: 期刊ID
        :param basic_data: 基本详情数据
        :param citescore_data: CiteScore数据
        :return: EngJournalItem对象
        """
        try:
            item = EngJournalItem()
            # 基本信息
            item['journal_name'] = basic_data.get('sourceTitle', '')
            item['page_url'] = f"https://www.scopus.com/source/sourceInfo.url?sourceId={journal_id}"
            # 开放获取标识 (NO记为0，YES记为1)
            open_access = basic_data.get('openAccessIndicator', 'NO')
            item['openaccess'] = JOURNAL_OPEN_ACCESS["open"] if open_access == 'YES' else JOURNAL_OPEN_ACCESS[
                "not_open"]
            # 学科分类（参考Scimagojr的处理方式）
            subject_areas_data = []
            full_subject_areas = basic_data.get('fullSubjectAreas', {})
            if full_subject_areas:
                # 按照Scimagojr的方式处理学科分类
                # 将学科按父类分组
                subject_groups = {}
                for code, subject in full_subject_areas.items():
                    if ':' in subject:
                        parts = subject.split(': ', 1)
                        parent = parts[0]
                        child = parts[1] if len(parts) > 1 else ''
                    else:
                        parent = subject
                        child = ''
                    if parent not in subject_groups:
                        subject_groups[parent] = {
                            'main_category': parent,
                            'sub_categories': []
                        }
                    if child and child not in subject_groups[parent]['sub_categories']:
                        subject_groups[parent]['sub_categories'].append(child)
                subject_areas_data = list(subject_groups.values())
            item['subject_areas'] = json.dumps(subject_areas_data, ensure_ascii=False)
            # 出版商
            item['publisher'] = basic_data.get('publisher', '')
            # ISSN和EISSN
            item['issn'] = basic_data.get('issn', '')
            item['eissn'] = basic_data.get('eissn', '')
            # 覆盖范围
            coverage_list = basic_data.get('coverageList', [])
            if coverage_list:
                coverage_parts = []
                for coverage in coverage_list:
                    start = coverage.get('coverageStart', '')
                    end = coverage.get('coverageEnd', '')
                    if start and end:
                        if start == end:
                            coverage_parts.append(start)
                        else:
                            coverage_parts.append(f"{start}-{end}")
                item['coverage'] = ','.join(coverage_parts)
            # 处理指标数据
            metrics = basic_data.get('metrics', [])
            sjr_data = []
            snip_data = []
            # 从基本数据中提取SJR和SNIP
            for metric in metrics:
                name = metric.get('name')
                value = metric.get('value')
                year = metric.get('year')

                if name == 'SJR':
                    sjr_data.append({
                        'year': year,
                        'value': value
                    })
                elif name == 'SNIP':  # 新增SNIP字段
                    snip_data.append({
                        'year': year,
                        'value': value
                    })
            # 按年份排序，取最近YEARS_TO_FETCH年
            sjr_data = sorted(sjr_data, key=lambda x: x['year'], reverse=True)[:self.YEARS_TO_FETCH]
            snip_data = sorted(snip_data, key=lambda x: x['year'], reverse=True)[:self.YEARS_TO_FETCH]
            item['sjr'] = json.dumps(sjr_data, ensure_ascii=False)
            item['snip'] = json.dumps(snip_data, ensure_ascii=False)  # 新增SNIP字段
            # 从CiteScore数据中提取详细指标
            last_year = int(citescore_data.get('lastYear', 0))
            year_info = citescore_data.get('yearInfo', {})
            predictor = citescore_data.get('predictor', {})
            # 合并yearInfo和predictor数据
            all_year_data = {**year_info, **predictor}
            # 提取最近YEARS_TO_FETCH年的数据
            citescore_data_list = []
            percentile_data_list = []
            for i in range(self.YEARS_TO_FETCH):
                year = last_year - i
                year_str = str(year)
                if year_str in all_year_data:
                    year_data = all_year_data[year_str]
                    # 提取CiteScore (rp字段)
                    metric_types = year_data.get('metricType', [])
                    for metric in metric_types:
                        if 'rp' in metric:
                            citescore_data_list.append({
                                'year': year,
                                'value': metric['rp']
                            })
                    # 提取排名信息
                    percentiles = year_data.get('percentiles', [])
                    for percentile in percentiles:
                        # 只记录大类信息
                        rank = percentile.get('rank', '')
                        total_source_count = percentile.get('totalSourceCount', '')
                        # 组合rank和totalSourceCount
                        subject_rank = f"{rank}/{total_source_count}" if rank and total_source_count else ""
                        percentile_data_list.append({
                            'year': year,
                            'category': percentile.get('parent', ''),
                            'subcategory': percentile.get('subName', ''),
                            'subject_rank': subject_rank,
                            'subject_percentile': percentile.get('subPercentage', '')
                        })
            # 按年份排序
            citescore_data_list = sorted(citescore_data_list, key=lambda x: x['year'], reverse=True)
            percentile_data_list = sorted(percentile_data_list, key=lambda x: x['year'], reverse=True)
            # 存储CiteScore数据 (对应citescore_quartiles字段)
            item['citescore_quartiles'] = json.dumps(percentile_data_list, ensure_ascii=False)
            # 存储Citescore数据 (新增字段，这里用citescore字段存储)
            item['citescore'] = json.dumps(citescore_data_list, ensure_ascii=False)
            self.base_logger.info(f"成功解析期刊信息: {item['journal_name']} (ID: {journal_id})")
            return item
        except Exception as e:
            self.base_logger.error(f"解析期刊 {journal_id} 详情数据失败: {e}")
            return None

    def _check_and_request_next_page(self, page_number):
        """
        检查当前页是否已处理完毕，如果是则请求下一页
        :author LGZ
        :param page_number: 当前页码
        :return: None
        """
        # 确保我们在处理当前页的回调
        if page_number != self.current_page:
            return

        # 如果还有待处理请求，不进行下一步
        if self.pending_detail_requests > 0:
            return

        # 所有详情请求已完成，请求下一页
        self.base_logger.info(f"页面 {page_number} 的所有期刊处理完毕，准备请求下一页")
        # 保存进度
        self._save_progress(page_number)

        # 如果有预先准备的下一页数据，发送请求
        if self.next_page_data and self.next_page_data['page'] > page_number:
            next_page = self.next_page_data['page']
            offset = self.next_page_data['offset']
            self.current_page = next_page
            self.next_page_data = None  # 重置下一页数据

            self.base_logger.info(f"开始请求第 {next_page} 页")
            # 使用Scrapy的engine直接添加请求
            for request in self._request_page_with_post(offset, next_page, next_page):
                self.crawler.engine.crawl(request)
        elif page_number < self.total_pages:
            # 如果没有预先准备的下一页数据，但还有更多页面需要处理
            next_page = page_number + 1
            offset = (next_page - 1) * self.results_per_page
            self.current_page = next_page

            self.base_logger.info(f"开始请求第 {next_page} 页")
            for request in self._request_page_with_post(offset, next_page, next_page):
                self.crawler.engine.crawl(request)
        else:
            self.base_logger.info("所有页面处理完毕，爬虫结束")
    def _load_source_ids(self):
        """
        从文件加载source_ids
        :author LGZ
        :return: None
        """
        if os.path.exists(self.source_ids_file):
            try:
                with open(self.source_ids_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        self.source_ids = content.split(',')
                        self.base_logger.info(f"已加载 {len(self.source_ids)} 个source_ids")
            except Exception as e:
                self.base_logger.warning(f"加载source_ids失败: {e}")
        else:
            self.base_logger.info("未找到source_ids文件")

    def _load_processed_journals(self):
        """
        从文件加载已处理的期刊ID
        :author LGZ
        :return: None
        """
        if os.path.exists(self.processed_journals_file):
            try:
                with open(self.processed_journals_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        journal_id = line.strip()
                        if journal_id:
                            self.processed_journals.add(journal_id)
                self.base_logger.info(f"已加载 {len(self.processed_journals)} 个已处理的期刊ID")
            except Exception as e:
                self.base_logger.warning(f"加载已处理期刊ID失败: {e}")
        else:
            self.base_logger.info("未找到已处理期刊记录文件，将创建新文件")

    def _save_processed_journal(self, journal_id):
        """
        保存已处理的期刊ID到文件

        :author LGZ
        :param journal_id: 期刊ID
        :return: None
        """
        try:
            with open(self.processed_journals_file, 'a', encoding='utf-8') as f:
                f.write(f"{journal_id}\n")
            self.processed_journals.add(journal_id)
            # 每次添加新的期刊ID时都更新进度文件中的processed_count
            self._save_progress(self.current_page - 1 if self.current_page > 1 else 1)
        except Exception as e:
            self.base_logger.warning(f"保存期刊ID失败: {e}")

    def _save_progress(self, page_number):
        """
        保存爬取进度到文件
        :author LGZ
        :param page_number: 当前处理的页码
        :return: None
        """
        try:
            progress_data = {
                'current_page': page_number + 1,  # 下次从下一页开始
                'total_pages': self.total_pages,
                'total_count': self.total_count,
                'processed_count': len(self.processed_journals),
            }
            # 确保目录存在
            os.makedirs(os.path.dirname(self.progress_file), exist_ok=True)
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.base_logger.warning(f"保存进度失败: {e}")


    def _load_progress(self):
        """
        从文件加载爬取进度
        :author LGZ
        :return: None
        """
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                self.current_page = progress_data.get('current_page', 1)
                self.total_pages = progress_data.get('total_pages', 0)
                self.total_count = progress_data.get('total_count', 0)
                # 更新processed_count
                processed_count = progress_data.get('processed_count', 0)
                self.base_logger.info(f"已加载进度信息: 当前页 {self.current_page}, 总页数 {self.total_pages}, 已处理 {processed_count} 个期刊")
            except Exception as e:
                self.base_logger.warning(f"加载进度失败: {e}")
        else:
            self.base_logger.info("未找到进度记录文件")


    def _save_source_ids(self, source_ids):
        """
        保存sourceIds到文件
        :author LGZ
        :param source_ids: ID列表
        :return: None
        """
        try:
            with open(self.source_ids_file, 'w', encoding='utf-8') as f:
                f.write(','.join(source_ids))
        except Exception as e:
            self.base_logger.warning(f"保存sourceIds失败: {e}")
