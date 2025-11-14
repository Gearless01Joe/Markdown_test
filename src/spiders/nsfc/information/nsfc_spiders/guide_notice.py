#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
# @Time    : 2025-02-20
# @User  : Tlg
# @Description  :爬取指南通知
"""
from urllib.parse import urljoin
import scrapy
import logging

from src.items.information_item import InformationItem

from src.spiders.nsfc.information.nsfc import NSFCSpiders


class GuideNoticeSpiders(NSFCSpiders):
    """
    爬虫类，继承自NSFCSpiders，用于抓取指南通知
    开发者：通力嘎
    日期：2025-02-20
    """
    name = 'guide_notice'
    list_url = "publish/portal0/tab434/module1146/more.htm"  # 指南通知路径
    target_table = "gzr_notices_list"  # 数据库表名

    def start_requests(self):
        """初始请求入口"""
        yield scrapy.Request(
            url=urljoin(self.base_url, self.list_url),
            callback=self.parse_notice_lists,
            meta={'table': self.target_table},
            dont_filter=True
        )

    def parse_notice_lists(self, response):
        """解析列表页"""
        yield from self._parse_common_list(
            response,
            self.parse_notice_details,
            response.meta.get('table')
        )

    def parse_notice_details(self, response):
        """
        解析指南通告详情页，提取详细信息及附件
        开发者：通力嘎
        日期：2025-02-20
        """
        try:
            item = InformationItem()
            item['resource_label']='指南通告'
            item['main_site'] = self.base_url
            fields = self._parse_basic_fields(response)  # 解析详细页面
            item.update(fields)  # 转换格式
            if fields.get('info_html'):
                item['link_data'] = self._extract_attachments(fields.get('info_html'), response.url)
                item['file_urls']= list(set([data['url'] for data in item['link_data']]))
            item['info_html']=item['info_html'].get()
            yield item
        except Exception as e:
            logging.error(f"parse_notice_details 详情页面解析失败，链接：{response.url}, {e}")
