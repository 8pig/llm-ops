import logging

from langchain_ollama import OllamaEmbeddings
import os
from dataclasses import dataclass

import tiktoken
from injector import inject
from langchain_classic.embeddings import CacheBackedEmbeddings
from langchain_community.storage import RedisStore
from langchain_core.embeddings import Embeddings
from redis import Redis


@inject
@dataclass
class EmbeddingsService:
    """文本嵌入模型服务"""
    _store: RedisStore
    _embeddings: Embeddings
    _cache_backed_embeddings: CacheBackedEmbeddings

    def __init__(self, redis: Redis):
        """构造函数，初始化文本嵌入模型客户端、存储器、缓存客户端"""
        self._store = RedisStore(client=redis)
        # self._embeddings = HuggingFaceEmbeddings(
        #     model_name="Qwen/Qwen3-Embedding-0.6B",
        #     cache_folder=os.path.join(os.getcwd(), "internal", "core", "embeddings"),
        #     model_kwargs={
        #         "trust_remote_code": True,
        #     }
        # )

        # 根据实际选择 8b/0.6b
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        embedding_model = os.getenv("EMBEDDING_MODEL", "qwen3-embedding:0.6b")

        self._embeddings = OllamaEmbeddings(
            model=embedding_model,
            base_url=ollama_base_url,
        )
        # self._embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self._cache_backed_embeddings = CacheBackedEmbeddings.from_bytes_store(
            self._embeddings,
            self._store,
            namespace="embeddings",
        )

    @classmethod
    def calculate_token_count(cls, query: str) -> int:
        """计算传入文本的token数"""
        # cl100k_base encoding，模型通用的本地编码方式
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(query))

    @property
    def store(self) -> RedisStore:
        return self._store

    @property
    def embeddings(self) -> Embeddings:
        length = self.calculate_token_count("hello world")
        logging.info(f"token length: {length}")
        return self._embeddings

    @property
    def cache_backed_embeddings(self) -> CacheBackedEmbeddings:
        return self._cache_backed_embeddings
