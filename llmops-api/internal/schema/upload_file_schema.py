from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed, FileSize

from internal.entity.upload_file_entity import ALLOWED_DOCUMENT_EXTENSIONS, ALLOWED_IMAGE_EXTENSIONS
from marshmallow import Schema, fields, pre_dump
from internal.model import UploadFile


class UploadFileReq(FlaskForm):
    file = FileField("file", validators=[
        FileRequired("文件不能为空"),
        FileSize(max_size=1024 * 1024 * 15, message="文件大小不能超过15M"),
        FileAllowed(ALLOWED_DOCUMENT_EXTENSIONS, f"只允许上传{'/'.join(ALLOWED_DOCUMENT_EXTENSIONS)}文件")
    ])





class UploadFileResp(Schema):
    """上传文件响应结构"""
    id = fields.UUID(dump_default="")
    account_id = fields.UUID(dump_default="")
    name = fields.String(dump_default="")
    key= fields.String(dump_default="")
    size= fields.Integer(dump_default=0)
    extension= fields.String(dump_default="")
    mime_type= fields.String(dump_default="")
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: UploadFile, **kwargs):
        return {
            "id": data.id,
            "account_id": data.account_id,
            "name": data.name,
            "key": data.key,
            "size": data.size,
            "extension": data.extension,
            "mime_type": data.mime_type,
            "created_at": int(data.created_at.timestamp()),
        }


class UploadImageReq(FlaskForm):
    file = FileField("file", validators=[
        FileRequired("图片不能为空"),
        FileSize(max_size=1024 * 1024 * 15, message="图片大小不能超过15M"),
        FileAllowed(ALLOWED_IMAGE_EXTENSIONS, f"只允许上传{'/'.join(ALLOWED_IMAGE_EXTENSIONS)}文件")
    ])
