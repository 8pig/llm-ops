from flask_wtf import FlaskForm
from marshmallow import Schema, fields
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired, Length, Email, regexp

from pkg.password import password_pattern


class PasswordLoginReq(FlaskForm):
    """登录验证"""

    password = StringField("password", validators=[
        DataRequired("password不能为空"),
        regexp(regex=password_pattern, message="密码格式错误")
    ])

    email = StringField("email", validators=[
        DataRequired("email不能为空"),
        Email("email不能为空"),
        Length(max=254, min=5,  message="长度不合法")
    ])


class PasswordLoginResp(Schema):
    """授权响应"""
    access_token = fields.String()
    expire_at = fields.Integer()