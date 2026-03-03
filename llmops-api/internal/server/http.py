import os

from flask import Flask

from config import Config
from internal.router import Router
from internal.exception import CustomException
from pkg.response import json, Response, HttpCode
from pkg.sqlalchemy import SQLAlchemy
from internal.model import App


class Http(Flask):

    def __init__(self, *args,conf: Config, db: SQLAlchemy, router: Router, **kwargs):
        super(Http, self).__init__(*args, **kwargs)


        # 注册绑定异常处理
        self.register_error_handler(Exception, self._register_error_handler)

        # 注册应用路由
        router.register_router(self)
        self.config.from_object(conf)

        # 初始化db
        db.init_app(self)
        with self.app_context():
            _ = App()
            db.create_all()



    def _register_error_handler(self, error: Exception):
        """注册异常处理"""
        print("异常", error)
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

