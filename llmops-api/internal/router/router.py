from injector import inject
from flask import Flask, Blueprint
from internal.handler import AppHandler, BuiltinToolHandler, ApiToolHandler
from dataclasses import dataclass


@inject
@dataclass
class Router:
    app_handler: AppHandler
    builtin_tool_handler: BuiltinToolHandler
    api_tool_handler: ApiToolHandler




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

        # 内置插件广场模块
        bp.add_url_rule(
            "/builtin-tools", methods=["get"],
            view_func=self.builtin_tool_handler.get_builtin_tools)
        bp.add_url_rule(
            "/builtin-tools/<string:provider_name>/tools/<string:tool_name>",
            methods=["get"], view_func=self.builtin_tool_handler.get_provider_tool)

        bp.add_url_rule(
            "/builtin-tools/<string:provider_name>/icon",
            view_func=self.builtin_tool_handler.get_provider_icon
        )
        bp.add_url_rule(
            "/builtin-tools/categories",
            view_func=self.builtin_tool_handler.get_provider_categories
        )

        #  自定义api插件模块
        bp.add_url_rule(
            "/api-tools/validate-openapi-schema",
            methods=["post"],
            view_func=self.api_tool_handler.validate_openapi_schema,
        )

        bp.add_url_rule(
            "/api-tools",
            methods=["post"],
            view_func=self.api_tool_handler.create_api_tool,
        )

        bp.add_url_rule(
            "/api-tools/<uuid:provider_id>",
            view_func=self.api_tool_handler.get_api_tool_provider,
        )

        app.register_blueprint(bp)

    def ping(self):
        return self.app_handler.ping()
