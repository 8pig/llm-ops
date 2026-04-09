from injector import inject
from dataclasses import dataclass

from pyarrow.lib import UUID

from internal.schema.api_tool_schema import ValidateOpenAPISchema, GetApiToolProviderResp, CreateApiToolReq
from internal.service import ApiToolService
from pkg.response import validate_error_json, success_message, success_json


@inject
@dataclass
class ApiToolHandler:
    """ 自定义api """
    api_tool_service: ApiToolService


    def create_api_tool(self):
        """ 创建api """

        # 1. 校验
        req = CreateApiToolReq()
        if not req.validate():
            return validate_error_json(req.errors)
    #     2调用
        self.api_tool_service.create_api_tool(req)

        return success_message("创建自定义API成功")


    def get_api_tool_provider(self, provider_id: UUID):

        api_tool_provider = self.api_tool_service.get_api_tool_provider(provider_id)

        return success_json(
            GetApiToolProviderResp().dump(api_tool_provider)
        )









    def validate_openapi_schema(self):
        """ 验证openapi_schema """
        req = ValidateOpenAPISchema()
        if not req.validate():
            return validate_error_json(req.errors)

        self.api_tool_service.parse_openapi_schema(req.openapi_schema.data)
        return success_message("数据验证成功")


