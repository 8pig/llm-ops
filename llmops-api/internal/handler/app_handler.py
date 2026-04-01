import dataclasses
import os
import uuid
from operator import itemgetter
from typing import Any

from flask import request, jsonify
from flask_migrate import history
from injector import inject
from langchain_classic.base_memory import BaseMemory
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.tracers import Run
from langchain_openai import ChatOpenAI
from openai import OpenAI

from internal.core.tools.builtin_tools import providers
from internal.schema.app_schema import  CompletionsReq
from pkg.response import success_json, validate_error_json, success_message
from internal.service import AppService
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda, RunnableConfig
from operator import itemgetter
from internal.core.tools.builtin_tools.providers import ProviderFactory

@inject
@dataclasses.dataclass
class AppHandler:
    app_service: AppService

    provider_factory: ProviderFactory

    """应用控制器"""
    def create_app(self):
        app = self.app_service.create_app()
        return success_message(f"应用已创建, id为{app.id}")

    def get_app(self, id: uuid.UUID):
        app = self.app_service.get_app(id)
        return success_message(f"应用名: {app.name}")

    def update_app(self, id: uuid.UUID):
        app = self.app_service.update_app(id)

        return success_message(f"更新成功: {app.name}")

    def delete_app(self, app_id: uuid.UUID):
        app = self.app_service.delete_app(app_id)
        return success_message(f"删除成功: {app.name}")

    @classmethod
    def _load_memory_variables(cls, input: dict[str, Any], config: RunnableConfig) -> dict[str, Any]:
        """加載记忆变量"""
        configurable = config.get("configurable", {})
        configurable_memory = configurable.get("memory", None)
        if configurable_memory is not None and isinstance(configurable_memory, BaseMemory):
            return configurable_memory.load_memory_variables(input)
        return {"history": []}


    @classmethod
    def _save_context(cls, run_obj: Run, config: RunnableConfig) -> None:
        """存储上下文信息 保存到记忆实体里"""
        configurable = config.get("configurable", {})
        configurable_memory = configurable.get("memory", None)
        if configurable_memory is not None and isinstance(configurable_memory, BaseMemory):
            configurable_memory.save_context(run_obj.inputs, run_obj.outputs)




    def debug(self, app_id: uuid.UUID):
        """聊天接口"""
        # 1. 提取用户输入
        # 2. 构建ai客户端发起请求
        # 3. 得到响应  返回前端
        req = CompletionsReq()
        if not req.validate():
            return validate_error_json(req.errors)
        query = request.json.get("query")

        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个强大且有丰富敢情的聊天机器人, 能更具用户的提问回复对应的问题"),
            MessagesPlaceholder(variable_name="history"),
            ("human", query)
        ])

        memory = ConversationBufferWindowMemory(
            k=3,
            memory_key="history",
            input_key="query",
            output_key="output",
            return_messages=True,
            chat_memory=FileChatMessageHistory("./storage/memory/chat_history.txt")
        )
        # 创建模型
        llm = ChatOpenAI(
            # model="MiniMax-M2.1",
            model="qwen3-max-2026-01-23",
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE_URL"),
        )
        # 创建chain
        chain = (RunnablePassthrough.assign(
            history=RunnableLambda(self._load_memory_variables) | itemgetter("history")
        ) |prompt | llm | StrOutputParser()).with_listeners(
            on_end=self._save_context
        )


        chain_input =  {"query": query}
        content = chain.invoke(chain_input, config={
            "configurable":{
                "memory": memory
            }
        })


        return success_json({"content": content})

    def ping(self):

        providers = self.provider_factory.get_provider_entities()


        return success_json({
            "providers":
                [
                    provider.dict()
                    for provider in providers
                ]
        })
        # google_serper = self.provider_factory.get_tool("google", "google_serper")()
        # print(google_serper)
        # print(google_serper.invoke("张雪峰"))
        # return success_json()
