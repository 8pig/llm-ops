from typing import Any, Optional

from internal.exception import FailException
from pkg.sqlalchemy import SQLAlchemy


class BaseService:
    """ 基础类  """
    db: SQLAlchemy

    def create(self, model: Any, **kwargs) -> Any:
        with self.db.auto_commit():
            model = model(**kwargs)
            self.db.session.add(model)
        return model

    def delete(self, model_instance: Any) -> Any:
        with self.db.auto_commit():
            self.db.session.delete(model_instance)
        return model_instance


    def update(self, model_instance: Any, **kwargs) -> Any:
        with self.db.auto_commit():
            for k, v in kwargs.items():
                if hasattr(model_instance, k):
                    setattr(model_instance, k, v)
                else:
                    raise FailException("更新数据失败")
        return model_instance

    def get(self, model: Any, primary_key: Any) -> Optional[ Any]:
        return self.db.session.query(model).get(primary_key)
        