from injector import inject
from dataclasses import dataclass

from uuid import UUID

from sqlalchemy import desc

from pkg.paginator import PaginatorReq, Paginator
from .base_service import BaseService
from pkg.db import SQLAlchemy
import secrets

from internal.model import Account, ApiKey
from internal.schema.api_key_schema import CreateApiKeyReq
from internal.exception import ForbiddenException


@inject
@dataclass
class ApiKeyService(BaseService):

    db: SQLAlchemy


    def create_api_key(self, req: CreateApiKeyReq, account: Account) -> ApiKey:
        """ 创建api key """
        return self.create(
            ApiKey,
            api_key=self.generate_api_key(),
            is_active=req.is_active.data,
            remark=req.remark.data,
            account_id=account.id,
        )


    def get_api_key(self, api_key_id: UUID, account: Account) -> ApiKey:
        """ 获取api key """
        api_key = self.get(ApiKey, api_key_id)
        if not api_key or api_key.account_id != account.id:
            raise ForbiddenException("api key not found")
        return api_key

    def get_api_by_credential(self, api_key: str) -> ApiKey:
        return self.db.session.query(ApiKey).filter(
            ApiKey.api_key == api_key
        ).one_or_none()


    def update_api_key(self, api_key_id: UUID, account: Account, **kwargs) -> ApiKey:
        """ 更新api key """
        api_key = self.get_api_key(api_key_id, account)
        self.update(
            api_key,
            **kwargs
        )
        return api_key

    def delete_api_key(self, api_key_id: UUID, account: Account) -> ApiKey:
        """ 删除api key """
        api_key = self.get_api_key(api_key_id, account)
        self.delete(api_key)
        return api_key

    def get_api_keys_with_page(self, req: PaginatorReq, account: Account) -> tuple[list[ApiKey], Paginator]:
        """ 获取api key 分页列表 """
        paginator = Paginator(db=self.db, req=req)
        api_keys = paginator.paginate(
            self.db.session.query(ApiKey).filter(
                ApiKey.account_id == account.id
            ).order_by(desc("created_at"))
        )

        return api_keys, paginator





    @classmethod
    def generate_api_key(cls, api_key_prefix: str = "joker-v1/") -> str:
        """生成48的apikey"""
        return api_key_prefix + secrets.token_urlsafe(48)