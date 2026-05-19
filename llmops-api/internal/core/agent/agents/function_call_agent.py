#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/10/01 15:53
@Author  : thezehui@gmail.com
@File    : function_call_agent.py
"""
import json
import time
import uuid
from threading import Thread
from typing import Literal, Generator

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage, ToolMessage, RemoveMessage
from langchain_core.messages import messages_to_dict
from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from internal.core.agent.entities.agent_entity import AgentState, AGENT_SYSTEM_PROMPT_TEMPLATE, \
    DATASET_RETRIEVAL_TOOL_NAME
from internal.core.agent.entities.queue_entity import AgentQueueEvent, QueueEvent
from internal.exception import FailException
from .base_agent import BaseAgent


class FunctionCallAgent(BaseAgent):
    """基于函数/工具调用的智能体"""

    def run(
            self,
            query: str,
            history: list[AnyMessage] = None,
            long_term_memory: str = "",
    ) -> Generator[AgentQueueEvent, None, None]:
        """运行智能体应用，并使用yield关键字返回对应的数据"""
        # 1.预处理传递的数据
        if history is None:
            history = []

        # 2.调用函数构建智能体
        agent = self._build_graph()

        # 3.调用智能体获取数据
        thread = Thread(
            target=agent.invoke,
            args=(
                {
                    "messages": [HumanMessage(content=query)],
                    "history": history,
                    "long_term_memory": long_term_memory,
                },
            )
        )
        thread.start()

        # 4.调用队列管理器监听数据并返回生成式数据
        yield from self.agent_queue_manager.listen()

    def _build_graph(self) -> CompiledStateGraph:
        """构建LangGraph图结构编译程序"""
        # 1.创建图
        graph = StateGraph(AgentState)

        # 2.添加节点
        graph.add_node("long_term_memory_recall", self._long_term_memory_recall_node)
        graph.add_node("llm", self._llm_node)
        graph.add_node("tools", self._tools_node)

        # 3.添加边，并设置起点和终点
        graph.set_entry_point("long_term_memory_recall")
        graph.add_edge("long_term_memory_recall", "llm")
        graph.add_conditional_edges("llm", self._tools_condition)
        graph.add_edge("tools", "llm")

        # 4.编译应用并返回
        agent = graph.compile()

        return agent

    def _long_term_memory_recall_node(self, state: AgentState) -> AgentState:
        """长期记忆召回节点"""
        # 1.根据传递的智能体配置判断是否需要召回长期记忆
        long_term_memory = ""
        if self.agent_config.enable_long_term_memory:
            long_term_memory = state["long_term_memory"]
            self.agent_queue_manager.publish(AgentQueueEvent(
                id=uuid.uuid4(),
                task_id=self.agent_queue_manager.task_id,
                event=QueueEvent.LONG_TERM_MEMORY_RECALL,
                observation=long_term_memory,
            ))

        # 2.构建预设消息列表，并将preset_prompt+long_term_memory填充到系统消息中
        preset_messages = [
            SystemMessage(AGENT_SYSTEM_PROMPT_TEMPLATE.format(
                preset_prompt=self.agent_config.preset_prompt,
                long_term_memory=long_term_memory,
            ))
        ]

        # 3.将短期历史消息添加到消息列表中
        history = state["history"]
        if isinstance(history, list) and len(history) > 0:
            # 4.校验历史消息是不是复数形式，也就是[人类消息, AI消息, 人类消息, AI消息, ...]
            if len(history) % 2 != 0:
                raise FailException("智能体历史消息列表格式错误")
            # 5.拼接历史消息
            preset_messages.extend(history)

        # 6.拼接当前用户的提问信息
        human_message = state["messages"][-1]
        preset_messages.append(HumanMessage(human_message.content))

        # 7.处理预设消息，将预设消息添加到用户消息前，先去删除用户的原始消息，然后补充一个新的代替
        return {
            "messages": [RemoveMessage(id=human_message.id), *preset_messages],
        }

    def _llm_node(self, state: AgentState) -> AgentState:
        """大语言模型节点"""
        # 1.从智能体配置中提取大语言模型
        id = uuid.uuid4()
        start_at = time.perf_counter()
        llm = self.agent_config.llm

        # 2.检测大语言模型实例是否有bind_tools方法，如果没有则不绑定，如果有还需要检测tools是否为空，不为空则绑定
        if hasattr(llm, "bind_tools") and callable(getattr(llm, "bind_tools")) and len(self.agent_config.tools) > 0:
            llm = llm.bind_tools(self.agent_config.tools)

        # 3.流式调用LLM输出对应内容
        gathered = None
        is_first_chunk = True
        generation_type = ""
        for chunk in llm.stream(state["messages"]):
            if is_first_chunk:
                gathered = chunk
                is_first_chunk = False
            else:
                gathered += chunk

            # 4.检测生成类型是工具参数还是文本生成
            if not generation_type:
                if chunk.tool_calls:
                    generation_type = "thought"
                elif chunk.content:
                    generation_type = "message"

            # 5.如果生成的是消息则提交智能体消息事件
            if generation_type == "message":
                self.agent_queue_manager.publish(AgentQueueEvent(
                    id=id,
                    task_id=self.agent_queue_manager.task_id,
                    event=QueueEvent.AGENT_MESSAGE,
                    thought=chunk.content,
                    messages=messages_to_dict(state["messages"]),
                    answer=chunk.content,
                    latency=(time.perf_counter() - start_at),
                ))

        # 6.如果类型为推理则添加智能体推理事件
        if generation_type == "thought":
            self.agent_queue_manager.publish(AgentQueueEvent(
                id=id,
                task_id=self.agent_queue_manager.task_id,
                event=QueueEvent.AGENT_THOUGHT,
                thought=json.dumps(gathered.tool_calls),
                messages=messages_to_dict(state["messages"]),
                latency=(time.perf_counter() - start_at),
            ))
        elif generation_type == "message":
            # 7.如果LLM直接生成answer则表示已经拿到了最终答案，则停止监听
            self.agent_queue_manager.stop_listen()

        return {"messages": [gathered]}

    def _tools_node(self, state: AgentState) -> AgentState:
        """工具执行节点"""
        # 1.将工具列表转换成字典，便于调用指定的工具
        tools_by_name = {tool.name: tool for tool in self.agent_config.tools}

        # 2.提取消息中的工具调用参数
        tool_calls = state["messages"][-1].tool_calls

        # 3.循环执行工具组装工具消息
        messages = []
        for tool_call in tool_calls:
            # 4.创建智能体动作事件id并记录开始时间
            id = uuid.uuid4()
            start_at = time.perf_counter()

            # 5.获取工具并调用工具
            tool = tools_by_name[tool_call["name"]]
            tool_result = tool.invoke(tool_call["args"])

            # 6.将工具消息添加到消息列表中
            messages.append(ToolMessage(
                tool_call_id=tool_call["id"],
                content=json.dumps(tool_result),
                name=tool_call["name"],
            ))

            # 7.判断执行工具的名字，提交不同事件，涵盖智能体动作以及知识库检索
            event = (
                QueueEvent.AGENT_ACTION
                if tool_call["name"] != DATASET_RETRIEVAL_TOOL_NAME
                else QueueEvent.DATASET_RETRIEVAL
            )
            self.agent_queue_manager.publish(AgentQueueEvent(
                id=id,
                task_id=self.agent_queue_manager.task_id,
                event=event,
                observation=json.dumps(tool_result),
                tool=tool_call["name"],
                tool_input=tool_call["args"],
                latency=(time.perf_counter() - start_at),
            ))

        return { "messages": messages }

    @classmethod
    def _tools_condition(cls, state: AgentState) -> Literal["tools", "__end__"]:
        """检测下一个节点是执行tools节点，还是直接结束"""
        # 1.提取状态中的最后一条消息(AI消息)
        messages = state["messages"]
        ai_message = messages[-1]

        # 2.检测是否存在tools_calls这个参数，如果存在则执行tools节点，否则结束
        if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
            return "tools"

        return END
