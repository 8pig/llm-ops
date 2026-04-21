from uuid import UUID

from celery import shared_task

@shared_task
def build_document(document_ids: list[UUID]) -> None:
    from model.module import injector
    from internal.service import IndexingService
    # 避免循环引用
    # 创建
    indexing_service = injector.get(IndexingService)
    indexing_service.build_document(document_ids)