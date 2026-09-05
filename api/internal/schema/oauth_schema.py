

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired
from marshmallow import Schema, fields


class AuthorizeReq(FlaskForm):
    """授权请求"""
    code = StringField("code", validators=[
        DataRequired("code不能为空")
    ])



class AuthorizeResp(Schema):
    """授权响应"""
    access_token = fields.String()
    expire_at = fields.Integer()