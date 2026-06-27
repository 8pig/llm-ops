from dataclasses import dataclass
from uuid import UUID

from flask import request
from flask_login import login_required, current_user
from injector import inject

from pkg.paginator import PageModel
from pkg.response import validate_error_json, compact_generate_response, success_json, success_message


@inject
@dataclass
class AssistantAgentHandler:


    @login_required
    def assistant_agent_chat(self):
        pass


    @login_required
    def stop_assistant_agent_chat(self):
        pass


    def get_assistant_agent_messages_with_page(self):