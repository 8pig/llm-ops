from injector import inject
from dataclasses import dataclass


@inject
@dataclass
class BuiltinToolHandler:
    """内置工具处理"""
    def get_builtin_tools(self):
        """获取内置工具"""
        pass


    def get_provider_tool(self, provider_name: str, tool_name:str):
        """根据供应商名+工具名 获取指定工具信息"""
        pass