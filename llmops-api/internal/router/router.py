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

        bp.add_url_rule("/apps/<uuid:app_id>/debug", methods=["post"], view_func=self.app_handler.debug)

        # bp.add_url_rule("/app", methods=["post"], view_func=self.app_handler.create_app)
        # bp.add_url_rule("/app/<id>", methods=["get"], view_func=self.app_handler.get_app)
        # bp.add_url_rule("/app/<id>", methods=["post"], view_func=self.app_handler.update_app)
        # bp.add_url_rule("/app/<id>", methods=["delete"], view_func=self.app_handler.delete_app)
        # 3. 应用注册蓝图
        app.register_blueprint(bp)

    def ping(self):
        return self.app_handler.ping()
