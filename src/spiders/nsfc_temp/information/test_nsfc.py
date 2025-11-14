# -*- coding: utf-8 -*-

"""
# @Time    : 2025/7/23 12:49
# @User  : Mabin
# @Description  :
"""
import scrapy
from src.spiders.base_spider import BaseSpider
from urllib.parse import urljoin
from src.component.base_selector_component import BaseSelectorComponent


class TestNsfcSpider(BaseSpider):
    name = 'nsfc_laws_temp'
    allowed_domains = ['www.nsfc.gov.cn']
    base_url = "https://www.nsfc.gov.cn"  # 网站根路径

    def start_requests(self):
        """
        入口请求：法律法规以及列表首页
        """
        url = urljoin(self.base_url, '/publish/portal0/tab609/')
        yield scrapy.Request(
            url, callback=self.parse_guide_list, dont_filter=True
        )

    def parse_guide_list(self, response):
        """
        解析法律法规一级列表页
        :param response:
        :return:
        """
        selector_model = BaseSelectorComponent()

        # 定义公共父选择器
        base_name = "list_menu"
        base_selector = "/html/body/form/div[4]/div[1]/div[4]//tr/td/div/ul/li"

        # 标题
        selector_model.add_field(
            selector=r".//a//text()",
            field_name="title",
            base_name=base_name,
            base_selector=base_selector,
        )

        # 链接
        selector_model.add_field(
            selector=r".//a/@href",
            field_name="url",
            field_type="href",
            base_name=base_name,
            base_selector=base_selector,
            callback=self.parse_detail_list
        )

        # 执行回调
        yield from selector_model.execute(response=response)
        print(f"parse_guide_list函数提取结果<{response.url}>：")
        print(selector_model.get_all_field())

    def parse_detail_list(self, response):
        """
        解析子列表，获取详细链接与翻页
        :param response:
        :return:
        """
        selector_model = BaseSelectorComponent()

        # 定义公共父选择器
        base_name = "detail_list"
        base_selector = "/html/body//tr/td/ul/ul/li"

        # 当前菜单标题
        selector_model.add_field(
            selector=r"/html//tr/td/div/ul/li[3]/a//text()",
            field_name="level",
        )
        # 下一页
        selector_model.add_field(
            selector=r'//a[text()="下一页"]/@href',
            field_name="next_url",
        )

        # 卡片信息-标题
        selector_model.add_field(
            selector=r".//span[2]//text()",
            field_name="name",
            base_name=base_name,
            base_selector=base_selector,
        )
        selector_model.add_field(
            selector=r".//span[2]/a/@href",
            field_name="url",
            field_type="href",
            base_name=base_name,
            base_selector=base_selector,
            callback=self.parse_detail,
            callback_parameter={
                "meta": {
                    "title": response.meta.get("title"),
                    "url": response.meta.get("url"),
                }
            }
        )
        selector_model.add_field(
            selector=r".//span[3]",
            field_name="date",
            base_name=base_name,
            base_selector=base_selector,
        )

        # 执行回调
        yield from selector_model.execute(response=response)
        print(f"parse_detail_list函数提取结果<{response.url}>：")
        print(selector_model.get_all_field())

    def parse_detail(self, response):
        """
        解析公告详情页
        :param response:
        :return:
        """
        selector_model = BaseSelectorComponent()

        selector_model.add_field(
            selector=r"div.title_xilan",
            field_name="title_xilan",
            selector_type="css"
        )
        selector_model.add_field(
            selector=r"div.line_xilan",
            field_name="line_xilan",
            selector_type="css"
        )
        selector_model.add_field(
            selector=r"div.content_xilan",
            field_name="content_xilan",
            selector_type="css"
        )

        # 执行回调
        yield from selector_model.execute(
            response=response,
            # scrapy_item=InformationItem
        )

        # 打印所有字段
        print(f"parse_detail函数提取结果<{response.url}>：")
        print(selector_model.get_all_field())
        print(response.meta)
