from typing import Any
from uuid import UUID

from flask_login import login_required, current_user
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

    @login_required
    def update_api_tool_provider(self, provider_id: UUID):
        req = UpdateApiToolProviderReq()
        if not req.validate():
            return validate_error_json(req.errors)

        self.api_tool_service.update_api_tool_provider(provider_id, req, current_user)
        return success_message("更新成功")

    @login_required
    def get_api_tool_providers_with_page(self):
        """ 获取api工具提供者列表 """
        req = GetApiToolProviderWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        api_tool_providers, paginator = self.api_tool_service.create_api_tool_providers_with_page(req, current_user)

        resp = GetApiToolProviderWithPageResp(many=True)
        return success_json(
            PageModel(list=resp.dump(api_tool_providers), paginator=paginator)
        )

    @login_required
    def create_api_tool_provider(self):
        """ 创建api """

        # 1. 校验
        req = CreateApiToolReq()
        if not req.validate():
            return validate_error_json(req.errors)
    #     2调用
        self.api_tool_service.create_api_tool(req, current_user)

        return success_message("创建自定义API成功")


    @login_required
    def get_api_tool(self, provider_id: UUID, tool_name: str):
        """"""

        api_tool_t = self.api_tool_service.get_api_tool(provider_id, tool_name, current_user)
        resp = GetApiToolResp()
        return success_json(resp.dump(api_tool_t))

    @login_required
    def get_api_tool_provider(self, provider_id: UUID):

        api_tool_provider = self.api_tool_service.get_api_tool_provider(provider_id, current_user)

        return success_json(
            GetApiToolProviderResp().dump(api_tool_provider)
        )

    @login_required
    def delete_api_tool_provider(self, provider_id: UUID):
        """ 删除api工具提供者 """
        self.api_tool_service.delete_api_tool_provider(provider_id, current_user)
        return success_message("删除成功")




    @login_required
    def validate_openapi_schema(self):
        """ 验证openapi_schema """
        req = ValidateOpenAPISchema()
        if not req.validate():
            return validate_error_json(req.errors)

        self.api_tool_service.parse_openapi_schema(req.openapi_schema.data)
        return success_message("数据验证成功")


