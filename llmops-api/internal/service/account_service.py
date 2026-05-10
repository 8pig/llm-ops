from dataclasses import dataclass
from typing import Any, Optional
from uuid import UUID

from injector import inject


from internal.service.base_service import BaseService
from pkg.db import SQLAlchemy
from internal.model import Account


@inject
@dataclass
class AccountService(BaseService):
    """账户服务"""

    db = SQLAlchemy

    def get_account(self, account_id: UUID)-> Optional[Account]:
        return self.get(Account, account_id)

