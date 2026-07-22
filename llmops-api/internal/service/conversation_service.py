
import logging
import os
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from flask import Flask
from injector import inject
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from internal.entity.conversation_entity import (
    SUMMARIZER_TEMPLATE,
    CONVERSATION_NAME_TEMPLATE,
    ConversationInfo,
    SUGGESTED_QUESTIONS_TEMPLATE,
    SuggestedQuestions, InvokeFrom,
)
from pkg.db import SQLAlchemy
from .base_service import BaseService
from internal.core.agent.entities.queue_entity import QueueEvent, AgentThought
from internal.model import MessageAgentThought, Conversation, Message


@inject
@dataclass
class ConversationService(BaseService):
    """会话服务"""
    db: SQLAlchemy

    @classmethod
    def summary(cls, human_message: str, ai_message: str, old_summary: str = "") -> str:
        """根据传递的人类消息、AI消息还有原始的摘要信息总结生成一段新的摘要"""
        # 1.创建prompt
        prompt = ChatPromptTemplate.from_template(SUMMARIZER_TEMPLATE)

        # 2.构建大语言模型实例，并且将大语言模型的温度调低，降低幻觉的概率

        llm = ChatOpenAI(
            model=os.getenv("LLM_MODEL"),
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE_URL"),
            temperature=0.5
        )

        # 3.构建链应用
        summary_chain = prompt | llm | StrOutputParser()

        # 4.调用链并获取新摘要信息
        new_summary = summary_chain.invoke({
            "summary": old_summary,
            "new_lines": f"Human: {human_message}\nAI: {ai_message}",
        })

        return new_summary

    @classmethod
    def generate_conversation_name(cls, query: str) -> str:
        """根据传递的query生成对应的会话名字，并且语言与用户的输入保持一致"""
        # 1.创建prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", f""""{CONVERSATION_NAME_TEMPLATE}。 \n请以 JSON 格式输出，包含 language_type、reasoning、subject 三个字段。"""),
            ("human", "{query}")
        ])

        # 2.构建大语言模型实例，并且将大语言模型的温度调低，降低幻觉的概率
        llm = ChatOpenAI(
            model=os.getenv("LLM_MODEL"),
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE_URL"),
            temperature=0,
        )

        # 3.构建链应用（使用 JsonOutputParser 替代 with_structured_output，避免模型 response_format 兼容问题）
        chain = prompt | llm | JsonOutputParser(pydantic_object=ConversationInfo)

        # 4.提取并整理query，截取长度过长的部分
        if len(query) > 2000:
            query = query[:300] + "...[TRUNCATED]..." + query[-300:]
        query = query.replace("\n", " ")

        # 5.调用链并获取会话信息
        conversation_info = chain.invoke({"query": query})
        print(conversation_info)
        # 6.提取会话名称

        name = "新的会话"
        try:
            #  防止获取不到   如果用到中转站大模型不对应 或者 大模型也有随机性不对应会出错
            if conversation_info and isinstance(conversation_info, dict) and conversation_info.get("subject"):
                name = conversation_info["subject"]
            elif conversation_info and hasattr(conversation_info, "subject"):
                name = conversation_info.subject
        except Exception as e:
            logging.exception(f"提取会话名称出错, conversation_info: {conversation_info}, 错误信息: {str(e)}")
        if len(name) > 75:
            name = name[:75] + "..."


        return name

    @classmethod
    def generate_suggested_questions(cls, histories: str) -> list[str]:
        """根据传递的历史信息生成最多不超过3个的建议问题"""
        # 1.创建prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", SUGGESTED_QUESTIONS_TEMPLATE),
            ("human", "{histories}")
        ])

        # 2.构建大语言模型实例，并且将大语言模型的温度调低，降低幻觉的概率
        llm = ChatOpenAI(
            model=os.getenv("LLM_MODEL"),
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE_URL"),
            temperature=0
        )
        structured_llm = prompt | llm | JsonOutputParser(pydantic_object=SuggestedQuestions)

        # 3.构建链应用
        chain = prompt | structured_llm

        # 4.调用链并获取建议问题列表
        suggested_questions = chain.invoke({"histories": histories})

        # 5.提取建议问题列表
        questions = []
        try:
            if suggested_questions and isinstance(suggested_questions, dict):
                questions = suggested_questions.get("questions", [])
            elif suggested_questions and hasattr(suggested_questions, "questions"):
                questions = suggested_questions.questions

            if not isinstance(questions, list):
                questions = []
        except Exception as e:
            logging.exception(f"提取建议问题出错, suggested_questions: {suggested_questions}, 错误信息: {str(e)}")

        if len(questions) > 3:
            questions = questions[:3]

        return questions


    def save_agent_thoughts(
            self,
            flask_app: Flask,
            account_id: UUID,
            app_id: UUID,
            app_config: dict[str, Any],
            conversation_id: UUID,
            message_id: UUID,
            agent_thoughts: list[AgentThought],
    ):
        """存储智能体推理步骤消息"""
        with flask_app.app_context():
            # 1.定义变量存储推理位置及总耗时
            position = 0
            latency = 0

            # 2.在子线程中重新查询conversation以及message，确保对象会被子线程的会话管理到
            conversation = self.get(Conversation, conversation_id)
            message = self.get(Message, message_id)

            # 3.循环遍历所有的智能体推理过程执行存储操作
            for agent_thought in agent_thoughts:
                # 4.存储长期记忆召回、推理、消息、动作、知识库检索等步骤
                if agent_thought.event in [
                    QueueEvent.LONG_TERM_MEMORY_RECALL,
                    QueueEvent.AGENT_THOUGHT,
                    QueueEvent.AGENT_MESSAGE,
                    QueueEvent.AGENT_ACTION,
                    QueueEvent.DATASET_RETRIEVAL,
                ]:
                    # 5.更新位置及总耗时
                    position += 1
                    latency += agent_thought.latency

                    # 6.创建智能体消息推理步骤
                    self.create(
                        MessageAgentThought,
                        app_id=app_id,
                        conversation_id=conversation.id,
                        message_id=message.id,
                        invoke_from=InvokeFrom.DEBUGGER,
                        created_by=account_id,
                        position=position,
                        event=agent_thought.event,
                        thought=agent_thought.thought,
                        observation=agent_thought.observation,
                        tool=agent_thought.tool,
                        tool_input=agent_thought.tool_input,
                        # 消息相关数据
                        message=agent_thought.message,
                        message_token_count=agent_thought.message_token_count,
                        message_unit_price=agent_thought.message_unit_price,
                        message_price_unit=agent_thought.message_price_unit,
                        # 答案相关字段
                        answer=agent_thought.answer,
                        answer_token_count=agent_thought.answer_token_count,
                        answer_unit_price=agent_thought.answer_unit_price,
                        answer_price_unit=agent_thought.answer_price_unit,
                        # Agent推理统计相关
                        total_token_count=agent_thought.total_token_count,
                        total_price=agent_thought.total_price,
                        latency=agent_thought.latency,
                    )

                # 7.检测事件是否为Agent_message
                if agent_thought.event == QueueEvent.AGENT_MESSAGE:
                    # 8.更新消息信息
                    self.update(
                        message,
                        # 消息相关字段
                        message=agent_thought.message,
                        message_token_count=agent_thought.message_token_count,
                        message_unit_price=agent_thought.message_unit_price,
                        message_price_unit=agent_thought.message_price_unit,
                        # 答案相关字段
                        answer=agent_thought.answer,
                        answer_token_count=agent_thought.answer_token_count,
                        answer_unit_price=agent_thought.answer_unit_price,
                        answer_price_unit=agent_thought.answer_price_unit,
                        # Agent推理统计相关
                        total_token_count=agent_thought.total_token_count,
                        total_price=agent_thought.total_price,
                        latency=latency,
                    )

                    # 9.检测是否开启长期记忆
                    if app_config["long_term_memory"]["enable"]:
                        new_summary = self.summary(
                            message.query,
                            agent_thought.answer,
                            conversation.summary
                        )
                        self.update(
                            conversation,
                            summary=new_summary,
                        )

                    # 10.处理生成新会话名称
                    if conversation.is_new:
                        new_conversation_name = self.generate_conversation_name(message.query)
                        self.update(
                            conversation,
                            name=new_conversation_name,
                        )

                # 11.判断是否为停止或者错误，如果是则需要更新消息状态
                if agent_thought.event in [QueueEvent.TIMEOUT, QueueEvent.STOP, QueueEvent.ERROR]:
                    self.update(
                        message,
                        status=agent_thought.event,
                        error=agent_thought.observation,
                    )
                    break
