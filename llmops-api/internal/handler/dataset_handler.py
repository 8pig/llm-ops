import logging

from flask import request

from injector import inject

from uuid import UUID

from internal.schema.dataset_schema import (
    CreateDatasetReq,
    GetDatasetResp,
    UpdateDatasetReq,
    GetDatasetsWithPageReq,
    GetDatasetWithPageResp, HitReq, GetDatasetQueriesResp
)
from internal.model import UploadFile
from pkg.paginator import PageModel
from pkg.response import validate_error_json, success_message, success_json
from internal.service import DatasetService,EmbeddingsService, JiebaService, VectorDatabaseService
from internal.core.file_extractor import FileExtractor
from pkg.db import SQLAlchemy
from dataclasses import dataclass

@inject
@dataclass
class DatasetHandler:
    db: SQLAlchemy
    dataset_service: DatasetService
    embedding_service: EmbeddingsService
    jieba_service: JiebaService
    file_extractor: FileExtractor
    vector_database_service: VectorDatabaseService


    def embedding_query(self):
        """测试embedding"""
        try:
            print("开始处理文件")
            file_id = "11cdbd5c-5555-4b9b-8f26-45ab2c84f793"
            print(f"开始查询文件: {file_id}")

            upload_file = self.db.session.query(UploadFile).get(file_id)

            if not upload_file:
                print(f"文件不存在: {file_id}")
                return success_json({"error": "文件不存在", "file_id": file_id})

            print(f"文件信息: name={upload_file.name}, key={upload_file.key}, extension={upload_file.extension}")

            content = self.file_extractor.load(upload_file, True)

            print(f"文件内容长度: {len(content) if content else 0}")

            query = request.args.get("query", content[:100] if content else "")


            return success_json({
                "content": content,
            })
        except Exception as e:
            logging.error(f"处理文件时出错: {str(e)}", exc_info=True)
            return success_json({
                "error": f"处理文件失败: {str(e)}",
                "error_type": type(e).__name__
            })

    def hit(self, dataset_id: UUID):
        req = HitReq()
        if not req.validate():
            return validate_error_json(req.errors)

        result = self.dataset_service.hit(dataset_id, req)
        return success_json(result)



    def get_dataset_queries(self, dataset_id: UUID):
        """ 获取查询记录"""

        dataset_queries = self.dataset_service.get_dataset_queries(dataset_id)
        resp  = GetDatasetQueriesResp(many=True)
        return success_json(resp.dump(dataset_queries))


        pass

    def create_dataset(self):

        req = CreateDatasetReq()
        if not req.validate():
            return validate_error_json(req.errors)

        dataset = self.dataset_service.create_dataset(req)
        return success_message(f"{dataset.name}创建成功")




    def get_dataset(self, dataset_id: str):
        """"""
        dataset = self.dataset_service.get_dataset(dataset_id)
        resp = GetDatasetResp()
        return success_json(resp.dump(dataset))


    def update_dataset(self, dataset_id: UUID):
        req = UpdateDatasetReq()
        if not req.validate():
            return validate_error_json(req.errors)

        dataset = self.dataset_service.update_dataset(dataset_id, req)
        return success_message(f"{dataset.name}更新成功")




    def get_datasets_with_page(self):
        """"""
        req = GetDatasetsWithPageReq(request.args)

        if not req.validate():
            return validate_error_json(req.errors)

        datasets, paginator = self.dataset_service.get_datasets_with_page(req)

        resp = GetDatasetWithPageResp(many=True)

        return success_json(PageModel(list=resp.dump(datasets), paginator=paginator))


    def delete_dataset(self, dataset_id: UUID):
        self.dataset_service.delete_dataset(dataset_id)
        return success_message(f"{dataset_id}删除成功")