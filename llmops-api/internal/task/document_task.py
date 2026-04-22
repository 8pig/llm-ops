from uuid import UUID

from celery import shared_task

@shared_task
def build_document(document_ids: list[UUID]) -> None:
    from internal.model.module import injector
    from internal.service.indexing_service import IndexingService
    # 避免循环引用
    # 创建
    indexing_service = injector.get(IndexingService)
    indexing_service.build_document(document_ids)


@shared_task
def update_document_enabled(document_id: UUID) -> None:
    """根据docid 修改enabled"""
    from internal.model.module import injector
    from internal.service.indexing_service import IndexingService
    # 避免循环引用
    # 创建
    indexing_service = injector.get(IndexingService)
    indexing_service.update_document_enabled(document_id)