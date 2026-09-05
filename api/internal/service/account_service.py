from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
from uuid import UUID
import secrets

from flask import request
from injector import inject
import base64

from internal.exception import UnauthorizedException
from pkg.password import hash_password, compare_password

from internal.service.base_service import BaseService
from pkg.db import SQLAlchemy
from internal.model import Account, AccountOAuth
from .jwt_service import JwtService


@inject
@dataclass
class AccountService(BaseService):
    """账户服务"""

    db: SQLAlchemy
    jwt_service: JwtService

    def get_account(self, account_id: UUID)-> Optional[Account]:
        return self.get(Account, account_id)

    def get_account_oauth_by_provider_name_and_openid(
            self,
            provider_name: str,
            openid: str
    ) -> AccountOAuth:
        """"""
        return self.db.session.query(AccountOAuth).filter(
            AccountOAuth.provider == provider_name,
            AccountOAuth.openid == openid
        ).one_or_none()

    def get_account_by_email(self, email: str) -> Account:
        return self.db.session.query(Account).filter(
            Account.email == email
        ).one_or_none()

    def create_account(self, **kwargs) -> Account:
        return self.create(Account, **kwargs)

    def update_account(self, account: Account, **kwargs) -> Account:
        """根据传递的信息更新账号"""
        self.update(account, **kwargs)
        return account


    def update_password(self, password: str, account: Account) -> Account:
        """更新当前账号密码信息"""
        # 1.生成密码随机盐值
        salt = secrets.token_bytes(16)
        base64_salt = base64.b64encode(salt).decode()

        # 2.利用盐值和password进行加密
        password_hashed = hash_password(password, salt)
        base64_password_hashed = base64.b64encode(password_hashed).decode()

        # 3.更新账号信息
        account = self.update_account(account, password=base64_password_hashed, password_salt=base64_salt)

        return account

    def password_login(self, email, pwd) -> dict[str, Any]:
        """ 邮箱密码登录"""
        account = self.get_account_by_email(email)
        if account is None:
            raise UnauthorizedException("用户不存在或者密码错误")

        if not account.is_password_set or not compare_password(pwd, account.password, account.password_salt):
            raise UnauthorizedException("用户不存在或者密码错误")

        expire_at = int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp())
        payload = {
            "sub": str(account.id),
            "iss": "llmops",
            "exp": expire_at,
        }
        access_token = self.jwt_service.generate_token(payload)
        self.update(
            account,
            last_login_at=datetime.now(),
            last_login_ip=request.remote_addr,
        )

        return {
            "expire_at": expire_at,
            "access_token": access_token,
        }



