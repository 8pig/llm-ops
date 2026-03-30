from injector import Module, Binder

from internal.extension.database_extension import db
from pkg.sqlalchemy import SQLAlchemy
from flask_migrate import  Migrate
from internal.extension.migrate_extension import  migrate

class ExtensionModule(Module):
    """拓展模块的依赖注入"""
    def configure(self, binder: Binder):
        binder.bind(SQLAlchemy, to=db)
        binder.bind(Migrate, to=migrate)
