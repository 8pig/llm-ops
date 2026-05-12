import os
import random
import uuid
from datetime import datetime

from injector import inject
from dataclasses import dataclass


from internal.model import UploadFile
from internal.service import BaseService
from pkg.db import SQLAlchemy


@inject
@dataclass
class UploadFileService(BaseService):
    """"""
    db: SQLAlchemy


    def create_upload_file(self, **kwargs) -> UploadFile:
        return self.create(UploadFile, **kwargs)