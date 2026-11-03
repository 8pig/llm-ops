
import os
from threading import Lock

from injector import inject
from langchain_community.vectorstores import FAISS
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, tool

from internal.core.agent.entities.agent_entity import DATASET_RETRIEVAL_TOOL_NAME
from internal.lib.helper import combine_documents
from .embeddings_service import EmbeddingsService


@inject
class FaissService:
    """Faiss向量数据库服务"""
    # 索引只读，进程内加载一次即可。injector默认非单例，每个请求都会新建本服务，
    # 若不缓存则每次请求都要重新反序列化索引文件(index.faiss + index.pkl)。
    _faiss_cache: FAISS | None = None
    _faiss_lock = Lock()

    faiss: FAISS
    embeddings_service: EmbeddingsService

    def __init__(self, embeddings_service: EmbeddingsService):
        """构造函数，完成Faiss向量数据库的初始化"""
        # 1.赋值embeddings_service
        self.embeddings_service = embeddings_service

        # 2.获取internal路径并计算本地向量数据库的实际路径
        internal_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        faiss_vector_store_path = os.path.join(internal_path, "core", "vector_store")

        # 3.初始化faiss向量数据库，命中类级缓存时直接复用
        if FaissService._faiss_cache is None:
            with FaissService._faiss_lock:
                if FaissService._faiss_cache is None:
                    FaissService._faiss_cache = FAISS.load_local(
                        folder_path=faiss_vector_store_path,
                        embeddings=self.embeddings_service.embeddings,
                        allow_dangerous_deserialization=True,
                    )
        self.faiss = FaissService._faiss_cache

    def convert_faiss_to_tool(self) -> BaseTool:
        """将Faiss向量数据库检索器转换成LangChain工具"""
        # 1.将Faiss向量数据库转换成检索器
        retrieval = self.faiss.as_retriever(
            search_type="mmr", # 最大相似性搜索
            search_kwargs={"k": 5, "fetch_k": 20},
        )

        # 2.构建检索链，并将检索的结果合并成字符串
        search_chain = retrieval | combine_documents

        class DatasetRetrievalInput(BaseModel):
            """知识库检索工具输入结构"""
            query: str = Field(description="知识库检索query语句，类型为字符串")

        @tool(DATASET_RETRIEVAL_TOOL_NAME, args_schema=DatasetRetrievalInput)
        def dataset_retrieval(query: str) -> str:
            """如果需要检索扩展的知识库内容，当你觉得用户的提问超过你的知识范围时，可以尝试调用该工具，输入为搜索query语句，返回数据为检索内容字符串"""
            return search_chain.invoke(query)

        return dataset_retrieval
