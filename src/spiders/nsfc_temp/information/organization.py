import logging
from urllib.parse import urljoin
import scrapy

from src.spiders.nsfc_temp.nsfc import NSFCSpiders
from src.utils.mixin_utils import *


class NsfcOrganizationSpider(NSFCSpiders):
    """国家自然科学基金——组织结构通知公告爬虫"""
    name = 'nsfc_organization'
    start_path = '/publish/portal0/jgsz/04/'
    target_table = 'gzr_organization_list'

    # 一级列表页面（机构列表）
    ORG_LIST_SCHEMA = {
        'baseSelector': '/html/body/form/div[4]//tr/td[5]/div',
        'fields': [
            {'name': 'institution_name', 'type': 'text', 'selector': './/a'},
            {'name': 'url', 'type': 'attribute', 'selector': './/a', 'attribute': 'href'},
        ]
    }

    # 二级列表页面（机构下的“通知公告”入口）
    NOTICE_ENTRY_SCHEMA = {
        'baseSelector': '',  # 不使用列表项，直接定位“通知公告”
        'baseField': [
            {'name': 'url', 'type': 'attribute', 'selector': '//a[text()="通知公告"]', 'attribute': 'href'},
        ]
    }

    # 通知公告分页列表
    NOTICE_LIST_SCHEMA = {
        'baseSelector': '/html/body/form/div[4]/div[2]/div/div[2]//li',
        'baseField': [
            {'name': 'next_url', 'type': 'attribute', 'selector': '//a[text()="下一页"]', 'attribute': 'href'},
        ],
        'fields': [
            {'name': 'list_title', 'type': 'text', 'selector': './/a'},
            {'name': 'url', 'type': 'attribute', 'selector': './/a', 'attribute': 'href'},
            {'name': 'date', 'type': 'text', 'selector': './/span[3]'},
        ]
    }

    def start_requests(self):
        """爬虫入口，抓取机构列表首页"""
        url = urljoin(self.base_url, self.start_path)
        yield scrapy.Request(url, callback=self.parse_org_list, meta={'table': self.target_table}, dont_filter=True)

    def parse_org_list(self, response):
        """解析机构列表页，进入各机构的“通知公告”入口"""
        schema = self.ORG_LIST_SCHEMA.copy()
        schema['fields_callback_function'] = self._filter_academy
        extractor = JsonXPathExtractionStrategy(schema, html_content=response.text)

        for inst in extractor.get_field():
            yield scrapy.Request(
                url=inst['url'], callback=self.parse_notice_entry, meta={'org': inst}
            )

    def parse_notice_entry(self, response):
        """解析机构详情页，定位到“通知公告”链接"""
        schema = self.NOTICE_ENTRY_SCHEMA.copy()
        extractor = JsonXPathExtractionStrategy(schema, html_content=response.text)
        entry = extractor.get_base_field()  # 获取基础固定爬虫信息

        yield scrapy.Request(
            url=self._abs_url(entry['url']), callback=self.parse_notice_list, meta={'org': response.meta['org']}
        )

    def parse_notice_list(self, response):
        """解析通知公告列表（含分页），抓取详情链接并翻页"""
        schema = self.NOTICE_LIST_SCHEMA.copy()
        extractor = JsonXPathExtractionStrategy(schema, html_content=response.text)

        base_field = extractor.get_base_field()  # 获取基础固定爬虫信息
        for notice in extractor.get_field(base_field=base_field):
            meta = {**response.meta['org'], **notice}
            yield scrapy.Request(url=self._abs_url(notice['url']), callback=self.parse_detail, meta={'item': meta})

        next_url = base_field.get('next_url')
        if next_url:
            next_page = urljoin(self.base_url, next_url)
            logging.info(f'请求下一页：{next_page}')
            yield scrapy.Request(url=next_page, callback=self.parse_notice_list, meta=response.meta)

    def parse_detail(self, response):
        """解析公告详情页，目前仅返回 meta 信息"""
        schema = self.NOTICE_SCHEMA.copy()

        extractor = JsonCssExtractionStrategy(schema, html_content=response.text)
        content = extractor.get_base_field()  # 获取基础固定爬虫信息
        yield response.meta['item']

    # ——— 私有工具方法 ———

    def _filter_academy(self, item):
        """只保留含“学部”的机构，并补全 URL"""
        if '学部' in item.get('institution_name', ''):
            item['url'] = self._abs_url(item['url'])
            return item
