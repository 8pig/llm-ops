from injector import inject
from dataclasses import dataclass
from internal.schema.api_tool_schema import ValidateOpenAPISchema
from internal.service import ApiToolService
from pkg.response import validate_error_json, success_message


@inject
@dataclass
class ApiToolHandler:
    """ 自定义api """
    api_tool_service: ApiToolService



    def validate_openapi_schema(self, openapi_schema):
        """ 验证openapi_schema """
        req = ValidateOpenAPISchema()
        if not req.validate():
            return validate_error_json(req.errors)

        self.api_tool_service.parse_openapi_schema(req.openapi_schema.data)
        return success_message("数据验证成功")


