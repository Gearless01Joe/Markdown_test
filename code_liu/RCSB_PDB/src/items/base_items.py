# -*- coding: utf-8 -*-

"""
# @Time    : 2025/3/5 12:16
# @User  : Mabin
# @Description  :Item所使用的Field类定义
"""
from scrapy import Field, Item


class BaseItem(Item):
    file_urls = Field()  # 需要下载的链接（Scrapy的FilesPipeline会处理）必须是列表!!!
    files = Field()  # 下载后的文件信息（Scrapy的FilesPipeline填充）
    page_url = Field()  # 链接地址
    original_html = Field()  # HTML原文
    stored_state = Field()  # 入库状态，布尔型，True为爬虫后续接口或Kafka推送成功
    stored_remark = Field()  # 入库情况备注，主要存储错误信息
    parsed_data = Field()  # 正式请求爬虫或Kafka时解析的最终结果数据


class StringField(Field):
    """
    字符串类型
    """
    pass


class IntField(Field):
    """
    整型类型
    """
    pass


class FloatField(Field):
    """
    浮点数类型（尽量少使用，存在传值精度丢失的问题）
    """
    pass


class DateField(Field):
    """
    时间类型(默认将当前字段数据转换为时间格式：%Y-%m-%d，可以通过定义重新调整时间格式字符串)
    例如：
    class A(BaseItem):
        test_field = DateField(format="%Y-%m-%d %H:%M:%S")
    """
    pass


class HTMLSectionField(Field):
    """
    HTML正文段落类型(针对该类型进行段落格式解析)
    """
    pass


class SectionField(Field):
    """
    HTML转写后的段落属性字段(即最终的入库格式)
    """
    pass


class FileOSSField(Field):
    """
    文件OSS字段（该字段不执行实际下载，主要将Scrapy下载中间件的结果写入到当前字段，同时将其调整为OSS路径类型）
    由爬虫写入文件的完整下载地址，后续的rich_text_replacement_pipeline管道将从files字段中获取下载信息来将该字段改写为以下格式：
    {"file_path": "intelligence/XXXX.png", "bucket_name": "XXX"}

    可以通过定义来具体说明OSS信息，当前支持bucket_sign、oss_path_sign、output_type字段，不设置默认选取资源湖字段
    其中bucket_sign是BaseOSS的bucket_sign参数，
        特别的，当bucket_sign为local时，将不上传OSS，FileOSSField字段将记录本地文件相对路径，格式如：2025-08-28-15/2319057f494c50d52bea30fe233550076045f73d.jpg
    oss_path_sign是BaseOSS的generate_oss_path函数的target_type参数

    output_type包括：
        default(
            字段写入格式：r"http://101.200.62.36:8001/static/1.png"
            字段重写后结果：{"file_path": "intelligence/XXXX.png", "bucket_name": "XXX"}
        )
        accessory(
            字段写入格式：[
                {
                    "accessory_name": "附件名称，可空",
                    "url": "文件实际链接"
                }
            ]
            字段重写后结果：[
                {
                    "accessory_name": "附件名称",
                    "accessory_url": {"file_path": "intelligence/XXXX.png", "bucket_name": "XXX"}
                }
            ]
        )

    # 字段使用实例，FileOSSField参数可以不写，会有默认值补充
    class A(BaseItem):
        test_field = FileOSSField(bucket_sign="technique",oss_path_sign="intelligence",output_type="default")
    """
    pass


class FileInfoField(Field):
    """
    文件信息字段（可以写入当前文件链接对应的MD5、文件大小等）
    由爬虫写入文件的完整下载地址，后续的rich_text_replacement_pipeline管道将从files字段中获取下载信息来将该字段改写为对应文件信息
    可以通过定义来具体说明文件具体的信息，当前支持：md5（文件对应的MD5）、size（文件大小，字节数），默认size
    class A(BaseItem):
        test_field = FileInfoField(info_type="md5")
        test_field = FileInfoField(info_type="size")
    """
    pass


class LanguageField(Field):
    """
    语言识别字段，当前位置的字段数据需要传入语言判断依据字符串
    data_cleaning_pipeline管道会自动依据传入文本来设置语言代码
    """
    pass


class EnumerationField(Field):
    """
    枚举字段
    data_cleaning_pipeline管道会自动判断当前传入值是否在预设的枚举范围内
    (None值会跳过判断，如有必要，None值的判断未来根据字段类的required属性来判断，True为必填字段)
    定义示例
    class A(BaseItem):
        test_field = EnumerationField(enum_set={"图片信息","研究报告","手册书籍"})
    """
    pass


def get_item_field(item):
    """
    获取item类的字段情况
    :author Mabin
    :param Item item:Scrapy-item实例
    :return:
    """
    # 获取 Item 类
    item_cls = type(item)

    # 遍历所有字段及其对应的 Field 对象
    buf = {}
    for field_name, field_obj in item_cls.fields.items():
        # 记录相关映射
        buf[field_name] = {
            "type": type(field_obj),  # 获取字段的原始 Field 类型
            "metadata": field_obj  # 定义时的元数据
        }

    # {
    #   'file_urls': {'type': <class 'scrapy.item.Field'>, 'metadata': {}},
    #   'files': {'type': <class 'scrapy.item.Field'>, 'metadata': {}},
    #   'test_field': {'type': <class '__main__.DateField'>, 'metadata': {'format': '%Y-%m-%d %H:%M:%S'}}
    # }
    return buf
