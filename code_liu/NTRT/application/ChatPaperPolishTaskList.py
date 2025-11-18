# -*- coding: utf-8 -*-

"""
# @Time    : 2025/8/14 11:09
# @User  : LGZ
# @Descriotion  :
"""
from sqlalchemy import Column, DateTime, Integer, JSON, text
from sqlalchemy.dialects.mysql import TEXT, TINYINT, VARCHAR
from application.web_utils.base_mysql import Base, BaseCRUD


class ChatPaperPolishTaskList(Base):
    __tablename__ = 'chat_paper_polish_task_list'
    __table_args__ = {'comment': '论文AI工具论文润色/校对任务列表', "extend_existing": True}

    list_id = Column(Integer, primary_key=True, comment='列表ID', autoincrement=True)
    task_id = Column(VARCHAR(32), nullable=False, index=True, comment='任务ID，以"paper_"为前缀的字符串')
    user_id = Column(Integer, nullable=False, index=True, comment='用户ID')
    task_name = Column(VARCHAR(255), nullable=False, comment='任务名称')
    task_type = Column(VARCHAR(32), nullable=False, server_default=text("'paper_polish'"), comment='任务类型，取值["paper_polish"(论文润色), "paper_proofread"(论文校对)]')
    paper_url = Column(JSON, nullable=False,
                       comment='论文文件存储地址，以数组方式记录，格式如{"bucket_name":"文件存储的bucket名称", "file_path":"文件在bucket下的存储路径"}，用户上传文件存储在OSS的medpeer-article下的ai_paper目录中')
    paper_length = Column(Integer, nullable=False, server_default=text("'0'"), comment='论文字符数，0为总量待定')
    yanzhi_consumption = Column(Integer, nullable=False, server_default=text("'0'"),
                                comment='研值消耗情况，0为消耗数额待定')
    paper_language = Column(VARCHAR(32), nullable=False, server_default=text("'eng'"), comment='论文语言，取值["chi"(中文), "eng"(英语)]')
    request_model = Column(VARCHAR(32), comment='请求的AI模型类型，表chat_paper_ai_model_dict的model_type字段标识')
    analyze_section = Column(TINYINT, comment='是否需要分析论文结构，仅对润色任务有效，0为否，1为是')
    yanzhi_actual = Column(Integer, comment='任务执行实际开销的研值成本，即任务各环节调用模型消耗的研值(yanzhi_expect)总和，只计算包干的开销，不包括单段润色/校对的开销')
    execution_status = Column(VARCHAR(32), comment='任务执行状态，取值["not_submit"(待提交), "analyze_section"(分析论文结构), "generate_guide"(生成润色指南), "do_task"(润色/校对中), "task_complete"(任务完成)]，对于校对任务暂无分析结构和指南生成状态')
    is_del = Column(TINYINT, nullable=False, server_default=text("'0'"), comment='是否删除，0为否，1为是')
    update_time = Column(DateTime, comment='更新时间')
    create_time = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), comment='创建时间')


class ChatPaperPolishTaskListModel(BaseCRUD):
    model = ChatPaperPolishTaskList
