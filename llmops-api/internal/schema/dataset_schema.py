from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length, URL, Optional
from marshmallow import Schema, fields, pre_dump

from internal.model import Dataset
from pkg.paginator import PaginatorReq


# from internal.model import Dataset

class CreateDatasetReq(FlaskForm):
    """创建知识库表单"""
    name = StringField("name", validators=[
        DataRequired("知识库名称不可为空"),
        Length(max=100, message="知识库名称长度不能超过100")
    ])
    icon = StringField("icon", validators=[
        DataRequired(message="图标不能为空"),
        Length(max=100, message="图标长度不能超过100"),
        URL("必须为url")
    ])
    description = StringField("description", default="", validators=[
        Optional(),
        Length(max=2000, message="描述长度不能超过2000")
    ])

class GetDatasetResp(Schema):
    """获取知识库详情接口 resp"""
    id = fields.UUID(dump_default="")
    name = fields.String(dump_default="")
    icon = fields.String(dump_default="")
    description = fields.String(dump_default="")
    document_count = fields.Integer(dump_default=0)
    hit_count = fields.Integer(dump_default=0)
    character = fields.Integer(dump_default=0)
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)
    related_app_count = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: Dataset, **kwargs) :

        return {
            "id": str(data.id),
            "name": data.name,
            "icon": data.icon,
            "description": data.description,
            "document_count": data.document_count,
            "hit_count": data.hit_count,
            "character": data.character_count,
            "related_app_count": data.related_app_count,
            "updated_at": int(data.updated_at.timestamp()),
            "created_at": int(data.created_at.timestamp())
        }


class UpdateDatasetReq(FlaskForm):
    """更新知识库表单"""
    name = StringField("name", validators=[
        DataRequired("知识库名称不可为空"),
        Length(max=100, message="知识库名称长度不能超过100")
    ])
    icon = StringField("icon", validators=[
        DataRequired(message="图标不能为空"),
        Length(max=100, message="图标长度不能超过100"),
        URL("必须为url")
    ])
    description = StringField("description", default="", validators=[
        Optional(),
        Length(max=2000, message="描述长度不能超过2000")
    ])


class GetDatasetsWithPageReq(PaginatorReq):
    """获取知识库列表接口 req"""
    search_word = StringField("search_word",default="", validators=[
        Optional()
    ])

class GetDatasetWithPageResp(Schema):
    """获取知识库列表接口 resp"""
    id = fields.UUID(dump_default="")
    name = fields.String(dump_default="")
    icon = fields.String(dump_default="")
    description = fields.String(dump_default="")
    document_count = fields.Integer(dump_default=0)
    character = fields.Integer(dump_default=0)
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)
    related_app_count = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: Dataset, **kwargs) :

        return {
            "id": str(data.id),
            "name": data.name,
            "icon": data.icon,
            "description": data.description,
            "document_count": data.document_count,
            "character": data.character_count,
            "related_app_count": data.related_app_count,
            "updated_at": int(data.updated_at.timestamp()),
            "created_at": int(data.created_at.timestamp())
        }
