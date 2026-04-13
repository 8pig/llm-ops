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
from internal.service import BaseService
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class UploadFileService(BaseService):
    """"""
    db: SQLAlchemy


    def create_upload_file(self, **kwargs) -> UploadFile:
        return self.create(UploadFile, **kwargs)