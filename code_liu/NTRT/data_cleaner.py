# -*- coding: utf-8 -*-

"""
# @Time    : 2025/11/10 13:41
# @User  : 刘子都
# @Descriotion  : 国自然科学基金项目推荐数据清洗模块
                  实现breadth_search和cited_articles字段的数据清洗和标准化处理
"""

import json

from sqlalchemy import or_, func

from base_mysql import session_dict
from application.NsfcTopicRcmdModels import (
    NsfcTopicRcmdTaskListModel,
    NsfcTopicRcmdTaskTopicListModel,
    NsfcTopicRcmdTaskAppInfoModel
)


BATCH_SIZE = 100
DEFAULT_DB_KEY = 'medicine'


class DataCleaner:
    """数据清洗类，负责数据库操作和数据清洗流程"""

    def __init__(self):
        """初始化数据清洗器。

        :author: LZD
        :date: 2025/11/10
        """
        self.db_key = DEFAULT_DB_KEY
        self.batch_size = BATCH_SIZE
        try:
            self._task_list_model = NsfcTopicRcmdTaskListModel()
            self._topic_list_model = NsfcTopicRcmdTaskTopicListModel()
            self._app_info_model = NsfcTopicRcmdTaskAppInfoModel()
        except Exception as exc:
            raise RuntimeError(f"初始化数据模型失败: {exc}") from exc

    def run(self):
        """执行所有清洗任务。

        :author: LZD
        :date: 2025/11/10
        """
        session = self._open_session()
        try:
            print("=" * 60)
            print("开始执行数据清洗任务")
            print(f"数据库: {self.db_key}")
            print("=" * 60)
            print()

            cleaning_plan = [
                {
                    'model_class': NsfcTopicRcmdTaskListModel,
                    'field_name': 'breadth_search',
                    'extra_filters': [
                        or_(
                            func.json_contains_path(
                                NsfcTopicRcmdTaskListModel.model.breadth_search,
                                'one',
                                '$.article_addition'
                            ) == 1,
                            func.json_contains_path(
                                NsfcTopicRcmdTaskListModel.model.breadth_search,
                                'one',
                                '$.project_addition'
                            ) == 1
                        )
                    ],
                    'processor': self._process_breadth_search,
                    'display_name': 'breadth_search 字段',
                },
                {
                    'model_class': NsfcTopicRcmdTaskTopicListModel,
                    'field_name': 'cited_articles',
                    'extra_filters': [
                        func.json_type(
                            NsfcTopicRcmdTaskTopicListModel.model.cited_articles
                        ) == 'ARRAY'
                    ],
                    'processor': self._process_cited_articles,
                    'display_name': '主题列表表的 cited_articles 字段',
                },
                {
                    'model_class': NsfcTopicRcmdTaskAppInfoModel,
                    'field_name': 'cited_articles',
                    'extra_filters': [
                        func.json_type(
                            NsfcTopicRcmdTaskAppInfoModel.model.cited_articles
                        ) == 'ARRAY'
                    ],
                    'processor': self._process_cited_articles,
                    'display_name': '应用信息表的 cited_articles 字段',
                },
            ]

            for task in cleaning_plan:
                self._clean_dataset(
                    session=session,
                    model_class=task['model_class'],
                    field_name=task['field_name'],
                    extra_filters=task['extra_filters'],
                    processor=task['processor'],
                    display_name=task['display_name'],
                )

            print("=" * 60)
            print("所有数据清洗任务完成！")
            print("=" * 60)
        finally:
            session.close()

    def _process_records(self, records, field_name, processor_func):
        """对查询结果进行处理并生成更新内容。

        :param records: 原始记录列表
        :param field_name: 需要处理的字段名
        :param processor_func: 数据处理函数
        :return: (updates, processed_count, skipped_count)
        :author: LZD
        :date: 2025/11/10
        """
        updates = []
        processed = 0
        skipped = 0

        if not records:
            return updates, processed, skipped

        for record in records:
            record_id = record.get('id')
            raw_payload = record.get(field_name)

            if not record_id or raw_payload is None:
                skipped += 1
                continue

            # ORM 会自动将 JSON 字段反序列化为 Python 对象（dict/list）
            # 如果已经是 dict 或 list，直接使用；如果是字符串，则解析 JSON
            if isinstance(raw_payload, (dict, list)):
                parsed_payload = raw_payload
            elif isinstance(raw_payload, str):
                try:
                    parsed_payload = json.loads(raw_payload)
                except json.JSONDecodeError:
                    skipped += 1
                    continue
            else:
                skipped += 1
                continue

            processed_payload = processor_func(parsed_payload)
            if processed_payload is None:
                skipped += 1
                continue

            updates.append((record_id, processed_payload))
            processed += 1

        return updates, processed, skipped

    def _get_model_instance(self, model_class):
        """获取已初始化的模型实例。

        :param model_class: 模型类
        :return: 模型实例
        :author: LZD
        :date: 2025/11/10
        """
        if model_class == NsfcTopicRcmdTaskListModel:
            return self._task_list_model
        elif model_class == NsfcTopicRcmdTaskTopicListModel:
            return self._topic_list_model
        elif model_class == NsfcTopicRcmdTaskAppInfoModel:
            return self._app_info_model
        else:
            raise ValueError(f"未注册的模型类: {model_class}")

    def _fetch_records_with_condition(self, session, model_class, field_name, extra_filters=None, offset=None, limit=None):
        """使用模型类查询满足条件的记录。

        :param session: 数据库会话
        :param model_class: CRUD模型类
        :param field_name: 目标字段名
        :param extra_filters: 额外的过滤条件列表
        :param offset: 起始偏移量
        :param limit: 分页大小
        :return: 查询结果列表，格式为 [{'id': record_id, field_name: field_value}, ...]
        :author: LZD
        :date: 2025/11/10
        """
        model = self._get_model_instance(model_class)
        records = model.fetch_records_for_cleaning(
            session,
            field_name,
            extra_filters or [],
            offset=offset,
            limit=limit
        )
        return records

    def _write_updates(self, session, model_class, field_name, updates):
        """使用模型类将处理结果写回数据库。

        :param session: 数据库会话
        :param model_class: CRUD模型类
        :param field_name: 更新字段名
        :param updates: 待写入的 (id, processed_data) 列表
        :return: 受影响的行数
        :author: LZD
        :date: 2025/11/10
        """
        if not updates:
            return 0

        model = self._get_model_instance(model_class)
        try:
            total_rows = model.batch_update_field(session, field_name, updates, self.batch_size)
            session.commit()
            return total_rows
        except Exception:
            session.rollback()
            raise

    def _clean_dataset(self, session, model_class, field_name, extra_filters, processor, display_name):
        """通用清洗流程封装。

        :param session: 数据库会话
        :param model_class: CRUD模型类
        :param field_name: 字段名称
        :param extra_filters: 额外过滤条件列表
        :param processor: 数据处理回调函数
        :param display_name: 用于输出的展示名称
        :author: LZD
        :date: 2025/11/10
        """
        print(f"开始清洗{display_name}...")
        total_found = 0
        total_processed = 0
        total_skipped = 0
        total_updated = 0
        offset = 0

        while True:
            records = self._fetch_records_with_condition(
                session, model_class, field_name, extra_filters, offset=offset, limit=self.batch_size
            )
            if not records:
                break

            total_found += len(records)
            updates, processed, skipped = self._process_records(
                records, field_name, processor
            )
            total_processed += processed
            total_skipped += skipped
            updated_rows = self._write_updates(
                session, model_class, field_name, updates
            )
            total_updated += updated_rows
            offset += len(records)

        print(f"  查询到 {total_found} 条记录")
        print(f"  处理成功: {total_processed} 条，跳过: {total_skipped} 条")
        print(f"  更新成功: {total_updated} 条记录")
        print(f"{display_name} 清洗完成\n")

    def _open_session(self):
        """打开数据库会话。

        :return: SQLAlchemy Session 实例
        :author: LZD
        :date: 2025/11/10
        """
        if session_dict is None:
            raise ImportError("base_mysql.session_dict 未找到")

        session_factory = session_dict.get(self.db_key)
        if not session_factory:
            raise KeyError(f"Unknown database alias: {self.db_key}")

        session = session_factory()
        return session

    @staticmethod
    def _process_cited_articles(data):
        """将引用文献数组整理成以 object_id 为键的字典。

        :param data: 原始引用数组
        :return: 标准化后的引用信息字典
        :author: LZD
        :date: 2025/11/10
        """
        if not isinstance(data, (list, tuple)):
            return None

        result = {}
        for item in data:
            if not isinstance(item, dict):
                continue

            object_id = item.get('object_id')
            object_type = item.get('object_type')
            object_info = item.get('object_info', {})

            if not object_id:
                continue

            if object_type == 'project':
                result[object_id] = DataCleaner._standardize_project_info(object_info)
            else:
                result[object_id] = object_info.copy()

        return result

    @staticmethod
    def _process_breadth_search(data):
        """解析 breadth_search，合并项目与文章信息。

        :param data: breadth_search 字段内容
        :return: 扁平化后的数据
        :author: LZD
        :date: 2025/11/10
        """
        if not isinstance(data, dict):
            return None

        result = {}

        # 处理项目数据：需要标准化
        project_addition = data.get('project_addition', {})
        if isinstance(project_addition, dict):
            for object_id, project_data in project_addition.items():
                if isinstance(project_data, dict):
                    result[object_id] = DataCleaner._standardize_project_info(project_data)

        # 处理文章数据：直接复制
        article_addition = data.get('article_addition', {})
        if isinstance(article_addition, dict):
            for object_id, article_data in article_addition.items():
                if isinstance(article_data, dict):
                    result[object_id] = article_data.copy()

        return result

    @staticmethod
    def _standardize_project_info(object_info):
        """将项目 object_info 转换为统一字段命名和格式。

        :param object_info: 原始项目字段
        :return: 标准化后的项目字段
        :author: LZD
        :date: 2025/11/10
        """
        if not isinstance(object_info, dict):
            return {}

        processed = {}

        field_mapping = {
            'unit_name': 'project_unit',
            'leader_name': 'project_leader',
            'category_name': 'project_category',
            'abstract': 'chs_abstract',
            'project_id': 'related_article',
        }
        for old_field, new_field in field_mapping.items():
            if old_field in object_info:
                processed[new_field] = object_info[old_field]

        apply_code = object_info.get('apply_code')
        if apply_code:
            processed['apply_code'] = {
                'apply_code': apply_code,
                'code_name': object_info.get('subject_info', ''),
            }

        project_keyword = object_info.get('project_keyword')
        if isinstance(project_keyword, str):
            processed['project_keyword'] = [
                keyword.strip() for keyword in project_keyword.split(',')
                if keyword.strip()
            ]
        elif isinstance(project_keyword, list):
            processed['project_keyword'] = project_keyword

        processed['type'] = 'nsfc_project'

        # 保留未显式处理的其他字段，避免信息丢失
        mapped_fields = set(field_mapping.keys())
        excluded_fields = {'apply_code', 'subject_info', 'related_project'}
        for original_key, original_value in object_info.items():
            if original_key in mapped_fields or original_key in excluded_fields:
                continue
            if original_key in processed:
                continue
            processed[original_key] = original_value

        return processed


if __name__ == '__main__':
    DataCleaner().run()
