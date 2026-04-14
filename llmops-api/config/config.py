import os
from typing import Any


def _get_env(key: str) -> Any:
    """获取配置"""
    return os.getenv(key)

def _get_bool_env(key: str):
    value = _get_env(key)
    return value.lower() == "true" if value is not None else False

class Config:
    """配置类"""
    def __init__(self):
        # 禁用csrf
        self.WTF_CSRF_ENABLED = _get_bool_env("WTF_CSRF_ENABLED")

        # 数据库配置
        self.SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
        self.SQLALCHEMY_ENgINE_OPTIONS = {
            "pool_size": int(_get_env("SQLALCHEMY_POOL_SIZE")),
            "pool_recycle": int(_get_env("SQLALCHEMY_POOL_RECYCLE"))
        }
        self.SQLALCHEMY_ECHO = _get_bool_env("SQLALCHEMY_ECHO")

        #REDIS
        self.REDIS_HOST = _get_env("REDIS_HOST")
        self.REDIS_PORT = int(_get_env("REDIS_PORT"))
        self.REDIS_PASSWORD = _get_env("REDIS_PASSWORD")
        self.REDIS_USERNAME = _get_bool_env("REDIS_USERNAME")
        self.REDIS_USE_SSL = _get_bool_env("REDIS_USE_SSL")
        self.REDIS_DB = int(_get_env("REDIS_DB"))

