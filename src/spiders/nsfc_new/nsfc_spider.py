import json
import re
from urllib.parse import urljoin

import scrapy

from src.component.base_selector_component import BaseSelectorComponent
from src.items.information_item import InformationItem
from src.spiders.base_spider import BaseSpider


class NsfcSpider(BaseSpider):
    """
    国家自然科学基金委员会（NSFC）官网爬虫。
    主要用于采集NSFC官网上资助成果相关信息。
    """

    name = "nsfc_spider"  # 爬虫名称
    allowed_domains = ["www.nsfc.gov.cn"]  # 限定允许的域名
    base_url = "https://www.nsfc.gov.cn"  # 网站基础 URL

    custom_settings = {
        'ITEM_PIPELINES': {
            # # 数据传输到数据库的管道
            # 'src.pipelines.storage.information_pipeline.InformationStoragePipeline': 300,
            # # 文件下载处理管道
            # 'src.pipelines.file_download_pipeline.FileDownloadPipeline': 210,
            # # 常用变量清洗管道
            # 'src.pipelines.data_cleaning_pipeline.DataCleaningPipeline': 199,
            # # 文件转换/替换管道
            # 'src.pipelines.file_replacement_pipeline.FileReplacementPipeline': 250,
            # 富文本解析管道
            'src.pipelines.rich_text_analysis_pipeline.RichTextAnalysisPipeline': 200,
        },
    }

    # 分类URL配置
    CATEGORY_URLS = {
        '通知公告': ['/p1/3381/2824/zntg.html'],
        '项目指南': ['/p1/2931/3441/2025ndxmznlb.html'],
        "申请与资助": ['/p1/2791/2809/zzgj.html'],
        "法规与规章": [
            '/p1/2871/2872/gjkxjsxgflfg.html',
            '/p1/2871/2873/gjzrkxjjtl.html',
            '/p1/2871/2874/gjzrkxjjgzzd.html',
        ],
        '资助成果': {
            '数学物理科学部': '/p1/2851/3085/zzcg111.html',
            '化学科学部': '/p1/2852/3169/3171/hxkxbzzcg.html',
            '生命科学部': '/p1/2853/3103/zzcg1111.html',
            '地球科学部': '/p1/2854/3146/dqkxzzcg.html',
            '工程与材料科学部': '/p1/2855/3131/zzcg111111.html',
            '信息科学部': '/p1/2856/3157/xxkxzzcg.html',
            '管理科学部': '/p1/2857/3204/glkxbzzcg.html',
            '医学科学部': '/p1/2858/3216/yxkxbzzcg.html',
            '交叉科学部': '/p1/2859/3190/jckxbzzcg.html',
        }
    }

    def start_requests(self):
        """
        爬虫入口函数，遍历 CATEGORY_URLS 配置中的分类和子类，生成起始请求。
        :return: scrapy.Request 迭代器
        """
        for top_category, submap in self.CATEGORY_URLS.items():
            if isinstance(submap, list):
                # 处理分类为列表的情况
                for url_link in submap:
                    url = urljoin(self.base_url, url_link)
                    meta = {'column_info': (top_category,)}
                    callback = self.parse_detail if top_category == "申请与资助" else self.parse_list
                    yield scrapy.Request(url, callback=callback, meta=meta)
            else:
                # 处理分类为字典的情况
                for sub_name, rel_path in submap.items():
                    url = urljoin(self.base_url, rel_path)
                    meta = {'column_info': (top_category, sub_name)}
                    yield scrapy.Request(url, callback=self.parse_list, meta=meta)

    def parse_detail(self, response):
        """
        解析详情页，提取文章标题、作者、日期、正文内容等信息。
        :param response: scrapy.Response 对象
        :return: InformationItem 实例
        """

        info = {'column_info': response.meta.get('column_info')}

        selector_model = BaseSelectorComponent()

        link_data = []
        files = []
        box = response.css('.fuj_lieb')  # 第一步
        if box:  # 防止页面没有该节点
            for a in box.css('a'):  # 第二步：内部所有 a
                url = urljoin(self.base_url, a.css('::attr(href)').get(''))
                link_data.append({
                    'url': url,
                    'accessory_name': a.css('::text').get('').strip()
                })
                files.append(url)
            info['link_data'] = link_data
            info['file_urls'] = files

        # 文章标题
        selector_model.add_field(field_name="info_name", selector='title', selector_type='css', field_type='text')

        # 作者信息
        selector_model.add_field(field_name="info_author", selector='[class="line_xilan"]', selector_type='css',
                                 field_type='text')

        # 来源信息
        selector_model.add_field(field_name="info_source", selector='[class="line_xilan"]', selector_type='css',
                                 field_type='text')

        # 发布时间
        selector_model.add_field(field_name="info_date", selector='[class="line_xilan"]', selector_type='css',
                                 field_type='text')

        # 正文 HTML 内容
        selector_model.add_field(field_name="info_html", selector='[class="content"]', selector_type='css',
                                 field_type='html', cleaning_function=self.transformation_html)

        # MARC 编码（暂时使用标题作为占位）
        selector_model.add_field(field_name='marc_code', selector='title', selector_type='css', field_type='text')

        # selector_model.add_ai_analysis(
        #     ai_type='info',
        # )
        yield from selector_model.execute(response=response, scrapy_item=InformationItem, meta=info)

    def parse_list(self, response):
        """
        解析列表页，提取文章标题、链接、时间，并发现下一页。
        :param response: scrapy.Response 对象
        :return: scrapy.Request 或 dict
        """
        meta = response.meta or {}
        base_selector = "/html/body/div/div[2]/div[2]/div[2]/ul/li"
        selector_model = BaseSelectorComponent()

        # 提取下一页链接
        selector_model.add_field(selector=r'//a[text()="下一页"]/@onclick', field_name="next_url")

        # 提取标题字段
        selector_model.add_field(selector=r".//span[1]//text()", field_name="title", base_name="detail_list",
                                 base_selector=base_selector)

        # 提取详情页 URL 字段
        callback_param = {"meta": meta} if meta else {}
        selector_model.add_field(selector=r".//a/@href", field_name="url", field_type="href", base_name="detail_list",
                                 base_selector=base_selector, callback=self.parse_detail,
                                 callback_parameter=callback_param)

        # 提取时间字段
        selector_model.add_field(selector=r".//span[2]//text()", field_name="date", base_name="detail_list",
                                 base_selector=base_selector)

        yield from selector_model.execute(response=response)

        # 翻页逻辑（如果需要可以开启）
        next_url = self.extract_url(response.url, selector_model.get_all_field().get('next_url'))
        if next_url:
            full_next = urljoin(self.base_url, next_url)
            self.logger.debug('发现下一页: %s', full_next)
            yield scrapy.Request(full_next, callback=self.parse_list, meta=meta)

    @staticmethod
    def transformation_html(html):
        """
        删除正文中不需要的html
        :param html 正文html
        :return: 过滤后的html
        """
        # 使用正则删除目标元素
        html = re.sub(r'<div\s+class="title_xilan">.*?</div>', '', html, flags=re.DOTALL)
        html = re.sub(r'<div\s+class="line_xilan">.*?</div>', '', html, flags=re.DOTALL)

        return html

    @staticmethod
    def extract_url(list_url, js_code):
        """
        提取 JavaScript 中 location.href=encodeURI(...) 的 URL。
        :param list_url: 列表页 URL
        :param js_code: 包含 JavaScript 代码的字符串
        :return: 提取到的 URL 字符串，如果未找到则返回 None
        """
        if not js_code:
            return None
        pattern = r"location\.href\s*=\s*encodeURI\(['\"](.*?)['\"]\)"
        match = re.search(pattern, js_code)
        if match:
            page_url = match.group(1)
            list_url = list_url.split('/')
            list_url[-1] = page_url
            return '/'.join(list_url)
        return None
