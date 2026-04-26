import dataclasses
import json
import os
import uuid
from threading import Thread
from typing import Any, Literal, Generator
from queue import Queue
from uuid import UUID
from flask import request
from injector import inject
from langchain_classic.base_memory import BaseMemory
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_core.messages import ToolMessage
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.tracers import Run
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph
from internal.schema.app_schema import CompletionReq

from internal.task.demo_task import demo_task
from pkg.response import success_json, validate_error_json, success_message, compact_generate_response
from internal.service import AppService, ApiToolService, VectorDatabaseService, ConversationService
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda, RunnableConfig
from operator import itemgetter
from dataclasses import dataclass
from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from langgraph.constants import END



@inject
@dataclass
class AppHandler:
    app_service: AppService
    api_tool_service: ApiToolService
    # provider_factory: ProviderFactory
    # vector_database_service: VectorDatabaseService
    builtin_provider_manager :BuiltinProviderManager
    coversation_service: ConversationService

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

    def debug(self, app_id: UUID):
        """应用会话调试聊天接口，该接口为流式事件输出"""
        # 1.提取从接口中获取的输入，POST
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.创建队列并提取query数据
        q = Queue()
        query = req.query.data

        # 3.创建graph图程序应用
        def graph_app() -> None:
            """创建Graph图程序应用并执行"""
            # 3.1 创建tools工具列表
            tools = [
                self.builtin_provider_manager.get_tool("google", "google_serper")(),
                self.builtin_provider_manager.get_tool("gaode", "gaode_weather")(),
                self.builtin_provider_manager.get_tool("dalle", "dalle3")(),
            ]

            # 3.2 定义大语言模型/聊天机器人节点
            def chatbot(state: MessagesState) -> MessagesState:
                """聊天机器人节点"""
                # 3.2.1 创建LLM大语言模型
                llm = ChatOpenAI(
                    model="qwen3.6-plus-2026-04-02",
                    api_key=os.getenv("OPENAI_API_KEY"),
                    base_url=os.getenv("OPENAI_API_BASE_URL"),
                ).bind_tools(tools)

                # 3.2.2 调用stream()函数获取流式输出内容，并判断生成内容是文本还是工具调用参数
                is_first_chunk = True
                is_tool_call = False
                gathered = None
                id = str(uuid.uuid4())
                for chunk in llm.stream(state["messages"]):
                    # 3.2.3 检测是不是第一个块，部分LLM的第一个块不会生成内容，需要抛弃掉
                    if is_first_chunk and chunk.content == "" and not chunk.tool_calls:
                        continue

                    # 3.2.4 叠加相应的区块
                    if is_first_chunk:
                        gathered = chunk
                        is_first_chunk = False
                    else:
                        gathered += chunk

                    # 3.2.5 判断是工具调用还是文本生成，往队列中添加不同的数据
                    if chunk.tool_calls or is_tool_call:
                        is_tool_call = True
                        q.put({
                            "id": id,
                            "event": "agent_thought",
                            "data": json.dumps(chunk.tool_call_chunks),
                        })
                    else:
                        q.put({
                            "id": id,
                            "event": "agent_message",
                            "data": chunk.content,
                        })

                return {"messages": [gathered]}

            # 3.3 定义工具/函数调用节点
            def tool_executor(state: MessagesState) -> MessagesState:
                """工具执行节点"""
                # 3.3.1 提取数据状态中的tool_calls
                tool_calls = state["messages"][-1].tool_calls

                # 3.3.2 将工具列表转换成字典便于使用
                tools_by_name = {tool.name: tool for tool in tools}

                # 3.3.3 执行工具并得到对应的结果
                messages = []
                for tool_call in tool_calls:
                    id = str(uuid.uuid4())
                    tool = tools_by_name[tool_call["name"]]
                    tool_result = tool.invoke(tool_call["args"])
                    messages.append(ToolMessage(
                        tool_call_id=tool_call["id"],
                        content=json.dumps(tool_result),
                        name=tool_call["name"],
                    ))
                    q.put({
                        "id": id,
                        "event": "agent_action",
                        "data": json.dumps(tool_result),
                    })

                return {"messages": messages}

            # 3.4 定义路由函数
            def route(state: MessagesState) -> Literal["tool_executor", "__end__"]:
                """定义路由节点，用于确认下一步步骤"""
                ai_message = state["messages"][-1]
                if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
                    return "tool_executor"
                return END

            # 3.5 创建状态图
            graph_builder = StateGraph(MessagesState)

            # 3.6 添加节点
            graph_builder.add_node("llm", chatbot)
            graph_builder.add_node("tool_executor", tool_executor)

            # 3.7 添加边
            graph_builder.set_entry_point("llm")
            graph_builder.add_conditional_edges("llm", route)
            graph_builder.add_edge("tool_executor", "llm")

            # 3.8 编译图程序为可运行组件
            graph = graph_builder.compile()

            # 3.9 调用图结构程序并获取结果
            result = graph.invoke({"messages": [("human", query)]})
            print("最终结果: ", result)
            q.put(None)

        def stream_event_response() -> Generator:
            """流式事件输出响应"""
            # 1.从队列中获取数据并使用yield抛出
            while True:
                item = q.get()
                if item is None:
                    break
                # 2.使用yield关键字返回对应的数据
                yield f"event: {item.get('event')}\ndata: {json.dumps(item)}\n\n"
                q.task_done()

        t = Thread(target=graph_app)
        t.start()

        return compact_generate_response(stream_event_response())

    def _debug(self, app_id: uuid.UUID):
        """聊天接口"""
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)
        query = request.json.get("query")

        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个强大且有丰富感情的聊天机器人, 能根据用户的提问回复对应的问题, 精准且幽默."),
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
            model="qwen3.6-plus-2026-04-02",
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
        human_messge = "你能详细介绍一下 , llm与agent 之间有什么联系吗"
        cn = self.coversation_service.generate_conversation_name(human_messge)
        return success_message({cn: cn})
        # return success_json({"message": "pong"})
        # demo_task.delay(uuid.uuid4())
        # return self.api_tool_service.api_tool_invoke()
