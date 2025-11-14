#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# @Time    : 2025-02-20
# @User  : Tlg
# @Description  :爬取项目指南
"""
from urllib.parse import urljoin
import scrapy
import logging

from src.items.information_item import InformationItem
from src.spiders.nsfc.information.nsfc import NSFCSpiders

class ProjectGuideSpiders(NSFCSpiders):
    """
    爬虫类，继承自 NSFCSpiders，用于抓取爬取项目指南
    开发者：通力嘎
    日期：2025-02-20
    """
    name = 'project_guide'
    list_url = "/publish/portal0/tab626/module1550/more.htm"  # 项目指南路径
    target_table = "gzr_guideproject_list"  # 数据库表名

    def start_requests(self):
        """初始请求入口"""
        yield scrapy.Request(
            url=urljoin(self.base_url, self.list_url),
            callback=self.parse_project_lists,
            meta={'table': self.target_table},
            dont_filter=True
        )

    # ----------------- 各类型页面解析 -----------------

    def parse_project_lists(self, response):
        """
        解析项目指南（法律法规一级标签页），并根据标题跳转到对应列表页
        开发者：通力嘎
        日期：2025-02-20
        """
        try:
            ql_area = response.css('[class="ql"]')
            if not ql_area:
                logging.error(f"parse_project_lists 未找到 ql 区域，链接：{response.url}")
                return

            for a in ql_area.css('a'):
                url = urljoin(self.base_url, a.css('::attr(href)').get())
                title = a.css('::text').get().strip()
                callback = self.parse_project_details
                if callback:
                    yield scrapy.Request(url=url, callback=callback,meta={'table': response.meta.get('table')})
                else:
                    logging.warning(f"parse_project_lists 未匹配到标题对应的回调函数：{title}")
        except Exception as e:
            logging.error(f"parse_project_lists 页面解析失败，链接：{response.url}, {e}")

    def parse_project_details(self, response):
        """
        解析项目指南列表页，进入详情页解析
        开发者：通力嘎
        日期：2025-02-20
        """
        yield from self._parse_common_list(response, self.parse_project_one_details,response.meta.get('table'))

    def parse_project_one_details(self, response):
        """
        解析项目指南详情页，提取详细信息及附件
        开发者：通力嘎
        日期：2025-02-20
        """
        try:
            item = InformationItem()
            item['resource_label'] = '项目指南'
            item['main_site'] = self.base_url
            fields = self._parse_basic_fields(response)  # 解析详细信息
            item.update(fields)
            if fields.get('info_html'):
                item['link_data'] = self._extract_attachments(fields.get('info_html'), response.url)
                item['file_urls']= list(set([data['url'] for data in item['link_data']]))
            item['info_html'] = item['info_html'].get()
            yield item
        except Exception as e:
            logging.error(f"parse_project_one_details 方法错误，链接：{response.url}, {e}")
