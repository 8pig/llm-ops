from flask_login import login_required, current_user
from injector import inject
from dataclasses import dataclass

from internal.schema.openapi_schema import OpenAPIChatReq
from internal.service import OpenAPIService
from pkg.response import success_message, validate_error_json, compact_generate_response


@inject
@dataclass
class OpenAPIHandler:
    """开放api"""
    openapi_service: OpenAPIService


    @login_required
    def chat(self):
        req = OpenAPIChatReq()
        if not req.validate():
            return validate_error_json(req.errors)

        resp = self.openapi_service.chat(req, current_user)
        return  compact_generate_response(resp)

