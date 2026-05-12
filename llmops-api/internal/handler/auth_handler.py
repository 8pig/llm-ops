from flask_login import logout_user, login_required
from dataclasses import dataclass

from injector import inject

from internal.schema.auth_schema import PasswordLoginReq, PasswordLoginResp
from internal.service import AccountService
from pkg.db import SQLAlchemy
from pkg.response import success_message, validate_error_json, success_json


@inject
@dataclass
class AuthHandler:
    """认证处理器"""
    db: SQLAlchemy
    account_service: AccountService

    @login_required
    def password_login(self):
        pwd = PasswordLoginReq()
        if not pwd.validate():
            return validate_error_json(pwd.errors)

        credential = self.account_service.password_login(pwd.email.data, pwd.password.data)

        resp = PasswordLoginResp()
        return success_json(resp.dump(credential))




    @login_required
    def logout(self):
        logout_user()
        return success_message("退出成功")