from injector import inject
from dataclasses import dataclass

from internal.schema.upload_file_schema import UploadFileReq, UploadFileResp, UploadImageReq
from internal.service import CosService
from pkg.response import validate_error_json, success_json


@inject
@dataclass
class UploadFileHandler:
    cos_service: CosService


    def upload_file(self):
        """ 上传文件文档"""
        # 1, 构建请求/校验
        req = UploadFileReq()
        if not req.validate():
            return validate_error_json(req.errors)
        # 上传文件 获取记录
        upload_file = self.cos_service.upload_file(req.file.data)

        # 3响应返回
        resp = UploadFileResp()
        return success_json(resp.dump(upload_file))

        pass

    def upload_image(self):
        req = UploadImageReq()
        if not req.validate():
            return validate_error_json(req.errors)
        upload_file = self.cos_service.upload_file(req.file.data, True)
        # 获取图片的实际url地址
        image_url = self.cos_service.get_file_url(upload_file.key)
        return success_json({"image_url": image_url})