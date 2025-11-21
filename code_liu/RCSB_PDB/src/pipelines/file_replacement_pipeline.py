# -*- coding: utf-8 -*-

"""
# @Time    : 2025/3/6 14:45
# @User  : Mabin
# @Description  :文件地址链接替换管道(包括富文本字段SectionField、普通文件字段FileOSSField)
该管道负责将 Scrapy 爬取的文件上传到 OSS，并将 Item 中的链接路径替换为 OSS 地址
"""
import os
import shutil
from pathlib import Path
from src.utils.base_oss import BaseOSS
from src.constant import STORAGE_PATH
from src.items.base_items import get_item_field, SectionField, FileOSSField, FileInfoField
from src.component.html_converter.handle import ClassifyParagraphAttr, ParseStandardizedHtml


class FileReplacementPipeline:
    """
    文件地址写回管道
    """
    bucket_sign = "technique"  # OSS所在Bucket
    oss_path_sign = "intelligence"  # 生成OSS路径所使用的标识
    oss_instance_type = 1  # OSS实例类型，1为外网实例，2为内网实例，3为海外加速实例

    def __init__(self):
        """
        初始化实例变量，用于存储数据
        :author:Mabin
        """
        self.spider_name = None  # 记录当前爬虫名
        self.storage_path = None  # 记录当前爬虫的存储根目录
        self.files_result_field = None  # 记录当前爬虫的文件结果字段名

    def open_spider(self, spider):
        """
        爬虫启动时调用，记录相关内容
        :author:Mabin
        :param spider:
        :return:
        """
        self.spider_name = spider.name
        self.storage_path = spider.settings.get("FILES_STORE")
        self.files_result_field = spider.settings.get("FILES_RESULT_FIELD", "files")

    def process_item(self, item, spider):
        """
        处理文件地址字段调整
        :author:Mabin
        :param item:
        :param spider:
        :return:
        """
        # 获取文件下载结果
        files_result = item.get(self.files_result_field, [])

        # 组织文件下载映射
        file_mapping = {}
        for file_item in files_result:
            file_mapping[file_item["url"]] = file_item

        if not file_mapping:
            # 不存在实际下载结果
            return item

        # 获取item的元数据情况
        section_field = {}
        file_field_buf = []
        file_info_field = []
        field_mapping = get_item_field(item)
        for field_name, field_value in field_mapping.items():
            field_type = field_value.get("type")
            if field_type is SectionField:
                # 查找SectionField对应的item属性类型
                section_field = {
                    "field": field_name,
                    "metadata": field_value.get("metadata", {})
                }
            elif field_type is FileOSSField:
                # 文件下载字段
                file_field_buf.append({
                    "field": field_name,
                    "metadata": field_value.get("metadata", {})
                })
            elif field_type is FileInfoField:
                # 文件MD5计算字段
                file_info_field.append({
                    "field": field_name,
                    "metadata": field_value.get("metadata", {})
                })

        # 获取输出结果
        exist_buf = []
        section_output = item.get(section_field.get("field"), None)
        for file_field_item in file_field_buf:
            # 获取字段信息
            file_field = file_field_item["field"]

            tmp_item = item.get(file_field, None)
            if tmp_item is not None:
                # 记录存在数据的字段名称
                exist_buf.append(file_field)

        if section_output is None and not exist_buf:
            raise Exception("替换文件链接时，存在需要下载的文本，但不存在需要修改的字段")

        # 文件字段
        for file_field_item in file_field_buf:
            # 获取字段信息
            file_field = file_field_item["field"]
            file_metadata = file_field_item["metadata"] or {}

            # 获取实际数据
            tmp_item = item.get(file_field, None)
            if tmp_item is None:
                continue

            # 获取bucket信息
            bucket_sign = file_metadata.get("bucket_sign") or self.bucket_sign
            oss_path_sign = file_metadata.get("oss_path_sign") or self.oss_path_sign

            # 获取输出类型
            output_type = file_metadata.get("output_type", "default")
            if output_type == "default":
                # 执行单个文件上传（默认）
                upload_result = self._handle_file_upload(
                    file_mapping=file_mapping, filed_data=tmp_item, root_path=self.storage_path,
                    bucket_sign=bucket_sign, oss_path_sign=oss_path_sign
                )
                if not upload_result["result"]:
                    raise Exception(f'执行{file_field_item}字段文件上传时，{upload_result["msg"]}')

                # 调整数据
                item[file_field] = upload_result["data"]
            elif output_type == "accessory":
                # 执行附件列表上传
                handle_result = self._handle_file_list(
                    current_data=tmp_item, file_mapping=file_mapping, root_path=self.storage_path,
                    bucket_sign=bucket_sign, oss_path_sign=oss_path_sign
                )
                if not handle_result["result"]:
                    raise Exception(f'处理文件列表字段时（字段名：{file_field_item}），{handle_result["msg"]}')

                # 覆盖原字段
                item[file_field] = handle_result["data"]

        # 段落文件处理
        if section_output:
            # 获取bucket信息
            section_metadata = section_field.get("metadata", {})
            bucket_sign = section_metadata.get("bucket_sign") or self.bucket_sign
            oss_path_sign = section_metadata.get("oss_path_sign") or self.oss_path_sign

            # 执行段落文件解析
            handle_result = self._handle_section_field(
                section_list=section_output, file_mapping=file_mapping, root_path=self.storage_path,
                bucket_sign=bucket_sign, oss_path_sign=oss_path_sign
            )
            if not handle_result["result"]:
                raise Exception(f'处理段落数据的文件上传时，{handle_result["msg"]}')

            # 调整数据
            item[section_field.get("field")] = handle_result["data"]

        # 文件MD5计算字段
        for file_field_item in file_info_field:
            # 获取字段信息
            current_data = item.get(file_field_item, {})
            current_field = current_data.get("field")
            current_metadata = current_data.get("metadata", {})

            # 获取实际数据
            tmp_item = item.get(current_field, None)

            # 调用相关函数
            handle_result = self._handle_file_info(
                current_data=tmp_item, file_mapping=file_mapping, root_path=self.storage_path,
                current_metadata=current_metadata
            )
            if not handle_result["result"]:
                raise Exception(f'处理文件信息字段时（字段名：{file_field_item}），{handle_result["msg"]}')

            # 覆盖原有数据
            item[current_field] = handle_result["data"]

        # 返回最终修改后的item
        return item

    def _handle_section_field(self, section_list, file_mapping, root_path, bucket_sign, oss_path_sign):
        """
        处理段落数据
        :author:Mabin
        :param list section_list:RichTextAnalysisPipeline处理的段落结果
        :param dict file_mapping:文件链接映射，value为Scrapy的file管道的存储形式
        :param str root_path:本地文件存储的根目录
        :param str bucket_sign:OSS bucket标识
        :param str oss_path_sign:OSS文件路径生成类别
        :return:
        """
        # 遍历相关数据
        for i, section_item in enumerate(section_list):
            section_attr = section_item.get("section_attr")
            text_info = section_item.get("text_info", {}).get("children", [])

            if section_attr in {
                ClassifyParagraphAttr.SECTION_ATTR_MAPPING["figure"],  # 图像
                ClassifyParagraphAttr.SECTION_ATTR_MAPPING["audio"],  # 音频
            } and len(text_info) == 1:
                # 需要将段内文件升级为整行数据
                tmp_data = text_info[0]
                tmp_url = tmp_data.get("url")
                tmp_text = tmp_data.get("text")

                # 执行上传
                upload_result = self._handle_file_upload(
                    file_mapping=file_mapping, filed_data=tmp_url, root_path=root_path,
                    bucket_sign=bucket_sign, oss_path_sign=oss_path_sign
                )
                if not upload_result["result"]:
                    return {"result": False, "msg": upload_result["msg"]}
                upload_result = upload_result["data"]

                # 赋值数据
                section_list[i]["media_info"] = upload_result

                # 检查是否存在文本
                if tmp_text:
                    # 调整段内类型为文本
                    del text_info[0]["url"]
                    tmp_data["type"] = ParseStandardizedHtml.INLINE_ATTR_MAPPING["text"]

                    # 重新赋值文本数据
                    section_list[i]["text_info"] = {"children": tmp_data}
                else:
                    section_list[i]["text_info"] = None
            else:
                # 检查是否存在段内文件
                for j, inline_item in enumerate(text_info):
                    tmp_type = inline_item.get("type")

                    # 段内类型
                    if tmp_type in {
                        ParseStandardizedHtml.INLINE_ATTR_MAPPING["figure"],
                        ParseStandardizedHtml.INLINE_ATTR_MAPPING["file"],
                    }:
                        tmp_url = inline_item.get("url")

                        # 执行上传
                        upload_result = self._handle_file_upload(
                            file_mapping=file_mapping, filed_data=tmp_url, root_path=root_path,
                            bucket_sign=bucket_sign, oss_path_sign=oss_path_sign
                        )
                        if not upload_result["result"]:
                            return {"result": False, "msg": upload_result["msg"]}
                        upload_result = upload_result["data"]

                        # 赋值
                        del text_info[j]["url"]
                        text_info[j]["file"] = upload_result

        # 返回相关数据
        return {
            "result": True, "msg": "ok!", "data": section_list
        }

    @staticmethod
    def _handle_file_info(current_data, file_mapping, root_path, current_metadata):
        """
        处理文件信息字段
        :author:Mabin
        :param str current_data:当前字段中的实际文件链接
        :param dict file_mapping:文件链接映射，value为Scrapy的file管道的存储形式
        :param str root_path:本地文件存储的根目录
        :param dict current_metadata:文件字段信息元数据
        :return:
        """
        # 获取具体元数据信息
        current_info_type = current_metadata.get("info_type", "size")

        # 根据数据获取对应的本地文件地址
        current_file = file_mapping.get(current_data)
        if not current_file:
            return {"result": False, "msg": f"调整文件信息字段时，未获取到实际文件：{current_file}"}

        # 根据文献信息写入类型调整
        if current_info_type == "md5":
            # 计算MD5并写回
            md5_result = BaseOSS.get_file_md5(str(os.path.join(root_path, current_file)))
            if not md5_result["result"]:
                raise Exception(f'计算文件MD5字段时，{md5_result["msg"]}')
            md5_result = md5_result["data"]
            return {"result": True, "msg": "ok", "data": md5_result}
        else:
            # 文件大小
            return {"result": True, "msg": "ok", "data": os.path.getsize(os.path.join(root_path, current_file))}

    def _handle_file_list(self, current_data, file_mapping, root_path, bucket_sign, oss_path_sign):
        """
        处理文件列表
        :author:Mabin
        :param list current_data:文件列表字段数据
        :param dict file_mapping:文件链接映射，value为Scrapy的file管道的存储形式
        :param str root_path:本地文件存储的根目录
        :param str bucket_sign:OSS bucket标识
        :param str oss_path_sign:OSS文件路径生成类别
        :return:
        """
        if current_data is None:
            current_data = []

        # 遍历其内部列表结构
        tmp_buf = []
        for current_item in current_data:
            accessory_name = current_item.get("accessory_name", None)
            accessory_url = current_item.get("url", None)

            # 执行上传
            upload_result = self._handle_file_upload(
                file_mapping=file_mapping, filed_data=accessory_url, root_path=root_path,
                bucket_sign=bucket_sign, oss_path_sign=oss_path_sign
            )
            if not upload_result["result"]:
                return {"result": False, "msg": f'执行文件列表字段文件上传时，{upload_result["msg"]}'}

            # 记录相关数据
            tmp_buf.append({
                "accessory_name": accessory_name,
                "accessory_url": upload_result["data"],
            })

        return {"result": True, "msg": "ok", "data": tmp_buf}

    def _handle_file_upload(
            self,
            file_mapping,
            filed_data,
            root_path,
            bucket_sign,
            oss_path_sign
    ):
        """
        执行文件上传
        :author:Mabin
        :param dict file_mapping:文件链接映射，value为Scrapy的file管道的存储形式
        :param str filed_data:文件目标链接
        :param str root_path:本地文件存储的根目录
        :param str bucket_sign:OSS bucket标识
        :param str oss_path_sign:OSS文件路径生成类别
        :return:
        """
        # 获取文件实际路径
        current_file = file_mapping.get(filed_data)
        if not current_file:
            return {"result": False, "msg": f"{filed_data}:该文件链接未查询到实际的下载结果"}
        current_file = current_file["path"]
        full_path = os.path.join(root_path, current_file)

        if bucket_sign == "local":
            # bucket类型为本地，则不必上传OSS，仅记录本地的相对路径（需要将文本转移至其他目录，避免被定期删除）
            move_result = self.move_file_with_relative_path(
                parent_dir=root_path,
                relative_path=current_file,
                dst_root=str(os.path.join(STORAGE_PATH, self.spider_name))
            )
            if not move_result:
                return {"result": False, "msg": f"文件路径替换管道在写回本地路径时，出现错误！{current_file}"}

            return {
                "result": True, "msg": "ok!", "data": current_file
            }

        # 实例化相关类
        oss_model = BaseOSS(bucket_sign=bucket_sign, instance_type=self.oss_instance_type)

        # 实例化相关路径
        oss_path = oss_model.generate_oss_path(local_file=str(full_path), target_type=oss_path_sign)
        if not oss_path["result"]:
            return {"result": False, "msg": f"生成文件OSS路径时报错，{oss_path['msg']}！"}
        oss_path = oss_path["data"]

        # 执行上传
        upload_result = oss_model.upload_file_object(local_file=str(full_path), oss_path=oss_path)
        if not upload_result["result"]:
            return {"result": False, "msg": f"上传文件到OSS时，{upload_result['msg']}！"}

        # 组织返回数据
        return {
            "result": True, "msg": "ok!",
            "data": {
                "file_path": oss_path,
                "bucket_name": oss_model.bucket_name
            }
        }

    @staticmethod
    def move_file_with_relative_path(parent_dir, relative_path, dst_root):
        """
        移动文件，源文件路径使用父目录 + 相对路径，将其移动至指定目录，并保持相对路径的目录结构
        :author:Mabin
        :param str parent_dir: 父目录（如 '/medpeer_hd/.../upload/'）
        :param str relative_path: 相对路径（如 '2025-08-28-15/xxx.jpg'）
        :param str dst_root: 目标根目录（如 '/medpeer_hd/.../storage/'）
        :return:
        """
        parent_dir = Path(parent_dir)
        relative_path = Path(relative_path)
        dst_root = Path(dst_root)

        # 源文件完整路径
        src_path = parent_dir / relative_path

        # 目标路径 = 目标根目录 + 相对路径
        dst_path = dst_root / relative_path

        # 检查源文件是否存在
        if not src_path.exists():
            return False

        # 创建目标目录（如果不存在）
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        # 如果目标文件已存在，则跳过
        if dst_path.exists():
            return True

        # 移动文件
        shutil.move(str(src_path), str(dst_path))
        return True
