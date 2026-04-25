import logging

from injector import inject
from dataclasses import dataclass

from pyarrow.lib import UUID
from sqlalchemy import desc

from internal.exception import NotFoundException
from internal.entity.dataset_entity import DEFAULT_DATASET_DESCRIPTION_FORMATTER
from internal.exception import FailException, ValidateException
from internal.model import Dataset, DatasetQuery, AppDatasetJoin
from internal.lib.helper import datetime_to_timestamp
from internal.model import Segment
from pkg.paginator import Paginator
from pkg.db import SQLAlchemy
from internal.schema.dataset_schema import CreateDatasetReq, GetDatasetResp, UpdateDatasetReq, GetDatasetsWithPageReq, \
    HitReq
from .retrieval_service import RetrievalService
from .base_service import BaseService
from internal.task.dataset_task import delete_dataset


@inject
@dataclass
class DatasetService(BaseService):
    db: SQLAlchemy
    retrieval_service: RetrievalService


    def create_dataset(self, req: CreateDatasetReq) -> Dataset:
        account_id = "550e8400-e29b-41d4-a716-446655440000"
        dataset = self.db.session.query(Dataset).filter_by(account_id=account_id, name=req.name.data).one_or_none()
        if dataset:
            raise ValidateException(f"{req.name.data}1该知识库已存在")

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


    def update_dataset(self, dataset_id: UUID, req: UpdateDatasetReq) -> Dataset:
        account_id = "550e8400-e29b-41d4-a716-446655440000"
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or str(dataset.account_id) != account_id:
            raise ValidateException("知识库不存在")

        check_dataset = self.db.session.query(Dataset).filter(
            Dataset.account_id == account_id,
            Dataset.name == req.name.data,
            Dataset.id != dataset_id
        ).one_or_none()
        if check_dataset:
            raise ValidateException(f"{req.name.data}该知识库已存在")

        if req.description.data is None or req.description.data.strip() == "":
            req.description.data = DEFAULT_DATASET_DESCRIPTION_FORMATTER.format(
                name = req.name.data
            )
        self.update(
            dataset,
            icon=req.icon.data,
            name=req.name.data,
            description=req.description.data
        )
        return dataset

    def get_datasets_with_page(self, req: GetDatasetsWithPageReq) -> tuple[list[Dataset], Paginator]:
        """列表分页"""
        account_id = "550e8400-e29b-41d4-a716-446655440000"
        # 1. 构建分页查询器
        paginator = Paginator(db=self.db, req=req)

        # 构建筛选

        filters = [Dataset.account_id == account_id]
        if req.search_word.data:
            filters.append(Dataset.name.like(f"%{req.search_word.data}%"))

            # 分页 查询

        datasetsq= (self.db.session.query(Dataset).
                   filter(*filters).
                   order_by(Dataset.created_at.desc()))
        datasets = paginator.paginate(datasetsq)

        return datasets, paginator


    def hit(self, dataset_id: UUID, req: HitReq) -> list[dict]:
        """根据传递的知识库id+请求执行召回测试"""
        # todo:等待授权认证模块完成进行切换调整
        account_id = "550e8400-e29b-41d4-a716-446655440000"

        # 1.检测知识库是否存在并校验
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or str(dataset.account_id) != account_id:
            raise NotFoundException("该知识库不存在")

        # 2.调用检索服务执行检索
        lc_documents = self.retrieval_service.search_in_datasets(
            dataset_ids=[dataset_id],
            **req.data,
        )

        lc_document_dict = {str(lc_document.metadata["segment_id"]): lc_document for lc_document in lc_documents}
        logging.error(lc_document_dict)
        # 3.根据检索到的数据查询对应的片段信息
        segments = self.db.session.query(Segment).filter(
            Segment.id.in_([str(lc_document.metadata["segment_id"]) for lc_document in lc_documents])
        ).all()

        # segment_dict = {}
        # for segment in segments:
        #     segment_id_str = str(segment.id)
        #     segment_dict[segment_id_str] = segment

        segment_dict = {str(segment.id): segment for segment in segments}
        # 4.排序片段数据
        sorted_segments = [
            segment_dict[str(lc_document.metadata["segment_id"])]
            for lc_document in lc_documents
            if str(lc_document.metadata["segment_id"]) in segment_dict
        ]

        # 5.组装响应数据
        hit_result = []
        for segment in sorted_segments:
            document = segment.document
            upload_file = document.upload_file
            hit_result.append({
                "id": segment.id,
                "document": {
                    "id": document.id,
                    "name": document.name,
                    "extension": upload_file.extension,
                    "mime_type": upload_file.mime_type,
                },
                "dataset_id": segment.dataset_id,
                "score": lc_document_dict[str(segment.id)].metadata["score"],
                "position": segment.position,
                "content": segment.content,
                "keywords": segment.keywords,
                "character_count": segment.character_count,
                "token_count": segment.token_count,
                "hit_count": segment.hit_count,
                "enabled": segment.enabled,
                "disabled_at": datetime_to_timestamp(segment.disabled_at),
                "status": segment.status,
                "error": segment.error,
                "updated_at": datetime_to_timestamp(segment.updated_at),
                "created_at": datetime_to_timestamp(segment.created_at),
            })

        return hit_result

    def get_dataset_queries(self, dataset_id):
        # todo:等待授权认证模块完成进行切换调整
        account_id = "550e8400-e29b-41d4-a716-446655440000"

        # 1.检测知识库是否存在并校验
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or str(dataset.account_id) != account_id:
            raise NotFoundException("该知识库不存在")
        dataset_queries= self.db.session.query(DatasetQuery).filter(
            DatasetQuery.dataset_id == dataset_id
        ).order_by(desc("created_at")).limit(10).all()

        return  dataset_queries

    def delete_dataset(self, dataset_id: UUID) -> Dataset:
        """根据传递的知识库id删除知识库信息，涵盖知识库底下的所有文档、片段、关键词，以及向量数据库里存储的数据"""
        # todo:等待授权认证模块完成进行切换调整
        account_id = "550e8400-e29b-41d4-a716-446655440000"

        # 1.获取知识库并校验权限
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or str(dataset.account_id) != account_id:
            raise NotFoundException("该知识库不存在")

        try:
            # 2.删除知识库基础记录以及知识库和应用关联的记录
            self.delete(dataset)
            with self.db.auto_commit():
                self.db.session.query(AppDatasetJoin).filter(
                    AppDatasetJoin.dataset_id == dataset_id,
                ).delete()

            # 3.调用异步任务执行后续的操作
            delete_dataset.delay(dataset_id)
        except Exception as e:
            logging.exception(f"删除知识库失败, dataset_id: {dataset_id}, 错误信息: {str(e)}")
            raise FailException("删除知识库失败，请稍后重试")
