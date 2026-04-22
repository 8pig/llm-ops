import logging
import random
import time
from datetime import datetime
from uuid import UUID

from injector import inject
from dataclasses import dataclass

from sqlalchemy import desc, asc, func

from internal.lib.helper import datetime_to_timestamp
from internal.model import Segment
from pkg.paginator import Paginator
from pkg.db import SQLAlchemy
from internal.entity.upload_file_entity import ALLOWED_DOCUMENT_EXTENSIONS
from internal.exception import ForbiddenException
from internal.exception import FailException
from internal.entity.dataset_entity import ProcessType, SegmentStatus, DocumentStatus
from internal.service import BaseService
from internal.model import UploadFile, ProcessRule, Dataset, Document
from internal.task.document_task import build_document, update_document_enabled
from internal.schema.document_schema import GetDocumentsWithPageReq
from internal.entity.cache_entity import LOCK_DOCUMENT_UPDATE_ENABLED, LOCK_EXPIRE_TIME
from redis import Redis


@inject
@dataclass
class DocumentService(BaseService):
    db:SQLAlchemy
    redis_client: Redis


    def create_documents(
            self,
            dataset_id: UUID,
            upload_file_ids: list[UUID],
            process_type: str = ProcessType.AUTOMATIC,
            rule: dict = None
    ) -> tuple[list[Document], str]:
        """ 根据传递的ids 创建文档列表 调用异步"""

        account_id = "550e8400-e29b-41d4-a716-446655440000"
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or str(dataset.account_id) != account_id:
            raise ForbiddenException("知识库不存在或无权限")

        upload_files = self.db.session.query(UploadFile).filter(
            UploadFile.account_id == account_id,
            UploadFile.id.in_(upload_file_ids)
        ).all()

        upload_files = [upload_file for upload_file in upload_files
            if upload_file.extension.lower() in ALLOWED_DOCUMENT_EXTENSIONS
        ]
        if len(upload_files)  == 0:
            logging.warning(f"暂未解析到合法文件,{account_id},dataset_id: {dataset_id}, upload_file_ids:{upload_file_ids}")
            raise FailException("暂未解析到合法文件, 请重新上传")

        # 创建批次 与处理规则
        batch = time.strftime("%Y%m%d%H%M%S") + str(random.randint(100000, 999999))
        process_rule = self.create(
            ProcessRule,
            account_id=account_id,
            dataset_id=dataset_id,
            mode=process_type,
            rule=rule
        )
        # 获取当前知识库的最新文档位置
        position = self.get_latest_position(dataset_id)

        documents = []
        for upload_file in upload_files:
            position += 1
            document = self.create(
                Document,
                account_id=account_id,
                dataset_id=dataset_id,
                upload_file_id = upload_file.id,
                process_rule_id=process_rule.id,
                batch=batch,
                position=position,
                name=upload_file.name,
            )
            documents.append(document)

        # 调用异步任务 完成后续操作
        build_document.delay([document.id for document in documents])

        #返回文档列表与批次
        return documents, batch

    def get_document_status(self, dataset_id, batch) -> list[dict]:

        account_id = "550e8400-e29b-41d4-a716-446655440000"
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or str(dataset.account_id) != account_id:
            raise ForbiddenException("知识库不存在或无权限")

    #     查询批次下文档
        documents = self.db.session.query(Document).filter(
            Document.dataset_id == dataset_id,
            Document.batch == batch
        ).order_by(asc("position")).all()

        if documents is None or len(documents) == 0:
            raise ModuleNotFoundError("批次下无文档")

        document_list_status = []

        for document in documents:
            # 4.查询每个文档的总片段数和已构建完成的片段数
            segment_count = self.db.session.query(func.count(Segment.id)).filter(
                Segment.document_id == document.id,
            ).scalar()
            completed_segment_count = self.db.session.query(func.count(Segment.id)).filter(
                Segment.document_id == document.id,
                Segment.status == SegmentStatus.COMPLETED,
            ).scalar()

            upload_file = document.upload_file
            document_list_status.append({
                "id": str(document.id),
                "name": document.name,
                "size": upload_file.size,
                "extension": upload_file.extension,
                "mime_type": upload_file.mime_type,
                "position": document.position,
                "segment_count": segment_count,
                "completed_segment_count": completed_segment_count,
                "error": document.error,
                "status": document.status,
                "processing_started_at": datetime_to_timestamp(document.processing_started_at),
                "parsing_completed_at": datetime_to_timestamp(document.parsing_completed_at),
                "splitting_completed_at": datetime_to_timestamp(document.splitting_completed_at),
                "indexing_completed_at": datetime_to_timestamp(document.indexing_completed_at),
                "completed_at": datetime_to_timestamp(document.completed_at),
                "stopped_at": datetime_to_timestamp(document.stopped_at),
                "created_at": datetime_to_timestamp(document.created_at),
            })

        return document_list_status




    def get_latest_position(self, dataset_id: UUID) -> int:
        document = self.db.session.query(Document).filter(
            Document.dataset_id == dataset_id
        ).order_by(desc("position")).first()
        return document.position if document else 0

    def get_document(self, dataset_id, document_id) -> Document:

        account_id = "550e8400-e29b-41d4-a716-446655440000"
        document = self.get(Document, document_id)
        if document is None:
            raise ForbiddenException("document不存在")
        if str(document.dataset_id) != str(dataset_id) or str(document.account_id) != account_id:
            raise ForbiddenException("document不存在或无权限")

        return  document

    def update_document_name(self, dataset_id, document_id, **kwargs):
        account_id = "550e8400-e29b-41d4-a716-446655440000"
        document = self.get(Document, document_id)
        if document is None:
            raise ForbiddenException("document不存在")
        if str(document.dataset_id) != str(dataset_id) or str(document.account_id) != account_id:
            raise ForbiddenException("document不存在或无权限修改")

        return self.update(
            document,
            **kwargs
        )

    def update_document_enabled(self, dataset_id: UUID, document_id: UUID, enabled: bool)-> Document:
        """ 修改状态 且 加锁"""
        account_id = "550e8400-e29b-41d4-a716-446655440000"

        document = self.get(Document, document_id)
        if document is None:
            raise ForbiddenException("document不存在")
        if str(document.dataset_id) != str(dataset_id) or str(document.account_id) != account_id:
            raise ForbiddenException("document不存在或无权限修改")
        # 判断是否可修改  只有构建完成才可以
        if document.status != DocumentStatus.COMPLETED:
            raise ForbiddenException("文档状态未构建完成，稍后重试")

        if document.enabled == enabled:
            raise FailException("当前状态无需修改")

        #  获取状态的缓存  并检测是否上锁
        cache_key = LOCK_DOCUMENT_UPDATE_ENABLED.format(document_id=document_id)
        cache_value = self.redis_client.get(cache_key)
        if cache_value is not None:
            raise FailException("当前文档正在修改中，请稍后重试")
        self.update(document,enabled=enabled, disabled_at=None if enabled else datetime.now())
        self.redis_client.setex(cache_key, LOCK_EXPIRE_TIME, 1)

        # 启用异步
        update_document_enabled.delay(document_id)

        return  document

        pass

    def get_documents_with_page(self, dataset_id: UUID, req: GetDocumentsWithPageReq):
        """分页文档分页数据"""

        account_id = "550e8400-e29b-41d4-a716-446655440000"
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or str(dataset.account_id) != account_id:
            raise ForbiddenException("知识库不存在或无权限")

        paginator = Paginator(db=self.db, req=req)
        filters = [
            Document.dataset_id == dataset_id,
            Document.account_id == account_id,
        ]
        if req.search_word.data:
            filters.append(Document.name.ilike(f"%{req.search_word.data}%"))

        documents = paginator.paginate(
            self.db.session.query(Document).filter(*filters).order_by(desc("created_at"))
        )
        return  documents, paginator