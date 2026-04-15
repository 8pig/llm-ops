from celery import Task, Celery
from flask import Flask


def init_app(app: Flask):
    """celery 初始化"""

    class FlaskTask(Task):
        """定义flasktask   确保celery 在上下文运行 保证访问"""
        def  __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)


    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()

    app.extensions["celery"] = celery_app