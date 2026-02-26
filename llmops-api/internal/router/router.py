from injector import inject
from flask import Flask, Blueprint
from internal.handler import AppHandler
from dataclasses import dataclass


@inject
@dataclass
class Router:
    def __init__(self, app_handler: AppHandler):
        self.app_handler = app_handler

    def register_router(self, app: Flask):
        """注册路由"""
        # 1. 创建一个蓝图
        bp = Blueprint("llmops", __name__, url_prefix="")

        # 2. url 与控制器绑定
        bp.add_url_rule("/ping", view_func=self.ping, methods=["GET"])

        # 3. 应用注册蓝图
        app.register_blueprint(bp)

    def ping(self):
        return self.app_handler.ping()
