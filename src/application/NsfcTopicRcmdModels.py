# -*- coding: utf-8 -*-

"""
# @Time    : 2025/11/11 11:28
# @User  : 刘子都
# @Description  : 国自然选题推荐数据清洗模块ORM模型
"""
from sqlalchemy import Column, Integer, JSON
from base_mysql import Base, BaseCRUD


class NsfcTopicRcmdTaskList(Base):
    """国自然选题推荐任务列表"""
    __tablename__ = 'nsfc_topic_rcmd_task_list'
    __table_args__ = {
        'comment': '国自然选题推荐任务列表', "extend_existing": True
    }

    list_id = Column(Integer, primary_key=True, comment='列表ID', autoincrement=True)
    breadth_search = Column(JSON, comment='广度搜索结果，JSON格式')


class NsfcTopicRcmdTaskTopicList(Base):
    """国自然选题推荐主题列表"""
    __tablename__ = 'nsfc_topic_rcmd_task_topic_list'
    __table_args__ = {
        'comment': '国自然选题推荐主题列表', "extend_existing": True
    }

    list_id = Column(Integer, primary_key=True, comment='列表ID', autoincrement=True)
    cited_articles = Column(JSON, comment='引用文献，JSON格式')


class NsfcTopicRcmdTaskAppInfo(Base):
    """国自然选题推荐应用信息"""
    __tablename__ = 'nsfc_topic_rcmd_task_app_info'
    __table_args__ = {
        'comment': '国自然选题推荐应用信息', "extend_existing": True
    }

    list_id = Column(Integer, primary_key=True, comment='列表ID', autoincrement=True)
    cited_articles = Column(JSON, comment='引用文献，JSON格式')


class CleaningModelMixin(BaseCRUD):
    """数据清洗通用 CRUD 操作封装。"""

    def fetch_records_for_cleaning(self, db, field_name, extra_filters=None, offset=None, limit=None):
        """查询需要清洗的记录。

        :param db: 数据库会话
        :param field_name: 目标字段名
        :param extra_filters: 额外过滤条件列表
        :param offset: 起始偏移量
        :param limit: 返回数量上限
        :return: 查询结果列表，格式为 [{'id': record_id, field_name: field_value}, ...]
        :author: LZD
        :date: 2025/11/10
        """
        if self.model is None:
            raise ValueError("未设置模型类，无法执行查询。")

        where_conditions = [
            getattr(self.model, field_name).isnot(None)
        ]

        if extra_filters:
            where_conditions.extend(extra_filters)

        field = [self.model.list_id, getattr(self.model, field_name)]
        result = self.get_list_info(
            db,
            field,
            where_conditions,
            first_row=offset,
            list_rows=limit,
            order=(self.model.list_id.asc(),)
        )
        if result.get('result'):
            return [
                {'id': item['list_id'], field_name: item[field_name]}
                for item in result.get('data', [])
            ]
        return []

    def batch_update_field(self, db, field_name, updates, batch_size=100):
        """批量更新字段。

        :param db: 数据库会话
        :param field_name: 更新字段名
        :param updates: 待写入的 (id, processed_data) 列表
        :param batch_size: 批量处理大小
        :return: 受影响的行数
        :author: LZD
        :date: 2025/11/10
        """
        if self.model is None:
            raise ValueError("未设置模型类，无法执行更新。")

        if not updates:
            return 0

        total_rows = 0
        # 按批次执行更新
        for start in range(0, len(updates), batch_size):
            chunk = updates[start:start + batch_size]
            for record_id, processed_data in chunk:
                # 使用BaseCRUD的update_data_info方法
                update_result = self.update_data_info(
                    db,
                    {field_name: processed_data},
                    [self.model.list_id == record_id],
                    is_commit=False
                )
                if update_result.get('result'):
                    total_rows += 1

        return total_rows


class NsfcTopicRcmdTaskListModel(CleaningModelMixin):
    """任务列表CRUD操作"""
    model = NsfcTopicRcmdTaskList


class NsfcTopicRcmdTaskTopicListModel(CleaningModelMixin):
    """主题列表CRUD操作"""
    model = NsfcTopicRcmdTaskTopicList


class NsfcTopicRcmdTaskAppInfoModel(CleaningModelMixin):
    """应用信息CRUD操作"""
    model = NsfcTopicRcmdTaskAppInfo

