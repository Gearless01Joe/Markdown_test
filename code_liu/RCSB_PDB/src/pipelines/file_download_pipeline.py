# -*- coding: utf-8 -*-

"""
# @Time    : 2025/3/6 14:21
# @User  : Mabin
# @Description  :文件下载管道（继承自Scrapy官方类）
"""
import os
import time
import shutil
import hashlib
import mimetypes
from typing import Any, cast
from pathlib import Path
from scrapy.http import Request, Response
from scrapy.pipelines.files import FilesPipeline
from scrapy.pipelines.media import MediaPipeline
from scrapy.utils.python import to_bytes
from src.utils.utils import remove_overdue_file


class FileDownloadPipeline(FilesPipeline):
    """
    继承自官方类，官方类默认需要item具备以下两个属性：
        file_urls：文件链接字符串或文件链接列表
        files：下载结果字典列表，大体上为[{"url":"文件链接","path":"本地文件存储路径","status":"downloaded/uptodate/cached"}]
    """

    def file_path(
            self,
            request: Request,
            response: Response = None,
            info: MediaPipeline.SpiderInfo = None,
            *,
            item: Any = None,
    ):
        """
        当前函数为父类函数的覆写，基本保持源代码，只调整了文件存储路径信息和移除过期文件的功能
        :author Mabin
        :param request:
        :param response:
        :param info:
        :param item:
        :return:
        """
        # 获取文件拓展名
        media_ext = Path(request.url).suffix
        if media_ext not in mimetypes.types_map:
            media_ext = ""
            media_type = mimetypes.guess_type(request.url)[0]
            if media_type:
                media_ext = cast(str, mimetypes.guess_extension(media_type))

        # 移除过期文件
        storage_path = info.spider.settings.get("FILES_STORE")
        remove_overdue_file(storage_path)

        # 组织文件名
        media_guid = hashlib.sha1(to_bytes(request.url)).hexdigest()  # nosec

        # 组织最终文件链接
        return f'{time.strftime("%Y-%m-%d-%H")}/{media_guid}{media_ext}'
