import io
import mimetypes

from flask import send_file
from injector import inject
from dataclasses import dataclass
from internal.service import BuiltinToolService
from pkg.response import success_json


@inject
@dataclass
class BuiltinToolHandler:


    builtin_tools_service: BuiltinToolService
    """内置工具处理"""
    def get_builtin_tools(self):
        """获取内置工具"""
        builtin_tools = self.builtin_tools_service.get_builtin_tools()
        return success_json(builtin_tools)


    def get_provider_tool(self, provider_name: str, tool_name:str):
        """根据供应商名+工具名 获取指定工具信息"""
        bt = self.builtin_tools_service.get_provider_tool(provider_name, tool_name)
        return success_json(bt)

    def get_provider_icon(self, provider_name: str):
        """ """
        icon, mimetype = self.builtin_tools_service.get_provider_icon(provider_name)

        return send_file(io.BytesIO(icon), mimetype=mimetype)

    def get_provider_categories(self):
        """获取所有分类"""
        pass