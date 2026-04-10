from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField
from wtforms.validators import DataRequired, URL, length

from .schema import ListField
from ..exception import ValidateException
from ..model import ApiToolProvider, ApiTool


class ValidateOpenAPISchema(FlaskForm):
    """验证OpenAPI Schema"""

    openapi_schema = StringField("openapi_schema", validators=[
        DataRequired(message="OpenAPI Schema不能为空")
    ])



class CreateApiToolReq(FlaskForm):
    name: str = StringField("name", validators=[
        DataRequired(message="名称不能为空"),
        length(min=1, max=30, message="名称长度1-30")
    ])

    icon: str = StringField("icon", validators=[
        DataRequired(message="图标不能为空"),
        URL(message="图标必须是一个有效的URL")
    ])

    openapi_schema: str = StringField("openapi_schema", validators=[
        DataRequired(message="OpenAPI Schema不能为空")
    ])

    headers = ListField("headers")


    @classmethod
    def validate_headers(cls, form, filed):
        """校验headers 的数据  列表校验"""
        for header in filed.data:
            if not isinstance(header, dict):
                raise ValidateException("headers必须为字典")
            if set(header.keys())  != {"key", "value"}:
                raise ValidateException("必须为key value")


class GetApiToolProviderResp(Schema):
    """获取api工具提供者 响应信息"""
    id = fields.UUID()
    name = fields.String()
    icon = fields.String()
    openapi_schema = fields.String()
    headers = fields.List(fields.Dict, default=[])
    created_at = fields.Integer(default=0)

    @pre_dump
    def process_data(self, obj: ApiToolProvider, **kwargs):
        """预处理数据"""
        return {
            "id": obj.id,
            "name": obj.name,
            "icon": obj.icon,
            "openapi_schema": obj.openapi_schema,
            "headers": obj.headers,
            "created_at":  int(obj.created_at.timestamp())
        }

class GetApiToolResp(Schema):
    """获取api工具 响应信息"""
    id = fields.UUID()
    name = fields.String()
    description = fields.String()
    inputs = fields.List(fields.Dict, default=[])
    provider = fields.Dict(default={})  # ✅ 正确：定义为字典

    @pre_dump
    def process_data(self, data: ApiTool, **kwargs):
        provider = data.provider
        return {
            "id": data.id,
            "name": data.name,
            "description": data.description,
            "inputs": [{k: v for k, v in parameter.items() if k != "in"} for parameter in data.parameters],
            "provider": {
                "id": provider.id,
                "name": provider.name,
                "icon": provider.icon,
                "description": provider.description,
                "headers": provider.headers,
            }
        }
