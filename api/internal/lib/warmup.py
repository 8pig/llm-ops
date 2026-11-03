"""应用启动预热

首次 chat 请求需要一次性完成大量初始化：LLM 客户端构建（含 httpx 连接池）、
FAISS 索引加载、langgraph 图编译、tiktoken 词表加载、数据库连接池建立。
实测这些成本叠加可达 30 秒以上，表现为"第一次聊天要等半天"。

这里在应用启动后于后台守护线程完成上述初始化，把一次性成本从首个用户请求
中挪走。预热是尽力而为：任意一项失败只记录日志，不影响应用启动与正常服务。
"""
import logging
import time
from threading import Thread
from uuid import uuid4

logger = logging.getLogger(__name__)


def _step(name: str, func, *args, **kwargs):
    """执行单个预热步骤并记录耗时，异常不外抛"""
    start_at = time.perf_counter()
    try:
        result = func(*args, **kwargs)
        logger.info("[warmup] %s ok %.2fs", name, time.perf_counter() - start_at)
        return result
    except Exception as exc:
        logger.warning("[warmup] %s failed %.2fs: %s", name, time.perf_counter() - start_at, exc)
        return None


def _warmup(app, injector) -> None:
    """按依赖顺序预热各重组件"""
    total_start = time.perf_counter()

    # 1.tiktoken词表：TokenBufferMemory统计token时使用，首次加载需读取缓存文件
    def _tiktoken():
        import tiktoken
        tiktoken.get_encoding("cl100k_base").encode("warmup")

    _step("tiktoken", _tiktoken)

    # 2.LLM客户端：构建Chat实例并触发底层httpx连接池创建
    #   llm_factory内部有lru_cache，预热后请求阶段直接命中，不再重复建连接
    def _llm():
        from internal.lib.llm_factory import get_assistant_chat
        llm = get_assistant_chat()
        _ = llm.root_client
        return llm

    llm = _step("llm_client", _llm)

    # 3.数据库连接池：执行一次查询以建立物理连接
    def _database():
        from sqlalchemy import text
        from pkg.db import SQLAlchemy
        db = injector.get(SQLAlchemy)
        with app.app_context():
            db.session.execute(text("SELECT 1"))
            db.session.remove()

    _step("database", _database)

    # 4.FAISS索引：首次加载需import faiss并反序列化索引文件
    #   FaissService内部有类级缓存(索引只读，进程内加载一次即可)，
    #   injector默认非单例，不加缓存的话每个请求都要重新反序列化索引。
    def _faiss():
        from internal.service.faiss_service import FaissService
        injector.get(FaissService)

    _step("faiss", _faiss)

    # 5.嵌入模型：FAISS检索与长期记忆召回都要先把query向量化
    #   首次调用会触发远端Ollama加载嵌入模型(秒级到十秒级)，放到预热里消化掉
    def _embedding():
        from internal.service.embeddings_service import EmbeddingsService
        service = injector.get(EmbeddingsService)
        service.embeddings.embed_query("warmup")

    _step("embedding", _embedding)

    # 6.langgraph图编译：走一次智能体构建，完成图编译与相关模块import
    #   构建本身不调用LLM，仅编译StateGraph(实测仅0.01s，主要是补齐模块import)
    def _agent():
        if llm is None:
            return
        from internal.core.agent.agents import FunctionCallAgent
        from internal.core.agent.entities.agent_entity import AgentConfig
        from internal.entity.conversation_entity import InvokeFrom
        FunctionCallAgent(
            llm=llm,
            agent_config=AgentConfig(
                user_id=uuid4(),
                invoke_from=InvokeFrom.ASSISTANT_AGENT,
                enable_long_term_memory=False,
                tools=[],
            ),
        )

    _step("agent_graph", _agent)

    logger.info("[warmup] completed in %.2fs", time.perf_counter() - total_start)


def start_warmup(app, injector) -> None:
    """在后台守护线程启动预热，不阻塞应用启动"""
    Thread(target=_warmup, args=(app, injector), name="app-warmup", daemon=True).start()
