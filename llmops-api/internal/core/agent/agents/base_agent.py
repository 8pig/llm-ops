import uuid
from abc import abstractmethod
from threading import Thread
from typing import Optional, Any, Iterator

from langchain_core.language_models import BaseLanguageModel
from langchain_core.load import Serializable
from pydantic import PrivateAttr, Field
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph.state import CompiledStateGraph

from internal.core.agent.entities.agent_entity import AgentConfig, AgentState
from internal.core.agent.entities.queue_entity import AgentResult, AgentThought
from internal.exception import FailException

from .agent_queue_manager import AgentQueueManager


class BaseAgent(Serializable, Runnable):
    """基于Runnable的基础智能体基类"""
    llm: BaseLanguageModel
    agent_config: AgentConfig
    name: Optional[str] = Field(default=None, description="Agent名称")
    _agent: CompiledStateGraph = PrivateAttr(None)
    _agent_queue_manager: AgentQueueManager = PrivateAttr(None)

    class Config:
        arbitrary_types_allowed = True

    def __init__(
            self,
            *,
            llm: BaseLanguageModel = None,
            agent_config: AgentConfig = None,
            name: str = None,
            **kwargs,
    ):
        """构造函数，初始化智能体图结构程序"""
        llm = llm or kwargs.get('llm')
        agent_config = agent_config or kwargs.get('agent_config')
        name = name or kwargs.get('name', self.__class__.__name__)

        init_data = {
            'llm': llm,
            'agent_config': agent_config,
            'name': name,
        }
        init_data = {k: v for k, v in init_data.items() if v is not None}

        super().__init__(**init_data, **kwargs)
        self._agent = self._build_agent()
        self._agent_queue_manager = AgentQueueManager(
            user_id=self.agent_config.user_id,
            invoke_from=self.agent_config.invoke_from,
        )

    @abstractmethod
    def _build_agent(self) -> CompiledStateGraph:
        """构建智能体函数，等待子类实现"""
        raise NotImplementedError("_build_agent()未实现")

    def invoke(self, input: AgentState, config: Optional[RunnableConfig] = None) -> AgentResult:
        """块内容响应，一次性生成完整内容后返回"""
        pass

    def stream(
            self,
            input: AgentState,
            config: Optional[RunnableConfig] = None,
            **kwargs: Optional[Any],
    ) -> Iterator[AgentThought]:
        """流式输出，每个Not节点或者LLM每生成一个token时则会返回相应内容"""
        if not self._agent:
            raise FailException("智能体未成功构建，请核实后尝试")

        input["task_id"] = input.get("task_id", uuid.uuid4())
        input["history"] = input.get("history", [])
        input["iteration_count"] = input.get("iteration_count", 0)

        thread = Thread(
            target=self._agent.invoke,
            args=(input,)
        )
        thread.start()

        yield from self._agent_queue_manager.listen(input["task_id"])

    @property
    def agent_queue_manager(self) -> AgentQueueManager:
        """只读属性，返回智能体队列管理器"""
        return self._agent_queue_manager

