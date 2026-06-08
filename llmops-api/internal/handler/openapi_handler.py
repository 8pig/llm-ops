from flask_login import login_required
from injector import inject
from dataclasses import dataclass

from pkg.response import success_message


@inject
@dataclass
class OpenAPIHandler:
    """开放api"""


    @login_required
    def chat(self):
        return success_message("开放chat对话接口")