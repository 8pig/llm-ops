from dataclasses import dataclass
from typing import Type, Optional, Callable

import requests
from injector import inject
from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, create_model, Field

from internal.core.tools.api_tools.entities import ToolEntity, ParameterTypeMap, ParameterIn


@inject
@dataclass
class ApiProviderManager(BaseModel):
    """ Api provider管理器  根据传递的工具信息生成langchain tool"""

    @classmethod
    def _create_tool_func_from_tool_entity(cls, tool_entity: ToolEntity) -> Callable:
        """ 发起api请求 把参数openapi 参数转换为可执行的request"""
        def tool_func(**kwargs):
            #  获取tool参数 填充request

            parameters = {
                ParameterIn.PATH: {},
                ParameterIn.HEADER: {},
                ParameterIn.QUERY: {},
                ParameterIn.COOKIE: {},
                ParameterIn.REQUEST_BODY: {},
            }
            parameter_map = {parameter.get("name"): parameter  for parameter in tool_entity.parameters}
            header_map = {header.get("key"): header.get("value")  for header in tool_entity.headers}

            # 遍历校验
            for k, v in kwargs.items():
                parameter = parameter_map.get(k)
                if parameter is None:
                    continue

                parameters[parameter.get("in", ParameterIn.QUERY)][k] = v

            return requests.request(
                method=tool_entity.method,
                url=tool_entity.url.format(**parameters[ParameterIn.PATH]),
                params=parameters[ParameterIn.QUERY],
                headers={**header_map, **parameters[ParameterIn.HEADER]},
                cookies=parameters[ParameterIn.COOKIE],
                json=parameters[ParameterIn.REQUEST_BODY]
            ).text

        return tool_func



    def _create_model_from_parameters(cls, parameters: list[dict]) -> Type[BaseModel]:
        """ 根据参数生成pydantic model"""
        fields = {}
        for parameter in parameters:
            field_name = parameter.get("name")
            field_type = ParameterTypeMap.get(parameter.get("type"), str)
            field_required = parameter.get("required", True)
            field_description = parameter.get("description", "")

            fields[field_name] = (
                field_type if field_required else Optional(field_type),
                Field(description=field_description),
            )
        return create_model("DynamicModel", **fields)


    def get_tool(self, tool_entity: ToolEntity) -> BaseTool:
        return StructuredTool.from_function(
            # 函数转换
            func=self._create_tool_func_from_tool_entity(tool_entity),
            name=f"{tool_entity.id}_{tool_entity.name}",
            description=tool_entity.description,
            args_schema=self._create_model_from_parameters(tool_entity.parameters)
        )
