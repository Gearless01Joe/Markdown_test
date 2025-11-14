# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
#
# """
# :Created: 2025-02-20
# :Author: Tlg
# :Description: 爬取国家自然科学基金委员会（NSFC）指南通知信息
# """
#
# import logging
# from urllib.parse import urljoin
#
# import scrapy
# from src.items.information_item import InformationItem
# from src.spiders.nsfc_temp.nsfc import NSFCSpiders
# from src.utils.mixin_utils import JsonXPathExtractionStrategy, JsonCssExtractionStrategy
#
#
# class NsfcGuideNoticeSpider(NSFCSpiders):
#     """国家自然科学基金指南通知爬虫"""
#     name = 'nsfc_guide_notice'
#
#     start_path = 'publish/portal0/tab434/module1146/more.htm'
#     target_table = 'gzr_notices_list'
#
#     # 列表页数据提取 schema
#     NOTICE_LIST_SCHEMA = {
#         'baseField': [
#             {
#                 'name': 'next_page',
#                 'type': 'attribute',
#                 'selector': '//td[1]/a[text()="下一页"]',
#                 'attribute': 'href',
#             },
#         ],
#         'baseSelector': '/html/body//tr/td/ul/ul/li',
#         'fields': [
#             {
#                 'name': 'title',
#                 'type': 'text',
#                 'selector': './/span[2]',
#             },
#             {
#                 'name': 'url',
#                 'type': 'attribute',
#                 'selector': './/span[2]/a',
#                 'attribute': 'href',
#             },
#             {'name': 'date', 'type': 'text', 'selector': './/span[3]'},
#         ],
#     }
#
#     def start_requests(self):
#         """入口请求：指南通知列表首页"""
#         first_page = urljoin(self.base_url, self.start_path)
#         yield scrapy.Request(
#             first_page,
#             callback=self.parse_list,
#             meta={'table': self.target_table},
#             dont_filter=True
#         )
#
#     def parse_list(self, response):
#         """解析通知列表页，并翻页"""
#         schema = self.NOTICE_LIST_SCHEMA.copy()
#         extractor = JsonXPathExtractionStrategy(schema, html_content=response.text)
#
#         base_info = extractor.get_base_field()  # 获取基础固定爬虫信息
#         for record in extractor.get_field(base_field=base_info):
#             detail_url = self._abs_url(record['url'])
#             yield scrapy.Request(
#                 detail_url,
#                 callback=self.parse_detail,
#                 meta={'item': record}
#             )
#
#         next_href = base_info.get('next_page')
#         if next_href:
#             next_url = self._abs_url(next_href)
#             logging.info(f'请求下一页：{next_url}')
#             yield scrapy.Request(next_url, callback=self.parse_list)
#
#     def parse_detail(self, response):
#         """解析公告详情页，目前仅返回 meta 信息"""
#         schema = self.NOTICE_SCHEMA.copy()
#
#         extractor = JsonCssExtractionStrategy(schema, html_content=response.text)
#         content = extractor.get_base_field()
#         yield response.meta['item']
