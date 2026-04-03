from injector import inject
from dataclasses import dataclass
from internal.exception import NotFoundException

from pydantic import BaseModel

from internal.core.tools.builtin_tools.entities import provider_entity, tool_entity
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
                **provider_entity.model_dump(exclude={"icon"}),
                "tools": []
            }
            # 循环便利提取提供者的所有工具实体
            for tool_entity in provider.get_tool_entities():
                # 构建工具实体信息
                tool = provider.get_tool(tool_entity.name)
                tool_dict = {
                    **tool_entity.model_dump(),
                    "inputs": self.get_tool_inputs(tool)
                }
                # 从提供者获取工具函数


                #检测工具是否有args args_schema

                builtin_tool["tools"].append(tool_dict)

            builtin_tools.append(builtin_tool)

        return builtin_tools




    def get_provider_tool(self, provider_name: str, tool_name: str) -> dict:
        """根据供应商名+工具名 获取指定工具信息"""
        print(provider_name, tool_name)
        provider = self.builtin_tool_manager.get_provider(provider_name)
        if provider is None:
            raise NotFoundException(f"未找到供应商: {provider_name}")

        tool_entity = provider.get_tool_entity(tool_name)
        if tool_entity is None:
            raise NotFoundException(f"未找到工具: {tool_name}")

        provider_entity = provider.provider_entity
        tool = provider.get_tool(tool_name)
        return {
           "provider": {**provider_entity.model_dump(exclude={"icon","create_at"})} ,
            **tool_entity.model_dump(),
            "create_at": provider_entity.create_at,
            "inputs": self.get_tool_inputs(tool)
        }


    @classmethod
    def get_tool_inputs(cls, tool: str) -> list:
        inputs = []
        if hasattr(tool, "args_schema") and issubclass(tool.args_schema, BaseModel):

            for field_name, field_info in tool.args_schema.model_fields.items():
                inputs.append({
                    "name": field_name,
                    "description": field_info.description or "",
                    "required": field_info.is_required(),
                    "type": field_info.annotation.__name__
                    if hasattr(field_info.annotation, '__name__') else
                    str(field_info.annotation),
                })
        return  inputs