

from injector import inject
from dataclasses import dataclass

from entity.dataset_entity import DEFAULT_DATASET_DESCRIPTION_FORMATTER
from exception import FailException, ValidateException
from internal.model import Dataset
from pkg.response import success_json
from pkg.sqlalchemy import SQLAlchemy
from schema.dataset_schema import CreateDatasetReq, GetDatasetResp
from .base_service import BaseService


@inject
@dataclass
class DatasetService(BaseService):
    db: SQLAlchemy


    def create_dataset(self, req: CreateDatasetReq) -> Dataset:
        account_id = "550e8400-e29b-41d4-a716-446655440000"
        dataset = self.db.session.query(Dataset).filter_by(account_id=account_id, name=req.name.data).one_or_none()
        if dataset:
            raise ValidateException(f"{req.name.data}该知识库已存在")

        if req.description.data is None or req.description.data.strip() == "":
            req.description.data = DEFAULT_DATASET_DESCRIPTION_FORMATTER.format(
                name = req.name.data
            )

        return self.create(
            Dataset,
            account_id=account_id,
            icon=req.icon.data,
            name=req.name.data,
            description=req.description.data
        )

    def get_dataset(self, dataset_id) -> Dataset:
        account_id = "550e8400-e29b-41d4-a716-446655440000"
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or str(dataset.account_id) != account_id:
            raise FailException("知识库不存在")
        return dataset

