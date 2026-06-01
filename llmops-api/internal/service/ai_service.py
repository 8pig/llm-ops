
import json
import os
from dataclasses import dataclass
from typing import Generator
from uuid import UUID

from injector import inject
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from internal.entity.ai_entity import OPTIMIZE_PROMPT_TEMPLATE
from internal.exception import ForbiddenException
from internal.model import Account, Message
from pkg.db import SQLAlchemy
from .base_service import BaseService
from .conversation_service import ConversationService


@inject
@dataclass
class AIService(BaseService):
    """AI服务"""
    db: SQLAlchemy
    conversation_service: ConversationService

    def generate_suggested_questions_from_message_id(self, message_id: UUID, account: Account) -> list[str]:
        """根据传递的消息id+账号生成建议问题列表"""
        message = self.get(Message, message_id)
        if not message or message.created_by != account.id:
            raise ForbiddenException("该条消息不存在或无权限")

        # 构建对话历史列表
        histories = f"Human: {message.query}\nAI: {message.answer}"

        # 生成建议问题
        return self.conversation_service.generate_suggested_questions(histories)

    @classmethod
    def optimize_prompt(cls, prompt: str) -> Generator[str, None, None]:
        """根据传递的prompt进行优化生成"""
        # 提示词模板
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", OPTIMIZE_PROMPT_TEMPLATE),
            ("human", "{prompt}")
        ])

        # LLM
        llm = ChatOpenAI(
            model=os.getenv("LLM_MODEL"),
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE_URL"),
            temperature=0.5,
        )


        optimize_chain = prompt_template | llm | StrOutputParser()

        # 流式事件返回
        for optimize_prompt in optimize_chain.stream({"prompt": prompt}):
            data = {"optimize_prompt": optimize_prompt}
            yield f"event: optimize_prompt\ndata: {json.dumps(data)}\n\n"
