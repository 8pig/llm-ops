from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, URL, length

from .schema import ListField
from ..exception import ValidateException


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


