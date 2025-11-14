# -*- coding: utf-8 -*-

"""
# @Time    : 2025/8/20 17:48
# @User  : LGZ
# @Description  : Scimagojr期刊数据爬虫
"""

import math
import json
import os
import scrapy
from urllib.parse import urljoin, parse_qs, urlparse

from src.constant import TEMP_PATH
from src.items.other.eng_journal_item import EngJournalItem, JOURNAL_OPEN_ACCESS
from src.spiders.base_spider import BaseSpider
from src.utils.base_logger import BaseLog

# 年份范围控制常量
YEARS_TO_FETCH = 5  # 获取最近5年的数据

class ScimagojrSpider(BaseSpider):
    name = 'scimagojr'
    allowed_domains = ['www.scimagojr.com']
    base_url = 'https://www.scimagojr.com/'

    custom_settings = {
        'ITEM_PIPELINES': {
            'src.pipelines.data_cleaning_pipeline.DataCleaningPipeline': 300,  # 数据清洗管道
            'src.pipelines.storage.eng_journal_pipeline.EngJournalPipeline': 500,  # 数据入库管道
        },
        "DOWNLOADER_MIDDLEWARES": {
            'src.middlewares.proxy_middleware.BaseProxyMiddleware': 400,  # 代理请求中间件
        },
        # 控制并发请求数量
        'CONCURRENT_REQUESTS': 32,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 16,
        'DOWNLOAD_DELAY': 0.25,
    }

    # 每批处理的页面数
    BATCH_SIZE = 10
    TEMP_DIR = os.path.join(TEMP_PATH, 'Scimagojr')

    def __init__(self, **kwargs):
        """
        初始化Scimagojr爬虫实例

        :author LGZ
        :param kwargs: 其他参数
        """
        super().__init__(**kwargs)
        self.base_logger = BaseLog()
        # 本地记录文件路径
        os.makedirs(self.TEMP_DIR, exist_ok=True)  # 确保目录存在
        self.last_page_file = os.path.join(self.TEMP_DIR, 'last_page.txt')
        self.processed_journals_file = os.path.join(self.TEMP_DIR, 'processed_journals.txt')
        self.page_journal_count_file = os.path.join(self.TEMP_DIR, 'page_journal_count.txt')
        # 已处理的期刊集合
        self.processed_journals = set()
        # 页面期刊计数 {page: count}
        self.page_journal_count = {}
        # 每页期刊数
        self.journals_per_page = 20
        # 总数据量和总页数
        self.total_count = 0
        self.total_pages = 0

    def start_requests(self):
        """
        开始请求第一页数据以获取总页数

        :author LGZ
        :return: scrapy请求对象
        """
        url = 'https://www.scimagojr.com/journalrank.php?page=1'
        self.base_logger.info(f"开始请求第一页数据: {url}")
        yield scrapy.Request(url, callback=self.parse_rank_list_first_page)

    def parse_rank_list_first_page(self, response):
        """
        解析第一页，获取总页数和期刊详情链接

        :author LGZ
        :param response: 响应对象
        :return: scrapy请求对象
        """
        self.base_logger.info("解析第一页数据")
        # 获取总数据量
        pagination_div = response.css('div.pagination')
        if pagination_div:
            pagination_text = pagination_div.css('::text').get()
            if 'of' in pagination_text:
                self.total_count = int(pagination_text.split('of')[1].split()[0])
                # 每页20条数据
                self.total_pages = math.ceil(self.total_count / self.journals_per_page)
                self.base_logger.info(f"总共找到 {self.total_count} 条数据，共 {self.total_pages} 页")

                # 加载已处理的期刊ID和页面计数
                self._load_processed_journals()
                self._load_page_journal_count()

                # 获取断点续爬信息
                last_processed_page = self._get_last_processed_page()
                self.base_logger.info(f"上次处理到第 {last_processed_page} 页，总共 {self.total_pages} 页")

                # 解析当前页的期刊链接
                self.base_logger.info("开始解析第一页期刊链接")
                yield from self.parse_journal_links(response)

                # 分批请求后续页面
                start_page = last_processed_page + 1
                if start_page <= self.total_pages:
                    yield from self._process_next_batch(start_page)
        else:
            self.base_logger.warning("未找到分页信息")

    def _process_next_batch(self, start_page):
        """
        分批处理页面请求

        :author LGZ
        :param start_page: 起始页码
        :return: scrapy请求对象
        """
        batch_end_page = min(start_page + self.BATCH_SIZE - 1, self.total_pages)

        self.base_logger.info(f"开始处理第 {start_page} 到 {batch_end_page} 页数据")

        # 请求一批页面
        for page in range(start_page, batch_end_page + 1):
            url = f'https://www.scimagojr.com/journalrank.php?page={page}&total_size={self.total_count}'
            self.base_logger.debug(f"请求第 {page} 页数据: {url}")
            yield scrapy.Request(url, callback=self.parse_journal_links,
                                 meta={'page': page})

        # 如果还有更多页面需要处理，则继续请求下一批
        next_batch_start = batch_end_page + 1
        if next_batch_start <= self.total_pages:
            # 使用一个回调函数来处理下一批页面
            yield scrapy.Request(
                url='https://www.scimagojr.com/journalrank.php?page=1',  # 使用一个占位URL
                callback=self._process_next_batch_callback,
                meta={'start_page': next_batch_start},
                dont_filter=True
            )

    def _process_next_batch_callback(self, response):
        """
        处理下一批页面的回调函数

        :author
        :param response: 响应对象
        :return: scrapy请求对象
        """
        start_page = response.meta.get('start_page', 1)
        if start_page <= self.total_pages:
            yield from self._process_next_batch(start_page)

    def parse_journal_links(self, response):
        """
        解析期刊列表页面，提取期刊详情链接

        :author LGZ
        :param response: 响应对象
        :return: scrapy请求对象
        """
        page = response.meta.get('page', 1)

        # 提取所有期刊详情链接和开放获取信息
        journal_entries = response.css('td.tit')
        self.base_logger.info(f"从第 {page} 页 {response.url} 中提取到 {len(journal_entries)} 个期刊条目")

        # 记录该页面的期刊数量
        self.page_journal_count[page] = len(journal_entries)
        self._save_page_journal_count(page, len(journal_entries))

        detail_requests = []
        for entry in journal_entries:
            # 获取期刊链接
            link = entry.css('a::attr(href)').get()
            if not link:
                continue

            full_url = urljoin(self.base_url, link)
            # 从链接中提取期刊ID
            journal_id = self._extract_journal_id(full_url)

            # 检查是否已处理过该期刊（断点续爬）
            if journal_id and journal_id in self.processed_journals:
                self.base_logger.debug(f"期刊 {journal_id} 已处理过，跳过")
                continue

            # 检查是否为开放获取期刊
            is_open_access = JOURNAL_OPEN_ACCESS["open"] if entry.css('img.openaccessicon[alt="Open Access"]') else JOURNAL_OPEN_ACCESS["not_open"]

            self.base_logger.debug(f"请求期刊详情页: {full_url}，开放获取: {is_open_access}")
            request = scrapy.Request(full_url, callback=self.parse_journal_detail,
                                     meta={'page': page, 'journal_id': journal_id, 'openaccess': is_open_access})
            detail_requests.append(request)

        # 返回详情页请求
        for request in detail_requests:
            yield request

        # 检查是否需要处理下一批页面
        if page == min(page + self.BATCH_SIZE - 1, self.total_pages):  # 当前批次的最后一页
            next_batch_start = page + 1
            if next_batch_start <= self.total_pages:
                yield scrapy.Request(
                    url='https://www.scimagojr.com/journalrank.php?page=1',  # 使用一个占位URL
                    callback=self._process_next_batch_callback,
                    meta={'start_page': next_batch_start},
                    dont_filter=True
                )

    def _extract_journal_id(self, url):
        """
        从期刊详情页链接中提取期刊ID

        :author LGZ
        :param url: 期刊详情页链接
        :return: 期刊ID或None
        """
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            return query_params.get('q', [None])[0]
        except Exception as e:
            self.base_logger.warning(f"提取期刊ID失败: {url}, 错误: {e}")
            return None

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
        except Exception as e:
            self.base_logger.warning(f"保存期刊ID失败: {e}")

    def _load_page_journal_count(self):
        """
        从文件加载页面期刊计数

        :author LGZ
        :return: None
        """
        if os.path.exists(self.page_journal_count_file):
            try:
                with open(self.page_journal_count_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            parts = line.strip().split(':')
                            if len(parts) == 2:
                                page_num = int(parts[0])
                                count = int(parts[1])
                                self.page_journal_count[page_num] = count
                self.base_logger.info(f"已加载 {len(self.page_journal_count)} 个页面的期刊计数")
            except Exception as e:
                self.base_logger.warning(f"加载页面期刊计数失败: {e}")

    def _save_page_journal_count(self, page, count):
        """
        保存页面期刊计数

        :author LGZ
        :param page: 页码
        :param count: 期刊数量
        :return: None
        """
        try:
            with open(self.page_journal_count_file, 'a', encoding='utf-8') as f:
                f.write(f"{page}:{count}\n")
        except Exception as e:
            self.base_logger.warning(f"保存页面期刊计数失败: {e}")

    def _get_last_processed_page(self):
        """
        获取上次处理的页码
        根据已处理的期刊数量和每页的期刊数量计算

        :author LGZ
        :return: 上次处理的页码
        """
        processed_count = len(self.processed_journals)

        # 计算完整处理的页数
        completed_pages = processed_count // self.journals_per_page

        # 如果有余数，说明当前页正在处理中
        if processed_count % self.journals_per_page > 0:
            completed_pages += 1

        self.base_logger.info(f"已处理期刊数: {processed_count}, 推算已完成页数: {completed_pages}")
        return completed_pages

    def parse_journal_detail(self, response):
        """
        解析期刊详情页面

        :author LGZ
        :param response: 响应对象
        :return: 期刊信息项
        """
        page = response.meta.get('page')
        journal_id = response.meta.get('journal_id')
        openaccess = response.meta.get('openaccess', JOURNAL_OPEN_ACCESS["not_open"])  # 默认为0（非开放获取）

        self.base_logger.info(f"开始解析期刊详情页: {response.url}")
        item = EngJournalItem()

        # 基本信息
        item['journal_name'] = response.css('title::text').get()
        item['page_url'] = response.url
        item['openaccess'] = str(openaccess)  # 添加开放获取字段
        self.base_logger.debug(f"期刊名称: {item['journal_name']}, 开放获取: {openaccess}")

        # 获取Homepage和投稿链接
        info_links = response.css('div h2:contains("Information") ~ p a')
        for link in info_links:
            text = link.css('::text').get()
            href = link.css('::attr(href)').get()
            if text == 'Homepage':
                item['homepage'] = href
            elif text and 'publish' in text.lower():
                item['publish_link'] = href

        # 期刊简介
        scope_div = response.css('div.fullwidth')
        # 排除 h2 和 a 标签的文本
        scope_text = scope_div.xpath('.//text()[not(parent::h2) and not(parent::a)]').getall()

        item['scope'] = ' '.join([text.strip() for text in scope_text if text.strip()]).strip()

        # 国家
        country_link = response.css('div h2:contains("Country") + p a::text').get()
        item['country'] = country_link

        # 学科分类（大类和小类）
        subject_areas_data = self._extract_subject_areas(response)
        item['subject_areas'] = json.dumps(subject_areas_data, ensure_ascii=False)
        self.base_logger.debug(f"提取到 {len(subject_areas_data)} 个学科分类")

        # 出版商
        publisher_text = response.css('div h2:contains("Publisher") + p a::text').get()
        item['publisher'] = publisher_text

        # 类型
        publication_type_text = response.css('div h2:contains("Publication type") + p::text').get()
        item['publication_type'] = publication_type_text

        # ISSN
        issn_text = response.css('div h2:contains("ISSN") + p::text').get()
        if issn_text:
            issn_parts = [part.strip() for part in issn_text.split(',')]

            # 格式化ISSN号，每4位字符用"-"分隔
            clean_issn = issn_parts[0].replace('-', '')
            if len(clean_issn) == 8:
                item['issn'] = f"{clean_issn[:4]}-{clean_issn[4:]}"
            else:
                item['issn'] = issn_parts[0]

            if len(issn_parts) > 1:
                clean_eissn = issn_parts[1].replace('-', '')
                if len(clean_eissn) == 8:
                    item['eissn'] = f"{clean_eissn[:4]}-{clean_eissn[4:]}"
                else:
                    item['eissn'] = issn_parts[1]

        # 覆盖范围
        coverage_text = response.css('div h2:contains("Coverage") + p::text').get()
        item['coverage'] = coverage_text

        # H-INDEX
        h_index_text = response.css('div h2:contains("H-Index") + p.hindexnumber::text').get()
        item['h_index'] = h_index_text

        # 分区数据
        quartiles_data = self._extract_quartiles_data(response, YEARS_TO_FETCH, subject_areas_data)
        item['sjr_quartiles'] = json.dumps(quartiles_data, ensure_ascii=False)

        # SJR数据
        sjr_data = self._extract_simple_table_data(response, 'SJR', YEARS_TO_FETCH)
        item['sjr'] = json.dumps(sjr_data, ensure_ascii=False)

        # 总文献量
        total_docs_data = self._extract_simple_table_data(response, 'Total Documents', YEARS_TO_FETCH)
        item['total_docs'] = json.dumps(total_docs_data, ensure_ascii=False)

        # 总被引量和自引量
        cites_data = self._extract_cites_data(response, YEARS_TO_FETCH)
        item['total_cites'] = json.dumps(cites_data.get('Total Cites', []), ensure_ascii=False)
        item['self_cites'] = json.dumps(cites_data.get('Self Cites', []), ensure_ascii=False)

        # 篇均外部引用数和篇均引用数
        cites_per_doc_data = self._extract_cites_per_doc_data(response, YEARS_TO_FETCH)
        item['external_cites_per_doc'] = json.dumps(cites_per_doc_data.get('External Cites per document', []),
                                                    ensure_ascii=False)
        item['cites_per_doc'] = json.dumps(cites_per_doc_data.get('Cites per document', []), ensure_ascii=False)

        # 国际合作比例
        international_data = self._extract_simple_table_data(response, '% International Collaboration', YEARS_TO_FETCH)
        item['international_collaboration'] = json.dumps(international_data, ensure_ascii=False)

        # 可引文献数和非可引文献数
        citable_data = self._extract_citable_data(response, YEARS_TO_FETCH)
        item['citable_docs'] = json.dumps(citable_data.get('Citable documents', []), ensure_ascii=False)
        item['non_citable_docs'] = json.dumps(citable_data.get('Non-citable documents', []), ensure_ascii=False)

        # 被引文献数和未被引文献数
        cited_data = self._extract_cited_data(response, YEARS_TO_FETCH)
        item['cited_docs'] = json.dumps(cited_data.get('Cited documents', []), ensure_ascii=False)
        item['uncited_docs'] = json.dumps(cited_data.get('Uncited documents', []), ensure_ascii=False)

        # 文章出版费
        apc_data = self._extract_simple_table_data(response, 'Estimated APC', YEARS_TO_FETCH)
        item['estimated_apc'] = json.dumps(apc_data, ensure_ascii=False)

        # 记录已处理的期刊（用于断点续爬）
        if journal_id:
            self._save_processed_journal(journal_id)
            self.base_logger.debug(f"记录已处理期刊: {journal_id}")

        self.base_logger.info(f"成功解析期刊信息: {item['journal_name']} (第{page}页)")
        yield item

    def _extract_subject_areas(self, response):
        """
        提取学科分类数据（大类和小类）

        :author LGZ
        :param response: 响应对象
        :return: 学科分类数据列表
        """
        data = []

        # 首先查找所有h2标题
        for h2 in response.css('h2'):
            # 检查是否是Subject Area标题
            if 'Subject Area and Category' in h2.get():
                # 找到包含这个h2的div
                div = h2.xpath('./parent::div')
                # 在这个div中查找ul
                main_categories = div.css('ul > li[style*="display: inline-block"]')

                for main_category in main_categories:
                    # 获取大类名称
                    main_category_name = main_category.css('a::text').get()
                    if main_category_name:
                        category_data = {
                            'main_category': main_category_name,
                            'sub_categories': []
                        }

                        # 获取小类
                        sub_categories = main_category.css('ul.treecategory li a::text').getall()
                        category_data['sub_categories'] = sub_categories

                        data.append(category_data)

                # 找到了Subject Area区域后就不需要继续查找了
                break

        return data

    def _extract_quartiles_data(self, response, limit, subject_areas_data=None):
        """
        提取分区数据

        :author LGZ
        :param response: 响应对象
        :param limit: 限制返回的数据条数
        :param subject_areas_data: 学科分类数据
        :return: 分区数据列表
        """
        data = []
        sections = response.xpath('//div[contains(.//div[@class="celltitle"], "Quartiles")]')
        if sections:
            rows = sections[0].css('table tbody tr')
            year_value_pairs = []
            for row in rows:
                cells = row.css('td::text').getall()
                if len(cells) >= 3:
                    category = cells[0]
                    year = int(cells[1])
                    quartile = cells[2]

                    # 创建基础数据项
                    entry = {
                        'year': year,
                        'subcategory': category,  # 原category改为subcategory
                        'subject_quartile': quartile
                    }

                    # 如果提供了学科分类数据，则查找对应的大类
                    if subject_areas_data:
                        for area in subject_areas_data:
                            main_category = area.get('main_category')
                            sub_categories = area.get('sub_categories', [])
                            # 如果在子类中找到了匹配项，则添加大类信息
                            if category in sub_categories:
                                entry['category'] = main_category
                                break

                    # 如果没有找到对应的大类，则使用子类名作为大类名
                    if 'category' not in entry:
                        entry['category'] = category

                    year_value_pairs.append(entry)

            # 按年份排序并取最近的limit条记录
            sorted_data = sorted(year_value_pairs, key=lambda x: x['year'], reverse=True)
            data = sorted_data[:limit]

        return data
    def _extract_simple_table_data(self, response, title, limit):
        """
        从包含特定标题的区域中提取简单表格数据（年份-值对）

        :author LGZ
        :param response: 响应对象
        :param title: 表格标题
        :param limit: 限制返回的数据条数
        :return: 表格数据列表
        """
        data = []
        # 查找包含特定标题的区域
        sections = response.css(f'div.celltitle:contains("{title}")')
        if sections:
            # 获取表格数据
            table = sections[0].xpath('./ancestor::div[contains(@class, "cell1x1")]//table')
            if table:
                rows = table.css('tbody tr')
                year_value_pairs = []
                for row in rows:
                    cells = row.css('td::text').getall()
                    if len(cells) >= 2:
                        # 第一列是年份，第二列是值
                        try:
                            year = int(cells[0])
                            value = cells[1]
                            year_value_pairs.append({
                                'year': year,
                                'value': value
                            })
                        except ValueError:
                            # 如果年份不是数字，跳过这一行
                            continue

                # 按年份排序并取最近的limit条记录
                sorted_data = sorted(year_value_pairs, key=lambda x: x['year'], reverse=True)
                data = sorted_data[:limit]

        return data

    def _extract_cites_data(self, response, limit):
        """
        提取总被引量和自引量数据

        :author LGZ
        :param response: 响应对象
        :param limit: 限制返回的数据条数
        :return: 被引量数据字典
        """
        data = {'Total Cites': [], 'Self Cites': []}
        sections = response.xpath('//div[contains(.//div[@class="celltitle"], "Total Cites")]')
        if sections:
            rows = sections[0].css('table tbody tr')
            total_cites = []
            self_cites = []
            for row in rows:
                cells = row.css('td::text').getall()
                if len(cells) >= 3:
                    cite_type = cells[0]
                    year = int(cells[1])
                    value = cells[2]
                    entry = {
                        'year': year,
                        'value': value
                    }
                    if cite_type == 'Total Cites':
                        total_cites.append(entry)
                    elif cite_type == 'Self Cites':
                        self_cites.append(entry)

            # 按年份排序并取最近的limit条记录
            data['Total Cites'] = sorted(total_cites, key=lambda x: x['year'], reverse=True)[:limit]
            data['Self Cites'] = sorted(self_cites, key=lambda x: x['year'], reverse=True)[:limit]

        return data

    def _extract_cites_per_doc_data(self, response, limit):
        """
        提取篇均引用数相关数据

        :author LGZ
        :param response: 响应对象
        :param limit: 限制返回的数据条数
        :return: 篇均引用数数据字典
        """
        data = {'Cites per document': [], 'External Cites per document': []}
        # 修改XPath选择器，使其能够正确选择到包含两种引用类型的区域
        sections = response.xpath(
            '//div[contains(.//div[@class="celltitle"], "Cites per Doc") and contains(.//div[@class="celltitle"], "External Cites per Doc")]')
        if sections:
            rows = sections[0].css('table tbody tr')
            cites_per_doc = []
            external_cites = []
            for row in rows:
                cells = row.css('td::text').getall()
                if len(cells) >= 3:
                    cite_type = cells[0]
                    year = int(cells[1])
                    value = cells[2]
                    entry = {
                        'year': year,
                        'value': value
                    }
                    # 使用精确匹配来区分两种类型
                    if cite_type == 'Cites per document':
                        cites_per_doc.append(entry)
                    elif cite_type == 'External Cites per document':
                        external_cites.append(entry)

            # 按年份排序并取最近的limit条记录
            data['Cites per document'] = sorted(cites_per_doc, key=lambda x: x['year'], reverse=True)[:limit]
            data['External Cites per document'] = sorted(external_cites, key=lambda x: x['year'], reverse=True)[:limit]
        return data

    def _extract_citable_data(self, response, limit):
        """
        提取可引文献数相关数据

        :author LGZ
        :param response: 响应对象
        :param limit: 限制返回的数据条数
        :return: 可引文献数数据字典
        """
        data = {'Citable documents': [], 'Non-citable documents': []}
        sections = response.xpath('//div[contains(.//div[@class="celltitle"], "Citable documents")]')
        if sections:
            rows = sections[0].css('table tbody tr')
            citable = []
            non_citable = []
            for row in rows:
                cells = row.css('td::text').getall()
                if len(cells) >= 3:
                    doc_type = cells[0]
                    year = int(cells[1])
                    value = cells[2]
                    entry = {
                        'year': year,
                        'value': value
                    }
                    if 'Citable documents' in doc_type:
                        citable.append(entry)
                    elif 'Non-citable documents' in doc_type:
                        non_citable.append(entry)

            # 按年份排序并取最近的limit条记录
            data['Citable documents'] = sorted(citable, key=lambda x: x['year'], reverse=True)[:limit]
            data['Non-citable documents'] = sorted(non_citable, key=lambda x: x['year'], reverse=True)[:limit]

        return data

    def _extract_cited_data(self, response, limit):
        """
        提取被引文献数相关数据

        :author LGZ
        :param response: 响应对象
        :param limit: 限制返回的数据条数
        :return: 被引文献数数据字典
        """
        data = {'Cited documents': [], 'Uncited documents': []}
        sections = response.xpath('//div[contains(.//div[@class="celltitle"], "Cited documents")]')
        if sections:
            rows = sections[0].css('table tbody tr')
            cited = []
            uncited = []
            for row in rows:
                cells = row.css('td::text').getall()
                if len(cells) >= 3:
                    doc_type = cells[0]
                    year = int(cells[1])
                    value = cells[2]
                    entry = {
                        'year': year,
                        'value': value
                    }
                    if 'Cited documents' in doc_type:
                        cited.append(entry)
                    elif 'Uncited documents' in doc_type:
                        uncited.append(entry)

            # 按年份排序并取最近的limit条记录
            data['Cited documents'] = sorted(cited, key=lambda x: x['year'], reverse=True)[:limit]
            data['Uncited documents'] = sorted(uncited, key=lambda x: x['year'], reverse=True)[:limit]

        return data
