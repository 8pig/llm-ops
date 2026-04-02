from injector import inject
from dataclasses import dataclass

from pydantic import BaseModel

from internal.core.tools.builtin_tools.entities import provider_entity
from internal.core.tools.builtin_tools.providers import BuiltinProviderManager


@inject
@dataclass
class BuiltinToolService:
    """内置工具服务"""

    builtin_tool_manager: BuiltinProviderManager

    def get_builtin_tools(self) -> list:
        """获取llmops内置工具列表"""
        providers = self.builtin_tool_manager.get_providers()
        builtin_tools = []
        for provider in providers:
            provider_entity = provider.provider_entity
            builtin_tool = {
                **provider_entity.model_dump(exclude=["icon"]),
                "tools": []
            }
            # 循环便利提取提供者的所有工具实体
            for tool_entity in provider.get_tool_entities():
                # 构建工具实体信息
                tool_dict = {
                    **tool_entity.model_dump(),
                    "inputs": []
                }
                # 从提供者获取工具函数
                tool = provider.get_tool(tool_entity.name)
                #检测工具是否有args args_schema
                if hasattr(tool, "args_schema") and issubclass(tool.args_schema, BaseModel):
                    inputs = []
                    for field_name, model_field in tool.args_schema.__fields__.items():
                         inputs.append({
                             "name": field_name,
                             "description": model_field.field_info.description or "",
                             "required": model_field.required,
                             "type": model_field.outer_type.__name__,
                         })
                    tool_dict["inputs"] = inputs

                builtin_tool["tools"].append(tool_dict)

            return builtin_tools




    def get_provider_tool(self, provider_name: str, tool_name: str) -> dict:
        """根据供应商名+工具名 获取指定工具信息"""
        return self.builtin_tool_manager.get_tool(provider_name, tool_name)