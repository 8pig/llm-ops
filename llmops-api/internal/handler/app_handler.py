import os

from flask import request
from openai import OpenAI
from internal.schema.app_schema import  CompletionsReq


class AppHandler:
    """应用控制器"""

    def completions(self):
        """聊天接口"""
        # 1. 提取用户输入
        # 2. 构建ai客户端发起请求
        # 3. 得到响应  返回前端
        req = CompletionsReq()
        if not req.validate():
            return req.errors
        query = request.json.get("query")
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE_URL"),
        )

        response = client.chat.completions.create(
            model="qwen-plus-2025-12-01",  # 使用聊天模型
            messages=[
                {
                    "role": "system",
                    "content": "你是一个贴心小助手, 你叫小黑，请根据用户的输入尽你所能回复对应的信息。"
                },
                {
                    "role": "user",
                    "content": query
                }
            ]
        )

        # 返回AI的回复
        # return {"response": response.choices[0].message.content}
        content = response.choices[0].message.content
        return content
