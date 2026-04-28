from typing import Literal

from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.constants import END
from langgraph.graph.state import CompiledStateGraph, StateGraph

from .base_agennt import BaseAgent
from internal.core.agent.entities.agent_entity import AgentState


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
        pass


    def _llm_node(self, state: AgentState) -> AgentState:
        # 大模型节点

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
