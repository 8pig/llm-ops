
from dataclasses import dataclass

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, trim_messages, get_buffer_string
from sqlalchemy import desc

from internal.entity.conversation_entity import MessageStatus
from internal.model import Conversation, Message
from pkg.db import SQLAlchemy

"""
多轮对话系统：在每次用户提问时，自动附带历史对话上下文
RAG 应用：结合知识库检索 + 对话历史，提供更连贯的回答
Token 优化：防止长对话超出模型的上下文窗口限制
记忆管理：智能保留最近的、相关的对话内容

双重限制：同时控制消息数量和 token 数量 
智能裁剪：使用 LangChain 的 trim_messages 策略 
数据过滤：只加载有效的、未删除的消息 ✅ 灵活输出：支持消息对象和文本两种格式
"""

@dataclass
class TokenBufferMemory:
    """基于token计数的缓冲记忆组件"""
    # / **
    # *基于token计数的缓冲记忆组件
    # * @ param
    # dataSource - TypeORM
    # 数据源实例
    # * @ param
    # conversation - 会话模型
    # * @ param
    # modelInstance - LLM大语言模型
    # * /
    db: SQLAlchemy  # 数据库实例
    conversation: Conversation  # 会话模型
    model_instance: BaseLanguageModel  # LLM大语言模型

    def get_history_prompt_messages(
            self,
            max_token_limit: int = 2000,
            message_limit: int = 10,
    ) -> list[AnyMessage]:
        """根据传递的token限制+消息条数限制获取指定会话模型的历史消息列表"""
        # 1.判断会话模型是否存在，如果不存在则直接返回空列表
        if self.conversation is None:
            return []

        # 2.查询该会话的消息列表，并且使用时间进行倒序，同时匹配答案不为空、匹配会话id、没有软删除、状态是正常
        messages = self.db.session.query(Message).filter(
            Message.conversation_id == self.conversation.id,
            Message.answer != "",
            Message.is_deleted == False,
            Message.status == MessageStatus.NORMAL,
        ).order_by(desc("created_at")).limit(message_limit).all()
        messages = list(reversed(messages))

        # 3.将messages转换成LangChain消息列表
        prompt_messages = []
        for message in messages:
            prompt_messages.extend([
                HumanMessage(content=message.query),
                AIMessage(content=message.answer),
            ])

        # 4.调用LangChain继承的trim_messages函数剪切消息列表
        #self.model_instance.get_num_tokens_from_messages()
        #self.model_instance.get_num_tokens()
        # 获取token数
        return trim_messages(
            messages=prompt_messages,
            max_tokens=max_token_limit,
            token_counter=self.model_instance,
            strategy="last",
        )

    def get_history_prompt_text(
            self,
            human_prefix: str = "Human",
            ai_prefix: str = "AI",
            max_token_limit: int = 2000,
            message_limit: int = 10,
    ) -> str:
        """根据传递的数据获取指定会话历史消息提示文本(短期记忆的文本形式，用于文本生成模型)"""
        # 1.根据传递的信息获取历史消息列表
        messages = self.get_history_prompt_messages(max_token_limit, message_limit)

        # 2.调用LangChain集成的get_buffer_string()函数将消息列表转换成文本
        return get_buffer_string(messages, human_prefix, ai_prefix)
