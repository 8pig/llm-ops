import hashlib
import os
import random
import uuid
from datetime import datetime

from injector import inject
from dataclasses import dataclass

from openai.types import file_content
from qcloud_cos import CosS3Client, CosConfig
from werkzeug.datastructures import FileStorage

from internal.entity.upload_file_entity import ALLOWED_DOCUMENT_EXTENSIONS, ALLOWED_IMAGE_EXTENSIONS
from internal.exception import FailException
from internal.model import UploadFile
from internal.service import UploadFileService


@inject
@dataclass
class CosService:
    upload_file_service: UploadFileService


    def upload_file(self,file:FileStorage, only_image:bool=False) -> UploadFile:
        """上传文件到cos文件存储  返回文件信息"""
        account_id = "550e8400-e29b-41d4-a716-446655440000"

        filename = file.filename
        extension = filename.rsplit(".", 1)[-1] if "." in filename else ""
        if extension.lower() not in (ALLOWED_DOCUMENT_EXTENSIONS+ALLOWED_IMAGE_EXTENSIONS):
            raise FailException(f"{file.filename}文件格式错误")
        elif only_image and extension not in ALLOWED_IMAGE_EXTENSIONS:
            raise FailException(f"{extension}文件格式不支持上传")

    #
        client = self._get_client()
        bucket = self._get_bucket()

        random_filename = str(uuid.uuid4()) + "." + extension
        now = datetime.now()
        upload_filename = f"{now.year}/{now.month:02d}/{now.day:02d}/{random_filename}"

        # 流式读取 并上传
        file_content = file.stream.read()
        try:
            client.put_object(
                Bucket=bucket,
                Body=file_content,
                Key=upload_filename
            )
        except Exception as e:
            raise FailException(f"上传文件失败: {e}")

        # 创建 upload file
        return self.upload_file_service.create_upload_file(
            account_id=account_id,
            name=filename,
            key=upload_filename,
            size=len(file_content),
            extension=extension,
            mime_type=file.mimetype,
            hash =  hashlib.sha3_256(file_content).hexdigest(),
        )

    def download_file(self, key: str, target_file_path: str):
        """下载文件"""
        client = self._get_client()
        bucket = self._get_bucket()
        client.download_file(bucket, key, target_file_path)

    @classmethod
    def get_file_url(cls, key: str) -> str:
        """根据云端的key 获取实际的url地址"""
        cos_domain = os.getenv("COS_DOMAIN")

        if not cos_domain:
            bucket = os.getenv("COS_BUCKET")
            scheme = os.getenv("COS_SCHEME")
            region = os.getenv("COS_REGION")
            cos_domain = f"{scheme}://{bucket}.cos.{region}.myqcloud.com"

        return f"{cos_domain}/{key}"
    """
    腾讯云COS服务
    """
    @classmethod
    def _get_client(cls) -> CosS3Client:
        conf = CosConfig(
            Region=os.getenv("COS_REGION"),
            SecretId=os.getenv("COS_SECRET_ID"),
            SecretKey=os.getenv("COS_SECRET_KEY"),
            Scheme=os.getenv("COS_SCHEME"),
            Token=None
        )
        return CosS3Client(conf)


    def _get_bucket(cls) -> str:
        """获取name"""
        return os.getenv("COS_BUCKET")