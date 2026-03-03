from injector import Module, Binder

from internal.extension.database_extension import db
from pkg.sqlalchemy import SQLAlchemy

class ExtensionModule(Module):
    """拓展模块的依赖注入"""
    def configure(self, binder: Binder):
        binder.bind(SQLAlchemy, to=db)
