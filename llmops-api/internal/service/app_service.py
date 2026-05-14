import uuid

from internal.entity.app_entity import AppStatus, AppConfigType, DEFAULT_APP_CONFIG
from internal.schema.app_schema import CreateAppReq
from .base_service import BaseService
from pkg.db import SQLAlchemy
from injector import inject
from dataclasses import dataclass
from internal.model import App, Account, AppConfigVersion
from ..exception import NotFoundException, ForbiddenException


@inject
@dataclass
class AppService(BaseService):
    db: SQLAlchemy

    def create_app(self, req: CreateAppReq, account: Account) -> App:
        """创建Agent应用服务"""
        # 1.开启数据库自动提交上下文
        with self.db.auto_commit():
            # 2.创建应用记录，并刷新数据，从而可以拿到应用id
            app = App(
                account_id=account.id,
                name=req.name.data,
                icon=req.icon.data,
                description=req.description.data,
                status=AppStatus.DRAFT,
            )
            self.db.session.add(app)
            self.db.session.flush()

            # 3.添加草稿记录
            app_config_version = AppConfigVersion(
                app_id=app.id,
                version=0,
                config_type=AppConfigType.DRAFT,
                **DEFAULT_APP_CONFIG,
            )
            self.db.session.add(app_config_version)
            self.db.session.flush()

            # 4.为应用添加草稿配置id
            app.draft_app_config_id = app_config_version.id

        # 5.返回创建的应用记录
        return app

    def get_app(self, app_id: uuid.UUID, account: Account) -> App:
        app = self.get(App, app_id)
        if not app:
            raise NotFoundException("请核实")

            # 3.判断当前账号是否有权限访问该应用
        if app.account_id != account.id:
            raise ForbiddenException("当前账号无权限访问该应用，请核实后尝试")

        return app

    def update_app(self, id: uuid.UUID, account: Account):
        with self.db.auto_commit():
            app = self.get_app(id, account)
            app.name = "洲哥ai robot机器人"
        return app

    def delete_app(self, id: uuid.UUID, account: Account):
        with self.db.auto_commit():
            app = self.get_app(id, account)
            self.db.session.delete(app)
        return app
