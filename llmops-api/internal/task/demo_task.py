import logging

from celery import shared_task
from uuid import UUID
from flask import current_app

import time


@shared_task
def demo_task(id: UUID) -> str:
    """demo task"""
    logging.info("睡5秒")
    time.sleep(5)
    logging.info(f"id: {id}")
    logging.info(f"config: {dict(current_app.config)}")
    print("demo task")
    return "demo task"