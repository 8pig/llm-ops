from injector import inject
from dataclasses import dataclass

from internal.schema.oauth_schema import AuthorizeReq, AuthorizeResp
from internal.service import OAuthService
from pkg.response import success_json, validate_error_json


@inject
@dataclass
class OAuthHandler:
    """第三方OAuth授权处理类"""
    oauth_service: OAuthService


    def provider(self, provider_name: str):
        oauth = self.oauth_service.get_oauth_by_provider_name(provider_name)

        redirect_url = oauth.get_authorization_url()

        return success_json({"redirect_url": redirect_url})


    def authorize(self, provider_name: str):

        req = AuthorizeReq()
        if not req.validate():
            return validate_error_json(req.errors)

        credential = self.oauth_service.oauth_login(provider_name, req.code.data)
        return success_json(AuthorizeResp().dump(credential))


