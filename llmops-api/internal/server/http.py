import os

from flask import Flask, send_from_directory
from flask_migrate import Migrate
from werkzeug.exceptions import NotFound

from config import Config
from internal.router import Router
from internal.exception import CustomException
from pkg.response import json, Response, HttpCode
from pkg.sqlalchemy import SQLAlchemy
from internal.model import App
from flask_migrate import Migrate


class Http(Flask):

    def __init__(
            self,
            *args,
            conf: Config,
            db: SQLAlchemy,
            migrate: Migrate,
            router: Router,
            **kwargs
    ):
        super(Http, self).__init__(*args, **kwargs)

        # 注册绑定异常处理
        self.register_error_handler(Exception, self._register_error_handler)

        # 注册 favicon 路由
        self.add_url_rule('/favicon.ico', view_func=self._favicon)

        # 注册应用路由
        router.register_router(self)
        self.config.from_object(conf)

        # 配置 JSON 序列化：支持中文显示（必须在 from_object 之后）
        self.json.ensure_ascii = False  # Flask 2.2+ 的新 API

        # 初始化db
        db.init_app(self)
        migrate.init_app(self, db, directory="internal/migration")
        # with self.app_context():
        #     _ = App()
        # db.create_all()

    def _favicon(self):
        """返回默认的 favicon"""
        return '', 204

    def _register_error_handler(self, error: Exception):
        """注册异常处理"""
        print("异常", error)

        # 处理 404 错误
        if isinstance(error, NotFound):
            return json(Response(
                code=HttpCode.NOT_FOUND,
                message="请求的资源不存在",
                data={}
            ))

        if isinstance(error, CustomException):
            return json(Response(
                code=error.code,
                message=error.message,
                data=error.data if error.data is not None else {}
            ))
        if self.debug or os.getenv("FLASK_ENV") == "development":
            raise error
        else:
            return json(Response(
                code=HttpCode.FAIL,
                message=str(error),
                data={}
            ))



