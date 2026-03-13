import dataclasses
import os
import uuid

from flask import request, jsonify
from injector import inject
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_openai import ChatOpenAI
from openai import OpenAI
from internal.schema.app_schema import  CompletionsReq
from pkg.response import success_json, validate_error_json, success_message
from internal.service import AppService
from langchain_core.prompts import ChatPromptTemplate

@inject
@dataclasses.dataclass
class AppHandler:
    app_service: AppService
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

    def delete_app(self, id: uuid.UUID):
        app = self.app_service.delete_app(id)
        return success_message(f"删除成功: {app.name}")

    def completions(self):
        """聊天接口"""
        # 1. 提取用户输入
        # 2. 构建ai客户端发起请求
        # 3. 得到响应  返回前端
        req = CompletionsReq()
        if not req.validate():
            return validate_error_json(req.errors)
        query = request.json.get("query")


        prompt = ChatPromptTemplate.from_template("请根据用户的提问进|行回答 \n {query}")
        parser = StrOutputParser()

        client = ChatOpenAI(
            model="qwen3-max-2026-01-23",
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE_URL"),
        )

        ai_message = client.invoke(prompt.invoke({"query": query}))

        content = parser.invoke(ai_message)


        return success_json({"content": content})
