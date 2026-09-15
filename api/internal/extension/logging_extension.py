
import logging
import os.path

from concurrent_log_handler import ConcurrentTimedRotatingFileHandler
from flask import Flask

# 第三方库日志清单，这些库在DEBUG级别下会输出海量连接/请求调试信息
NOISY_LOGGERS = [
    "httpx",
    "httpcore",
    "urllib3",
    "requests",
    "asyncio",
    "openai",
    "langchain",
    "langchain_core",
    "langchain_community",
    "langgraph",
    "langsmith",
    "celery",
    "kombu",
    "huggingface_hub",
    "transformers",
    "sentence_transformers",
    "filelock",
    "fsspec",
    "jieba",
    "weaviate",
]


def init_app(app: Flask):
    """日志记录器初始化"""
    # 1.判断是否处于开发环境，并推导日志级别
    is_dev = app.debug or os.getenv("FLASK_ENV") == "development"
    level = logging.DEBUG if is_dev else logging.WARNING

    # 2.设置根日志记录器级别
    logging.getLogger().setLevel(level)

    # 3.设置日志存储的文件夹，如果不存在则创建
    log_folder = os.path.join(os.getcwd(), "storage", "log")
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    # 4.定义日志的文件名与格式
    log_file = os.path.join(log_folder, "app.log")
    formatter = logging.Formatter(
        "[%(asctime)s.%(msecs)03d] %(filename)s -> %(funcName)s line:%(lineno)d [%(levelname)s]: %(message)s"
    )

    # 5.文件handler使用跨进程安全实现，因为API与Celery会同时写入同一个文件
    file_handler = ConcurrentTimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)

    # 6.开发环境额外输出到控制台，但只输出WARNING以上
    #    控制台IO在Windows上开销极高，若跟随DEBUG级别会显著拖慢请求响应
    if is_dev:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_handler)

    # 7.收敛第三方库的调试日志，避免海量DEBUG日志阻塞请求处理
    for name in NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
