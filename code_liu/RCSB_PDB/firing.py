# -*- coding: utf-8 -*-

"""
# @Time    : 2022/3/3 17:20
# @User  : Mabin
# @Descriotion  :启动爬虫
"""
import os
import time
import argparse
from scrapy import cmdline

from src.settings import LOG_FILE
import os

# os.environ['http_proxy'] = 'http://127.0.0.1:10810'
# os.environ['https_proxy'] = 'http://127.0.0.1:10810'
# # 我租的外网sentry地址要开代理
# sentry_sdk.init(
#     dsn=TEMP_SENTRY_DNS,
#     # Add data like request headers and IP for users,
#     # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
#     send_default_pii=True,
# )


def start_spider(spider_name, **extra_param):
    """
    启动爬虫（使用当前函数唤醒爬虫，可以使用断点调试）
    :author Mabin
    :param str spider_name:爬虫名称
    :param any extra_param: 启动爬虫时，追加的额外参数
    :return:
    """
    if not spider_name:
        return False

    spider_cmd = f"scrapy crawl {spider_name}"

    # 追加额外参数
    tmp_file_part = ""
    for param_key, param_item in extra_param.items():
        if param_item is None:
            continue

        spider_cmd += f" -a {param_key}={param_item}"
        tmp_file_part += f"{param_key}_{param_item}-"

    # 检查是否需要设置爬虫日志
    if LOG_FILE:
        tmp_file_part = tmp_file_part.strip("-")
        tmp_log_file = os.path.join(LOG_FILE, f"{spider_name}-{time.strftime('%d')}-{tmp_file_part}.log")
        # 判断日志文件是否存在，不存在则创建
        if not os.path.exists(LOG_FILE):
            os.makedirs(LOG_FILE)

        spider_cmd += f" -s LOG_FILE={tmp_log_file}"

    # 执行爬虫
    cmdline.execute(spider_cmd.split())
    return True


def generate_spider(spider_name, spider_website, **extra_param):
    """
    生成爬虫
    :author Mabin
    :param str spider_name:爬虫名称
    :param str spider_website:爬虫网站
    :param extra_param:
    :return:
    """
    if not all([spider_name, spider_website]):
        return False

    spider_cmd = f"scrapy genspider {spider_name} {spider_website}"

    # 执行命令行
    cmdline.execute(spider_cmd.split())
    return True


def parse_input_argv():
    """
    解析命令行输出参数，并调用爬虫
    :author Mabin
    """
    # 创建 ArgumentParser 对象
    parser = argparse.ArgumentParser(description="运行爬虫代码")

    # 添加参数
    parser.add_argument('--name', type=str, help='爬虫名称', required=True)
    # parser.add_argument('--year', type=int, default=None, help='爬虫指定的爬取年份')# 额外参数输入示例
    parser.add_argument('--service_object', type=str, default="医学信息支撑服务平台",
                        help='服务对象，例如：医学信息支撑服务平台')  # 额外参数输入示例

    # 解析命令行参数
    args = parser.parse_args()

    # 运行爬虫
    start_spider(
        spider_name=args.name,
        # target_year=args.year,
        service_object=args.service_object,
    )


if __name__ == '__main__':
    # 国自然结题报告爬虫（application_code参数：A、B、C、D、E、F、G、H）-nsfc_report
    # 国自然项目爬虫（application_code参数：A、B、C、D、E、F、G、H）-nsfc_project
    # python firing.py --name nsfc_report --year 2023
    # parse_input_argv()

    start_spider(
        spider_name="rcsb_all_api",
    )
