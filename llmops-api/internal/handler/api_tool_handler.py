from typing import Any
from uuid import UUID

from injector import inject
from dataclasses import dataclass
from flask import request

from internal.core.tools.builtin_tools import providers
from internal.model import api_tool
from internal.schema.api_tool_schema import (
    ValidateOpenAPISchema, GetApiToolProviderResp, CreateApiToolReq,
    GetApiToolResp, GetApiToolProviderWithPageReq, GetApiToolProviderWithPageResp, UpdateApiToolProviderReq
)
from internal.service import ApiToolService
from pkg.paginator import paginator, PageModel
from pkg.response import validate_error_json, success_message, success_json


@inject
@dataclass
class ApiToolHandler:
    """ 自定义api """
    api_tool_service: ApiToolService


    def update_api_tool_provider(self, provider_id: UUID):
        req = UpdateApiToolProviderReq()
        if not req.validate():
            return validate_error_json(req.errors)

        self.api_tool_service.update_api_tool_provider(provider_id, req)
        return success_message("更新成功")

    def get_api_tool_providers_with_page(self):
        """ 获取api工具提供者列表 """
        req = GetApiToolProviderWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        api_tool_providers, paginator = self.api_tool_service.create_api_tool_providers_with_page(req)

        resp = GetApiToolProviderWithPageResp(many=True)
        return success_json(
            PageModel(list=resp.dump(api_tool_providers), paginator=paginator)
        )


    def create_api_tool_provider(self):
        """ 创建api """

        # 1. 校验
        req = CreateApiToolReq()
        if not req.validate():
            return validate_error_json(req.errors)
    #     2调用
        self.api_tool_service.create_api_tool(req)

        return success_message("创建自定义API成功")



    def get_api_tool(self, provider_id: UUID, tool_name: str):
        """"""

        api_tool_t = self.api_tool_service.get_api_tool(provider_id, tool_name)
        resp = GetApiToolResp()
        return success_json(resp.dump(api_tool_t))


    def get_api_tool_provider(self, provider_id: UUID):

        api_tool_provider = self.api_tool_service.get_api_tool_provider(provider_id)

        return success_json(
            GetApiToolProviderResp().dump(api_tool_provider)
        )

    def delete_api_tool_provider(self, provider_id: UUID):
        """ 删除api工具提供者 """
        self.api_tool_service.delete_api_tool_provider(provider_id)
        return success_message("删除成功")





    def validate_openapi_schema(self):
        """ 验证openapi_schema """
        req = ValidateOpenAPISchema()
        if not req.validate():
            return validate_error_json(req.errors)

        self.api_tool_service.parse_openapi_schema(req.openapi_schema.data)
        return success_message("数据验证成功")


