import uuid

from pkg.db import SQLAlchemy
from injector import inject
from dataclasses import dataclass
from internal.model import App, Account


@inject
@dataclass
class AppService:
    db: SQLAlchemy

    def create_app(self, account: Account) -> App:
        with self.db.auto_commit():
            app = App()
            app.name = "测试机器人"
            app.description = "这是一个简单的测试机器人"
            app.account_id = account.id
            self.db.session.add(app)
        return app

    def get_app(self, id: uuid.UUID, account: Account) -> App:
        app = self.db.session.query(App).get(id)
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
