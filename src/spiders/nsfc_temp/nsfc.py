# -*- coding: utf-8 -*-
"""
# @Time    : 2025-03-10
# @User  : Tlg
# @Description  :爬取国家自然科学基金相关信息主类，子类继承并使用公共方法
"""

from urllib.parse import urljoin
import scrapy


def detail_content(item):
    if item and item.get('title_xilan'):
        item['title_xilan'] = item.get('title_xilan')
        if item.get('line_xilan'):
            item['line_xilan'] = item.get('line_xilan')[:200]
        if item.get('content_xilan'):
            item['content_xilan'] = item.get('content_xilan')[:200]
        print(item)
        return item


class NSFCSpiders(scrapy.Spider):
    """
    开发者：通力嘎
    日期：2025-03-10
    """
    allowed_domains = ['www.nsfc.gov.cn']
    base_url = "https://www.nsfc.gov.cn"  # 网站根路径

    name = "nsfc_temp"
    # custom_settings = {
    #     'ITEM_PIPELINES': {
    #         'src.pipelines.storage.information_storage_pipeline.InformationStoragePipeline': 300,  # 数据库传输管道
    #         'src.pipelines.file_download_pipeline.FileDownloadPipeline': 90,  # 文件下载管道
    #         'src.pipelines.data_cleaning_pipeline.DataCleaningPipeline': 200,  # 常用变量清洗管道
    #         'src.pipelines.file_replacement_pipeline.FileReplacementPipeline': 100,  # 文件转换管道
    #         'src.pipelines.rich_text_analysis_pipeline.RichTextAnalysisPipeline': 200,  # 富文本解析管道
    #     },
    # }
    NOTICE_SCHEMA = {
        'baseField': [
            {'name': 'title_xilan', 'type': 'text', 'selector': 'div.title_xilan'},
            {'name': 'line_xilan', 'type': 'html', 'selector': 'div.line_xilan'},
            {'name': 'content_xilan', 'type': 'html', 'selector': 'div.content_xilan'},
        ],
        'base_fields_callback_function': detail_content
    }

    def start_requests(self):
        '''
        运行继承NSFCSpiders的所有爬虫作业
        '''
        # 手动运行所有子类
        for subclass in self.__class__.__subclasses__():
            yield from subclass().start_requests()

    # ----------------- 公共辅助方法 -----------------
    def _abs_url(self, href):
        try:
            return urljoin(self.base_url, href)
        except Exception as e:
            print(href)
            raise e
