# -*- coding: utf-8 -*-

"""
# @Time    : 2023/8/11 9:55
# @User  : Mabin
# @Descriotion  :MySQL数据库连接工具
"""
from sqlalchemy import create_engine
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from application.settings import DATABASES
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.decl_api import DeclarativeMeta

# 数据库模型或类（ORM 模型）的基类
Base = declarative_base()

# 初始化数据库连接
session_dict = {}
for database_key, database_item in DATABASES.items():
    # 组织数据库链接
    tmp_database_url = f"mysql+pymysql://{database_item['USER']}:{database_item['PASSWORD']}" \
                       f"@{database_item['HOST']}:{database_item['PORT']}/{database_item['NAME']}" \
                       f"?charset={database_item['CHARSET']}"

    # 创建 SQLAlchemy 引擎
    engine = create_engine(
        tmp_database_url, pool_pre_ping=True,
        # poolclass=NullPool
    )

    # 创建SessionLocal类
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session_dict[database_key] = SessionLocal


class BaseCRUD:
    model = None

    def create_single_info(self, db, create_data, create_cond, **extra_param):
        """
        单条创建信息
        :param db:
        :param dict create_data:创建时使用的数据
        :param list create_cond:数据查询条件
        :param any extra_param:额外参数，用于拓展字段
        :return:
        """
        if not all([create_data, create_cond]):
            return {"result": False, "msg": "传入参数为空！"}

        existing_record = db.query(self.model).filter(*create_cond).first()
        if existing_record:
            return {"result": False, "msg": "数据已经存在！"}

        # 不存在，则执行创建
        create_res = self.model(**create_data)
        db.add(create_res)

        # 判断是否提交
        if extra_param.get("is_commit", True):
            db.commit()
            db.refresh(create_res)

        return {"result": True, "msg": "ok！"}

    def create_single(self, db, create_data, **extra_param):
        """
        单条创建信息不判重
        :param db:
        :param dict create_data:创建时使用的数据
        :param any extra_param:额外参数，用于拓展字段
            auto_field=>"返回的自增ID字段"
        :return:
        """
        if not create_data:
            return {"result": False, "msg": "传入参数为空！"}

        # 获取额外字段
        auto_field = extra_param.get("auto_field", None)

        create_res = self.model(**create_data)
        db.add(create_res)
        db.commit()
        db.refresh(create_res)

        # 获取自增ID
        auto_field_val = None
        if auto_field:
            auto_field_val = getattr(create_res, auto_field)

        return {"result": True, "msg": "ok！", "data": auto_field_val}

    def batch_create_info(self, db, create_list, **extra_param):
        """
        批量创新数据不判重
        :param db:
        :param list create_list:待插入的数据
        :param extra_param:
        :return:
        """
        if not create_list:
            return {"result": False, "msg": "传入参数为空！"}

        # 插入数据
        db.bulk_insert_mappings(self.model, create_list)
        db.commit()

        return {"result": True, "msg": "ok！"}

    def update_data_info(self, db, update_data, update_cond, **extra_param):
        """
        修改目标数据
        :author:HJL
        :param db :
        :param dict update_data:待修改数据
        :param list update_cond:修改条件
        :param any extra_param:额外参数，用于拓展字段
        :return:
        """
        if not all([update_data, update_cond]):
            return {"result": False, "msg": "传入参数为空！"}

        # 检查数据是否存在
        exist = db.query(self.model).filter(*update_cond).first()
        if not exist:
            return {"result": False, "msg": "待修改的数据不存在！"}

        # 获取历史信息
        history_dict = self._get_model_dict(exist)

        # 更新数据
        for key, value in update_data.items():
            setattr(exist, key, value)
            flag_modified(exist, key)

        # 判断是否提交
        if extra_param.get("is_commit", True):
            db.commit()

        return {"result": True, "msg": "数据修改成功！", "history": history_dict}

    def get_single_info(self, db, field, where=None, **extra_param):
        """
        单条查询信息
        :author Hjl
        :param db:
        :param list field:查询字段 [model.Column]
        :param list where:查询条件 [MyModel.field1 == 'some_value', MyModel.field2 > 10]
        :param any extra_param:额外参数，用于拓展字段
            order=>查询条件
        :return:
        """
        if not field:
            return {"result": False, "msg": "传入参数为空！"}

        # 获取额外参数
        order = extra_param.get("order")  # 排序条件

        query = db.query(self.model).with_entities(*field)

        if where:
            query = query.filter(*where)

        # 加入排序条件
        if order:
            query = query.order_by(*order)

        # 判断数据是否存在
        query_res = query.first()
        if not query_res:
            return {"result": False, "msg": "相关数据不存在！", "data": {}}

        return {"result": True, "msg": "查询成功！", "data": query_res._mapping}

    def get_list_info(self, db, field, where=None, first_row=None, list_rows=None, order=None, **extra_param):
        """
        获取列表信息
        :author: Hjl
        :param db:
        :param list field:查询字段 [model.Column]
        :param list where:查询条件 [MyModel.field1 == 'some_value', MyModel.field2 > 10]
        :param int|None first_row:起始行数
        :param int|None list_rows:每页显示行数
        :param tuple order:排序字段
        :param any extra_param:额外参数，用于拓展字段
            q_list=>Q查询列表（该查询用于实现or、and）
        """
        if not field:
            return {"result": False, "msg": "传入参数为空！"}

        query = db.query(self.model).with_entities(*field)

        if where:
            query = query.filter(*where)

        # 加入排序条件
        if order:
            query = query.order_by(*order)

        # 加入分页信息
        if first_row:
            query = query.offset(first_row)
        if list_rows:
            query = query.limit(list_rows)

        # 判断数据是否存在
        query_res = query.all()
        if not query_res:
            return {"result": True, "msg": "相关数据不存在！", "data": []}

        # 组织返回数据
        buf = []
        for query_item in query_res:
            buf.append(query_item._mapping)

        return {"result": True, "msg": "ok！", "data": buf}

    def get_count_info(self, db, where=None):
        """
        获取数据库查询数量
        :author Mabin
        :param db:
        :param where:
        :return:
        """
        if where:
            # 组织查询条件
            query_count = db.query(self.model).filter(*where).count()
        else:
            query_count = db.query(self.model).count()

        # 返回查询结果
        return query_count

    @staticmethod
    def _get_model_dict(model_object):
        """
        获取模型类的字典格式
        :author Mabin
        :param DeclarativeMeta model_object:sqlalchemy模型类
        :return:
        """
        buf = {}
        for c in inspect(model_object).mapper.column_attrs:
            buf[c.key] = getattr(model_object, c.key)

        return buf
