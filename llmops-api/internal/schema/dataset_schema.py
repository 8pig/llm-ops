from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField
from wtforms.validators import DataRequired, Length, URL, Optional, AnyOf, NumberRange
from marshmallow import Schema, fields, pre_dump

from internal.entity.dataset_entity import RetrievalStrategy
from internal.model import Dataset, DatasetQuery
from internal.lib.helper import datetime_to_timestamp
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


class HitReq(FlaskForm):
    """知识库召回测试请求"""
    query = StringField("query", validators=[
        DataRequired("查询语句不能为空"),
        Length(max=200, message="查询语句的最大长度不能超过200")
    ])
    retrieval_strategy = StringField("retrieval_strategy", validators=[
        DataRequired("检索策略不能为空"),
        AnyOf([item.value for item in RetrievalStrategy], message="检索策略格式错误")
    ])
    k = IntegerField("k", validators=[
        DataRequired("最大召回数量不能为空"),
        NumberRange(min=1, max=10, message="最大召回数量的范围在1-10")
    ])
    score = FloatField("score", validators=[
        NumberRange(min=0, max=0.99, message="最小匹配度范围在0-0.99")
    ])


class GetDatasetQueriesResp(Schema):
    """获取知识库最近查询响应结构"""
    id = fields.UUID(dump_default="")
    dataset_id = fields.UUID(dump_default="")
    query = fields.String(dump_default="")
    source = fields.String(dump_default="")
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: DatasetQuery, **kwargs):
        return {
            "id": data.id,
            "dataset_id": data.dataset_id,
            "query": data.query,
            "source": data.source,
            "created_at": datetime_to_timestamp(data.created_at),
        }
