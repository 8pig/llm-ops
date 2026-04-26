from flask_wtf import FlaskForm
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired, Length


class CompletionReq(FlaskForm):
    """基础聊天接口验证"""

    query = StringField("query", validators=[
        DataRequired("问题不能为空"),
        Length(max=2000, message="问题长度不能超过2000")
    ])