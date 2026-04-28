from typing import Literal

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage, RemoveMessage
from langgraph.constants import END
from langgraph.graph.state import CompiledStateGraph, StateGraph

from internal.exception import FailException
from .base_agennt import BaseAgent
from internal.core.agent.entities.agent_entity import AgentState, AGENT_SYSTEM_PROMPT_TEMPLATE


class FunctionCallAgent(BaseAgent):


    def run(self, query: str, history: list[AnyMessage] = None, long_term_memory: str = None):
        """运行智能体  """
        if history is None:
            history = []

        agent = self._build_graph()
        return agent.invoke({
            "messages": [HumanMessage(content=query)],
            "history": history,
            "long_term_memory": long_term_memory,
        })


    def _build_graph(self) -> CompiledStateGraph:
        """ graph 图构建编译"""

        graph = StateGraph(AgentState)

        graph.add_node( "long_term_memory_recall",  self._long_term_memory_recall_node)
        graph.add_node( "llm", self._llm_node)
        graph.add_node( "tools", self._tools_node)

        # 边 起点终点
        graph.set_entry_point("long_term_memory_recall")
        graph.add_edge("long_term_memory_recall", "llm")
        #  对于大模型，需要条件判断下一步
        graph.add_conditional_edges("llm", self._tools_condition)
        graph.add_edge("tools", "llm")

        # 编译
        agent = graph.compile()

        return agent


        pass

    def _long_term_memory_recall_node(self, state: AgentState) -> AgentState:
        # 长期记忆召回
        # 根据传递的智能体配置判断是否需要召回长期记忆
        long_term_memory = ""
        if self.agent_config.enable_long_term_memory:
            long_term_memory = state["long_term_memory"]

        # 构建预设消息列表，并将preset_prompt+long_term_memory填充到系统消息中
        preset_messages = [
            SystemMessage(AGENT_SYSTEM_PROMPT_TEMPLATE.format(
                preset_prompt=self.agent_config.preset_prompt,
                long_term_memory=long_term_memory,
            ))
        ]

        # 将短期历史消息添加到消息列表中
        history = state["history"]
        if isinstance(history, list) and len(history) > 0:
            # 校验历史消息是不是复数形式，[人类消息, AI消息, 人类消息, AI消息, ...]
            if len(history) % 2 != 0:
                raise FailException("智能体历史消息列表格式错误")
            # 拼接历史消息
            preset_messages.extend(history)

            # 因为
            # LangChain
            # 的消息对象是不可变的，而且消息的位置由添加到列表的顺序决定。所以必须：
            # 删除旧位置的消息
            # 在新位置添加新消息

        # 拼接当前用户的提问信息
        human_message = state["messages"][-1]
        preset_messages.append(HumanMessage(human_message.content))

        # 处理预设消息，将预设消息添加到用户消息前，先去删除用户的原始消息，然后补充一个新的代替
        return {
            "messages": [RemoveMessage(id=human_message.id), *preset_messages],
        }

    def _llm_node(self, state: AgentState) -> AgentState:
        # 大模型节点
        llm = self.agent_config.llm
        # 判断llm 是否有bind_tools
        if hasattr(llm, "bind_tools") and callable(llm.bind_tools) and len(self.agent_config.tools) > 0:
            llm = llm.bind_tools(self.agent_config.tools)



        pass


    def _tools_node(self, state: AgentState) -> AgentState:
        # 工具执行节点
        pass



    def _tool_call_node(self, state: AgentState) -> AgentState:
        pass

    @classmethod
    def _tools_condition(cls, state: AgentState) -> Literal["tools", "__end__"]:
        # 提取最后一条消息
        message = state["messages"]
        ai_message = message[-1]

        #是否存在tools_calls 满足走工具调用
        if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
            return "tools"

        return END
