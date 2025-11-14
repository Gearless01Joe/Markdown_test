# -*- coding: utf-8 -*-
"""
# @Time    : 2025-03-10
# @User  : Tlg
# @Description  :爬取国家自然科学基金相关信息主类，子类继承并使用公共方法
"""
import datetime
import re
from urllib.parse import urljoin
import scrapy
import logging
from functools import partial

from src.utils.mysql_manager import MySQLManager


class NSFCSpiders(scrapy.Spider):
    """
    开发者：通力嘎
    日期：2025-03-10
    """
    allowed_domains = ['www.nsfc.gov.cn']
    base_url = "https://www.nsfc.gov.cn"  # 网站根路径

    name = "nsfc"
    custom_settings = {
        'ITEM_PIPELINES': {
            'src.pipelines.storage.information_storage_pipeline.InformationStoragePipeline': 300,  # 数据库传输管道
            'src.pipelines.file_download_pipeline.FileDownloadPipeline': 90,  # 文件下载管道
            'src.pipelines.data_cleaning_pipeline.DataCleaningPipeline': 200,  # 常用变量清洗管道
            'src.pipelines.file_replacement_pipeline.FileReplacementPipeline': 100,  # 文件转换管道
            'src.pipelines.rich_text_analysis_pipeline.RichTextAnalysisPipeline': 200,  # 富文本解析管道
        },
    }

    def start_requests(self):
        '''
        运行继承NSFCSpiders的所有爬虫作业
        '''
        # 手动运行所有子类
        for subclass in self.__class__.__subclasses__():
            yield from subclass().start_requests()

    # ----------------- 公共辅助方法 -----------------

    # @暂时弃用
    def _get_date_url(self, table):
        '''
        做增量更新，查找最大日期和url
        :param table: 数据库表名
        :return: 字典{"表中最大日期",【最大日期对应的所有url的列表】}或者None
        '''
        data_url_dict = {}

        try:
            test_model = MySQLManager()
            with test_model.mysql_pool.connection() as conn, conn.cursor() as cursor:
                sql = f"SELECT max(publish_date) as max FROM `{table}`;"
                cursor.execute(sql)
                data = cursor.fetchone()  # 最大日期

                if data.get('max'):
                    data_url_dict['data'] = datetime.date.strftime(data.get('max'), '%Y-%m-%d')
                    sql = f"SELECT url FROM `{table}` where publish_date = '{data_url_dict['data']}';"
                    cursor.execute(sql)
                    data = cursor.fetchall()  # 对应的所有url
                    data_url_dict['urls'] = set([i.get('url') for i in data])
                else:
                    data_url_dict['data'] = None
                    data_url_dict['urls'] = set()
                return data_url_dict
        except Exception as e:
            logging.error(f"get_date_url 数据库链接错误 错误: {e}")
        return data_url_dict

    def _parse_basic_fields(self, response, include_author=True):
        """
        从 response 中提取标题、发布日期、（可选）来源和正文内容
        :param include_author: 是否提取作者/来源信息
        :return: 包含字段信息的字典和正文 用于后续附件/图片提取）
        开发者：通力嘎
        日期：2025-02-20
        """
        fields = {}
        fields['details_page'] = response.url
        title_tag = response.css('[class="title_xilan"]')  # 提取文章名class
        if title_tag:
            fields['info_name'] = ''.join(title_tag.css("::text").getall()).strip()  # 去除文章名左右空格等字符

        line_tag = response.css('[class="line_xilan"]')  # 提取文章发布信息class
        '''
        发布信息都是在一行的字符串，使用特殊的分隔符等切割对应信息
        '''
        if line_tag:
            parts = line_tag.css("::text").getall()
            if parts:
                date = parts[0].split("\u3000\xa0")  #
                fields['info_date'] = date[0].replace('日期 ', '')
            # if include_author and len(parts) >= 2:
            #     fields['source'] = parts[1].strip().replace('\u3000\xa0 作者：', '').replace('作者：', '')

        fields['info_html'] = response.css('[class="content_xilan"]')  # 先提取html；后期在管道解析详细信息

        return fields

    def _extract_attachments(self, content, response_url):
        """
        从正文内容中提取附件链接
        :param content: content正文html（scrapy解析类型）
        :param response_url: 当前页面 URL，用于构造完整链接
        :return: 附件名称和链接的字典
        开发者：通力嘎
        日期：2025-02-20
        """
        attachments = []

        for a in content.css('a'):
            span = a.css('span::attr(style)').get()
            if span and 'text-decoration: underline; color: #0070c0;' in span:  # 找到附件的特殊格式
                # 如果<span>的style属性符合要求，则提取href和内部文字
                attachment = {}
                href = a.attrib['href']
                text = a.css('span::text').get().strip()
                # 将提取的信息存储到字典中
                attachment['accessory_name'] = text
                attachment['url'] = urljoin(response_url, href)
                attachments.append(attachment)
        return attachments

    def _extract_images(self, content):
        """
        从正文中提取图片链接
        :param content:content正文html（scrapy解析类型）
        :return: 图片索引和链接的字典
        开发者：通力嘎
        日期：2025-02-21
        """
        images = []
        for index, img in enumerate(content.css('img')):
            image = {}
            img_url = img.css("::attr(src)").get()  # 找到图片的特殊格式
            if img_url:
                image[f'accessory_name'] = f'img{index + 1}'
                image[f'url'] = urljoin(self.base_url, img_url)
                images.append(image)
        return images

    def _yield_next_page(self, response, detail_callback, data_url_dict):
        """
        分页逻辑：查找并发送“下一页”的请求
        """
        try:
            bottom = response.css('[valign="bottom"]')  # 提取翻页行对象
            if bottom:
                links = bottom.css('a')  # 提取所有a标签
                if len(links) >= 2:
                    next_page = links[-2]  # 提取倒数第二元素（下一页）
                    next_href = next_page.css('::attr(href)').get()  # 如果当前页面就是最后一页就过了
                    if next_href:
                        # 使用partial固定参数，避免lambda参数问题
                        callback = partial(
                            self._parse_common_list,
                            detail_callback=detail_callback,
                            table=data_url_dict
                        )  # 将data_url_dict表信息传递给下面
                        yield scrapy.Request(
                            url=urljoin(self.base_url, next_href),
                            callback=callback
                        )
        except Exception as e:
            logging.error(f"_yield_next_page 错误: {e}")

    def _convert_to_date(self, date_str):
        """
        使用正则表达式判断格式是否为 [xx-xx-xx]
        :param date_str: 字符串（日期）
        开发者：通力嘎
        日期：2025-02-20
        :return 解析成日期类型
        """
        if re.match(r'^\[\d{2}-\d{2}-\d{2}\]$', date_str):
            # 去掉中括号
            date_str = date_str.strip('[]')
            # 转换为日期格式
            return datetime.datetime.strptime(date_str, '%y-%m-%d')
        else:
            # 格式不匹配，直接返回原字符串
            return datetime.datetime.strptime(date_str, '%Y-%m-%d')

    def _parse_common_list(self, response, detail_callback, table=None):
        """
        通用列表解析函数：解析列表页中的各详情页链接，并处理翻页
        :param response: 列表页响应对象
        :param detail_callback: 详情页回调函数
        :table 有两种形式1、字符串表名字 2、字典{“最大日期”，“url列表”}
        开发者：通力嘎
        日期：2025-02-20
        """
        if isinstance(table, str):  # 判断类型
            data_url_dict = {}  # 暂时不进行增量
            # data_url_dict = self._get_date_url(table)
        else:
            data_url_dict = table or {}

        try:
            dp_lia = response.css('[class="dp_lia"]')  # 所有详细和翻页的大容器
            if not dp_lia:
                logging.error(f"_parse_common_list 未找到 dp_lia 元素，链接：{response.url}")
                return

            for pa in dp_lia.css('[class="clearfix"]'):  # 所有详细信息链接列表
                a_tag = pa.css('a')
                if not a_tag:
                    continue

                href = a_tag.css('::attr(href)').get()
                if not href:
                    continue

                absolute_url = urljoin(self.base_url, href)  # 拼接

                # 处理存在数据日期的情况
                if data_url_dict.get("data"):  # 处理表中空日期或者表是空表
                    try:
                        '''
                        处理特殊的日期格式 例子：[25-01-02]
                        '''
                        date_str = pa.css('::text').getall()[-1].strip()
                        new_date = self._convert_to_date(date_str)
                        base_date = self._convert_to_date(data_url_dict['data'])
                    except Exception as e:
                        logging.warning(f"日期解析失败: {e}，链接：{absolute_url}")
                        continue  # 跳过无法解析日期的条目

                    # 仅当新日期大于等于基准日期且url不在表中时生成请求
                    if new_date >= base_date and absolute_url not in data_url_dict.get("urls"):
                        yield scrapy.Request(url=absolute_url, callback=detail_callback)
                else:
                    # 无基准数据时直接生成请求
                    yield scrapy.Request(url=absolute_url, callback=detail_callback)

            # 处理翻页
            yield from self._yield_next_page(response, detail_callback, data_url_dict)

        except Exception as e:
            logging.error(f"_parse_common_list 方法错误，链接：{response.url}, 错误：{e}", exc_info=True)
