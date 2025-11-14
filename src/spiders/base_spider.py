# -*- coding: utf-8 -*-

"""
# @Time    : 2025/2/25 10:39
# @User  : Mabin
# @Description  :基础爬虫类
"""
import scrapy
from dateutil.parser import parse
from src.constant import CACHE_SUMMARY
from src.utils.utils import str_to_md5
from src.utils.redis_manager import RedisManager
from scrapy.http import Request, Response
from scrapy.responsetypes import responsetypes
from playwright.async_api import Page
from twisted.python.failure import Failure


class BaseSpider(scrapy.Spider):
    # 定义主站基础URL
    base_url = None

    def __init__(self, **kwargs):
        """
        初始化类
        :author Mabin
        :param kwargs:
        """
        super().__init__(**kwargs)

        # 主站基础URL
        if self.base_url is None:
            raise Exception("基础主站链接不可为空！后续公共管道需要使用该链接来组成拼接链接！")

        # 服务对象
        self.service_object = kwargs.get('service_object', '医学信息支撑服务平台')

        # 实例化Redis对象
        self.redis_model = RedisManager()
        # 获取Redis连接
        self._redis_client = self.redis_model.get_connection()

    @staticmethod
    async def _organ_playwright_response(page: Page, response: Response) -> Response:
        """
        修改Scrapy的response，生成全新的Response（通过Playwright Page对象）
        :author Mabin
        :param page:Playwright的Page对象
        :param response:Scrapy的本次响应
        :return:
        """
        # 获取编码（如果是TextResponse）或使用默认utf-8
        encoding = getattr(response, 'encoding', 'utf-8')

        try:
            await page.wait_for_load_state("networkidle", timeout=50000)
        except TimeoutError:
            await page.wait_for_load_state("load", timeout=30000)

        # 创建新body
        new_text = await page.content()
        new_body = new_text.encode(encoding)

        # 使用replace方法创建新response（保持原response类型）
        return response.replace(body=new_body, url=page.url)

    async def playwright_request_error(self, failure):
        """
        Playwright请求报错处理
        :author Mabin
        :param failure:错误对象
        :return:
        """
        self.logger.error(f"Playwright请求失败: {failure}")

        # 获取原始请求
        request = failure.request

        # 检查是否存在Page对象
        page = request.meta.get("playwright_page")
        if isinstance(page, Page) and not page.is_closed():
            # 关闭页面
            await page.close()

        # 获取最大重试次数
        retry_times = self.crawler.settings.getint('RETRY_TIMES', 3)

        # 获取请求信息
        request = failure.request
        if request.meta.get('retry_times', 0) < retry_times:
            # 复制请求，重新发送
            retryreq = request.copy()
            retryreq.meta['retry_times'] = request.meta.get('retry_times', 0) + 1
            retryreq.dont_filter = True  # 确保请求不会被过滤

            return retryreq

    @staticmethod
    def is_seen(key, record_sign=True):
        """
        判断key是否已爬取（当前方法用来占位，主要实现在HistoryDataMiddleware中）
        :author Mabin
        :param key:判定用的key
        :param record_sign:是否记录当前数据
        :return:
        """
        return False
