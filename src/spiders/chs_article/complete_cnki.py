# # -*- coding: utf-8 -*-
#
# """
# # @Time    : 2025/8/6 16:46
# # @User  : Mabin
# # @Description  :CNKI爬取代码（完整）
# """
# import datetime
# import re
# from src.utils.utils import is_valid_http_url
# from typing import cast, Iterable, Literal
# import scrapy
# from playwright.async_api import Page
# from scrapy.http import Request, Response
# from scrapy.selector import Selector
# from scrapy_playwright.page import PageMethod
# from src.component.base_selector_component import BaseSelectorComponent
# from src.component.playwright_helper import PlaywrightTools
# from src.items.other.chi_article_item import JOURNAL_OPEN_ACCESS, CO_FIRST_AUTHOR, CORRESPONDING_AUTHOR, \
#     AUTHOR_IS_DISPLAY, AUTHOR_TYPE, CnJournalItem, JOURNAL_UNIT_RELATION_TYPE, JOURNAL_PLATFORM_CODE, CnArticleItem, \
#     ARTICLE_ABSTRACT_SECTION_ATTR, ARTICLE_PUBLISHED_TIME_PRECISION, JOURNAL_IS_SUSPENDED
# from src.spiders.base_spider import BaseSpider
# from src.utils.utils import en_cn_correction
#
#
# class CnkiSpider(BaseSpider):
#     name = 'complete_cnki'
#     allowed_domains = ["kns.cnki.net", "navi.cnki.net", "c61.cnki.net", "xztg.cnki.net"]
#     base_url = "https://navi.cnki.net"
#     years_to_crawl = 5  # 爬取最近几年的数据
#     click_timeout = 30000  # 点击等待延迟
#     network_timeout = 30000  # 等待页面延迟
#     breathing_timeout = 3000  # 喘息时间（较短的时间间隔）
#     submission_link = "https://xztg.cnki.net/#/complete-journal-collection/selection-detail?id={journal_id}"
#     platform_code = "cnki"  # 平台标识
#
#     """
#     自定义配置
#     """
#     custom_settings = {
#         "CONCURRENT_REQUESTS": 5,  # 降低并发量
#         "MONGO_DATABASE": "raw_cn_article_list",
#         # "CONCURRENT_REQUESTS_PER_DOMAIN": 3,  # 降低并发量
#         "DOWNLOAD_HANDLERS": {
#             "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
#             "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
#         },
#         "DEFAULT_REQUEST_HEADERS": {
#             'Referer': 'https://navi.cnki.net/knavi/journals/index',
#             'Origin': 'https://navi.cnki.net',
#         },
#         "PLAYWRIGHT_LAUNCH_OPTIONS": {
#             "headless": False,
#         },
#         "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 180 * 1000,  # Playwright 请求页面时使用的超时时间
#         # # 每个上下文最大只能打开一个页面，控制瞬时网速
#         # "PLAYWRIGHT_MAX_PAGES_PER_CONTEXT": 1,
#         # "PLAYWRIGHT_BROWSER_TYPE": "firefox",
#         "CAPTCHA_URLS": ["kns.cnki.net/verify"],
#         "CAPTCHA_TRIGGER_PATTERNS": ["知网节超时验证"],
#         'ITEM_PIPELINES': {
#             'src.pipelines.data_cleaning_pipeline.DataCleaningPipeline': 99,
#             'src.pipelines.file_download_pipeline.FileDownloadPipeline': 100,
#             'src.pipelines.file_replacement_pipeline.FileReplacementPipeline': 200,
#             'src.pipelines.storage.chi_article_pipeline.CNArticleInterfacePipeline': 300,
#             'src.pipelines.storage.chi_article_pipeline.CNArticlePipeline': 301,
#             'src.pipelines.storage.chi_journal_pipeline.CNJournalInterfacePipeline': 302,
#             'src.pipelines.storage.chi_journal_pipeline.CNJournalPipeline': 303,
#
#         },
#         "EXTENSIONS": {
#             'scrapy.extensions.logstats.LogStats': None,
#             'src.extensions.verbose_log_stats.VerboseLogStats': 500,  # 510是优先级
#         },
#         # "SEMAPHORE_CONFIGS": {
#         #     "journal_index": 10,  # 期刊详情页
#         #     "journal_detail": 1,  # 期刊文献列表页
#         #     "journal_submission": 10,  # 期刊投稿页
#         #     "paper": 5,  # 文献详情页
#         # }
#     }
#
#     def __init__(self, **kwargs):
#         """
#         初始化当前类
#         :param kwargs:
#         """
#         super().__init__(**kwargs)
#
#         # 确定爬取年份范围
#         current_year = datetime.datetime.now().year
#         self.crawling_years_range = {f"{current_year - i}" for i in range(self.years_to_crawl)}
#
#     def start_requests(self):
#         """
#         开始请求
#         """
#         yield scrapy.Request(
#             "https://navi.cnki.net/knavi/journals/index",
#             callback=self.parse_index,
#             meta={
#                 'playwright': True,
#                 "playwright_include_page": True,
#                 "playwright_page_init_callback": self.init_page,
#                 "playwright_page_methods": [
#                     PageMethod("wait_for_load_state", timeout=self.network_timeout, state="networkidle"),
#                 ],
#             },
#             errback=self.playwright_request_error,
#         )
#
#     async def parse_index(self, response: Response, **kwargs):
#         """
#         解析期刊页面
#         :param response:
#         :param kwargs:
#         :return:
#         """
#         # 获取page对象
#         page: Page = response.meta["playwright_page"]
#
#         # 点击"卓越期刊导航"
#         await PlaywrightTools.safe_click_spa(
#             page=page,
#             selector='.item:has-text("卓越期刊导航")',
#             click_timeout=self.click_timeout
#         )
#
#         # 点击"中国科技期刊卓越行动计划入选项目"
#         await PlaywrightTools.safe_click_spa(
#             page=page,
#             selector='a:has-text("中国科技期刊卓越行动计划入选项目")',
#             click_timeout=self.click_timeout
#         )
#
#         # 循环处理分页
#         journal_buf = []
#         while True:
#             # 等待并获取链接
#             await page.wait_for_selector('.result a[target="_blank"]', timeout=self.network_timeout)
#
#             # 获取所有链接元素
#             journal_locator = page.locator('.result a[target="_blank"]')
#             count = await journal_locator.count()
#
#             # 检查是否有足够的链接
#             if count == 0:
#                 break
#
#             # 逐个处理
#             for i in range(count):
#                 link_element = journal_locator.nth(i)
#
#                 # 获取期刊详情页链接
#                 journal_url = await link_element.get_attribute('href')
#                 journal_name = await link_element.get_attribute('title')
#
#                 if journal_url:
#                     # 存在链接
#                     journal_buf.append({
#                         "journal_url": journal_url,
#                         "journal_name": journal_name,
#                     })
#
#             # 检查是否有下一页
#             next_sign = await PlaywrightTools.safe_click_spa(
#                 page=page,
#                 selector='.pagenav .next',
#                 click_timeout=self.click_timeout
#             )
#             if not next_sign:
#                 # 不存在下一页
#                 break
#
#         # 释放页面
#         await page.close()
#
#         # 依次执行期刊详情页的请求
#         for journal_item in journal_buf:
#             # 等待信号量
#             yield response.follow(
#                 journal_item["journal_url"],
#                 callback=self.parse_journal_detail,
#                 meta={
#                     'playwright': True,
#                     "playwright_page_init_callback": self.init_page,
#                     "journal_name": journal_item["journal_name"],
#                     # "semaphore_key": "journal_index",  # 控制并发数
#                 }
#             )
#
#     async def parse_journal_detail(self, response: Response, **kwargs):
#         """
#         解析期刊详情页
#         :param response:
#         :param kwargs:
#         :return:
#         """
#         # 获取基本数据
#         journal_name = response.meta.get("journal_name")
#
#         # 执行提取
#         selector_model = BaseSelectorComponent()
#
#         # 是否为完全OA期刊
#         selector_model.add_field(
#             selector="span:has(b.comOA)",
#             field_name="open_access",
#             selector_type="css"
#         )
#
#         # 收录信息
#         base_name = "index_list"
#         base_selector = ".journalType2 span"
#         base_selector_type: Literal["css"] = "css"
#         selector_model.add_field(
#             selector=".",
#             field_name="index_name",
#             base_name=base_name,
#             base_selector=base_selector,
#             base_selector_type=base_selector_type
#         )
#         selector_model.add_field(
#             selector="::attr(title)",
#             field_name="index_intro",
#             selector_type="css",
#             base_name=base_name,
#             base_selector=base_selector,
#             base_selector_type=base_selector_type
#         )
#
#         # 专辑名称（父学科）
#         selector_model.add_field(
#             selector="#jiName",
#             field_name="album_name",
#             selector_type="css"
#         )
#
#         # 专题名称（子学科，可能不存在）
#         selector_model.add_field(
#             selector="#tiName",
#             field_name="topic_name",
#             selector_type="css"
#         )
#
#         # 期刊ID
#         selector_model.add_field(
#             selector='//input[@id="pykm"]/@value',
#             field_name="journal_id",
#             required=True  # 必填
#         )
#
#         # 期刊ISSN
#         selector_model.add_field(
#             selector='//p[@class="hostUnit"][contains(., "ISSN")]',
#             field_name="journal_issn",
#         )
#
#         # 执行提取
#         extract_result = selector_model.execute_non_yield(response=response)
#         if not extract_result["result"]:
#             raise ValueError(extract_result["msg"])
#         extract_result = extract_result["data"]
#
#         # ISSN数据需要额外处理
#         if extract_result["journal_issn"]:
#             extract_result["journal_issn"] = str(extract_result["journal_issn"]).replace("ISSN：", "").strip()
#
#         # 追加期刊标题和链接
#         extract_result["journal_name"] = journal_name
#         extract_result["journal_url"] = response.url
#
#         # 投稿链接拼接链接请求即可，且不必再操作Page
#         yield scrapy.Request(
#             self.submission_link.format(journal_id=extract_result["journal_id"]),
#             callback=self.parse_submission_page,
#             meta={
#                 'playwright': True,
#                 "playwright_page_init_callback": self.init_page,
#                 "playwright_page_methods": [
#                     PageMethod("wait_for_timeout", timeout=self.network_timeout),
#                 ],
#                 "journal_info": extract_result,
#             },
#             dont_filter=True,
#             priority=100,  # 紧急链接 - 最高优先级
#         )
#
#     def parse_submission_page(self, response: Response, **kwargs):
#         """
#         解析投稿链接信息
#         :author Mabin
#         :param response:
#         :param kwargs:
#         :return:
#         """
#         # 获取meta数据
#         journal_meta = response.meta.get("journal_info", {}) or {}
#         journal_url = journal_meta["journal_url"]
#
#         # 处理表格数据
#         table_mapping = {}
#         table_selector = response.css('tr.ant-descriptions-row')
#         table_selector = cast(Iterable[Selector], table_selector)  # 显式声明类型
#         for row in table_selector:
#             # 获取当前行中的所有<th>和<td>元素
#             cells = row.css('th.ant-descriptions-item-label, td.ant-descriptions-item-content')
#
#             # 成对处理标签和内容
#             for i in range(0, len(cells), 2):
#                 if i + 1 >= len(cells):
#                     break
#
#                 # 获取标签名和对应的值
#                 label = cells[i].css('::text').get().strip('：').strip()
#                 value = cells[i + 1].css('::text').get().replace("\n", "").replace("\r", "").strip()
#
#                 # 将键值对存入字典
#                 if label and value and value != "暂无" and value != "/":
#                     table_mapping[label] = value
#
#         # 执行提取
#         selector_model = BaseSelectorComponent()
#
#         # 封面图
#         selector_model.add_field(
#             selector=".show-img img::attr(src)",
#             field_name="cover_image",
#             selector_type="css",
#             field_type="href"
#         )
#         # 期刊中文名
#         selector_model.add_field(
#             selector=".basics-info-left h2 a",
#             field_name="journal_cn_name",
#             selector_type="css",
#             field_type="text"
#         )
#         # 期刊英文名
#         selector_model.add_field(
#             selector=".Eng-title:not(.former-title)",
#             field_name="journal_en_name",
#             selector_type="css",
#             field_type="text"
#         )
#         # 曾用刊名
#         selector_model.add_field(
#             selector=".Eng-title.former-title",
#             field_name="former_title",
#             selector_type="css",
#             field_type="text"
#         )
#         # 出版周期
#         selector_model.add_field(
#             selector='.stat-item:contains("出版周期") p',
#             field_name="publish_cycle",
#             selector_type="css",
#             field_type="text"
#         )
#         # 期刊介绍 (获取所有段落)
#         selector_model.add_field(
#             selector='.desc-text p',
#             field_name="journal_cn_intro",
#             selector_type="css",
#         )
#         # 执行提取
#         extract_result = selector_model.execute_non_yield(response=response)
#         if not extract_result["result"]:
#             raise ValueError(extract_result["msg"])
#         extract_data = extract_result["data"]
#
#         # 曾用刊名
#         former_title = extract_data["former_title"] or None
#         if former_title:
#             former_title = former_title.replace('曾用刊名：', '').strip()
#             former_title = str(former_title).split(";")
#
#         # 纠正中英文描述情况
#         journal_intro = en_cn_correction(
#             text_list=[
#                 extract_data["journal_cn_intro"]
#             ],
#             chs_field_name="journal_cn_intro",
#             eng_field_name="journal_en_intro",
#         )
#
#         # 纠正中英文字段名称情况
#         journal_name = en_cn_correction(
#             text_list=[
#                 extract_data["journal_en_name"],
#                 extract_data["journal_cn_name"],
#             ],
#             chs_field_name="journal_cn_name",
#             eng_field_name="journal_en_name",
#         )
#
#         # 出版商、主办单位和主管单位信息列表
#         unit_list = []
#         if table_mapping.get("主管单位"):
#             unit_list.append({
#                 "unit_name": table_mapping.get("主管单位"),
#                 "relation_type": JOURNAL_UNIT_RELATION_TYPE["authority"]
#             })
#         if table_mapping.get("主办单位"):
#             tmp_data = {
#                 "unit_name": table_mapping.get("主办单位"),
#                 "relation_type": JOURNAL_UNIT_RELATION_TYPE["sponsor"]
#             }
#             # if table_mapping.get("编辑部地址"):
#             #     tmp_data["unit_place"] = table_mapping.get("编辑部地址")
#
#             unit_list.append(tmp_data)
#
#         # 期刊平台信息
#         platform_list = [
#             {
#                 "platform_id": journal_meta.get("journal_id"),
#                 "platform_code": JOURNAL_PLATFORM_CODE["cnki"],
#             }
#         ]
#         if table_mapping.get("CN"):
#             platform_list.append({
#                 "platform_id": table_mapping.get("CN"),
#                 "platform_code": JOURNAL_PLATFORM_CODE["cnsn"],
#             })
#         if table_mapping.get("ISSN"):
#             platform_list.append({
#                 "platform_id": table_mapping.get("ISSN"),
#                 "platform_code": JOURNAL_PLATFORM_CODE["issn"],
#             })
#
#         # 学科信息
#         subject_info = []
#         if journal_meta.get("album_name"):
#             # 一级学科
#             tmp_data = {
#                 "first": journal_meta.get("album_name"),
#                 "second": [],
#             }
#
#             if journal_meta.get("topic_name"):
#                 # 二级学科
#                 topic_name = str(journal_meta.get("topic_name")).split(";")  # 执行分割
#                 for topic_item in topic_name:
#                     tmp_data["second"].append(topic_item)
#
#             # 记录数据
#             subject_info.append(tmp_data)
#
#         # 期刊额外信息
#         extra_info = {
#             "first_chief": table_mapping.get("主编"),
#             "deputy_chief": table_mapping.get("副主编"),
#             "phone": table_mapping.get("联系电话"),
#             "email": table_mapping.get("投稿邮箱"),
#             "address": table_mapping.get("出版地"),
#             "submission_method": table_mapping.get("投稿方式"),
#             "editorial_department_address": table_mapping.get("编辑部地址"),
#         }
#         extra_info = {k: v for k, v in extra_info.items() if v}
#
#         # 检查封面图是否为链接
#         cover_image = None
#         if is_valid_http_url(extract_data["cover_image"]):
#             cover_image = extract_data["cover_image"]
#
#         # 分离官方网址
#         official_website = table_mapping.get("官网网址")
#         if official_website:
#             official_website = str(official_website).split(";")[0]
#
#         # 构造期刊Item
#         yield CnJournalItem(
#             journal_en_name=journal_name["journal_en_name"],
#             journal_cn_name=journal_name["journal_cn_name"],
#             former_name=former_title,  # 管道中在对其向入库接口发送时，进行格式整理
#             journal_cn_intro=journal_intro["journal_cn_intro"],
#             journal_en_intro=journal_intro["journal_en_intro"],
#             data_source=self.platform_code,
#             file_urls=[cover_image],
#             journal_image=cover_image,
#             journal_lang=extract_data["journal_cn_name"],
#             publish_cycle=extract_data["publish_cycle"],
#             extra_info=extra_info,
#             start_year=table_mapping.get("创刊时间"),
#             end_year=table_mapping.get("收录结束年"),  # 停刊判断逻辑位于入库管道中
#             is_suspended=JOURNAL_IS_SUSPENDED["not_suspended"] if table_mapping.get("收录结束年")
#             else JOURNAL_IS_SUSPENDED["suspended"],  # 如果不存在收录结束年，则按照停刊处理
#             official_website=official_website,
#             submission_address=table_mapping.get("投稿网址"),
#             open_access=JOURNAL_OPEN_ACCESS["open"] if journal_meta.get("open_access")
#             else JOURNAL_OPEN_ACCESS["not_open"],
#             index_list=journal_meta.get("index_list", []),
#             unit_list=unit_list,
#             platform_list=platform_list,
#             subject_info=subject_info,  # 一级学科的名称规范位于管道中
#             original_html=response.text,  # 详情页内容
#             page_url=response.url,
#         )
#
#         if not journal_meta.get("album_name"):
#             # 不存在一级学科的期刊，不再爬取文献列表
#             return
#
#         # 构造文献列表页请求
#         for year_item in self.crawling_years_range:
#             yield scrapy.Request(
#                 journal_url,
#                 callback=self.parse_literature_list,
#                 meta={
#                     'playwright': True,
#                     "playwright_include_page": True,
#                     "playwright_page_init_callback": self.init_page,
#                     "journal_info": journal_meta,
#                     # "semaphore_key": "journal_detail",  # 控制并发数
#                     "journal_year": year_item
#                 },
#                 dont_filter=True,
#                 errback=self.playwright_request_error,
#             )
#
#     async def parse_literature_list(self, response: Response, **kwargs):
#         """
#         解析文献列表
#         :author Mabin
#         :param response:
#         :param kwargs:
#         :return:
#         """
#         # 获取基本数据
#         journal_info = response.meta.get("journal_info")
#         journal_year = response.meta.get("journal_year")
#         page: Page = response.meta["playwright_page"]
#         try:
#             # 滚动页面
#             await PlaywrightTools.page_screen_scroll(page=page)
#
#             # 处理年份侧边栏
#             async for article_item in self._process_years(page, {journal_year}):
#                 # 遍历文献列表
#                 # literature_links 格式如
#                 # {'article_title': '文献标题', 'article_url': '文献链接', 'article_type': '文献类型', 'article_year': '2025', 'article_issue': '06', 'article_page':'1'}
#
#                 # 检查是否存在历史数据
#                 history_key = self.generate_unique_key({
#                     "journal_info": journal_info,
#                     "article_year": article_item["article_year"],
#                     "issue": article_item["article_issue"],
#                     "article_cn_name": article_item["article_title"],
#                 })
#                 if self.is_seen(history_key):
#                     # 存在历史，则跳过
#                     continue
#
#                 yield scrapy.Request(
#                     article_item["article_url"],
#                     callback=self.parse_literature_detail,
#                     meta={
#                         'playwright': True,
#                         "playwright_include_page": True,
#                         "playwright_page_init_callback": self.init_page,
#                         "playwright_page_methods": [
#                             PageMethod("wait_for_load_state", timeout=self.network_timeout, state="networkidle"),
#                         ],
#                         "journal_info": journal_info,
#                         "article_info": {
#                             "title_text": article_item["article_title"],
#                             "issue_info": article_item["article_issue"],
#                             "article_type": article_item["article_type"],
#                             "article_year": article_item["article_year"],
#                             "article_page": article_item["article_page"],
#                         },
#                         # "semaphore_key": "paper",  # 控制并发数
#                     },
#                     priority=50,  # 重要链接 - 高优先级
#                     errback=self.playwright_request_error,
#                 )
#         finally:
#             # 释放页面及信号量
#             await page.close()
#
#     async def parse_literature_detail(self, response: Response, **kwargs):
#         """
#         解析文献详情页
#         :author Mabin
#         :param response:
#         :param kwargs:
#         :return:
#         """
#         page: Page = response.meta["playwright_page"]
#         response_meta = response.meta or {}
#         journal_info = response_meta.get("journal_info") or {}
#         article_info = response_meta.get("article_info") or {}
#         try:
#             # 滚动至底部
#             # await PlaywrightTools.page_screen_scroll(page=page, scroll_type="bottom")
#
#             # 实例化选择器
#             selector_model = BaseSelectorComponent()
#
#             # 摘要信息
#             selector_model.add_field(
#                 selector='//*[@id="abstract_text"]/@value',
#                 field_name="article_abstract",
#             )
#
#             # 关键词
#             selector_model.add_field(
#                 selector=".keywords a",
#                 field_name="article_keywords",
#                 selector_type="css",
#                 field_type="list",
#                 default=[],
#             )
#
#             # 基金资助
#             selector_model.add_field(
#                 selector=".funds > span",
#                 field_name="article_grant",
#                 selector_type="css",
#                 field_type="list",
#                 default=[],
#             )
#
#             # 文献唯一标识
#             selector_model.add_field(
#                 selector='//*[@id="ID"]/@value',
#                 field_name="platform_id",
#             )
#
#             # DOI
#             selector_model.add_field(
#                 selector='//li[@class="top-space"][contains(., "DOI")]',
#                 field_name="article_doi",
#             )
#
#             # CLC分类
#             selector_model.add_field(
#                 selector='//li[@class="top-space"][contains(., "分类号")]',
#                 field_name="clc_codes",
#             )
#
#             # 在线公开时间
#             selector_model.add_field(
#                 selector='//li[@class="top-space"][contains(., "在线公开时间")]',
#                 field_name="published_time",
#             )
#
#             # 年份,卷(期)
#             selector_model.add_field(
#                 selector=".top-tip a:nth-child(2)",
#                 field_name="published_info",
#                 selector_type="css"
#             )
#
#             # 页码
#             selector_model.add_field(
#                 selector='//p[@class="total-inform"]//span[contains(., "页码")]',
#                 field_name="page_info",
#             )
#
#             # 处理作者机构信息
#             author_result = self._parse_author_institutions(response)
#
#             # 执行提取
#             extract_result = selector_model.execute_non_yield(response=response)
#             if not extract_result["result"]:
#                 raise ValueError(extract_result["msg"])
#             extract_result = extract_result["data"]
#
#             # 处理参考文献
#             # references_buf = await self._parse_references_list(page=page)
#
#             # 整理关键词
#             article_keywords = []
#             for article_key in extract_result["article_keywords"]:
#                 tmp_key = en_cn_correction(
#                     text_list=[
#                         str(article_key).rstrip('；;').strip()
#                     ],
#                     chs_field_name="keyword_chs",
#                     eng_field_name="keyword_eng",
#                 )
#                 article_keywords.append(tmp_key)
#
#             # 整理资助基金
#             article_grant = []
#             i = 1
#             for grant_item in extract_result["article_grant"]:
#                 grant_string = grant_item.rstrip("~；;").strip()
#                 article_grant.append({
#                     "grant_name": grant_string,
#                     "grant_order": i,
#                 })
#                 i += 1
#
#                 # 负向前瞻和负后顾
#                 # 括号内的不切割
#                 # grant_result = re.split(r'[;；、](?![^（(]*[)）])', grant_string)
#                 # grant_platform_id, grant_name = self._process_grant_string(grant_item)
#
#                 # # 组织基金数据
#                 # for item in grant_result:
#                 #     # 记录数据
#                 #     article_grant.append({
#                 #         "grant_name": item,
#                 #         "grant_order": i,
#                 #     })
#                 #     i += 1
#
#             # 整理分类号
#             clc_codes = extract_result["clc_codes"] or ""
#             clc_codes = re.sub(r'^.*分类号[：:]', '', clc_codes).strip()  # 使用正则表达式匹配并移除开头部分
#             clc_codes = None if clc_codes == "+" else clc_codes  # 去除纯+号的分类号
#             if clc_codes:
#                 clc_codes = clc_codes.split(';')
#                 clc_codes = [x.strip() for x in clc_codes if x.strip()]
#
#             # 整理页码
#             page_info = extract_result["page_info"] or ""
#             page_info = re.sub(r'^.*页码[：:]', '', page_info).strip()  # 使用正则表达式匹配并移除开头部分
#             if not page_info:
#                 # 若不存在页码，则选取期刊详情页中的页码
#                 page_info = article_info.get("article_page")
#
#             # 提取年份,卷(期)中的卷
#             article_year = article_info.get("article_year", "")
#             published_volume = extract_result["published_info"] or ""
#             tmp_published_info = self.extract_volume_issue(published_volume)
#             if tmp_published_info:
#                 # 匹配成功
#                 issue_info = tmp_published_info["issue"]
#                 published_volume = tmp_published_info["volume"]
#             else:
#                 # 匹配失败，备选方案
#                 issue_info = article_info.get("issue_info", "")
#                 published_volume = (published_volume
#                                     .replace(article_year, "")
#                                     .replace(f"({issue_info})", "")
#                                     .replace(",", "")
#                                     .replace("，", "")
#                                     .strip())
#
#             # 整理在线公开时间
#             published_time = article_year
#             tmp_published_time = extract_result["published_time"] or ""
#             cleaned_text = re.sub(r'^.*在线公开时间[：:]', '', tmp_published_time)  # 使用正则表达式匹配并移除开头部分
#             match_result = re.search(r'[\d\-:\s]+', cleaned_text)  # 匹配连续的数字、-和:组成的部分
#             if match_result:
#                 published_time = match_result.group().strip()
#
#             # 确定发表时间精度
#             if len(published_time) <= 4:
#                 # 年
#                 published_time_precision = ARTICLE_PUBLISHED_TIME_PRECISION["Y"]
#             elif len(published_time) <= 7:
#                 # 月
#                 published_time_precision = ARTICLE_PUBLISHED_TIME_PRECISION["M"]
#             else:
#                 # 日
#                 published_time_precision = ARTICLE_PUBLISHED_TIME_PRECISION["D"]
#
#             # 整理DOI
#             article_doi = extract_result["article_doi"] or ""
#             article_doi = re.sub(r'^.*DOI[：:]', '', article_doi).strip()  # 使用正则表达式匹配并移除开头部分
#             article_doi = article_doi or None
#
#             # 整理文献标题
#             article_name = en_cn_correction(
#                 text_list=[
#                     article_info.get("title_text")
#                 ],
#                 chs_field_name="article_cn_name",
#                 eng_field_name="article_en_name",
#             )
#
#             # 整理文献类型
#             article_type = {}
#             if article_info.get("article_type"):
#                 article_type = en_cn_correction(
#                     text_list=[
#                         article_info.get("article_type")
#                     ],
#                     chs_field_name="chi",
#                     eng_field_name="eng",
#                 )
#
#             # 整理文献摘要
#             tmp_abstract = extract_result.get("article_abstract") or ""
#             tmp_abstract = tmp_abstract.removeprefix("<正>").strip()
#             article_abstract = en_cn_correction(
#                 text_list=[
#                     tmp_abstract
#                 ],
#                 chs_field_name="chs_info",
#                 eng_field_name="eng_info",
#             )
#
#             yield CnArticleItem(
#                 article_en_name=article_name["article_en_name"],
#                 article_cn_name=article_name["article_cn_name"],
#                 article_doi=article_doi,
#                 type_name=article_type,
#                 journal_info={
#                     "journal_issn": journal_info.get("journal_issn"),
#                     "journal_name": journal_info.get("journal_name"),
#                 },
#                 article_year=article_year,
#                 article_language=article_info.get("title_text"),
#                 published_time=published_time,
#                 published_time_precision=published_time_precision,
#                 online_date=published_time,
#                 volume=published_volume,
#                 issue=issue_info,
#                 page=page_info,
#                 clc_codes=clc_codes,
#                 platform_source=self.platform_code,
#                 platform_id=extract_result["platform_id"],
#                 article_abstract={
#                     "chs_info": [
#                         {
#                             "section_attr": ARTICLE_ABSTRACT_SECTION_ATTR["abstract"],
#                             "section_text": article_abstract["chs_info"]
#                         }
#                     ] if article_abstract["chs_info"] else [],
#                     "eng_info": [
#                         {
#                             "section_attr": ARTICLE_ABSTRACT_SECTION_ATTR["abstract"],
#                             "section_text": article_abstract["eng_info"]
#                         }
#                     ] if article_abstract["eng_info"] else [],
#                 },
#                 # article_reference=references_buf,
#                 article_reference=[],
#                 article_keywords=article_keywords,
#                 article_grant=article_grant,
#                 article_author=author_result,
#                 original_html=response.text,
#                 page_url=response.url,
#             )
#         finally:
#             # 释放页面及信号量
#             await page.close()
#
#     async def _process_years(self, page: Page, crawling_years_range: set):
#         """
#         异步生成器：遍历年份侧边栏，逐个处理年份
#         :author Mabin
#         :param page:Playwright 页面对象
#         :param crawling_years_range:需要爬取的年份集合
#         :return:
#         """
#         while True:
#             # 获取所有可见的年份项
#             year_list = await page.locator('.yearissuepage dl').filter(visible=True).all()
#             for year_item in year_list:
#                 # 提取年份文本
#                 year_text = (await year_item.locator('dt').inner_text()).strip()
#
#                 # 如果年份不在目标范围内，则跳过
#                 if year_text not in crawling_years_range:
#                     continue
#
#                 # 点击年份项以展开期列表
#                 await PlaywrightTools.safe_click_spa(
#                     page=page,
#                     locator_obj=year_item,
#                     click_timeout=self.click_timeout
#                 )
#
#                 # 处理该年份下的所有期
#                 async for link in self._process_issues(page, year_item, year_text):
#                     yield link
#
#             # 点击年份侧边栏的下一页按钮
#             next_sign = await PlaywrightTools.safe_click_spa(
#                 page=page,
#                 selector='.page-list .next',
#                 should_retry=False,
#                 click_timeout=self.click_timeout
#             )
#             if not next_sign:
#                 # 如果没有下一页，则退出循环
#                 break
#
#     async def _process_issues(self, page: Page, year_item, year_text: str):
#         """
#         异步生成器：处理某个年份下的所有期
#         :author Mabin
#         :param page:Playwright 页面对象
#         :param year_item:当前年份的定位器对象
#         :param year_text:当前年份文本
#         :return:
#         """
#         # 获取该年份下所有可见的期链接
#         issue_locator = await year_item.locator('dd a').filter(visible=True).all()
#
#         for issue_item in issue_locator:
#             # 点击期链接
#             await PlaywrightTools.safe_click_spa(
#                 page=page,
#                 locator_obj=issue_item,
#                 click_timeout=self.click_timeout
#             )
#
#             # 等待内容加载完成
#             locator = page.locator("#CataLogContent").filter(has_not_text="正在加载数据")
#             await locator.wait_for(timeout=self.network_timeout)
#
#             # 提取期号文本
#             issue_text = await issue_item.inner_text()
#             issue_text = issue_text.strip().lower().replace("no.", "")
#
#             # 迭代该期下的所有板块内容
#             async for link in self._process_blocks(page, year_text=year_text, issue_text=issue_text):
#                 yield link
#
#     async def _process_blocks(self, page: Page, year_text: str, issue_text: str):
#         """
#         异步生成器：处理当前页面下的所有板块
#         :author Mabin
#         :param page:Playwright 页面对象
#         :param year_text:当前年份文本
#         :param year_text:期号文本
#         :return:
#         """
#         while True:
#             # 选取板块列表（选取#CataLogContent下的dt或dd标签上一层的div）
#             block_locator = page.locator(
#                 "#CataLogContent dt, #CataLogContent dd"
#             ).locator("..")
#             await block_locator.first.wait_for()
#             block_list = await block_locator.all()
#
#             # 遍历各个板块
#             for block_item in block_list:
#                 # 获取板块标题
#                 try:
#                     block_title = await block_item.locator('dt').inner_text()
#                     block_title = block_title.strip() or None
#                 except:
#                     block_title = None
#
#                 # 获取板块下的所有文献列表
#                 literature_list = await block_item.locator('dd').all()
#                 for literature_item in literature_list:
#                     # 获取文献链接
#                     title_link = literature_item.locator('.name a')
#                     literature_url = await title_link.get_attribute('href')
#
#                     # 如果链接为空则跳过
#                     if not literature_url:
#                         continue
#
#                     # 文献标题保留sub、sup标签
#                     title_text = BaseSelectorComponent.get_sub_sup_text(await title_link.inner_html())
#
#                     # 页码
#                     page_locator = literature_item.locator('.company')
#                     page_info = await page_locator.inner_text()
#
#                     # 迭代返回
#                     yield {
#                         'article_title': title_text,
#                         'article_url': literature_url,
#                         'article_type': block_title,
#                         'article_year': year_text,
#                         'article_issue': issue_text,
#                         'article_page': page_info,
#                     }
#
#             # 点击文献列表的下一页按钮
#             next_sign = await PlaywrightTools.safe_click_spa(
#                 page=page,
#                 selector='.pagebox .next',
#                 should_retry=False,
#                 click_timeout=self.click_timeout
#             )
#             if not next_sign:
#                 # 如果没有下一页，则退出循环
#                 break
#
#     def _parse_author_institutions(self, response: Response):
#         """
#         解析作者机构信息
#         :author Mabin
#         :param response:
#         :return:
#         """
#         # 提取机构信息
#         institutions = {}
#         default_index = None  # 机构默认索引
#         institution_spans = response.xpath('//h3[@class="author" and not(@id)]/span')
#         institution_spans = cast(Iterable[Selector], institution_spans)  # 显式声明类型
#         for span in institution_spans:
#             institution = BaseSelectorComponent.get_sub_sup_text(span.get())
#             if institution:
#                 # 提取机构名和编号（如"1.天津大学..."中的1）
#                 institution = institution.strip()
#                 number = institution.split('.')[0] if '.' in institution else default_index
#
#                 institutions[number] = '.'.join(institution.split('.')[1:]).strip() \
#                     if '.' in institution else institution
#
#         # 提取作者信息
#         authors = []
#         author_spans = response.xpath('//h3[@class="author" and @id="authorpart"]/span')
#         author_spans = cast(Iterable[Selector], author_spans)  # 显式声明类型
#         for span in author_spans:
#             name = span.xpath('.//a/text()').get()
#             if name:
#                 # 提取作者名和编号（如"蔡云帆1"中的1）
#                 name = name.strip()
#                 sup = span.xpath('.//sup/text()').get()
#                 author_code = span.xpath('.//input[@class="authorcode"]/@value').get()
#                 email = span.xpath('.//p[@class="authortip"]').getall()
#
#                 # 组织作者信息
#                 author_data = {
#                     'author_name': name.replace(sup, '') if sup else name,
#                     'co_first_author': CO_FIRST_AUTHOR["not_first"],  # CNKI目前已知不存在共同第一作者
#                     "corresponding_author": CORRESPONDING_AUTHOR["corp"] if email else CORRESPONDING_AUTHOR["not_corp"],
#                     "is_display": AUTHOR_IS_DISPLAY["display"],  # CNKI目前已知无法区分指南的机构作者信息
#                     "author_email": [],
#                     "platform_info": {
#                         "platform_id": author_code,
#                         "platform_code": self.platform_code,
#                     },
#                     "author_type": AUTHOR_TYPE["person"],
#                 }
#
#                 # 存在邮件
#                 if email:
#                     tmp_email = []
#                     for email_item in email:
#                         tmp_email.append(BaseSelectorComponent.get_sub_sup_text(email_item))
#                     author_data["author_email"] = tmp_email
#
#                 # 处理作者编号（可能包含逗号分隔的多个数字）
#                 numbers = []
#                 if sup:
#                     try:
#                         # 尝试分割逗号分隔的数字
#                         numbers = [num.strip() for num in sup.split(',') if num.strip().isdigit()]
#                     except (ValueError, AttributeError):
#                         pass
#
#                 # 组织机构数据
#                 unit_info = []
#                 for number in numbers:
#                     if number not in institutions:
#                         continue
#
#                     unit_info.append({
#                         "unit_name": institutions[number]
#                     })
#
#                 if not unit_info and institutions.get(default_index):
#                     # 存在不带有数字的机构信息，且当前作者不存在机构
#                     unit_info.append({
#                         "unit_name": institutions.get(default_index)
#                     })
#
#                 # 记录单位信息
#                 author_data["unit_info"] = unit_info
#
#                 # 记录完整数据
#                 authors.append(author_data)
#
#         if not authors and institutions:
#             # 没有作者，但存在机构，则将机构作为作者存储，并标记其为机构
#             for key, item in institutions.items():
#                 authors.append({
#                     "author_name": item,
#                     "co_first_author": CO_FIRST_AUTHOR["not_first"],
#                     "corresponding_author": CORRESPONDING_AUTHOR["not_corp"],
#                     "is_display": AUTHOR_IS_DISPLAY["not_display"],  # CNKI目前已知无法区分指南的机构作者信息
#                     "author_type": AUTHOR_TYPE["unit"],
#                     "unit_info": [
#                         {
#                             "unit_name": item
#                         }
#                     ]
#                 })
#
#         return authors
#
#     async def _parse_references_list(self, page: Page):
#         """
#         解析参考文献列表
#         :author Mabin
#         :param page:Playwright 页面对象
#         :return:
#         """
#         # 处理参考文献
#         references_list = await page.locator("#quoted-references > div").filter(visible=True).all()
#
#         # 遍历各参考文献各个类型
#         references_buf = []
#         for references_item in references_list:
#             # 判断是否存在.dbTitle元素
#             db_title_locator = references_item.locator(".dbTitle")
#             if not await db_title_locator.is_visible():
#                 # 不存在.dbTitle
#                 continue
#             db_title_text = await db_title_locator.inner_text()
#             db_title_text = db_title_text.split("共")[0].strip() or None  # 期刊、国际期刊、硕士、博士等等文献分类
#
#             while True:
#                 # 遍历文献列表
#                 article_locator = references_item.locator("li")
#                 article_list = await article_locator.all()
#
#                 # 遍历具体文献列表
#                 for article_item in article_list:
#                     # 文献引文
#                     ref_text = await article_item.inner_text()
#                     ref_text = re.sub(r'^\[\d+]\s*', '', ref_text.strip())
#
#                     # 文献标题
#                     ref_title = None
#                     ref_title_locator = article_item.locator(".document-title")
#                     if await ref_title_locator.count() > 0:
#                         # 存在链接标题
#                         ref_title = await ref_title_locator.inner_text()
#                         ref_title = ref_title.strip()
#
#                     references_buf.append({
#                         "citation": ref_text,
#                         "ref_title": ref_title,
#                         "categories": db_title_text,
#                     })
#
#                 # 点击下一页（期刊）
#                 next_element = await PlaywrightTools.safe_click_spa(
#                     page=page,
#                     locator_obj=references_item.locator("a.next"),
#                     click_timeout=self.click_timeout,
#                     should_retry=False,
#                 )
#                 if not next_element:
#                     break
#
#                 # 存在下一页（等待一段时间）
#                 await page.wait_for_timeout(self.breathing_timeout)
#
#                 # 处理滑块验证码
#                 slide_result = await PlaywrightTools.slide_verify(
#                     page=page,
#                     slider_selector=".canvas_slider",
#                     bg_canvas_selector="#canvas_wrap > div.canvas_wrap > canvas:nth-child(1)",
#                     gap_canvas_selector="#canvas_wrap > div.canvas_wrap > canvas:nth-child(2)",
#                     success_hidden_element="#canvas_wrap"
#                 )
#                 if not slide_result["result"]:
#                     raise Exception(slide_result["msg"])
#
#         return references_buf
#
#     async def solve_captcha(self, request: Request, response: Response):
#         """
#         处理验证码
#         :author Mabin
#         :param request:
#         :param response:
#         :return:
#         """
#         page = response.meta["playwright_page"]
#
#         # 检查页面是否包含特定文本
#         await page.wait_for_load_state(timeout=self.network_timeout, state="networkidle")
#         content = await page.content()
#         if "系统检测到您的访问行为异常" in content:
#             await self.simple_captcha_code(page)
#         else:
#             await PlaywrightTools.slide_verify(
#                 page=page,
#                 slider_selector=".verify-move-block",
#                 bg_base64_selector=".verify-img-panel img",
#                 gap_base64_selector=".verify-move-block img",
#             )
#
#         # 构造全新的Scrapy响应对象
#         return await self._organ_playwright_response(page=page, response=response)
#
#     @staticmethod
#     async def simple_captcha_code(page):
#         """
#         校验CNKI简单验证码
#         :author Mabin
#         :param page:Playwright页面对象
#         :return:
#         """
#         # 获取元素并计算left值
#         slide_x = await page.locator('.verify-gap').evaluate('el => parseFloat(getComputedStyle(el).left)')
#
#         # 滑动滑块
#         slider_result = await PlaywrightTools.mouse_move_slider(
#             page=page, slider_selector=".verify-left-bar", slide_distance=slide_x
#         )
#         if not slider_result["result"]:
#             raise ValueError(slider_result["msg"])
#
#         return page
#
#     @staticmethod
#     async def init_page(page, request):
#         """
#         请求前的动作
#         :author Mabin
#         :param page:
#         :param request:
#         :return:
#         """
#         await page.set_extra_http_headers({'Origin': 'https://navi.cnki.net'})
#
#     @staticmethod
#     def generate_unique_key(doc: dict) -> str:
#         """
#         组织历史数据判重键
#         :author Mabin
#         :param doc:文档信息
#         :return:
#         """
#         tmp_str = (f"{doc.get('journal_info', {}).get('journal_issn')}"
#                    f"-{doc.get('article_year')}"
#                    f"-{doc.get('issue')}")
#
#         # 加入文献名称
#         if doc.get("article_en_name"):
#             tmp_str += f'-{doc.get("article_en_name")}'
#         elif doc.get("article_cn_name"):
#             tmp_str += f'-{doc.get("article_cn_name")}'
#
#         return tmp_str
#
#     @staticmethod
#     def _process_grant_string(grant_string):
#         """
#         处理资助项目字符串，提取括号中的批准号信息。
#
#         该函数的主要功能包括：
#         1. 清理字符串首尾的特定字符
#         2. 提取所有括号内的内容
#         3. 筛选出符合条件的括号（不含中文或包含"批准号:"）
#         4. 返回最后一个符合条件的括号内容和清理后的字符串
#         :author Mabin
#         :param grant_string:原始的资助项目字符串
#         :return:
#         """
#         # 1) 去除字符串首尾的波浪号、分号等特定字符，并进行常规空白字符清理
#         grant_string = grant_string.strip("~；;").strip()
#
#         # 2) 使用正则表达式匹配所有括号内容，支持中英文括号
#         #    pattern: 匹配(内容)或（内容）格式的括号
#         #    matches: 存储匹配结果，每个元素为(括号内内容, 起始位置, 结束位置)
#         pattern = re.compile(r'[(（]([^)]*)[)）]')
#         matches = []
#         for m in pattern.finditer(grant_string):
#             inner = m.group(1)  # 获取括号内的内容
#             matches.append((inner, m.start(), m.end()))
#
#         # 3) 筛选出符合条件的候选括号：
#         #    条件1：包含"批准号:"关键字
#         #    条件2：完全不包含中文字符
#         #    满足任一条件的括号都被视为候选
#         candidates = []
#         for inner, start, end in matches:
#             if "批准号:" in inner or not any('\u4e00' <= ch <= '\u9fff' for ch in inner):
#                 candidates.append((inner, start, end))
#
#         # 如果没有找到符合条件的括号，返回空字符串和原字符串
#         if not candidates:
#             return None, grant_string.strip()
#
#         # 4) 取最后一个符合条件的括号内容
#         last_inner, start, end = candidates[-1]
#
#         # 5) 从原字符串中移除该括号及其内容，得到清理后的字符串
#         s_removed = grant_string[:start] + grant_string[end:]
#
#         # 6) 返回批准号内容（去除"批准号:"前缀）和清理后的字符串
#         return last_inner.replace("批准号:", ""), s_removed.strip()
#
#     @staticmethod
#     def extract_volume_issue(text):
#         """
#         提取字符串中的卷、期，字符串示例：2025 ,68 (02) ，其结构为年份,卷(期)
#         :author Mabin
#         :param text:待提取文本
#         :return:
#         """
#         # 找逗号
#         comma_index = text.find(',')
#         if comma_index == -1:
#             return None
#
#         # 找括号
#         open_paren = text.find('(', comma_index)
#         close_paren = text.find(')', open_paren)
#         if open_paren == -1 or close_paren == -1:
#             # 尝试方括号
#             open_bracket = text.find('[', comma_index)
#             close_bracket = text.find(']', open_bracket)
#             if open_bracket == -1 or close_bracket == -1:
#                 return None
#             open_paren, close_paren = open_bracket, close_bracket
#
#         # 提取卷和期
#         volume = text[comma_index + 1:open_paren].strip()
#         issue = text[open_paren + 1:close_paren].strip()
#         return {'volume': volume, 'issue': issue}
