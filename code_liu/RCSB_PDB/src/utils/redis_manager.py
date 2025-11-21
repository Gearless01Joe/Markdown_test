# -*- coding: utf-8 -*-

"""
# @Time    : 2025/3/4 10:46
# @User  : Mabin
# @Description  :Redis数据库操作工具类（单例、连接池）
"""
import redis
from threading import Lock
from src.settings import REDIS_DATABASES


class RedisManager:
    """
    Redis数据库管理类
    :author Mabin
    使用示例(结合with)：
    test_model = RedisManager()
    with test_model.get_connection() as r:
        r.hset("1", "2", "3")

    使用示例（依次调用）
    test_model = RedisManager()
    r = test_model.get_connection()
    r.set('key', 'value')
    """
    _instances = {}  # 存储不同URI的连接实例
    _lock = Lock()  # 线程安全锁

    def __new__(cls, connect_key="default"):
        """
        单例核心逻辑
        :author Mabin
        :param str connect_key:数据库连接标识
        """
        if connect_key not in cls._instances:
            # 不存在对应连接标识的实例
            with cls._lock:
                # 实例化
                instance = super().__new__(cls)

                # 初始化数据库连接
                instance._init_connection(connect_key=connect_key)

                # 存储
                cls._instances[connect_key] = instance

        # 返回实例
        return cls._instances[connect_key]

    def _init_connection(self, connect_key="default"):
        """
        初始化新连接(连接池)
        :author Mabin
        :param str connect_key:数据库连接标识
        :return:
        """
        # 获取数据库链接配置
        connect_config = REDIS_DATABASES.get(connect_key, None)
        if not connect_config:
            raise Exception(f"创建Redis数据库连接时，未查询到数据库链接配置！{connect_key}")

        # 创建连接池（自动管理连接池）
        self.redis_pool = redis.ConnectionPool(
            host=connect_config["host"],
            port=connect_config["port"],
            db=connect_config["database"],
            password=connect_config["password"],
            max_connections=100,  # 最大连接数
            socket_connect_timeout=300,  # 连接超时(秒)
            socket_timeout=30,  # 操作超时
            decode_responses=True,  # 自动解码返回字符串
            health_check_interval=150,  # 健康检查间隔
        )

    def get_connection(self):
        """
        从连接池中获取连接
        :author Mabin
        :return:
        """
        return redis.StrictRedis(connection_pool=self.redis_pool)


if __name__ == '__main__':
    test_model = RedisManager()
    with test_model.get_connection() as r:
        r.hset("1", "2", "3")
