# -*- coding: utf-8 -*-

"""
# @Time    : 2025/11/11 10:06
# @User  : 刘子都
# @Descriotion  : 国自然科学基金项目推荐数据清洗模块配置文件
"""

# Database
DATABASES = {
    'default': {
        # 测试服转移至79，由于模型配置由系统组编写，且使用该数据库
        'HOST': '47.93.246.79',  # 主机
        'PORT': '3306',  # 端口
        'USER': 'test_medpeer',  # 账号
        'PASSWORD': 'Test_MedPeer',  # 密码
        'NAME': 'test_medpeer',  # 数据库名
        'CHARSET': 'utf8mb4',  # 字符集
    },
    'saas': {
        'HOST': '47.93.246.79',  # 主机
        'PORT': '3306',  # 端口
        'USER': 'test_medpeer',  # 账号
        'PASSWORD': 'Test_MedPeer',  # 密码
        'NAME': 'saas',  # 数据库名
        'CHARSET': 'utf8mb4',  # 字符集
    },
    'medicine': {
        'HOST': '192.168.1.243',  # 主机
        'PORT': '3306',  # 端口
        'USER': 'medpeer',  # 账号
        'PASSWORD': 'medpeer',  # 密码
        'NAME': 'medicine',  # 数据库名
        'CHARSET': 'utf8mb4',  # 字符集
    },



    # 本地测试数据库
    'medicine_test': {
        'HOST': 'localhost',  # 主机
        'PORT': '3306',  # 端口
        'USER': 'root',  # 账号
        'PASSWORD': '248655',  # 密码
        'NAME': 'medicine_test',  # 数据库名
        'CHARSET': 'utf8mb4',  # 字符集
    },
}