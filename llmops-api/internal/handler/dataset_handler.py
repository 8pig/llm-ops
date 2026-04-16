import logging

from injector import inject
from dataclasses import dataclass

from internal.schema.dataset_schema import (
CreateDatasetReq
)
from pkg.response import validate_error_json, success_message, success_json
from internal.service import DatasetService
from schema.dataset_schema import GetDatasetResp


@inject
@dataclass
class DatasetHandler:
    dataset_service: DatasetService

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


    def update_dataset(self, dataset_id: str):
        """"""
        pass



    def get_datasets_with_page(self):
        """"""
        pass