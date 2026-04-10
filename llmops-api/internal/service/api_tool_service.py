from dataclasses import dataclass
from uuid import UUID

from injector import inject

import json

from internal.core.tools.api_tools.entities import OpenAPISchema
from internal.exception import ValidateException, NotFoundException
from internal.model import ApiToolProvider, ApiTool, api_tool
from internal.schema.api_tool_schema import CreateApiToolReq
from pkg.sqlalchemy import SQLAlchemy

@inject
@dataclass
class ApiToolService:
    """ 自定义api服务 """

    db: SQLAlchemy


    def get_api_tool(self, provider_id, tool_name):
        """根据id name 获取对应工具参数详情"""
        account_id = "550e8400-e29b-41d4-a716-446655440000"
        api_tool = self.db.session.query(ApiTool).filter_by(
            provider_id=provider_id,
            name=tool_name
        ).one_or_none()
        if api_tool is None or str(api_tool.account_id) != account_id:
            raise NotFoundException(f"该工具不存在{tool_name}")

        return api_tool



    def get_api_tool_provider(self, provider_id) -> ApiToolProvider:
        account_id = "550e8400-e29b-41d4-a716-446655440000"



        api_tool_provider = self.db.session.query(ApiToolProvider).get(
            provider_id
        )
        if api_tool_provider is None or str(api_tool_provider.account_id) != account_id:
            raise NotFoundException("该工具提供者不存在")

        return api_tool_provider



    def create_api_tool(self, req: CreateApiToolReq):
        """ 根据请求创建api """

        # 1. 校验http://127.0.0.1:4523/m1/7855483-7604388-default/builtin-tools

        # 2. 验证openapi_schema
        # todo 认证授权
        account_id = "550e8400-e29b-41d4-a716-446655440000"

        openapi_schema = self.parse_openapi_schema(req.openapi_schema.data)
        print("111")
        print({
            'name': req.name.data,
            'icon': req.icon.data,
            'openapi_schema': req.openapi_schema.data[:100] + '...',  # 只打印前100字符
            'headers': req.headers.data
        })

        api_tool_provider = self.db.session.query(ApiToolProvider).filter(
            ApiToolProvider.account_id == account_id,
            ApiToolProvider.name == req.name.data
        ).one_or_none()
        if api_tool_provider:
            raise ValidateException(f"该名称已存在{req.name.data}")

        with self.db.auto_commit():
            api_tool_provider = ApiToolProvider(
                account_id=account_id,
                name=req.name.data,
                description=openapi_schema.description,
                openapi_schema=req.openapi_schema.data,
                headers=req.headers.data,
            )
            self.db.session.add(api_tool_provider)
            self.db.session.flush()

            for path, path_item in openapi_schema.paths.items():
                for method, method_item in path_item.items():
                    api_tool = ApiTool(
                        account_id=account_id,
                        provider_id=api_tool_provider.id,
                        name=method_item.get("operationId"),
                        description=method_item.get("description"),
                        url=f"{openapi_schema.server}{path}",
                        method=method,
                        parameters=method_item.get("parameters"),
                    )
                    self.db.session.add(api_tool)

    def delete_api_tool_provider(self, provider_id: UUID):

        account_id = "550e8400-e29b-41d4-a716-446655440000"

        api_tool_provider = self.db.session.query(ApiToolProvider).get(provider_id)
        print("1111")
        if api_tool_provider is None or str(api_tool_provider.account_id) != account_id:
            raise NotFoundException("该工具提供者不存在")

        with self.db.auto_commit():
            self.db.session.query(ApiTool).filter(
                ApiTool.provider_id == provider_id,
                ApiTool.account_id == account_id
            ).delete()

            self.db.session.delete(api_tool_provider)



        pass


    @classmethod
    def parse_openapi_schema(cls, openapi_schema_str: str):
        """ 验证openapi_schema str """

        try:
            data = json.loads(openapi_schema_str)
            if not isinstance(data, dict):
                raise
        except Exception as e:
            raise ValidateException("传递数据必须符合OpenAPI规范")

        return OpenAPISchema(**data)


