import logging
from uuid import UUID

from celery import shared_task


@shared_task
def auto_create_app(
        name: str,
        description: str,
        account_id: UUID,
) -> None:
    """根据传递的名称、描述、账号id创建一个Agent"""
    try:
        from internal.model.module import injector
        from internal.service import AppService

        app_service = injector.get(AppService)
        app_service.auto_create_app(name, description, account_id)
    except Exception as e:
        # 记录异常堆栈，避免异步任务静默失败后无从排查
        logging.exception("自动创建Agent应用失败, name=%s, account_id=%s, error=%s", name, account_id, str(e))
        # 继续向上抛出，让Celery将任务状态标记为FAILURE
        raise
