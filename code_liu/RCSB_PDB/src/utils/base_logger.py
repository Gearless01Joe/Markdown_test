# -*- coding: utf-8 -*-

"""
# @Time    : 2022/7/7 10:38
# @User  : Mabin
# @Descriotion  :日志记录类
"""
import time
import os
import logging.config
from src.constant import LOG_PATH, LOG_STDOUT
from scrapy.logformatter import LogFormatter, referer_str


class RequireDebugFalse(logging.Filter):
    """
    日志记录过滤器
    """

    def filter(self, record):
        return not LOG_STDOUT


class RequireDebugTrue(logging.Filter):
    """
    日志记录过滤器
    """

    def filter(self, record):
        return LOG_STDOUT


DEFAULT_LOGGING = {
    # dictConnfig的版本
    'version': 1,
    # 是否禁用所有的已经存在的日志配置
    'disable_existing_loggers': False,
    # 日志格式
    'formatters': {
        # 详细格式
        'verbose': {
            'format': '---------------------------------------------------------------\n'
                      '[%(levelname)s] [%(asctime)s]\n'
                      '%(message)s',
        },
        # 简单格式
        'simple': {
            'format': '---------------------------------------------------------------\n'
                      '[%(asctime)s] %(levelname)s %(message)s',
        },
    },
    # 日志处理
    'handlers': {
        # 错误日志
        'error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_PATH, time.strftime('%Y-%m'), 'error-{}.log'.format(time.strftime('%d'))),
            'maxBytes': 1024 * 1024 * 100,  # 文件大小
            'backupCount': 10,  # 备份数
            'formatter': 'verbose',  # 输出格式
            'encoding': 'utf-8',  # 设置默认编码
            'delay': True  # 延迟到第一次调用emit写入数据时才打开文件
        },
        'warning': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_PATH, time.strftime('%Y-%m'),
                                     'warning-{}.log'.format(time.strftime('%d'))),
            'maxBytes': 1024 * 1024 * 100,  # 文件大小
            'backupCount': 10,  # 备份数
            'formatter': 'verbose',  # 输出格式
            'encoding': 'utf-8',  # 设置默认编码
            'delay': True  # 延迟到第一次调用emit写入数据时才打开文件
        },
        # 控制台Debug日志
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        },
        # 简单日志
        'info': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_PATH, time.strftime('%Y-%m'), 'info-{}.log'.format(time.strftime('%d'))),
            'maxBytes': 1024 * 1024 * 100,  # 文件大小
            'backupCount': 10,  # 备份数
            'formatter': 'simple',  # 输出格式
            'encoding': 'utf-8',  # 设置默认编码
            'delay': True  # 延迟到第一次调用emit写入数据时才打开文件
        },
        # 调试日志
        "debug": {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_PATH, time.strftime('%Y-%m'), 'debug-{}.log'.format(time.strftime('%d'))),
            'maxBytes': 1024 * 1024 * 100,  # 文件大小
            'backupCount': 10,  # 备份数
            'formatter': 'verbose',  # 输出格式
            'encoding': 'utf-8',  # 设置默认编码
            'delay': True  # 延迟到第一次调用emit写入数据时才打开文件
        },
    },
    # 日志入口
    'loggers': {
        # log 调用时需要当作参数传入
        'local_log': {
            'handlers': [
                'console',
                'error',
                "debug",
                "info",
                "warning",
            ],
            'level': 'DEBUG',
            'propagate': False
        },
    },
    # 过滤
    'filters': {
        'require_debug_true': {
            '()': RequireDebugTrue,
        },
    },
}


class BaseLog:
    """
    日志记录类
    """

    def __init__(self, log_config=None, log_dir=None):
        """
        初始化日志相关配置
        :author:Mabin
        :param dict log_config:日志配置
        :param str log_dir:日志文件存放的目录
        """
        if log_config is None:
            # 初始化日志参数
            log_config = DEFAULT_LOGGING

        if log_dir is None:
            # 检查日志目录
            log_dir = os.path.join(LOG_PATH, time.strftime('%Y-%m'))
            if not os.path.exists(log_dir) and log_dir:
                # 目录不存在 则创建
                os.makedirs(log_dir)

        # 加载日志配置
        logging.config.dictConfig(log_config)

        # 初始化logger
        self._logger = logging.getLogger('local_log')

    def debug(self, msg):
        """
        记录DEBUG
        :author:Mabin
        :param str msg:待记录的信息
        :return:
        """
        return self._logger.debug(msg)

    def info(self, msg):
        """
        记录INFO
        :author:Mabin
        :param str msg:待记录的信息
        :return:
        """
        return self._logger.info(msg)

    def warning(self, msg):
        """
        记录WARNING
        :author:Mabin
        :param str msg:待记录的信息
        :return:
        """
        return self._logger.warning(msg)

    def error(self, msg):
        """
        记录ERROR
        :author:Mabin
        :param str msg:待记录的信息
        :return:
        """
        return self._logger.error(msg)


class BaseSpiderLogFormatter(LogFormatter):
    def crawled(self, request, response, spider):
        """
        当爬虫爬取到页面时触发当前回调
        :author:Mabin
        :param request:
        :param response:
        :param spider:
        :return:
        """
        request_flags = f' {str(request.flags)}' if request.flags else ''
        response_flags = f' {str(response.flags)}' if response.flags else ''
        return {
            'level': logging.DEBUG,
            'msg': "Crawled (%(status)s) %(request)s%(request_flags)s (referer: %(referer)s)%(response_flags)s\n"
                   "Request-Body %(request_body)s",
            'args': {
                'status': response.status,
                'request': request,
                'request_flags': request_flags,
                'referer': referer_str(request),
                'response_flags': response_flags,
                # backward compatibility with Scrapy logformatter below 1.4 version
                'flags': response_flags,
                'request_body': request.body.decode(),
            }
        }


if __name__ == '__main__':
    model = BaseLog()
    model.debug("哈哈")
    model.info("哈哈1")
    model.error("哈哈2")
    model.warning("哈哈3")
