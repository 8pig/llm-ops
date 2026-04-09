from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class ValidateOpenAPISchema(FlaskForm):
    """验证OpenAPI Schema"""

    openapi_schema = StringField("openapi_schema", validators=[
        DataRequired(message="OpenAPI Schema不能为空")
    ])