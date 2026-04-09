from dataclasses import dataclass

from injector import inject

import json

from internal.exception import ValidateException


@inject
@dataclass
class ApiToolService:
    """ 自定义api服务 """


    @classmethod
    def parse_openapi_schema(cls, openapi_schema_str: str):
        """ 验证openapi_schema str """

        try:
            data = json.loads(openapi_schema_str)
            if not isinstance(data, dict):
                raise
        except Exception as e:
            raise ValidateException("传递数据必须符合OpenAPI规范")
