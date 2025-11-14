# import logging
# from urllib.parse import urljoin
#
# import scrapy
# from src.items.information_item import InformationItem
# from src.spiders.nsfc_temp.nsfc import NSFCSpiders
# from src.utils.mixin_utils import JsonXPathExtractionStrategy, JsonCssExtractionStrategy
#
#
# class NsfcProjectGuideSpider(NSFCSpiders):
#     """
#     国家自然科学基金项目指南爬虫
#     """
#     name = 'nsfc_project_guide'
#     start_path = '/publish/portal0/tab626/module1550/more.htm'
#     target_table = 'gzr_guideproject_list'
#
#     #: 列表页数据提取 Schema
#     GUIDE_LIST_SCHEMA = {
#         'baseField': [],
#         'baseSelector': '/html/body/form/div[4]/div[1]/div[4]//tr/td/div/ul/li',
#         'fields': [
#             {'name': 'title', 'type': 'text', 'selector': './/a'},
#             {'name': 'url', 'type': 'attribute', 'selector': './/a', 'attribute': 'href'},
#         ],
#     }
#
#     #: 子列表（详细页链接）提取 Schema
#     DETAIL_LIST_SCHEMA = {
#         'baseField': [
#             {'name': 'level', 'type': 'text', 'selector': '/html//tr/td/div/ul/li[3]/a'},
#             {'name': 'next_url', 'type': 'attribute', 'selector': '//a[text()="下一页"]', 'attribute': 'href'},
#         ],
#         'baseSelector': '/html/body//tr/td/ul/ul/li',
#         'fields': [
#             {'name': 'name', 'type': 'text', 'selector': './/span[2]'},
#             {'name': 'url', 'type': 'attribute', 'selector': './/span[2]/a', 'attribute': 'href'},
#             {'name': 'date', 'type': 'text', 'selector': './/span[3]'},
#         ],
#     }
#
#     def start_requests(self):
#         """
#         入口请求：项目指南列表首页
#         """
#         url = urljoin(self.base_url, self.start_path)
#         yield scrapy.Request(
#             url, callback=self.parse_guide_list, meta={'table': self.target_table}, dont_filter=True
#         )
#
#     def parse_guide_list(self, response):
#         """
#         解析项目指南列表页
#         """
#         schema = self.GUIDE_LIST_SCHEMA.copy()
#         extractor = JsonXPathExtractionStrategy(schema, html_content=response.text)
#         base = extractor.get_base_field()  # 获取基础固定爬虫信息
#
#         for rec in extractor.get_field(base_field=base):
#             guide_url = self._abs_url(rec['url'])
#             yield scrapy.Request(
#                 guide_url, callback=self.parse_detail_list, meta={'item': rec}
#             )
#
#     def parse_detail_list(self, response):
#         """
#         解析子列表，获取详细链接与翻页
#         """
#         schema = self.DETAIL_LIST_SCHEMA.copy()
#         extractor = JsonXPathExtractionStrategy(schema, html_content=response.text)
#         base_field = extractor.get_base_field()  # 获取基础固定爬虫信息
#
#         for item in extractor.get_field(base_field=base_field):
#             detail_url = self._abs_url(item['url'])
#             merged = {**response.meta['item'], **item}
#             yield scrapy.Request(
#                 detail_url, callback=self.parse_detail, meta={'item': merged}
#             )
#
#         next_href = base_field.get('next_url')
#         if next_href:
#             next_url = self._abs_url(next_href)
#             logging.info(f"请求下一页：{next_url}")
#             yield scrapy.Request(next_url, callback=self.parse_detail_list, meta=response.meta)
#
#     def parse_detail(self, response):
#         """解析公告详情页，目前仅返回 meta 信息"""
#         schema = self.NOTICE_SCHEMA.copy()
#         extractor = JsonCssExtractionStrategy(schema, html_content=response.text)
#         content = extractor.get_base_field()  # 获取基础固定爬虫信息
#         yield response.meta['item']
