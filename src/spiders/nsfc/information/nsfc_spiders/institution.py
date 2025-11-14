#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
# @Time    : 2025-02-20
# @User  : Tlg
# @Description  :爬取资助成果
"""
from urllib.parse import urljoin
import scrapy
import logging

from src.items.information_item import InformationItem
from src.spiders.nsfc.information.nsfc import NSFCSpiders

class InstitutionSpiders(NSFCSpiders):
    """
    爬虫类，继承自NSFCSpiders，用于抓取资助成果
    开发者：通力嘎
    日期：2025-02-20
    """

    name = 'institution'
    list_url = "/publish/portal0/jgsz/04"  # 资助成果路径
    target_table = "gzr_institution_list"  # 数据库表名

    def start_requests(self):
        """初始请求入口"""
        yield scrapy.Request(
            url=urljoin(self.base_url, self.list_url),
            callback=self.parse_institution_lists,
            meta={'table': self.target_table},
            dont_filter=True
        )

    # ----------------- 各类型页面解析 -----------------
    def parse_institution_lists(self, response):
        """
        第一个请求的是《机构设置》然后在跳转学部
        解析资助成果机构学部列表页，提取各学部链接，进入具体学部详情页
        开发者：通力嘎
        日期：2025-02-20
        """
        try:
            top = response.css("[valign='top']")
            if not top:
                logging.error(f"parse_institution_lists 未找到 top 元素，链接：{response.url}")
                return

            for a in top.css('a'):
                if "学部" in a.css("::text").get():  # 提取各个学部链接并跳转
                    url = urljoin(self.base_url, a.attrib['href'])
                    yield scrapy.Request(url=url, callback=self.parse_one_institution_lists,
                                         meta={'table': response.meta.get('table')})
        except Exception as e:
            logging.error(f"parse_institution_lists 方法错误，链接：{response.url}, {e}")

    def parse_one_institution_lists(self, response):
        """
        第二次跳转到资助成果
        解析具体学部页面，提取“资助成果”链接进入下一步
        开发者：通力嘎
        日期：2025-02-20
        """
        try:
            top = response.css("[class='ql']")
            if not top:
                logging.error(f"parse_one_institution_lists 未找到 ql 元素，链接：{response.url}")
                return

            for a in top.css('a'):
                if "资助成果" in a.css("::text").get():#查找资助成果专栏
                    url = urljoin(self.base_url, a.attrib['href'])
                    yield scrapy.Request(url=url, callback=self.parse_institution_lists_data,
                                         meta={'table': response.meta.get('table')})
                    break
        except Exception as e:
            logging.error(f"parse_one_institution_lists 方法错误，链接：{response.url}, {e}")

    def parse_institution_lists_data(self, response):
        """
        解析机构资助成果列表页，并调用详情页解析函数
        开发者：通力嘎
        日期：2025-02-20
        """
        yield from self._parse_common_list(response, self.parse_institution_details, response.meta.get('table'))

    def parse_institution_details(self, response):
        """
        解析机构资助成果详情页，提取数据和图片链接
        开发者：通力嘎
        日期：2025-02-20
        """
        try:
            item = InformationItem()
            item['resource_label'] = '资助成果'
            item['main_site'] = self.base_url
            fields = self._parse_basic_fields(response)  # 解析详细页面
            item.update(fields)  # 处理字典
            if fields.get('info_html'):
                item['link_data'] = self._extract_images(fields.get('info_html'))

                item['file_urls'] =list(set([data['url'] for data in item['link_data']]))
            item['info_html'] = item['info_html'].get()
            yield item
        except Exception as e:
            logging.error(f"parse_institution_details 详情页面解析失败，链接：{response.url}, {e}")
