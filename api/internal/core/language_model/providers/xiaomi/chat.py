
from langchain_openai import ChatOpenAI

from internal.core.language_model.entities.model_entity import BaseLanguageModel
from internal.core.language_model.entities.reasoning_mixin import ReasoningMixin


class Chat(ReasoningMixin, ChatOpenAI, BaseLanguageModel):
    """小米MiMo聊天模型，支持提取reasoning_content(思维链)"""
    pass
