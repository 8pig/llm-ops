import logging
from flask import request
from gitdb.util import mman

from injector import inject
from dataclasses import dataclass

from pyarrow.lib import UUID

from internal.schema.dataset_schema import (
    CreateDatasetReq,
    GetDatasetResp,
    UpdateDatasetReq,
    GetDatasetsWithPageReq,
    GetDatasetWithPageResp
)
from pkg.paginator import PageModel
from pkg.response import validate_error_json, success_message, success_json
from internal.service import DatasetService,EmbeddingsService


@inject
@dataclass
class DatasetHandler:
    dataset_service: DatasetService
    embedding_service: EmbeddingsService



    def embedding_query(self):
        """测试embedding"""
        query = request.args.get("query")
        vectors = self.embedding_service.cache_backed_embeddings.embed_query(query)
        return success_json({"vectors": vectors})

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