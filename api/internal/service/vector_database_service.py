
import os

from dataclasses import dataclass
import weaviate
from flask_weaviate import FlaskWeaviate
from injector import inject
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import OpenAIEmbeddings
from langchain_weaviate import WeaviateVectorStore
from weaviate import WeaviateClient
from weaviate.collections import Collection
from weaviate.classes.config import Configure, DataType, Property

from .embeddings_service import EmbeddingsService


# 向量库集合名字
COLLECTION_NAME = "Dataset"

@inject
@dataclass
class VectorDatabaseService:
    """向量数据库服务"""
    _instance = None
    _initialized = False

    weaviate: FlaskWeaviate
    embedding_service: EmbeddingsService

    def _ensure_collection(self) -> None:
        """确保向量集合存在，如果不存在则创建

        属性表必须与写入侧 metadata(indexing_service / segment_service)以及
        检索过滤字段(SemanticRetriever)保持一致，否则集合重建后语义检索会因
        过滤字段 document_enabled / segment_enabled 不存在而直接报错。
        """
        try:
            if not self.weaviate.client.collections.exists(COLLECTION_NAME):
                print(f"Creating collection '{COLLECTION_NAME}'")

                self.weaviate.client.collections.create(
                    name=COLLECTION_NAME,
                    vectorizer_config=Configure.Vectorizer.none(),
                    properties=[
                        Property(name="text", data_type=DataType.TEXT),
                        Property(name="account_id", data_type=DataType.UUID),
                        Property(name="dataset_id", data_type=DataType.UUID),
                        Property(name="document_id", data_type=DataType.UUID),
                        Property(name="segment_id", data_type=DataType.UUID),
                        Property(name="node_id", data_type=DataType.UUID),
                        Property(name="document_enabled", data_type=DataType.BOOL),
                        Property(name="segment_enabled", data_type=DataType.BOOL),
                    ],
                    vector_index_config=Configure.VectorIndex.hnsw(
                        distance_metric=Configure.VectorIndex.Distance.COSINE
                    )
                )
                print(f"Collection '{COLLECTION_NAME}' created successfully")
            else:
                print(f"Collection '{COLLECTION_NAME}' already exists")
        except Exception as e:
            print(f"Error ensuring collection: {e}")
            raise

    def get_retriever(self) -> VectorStoreRetriever:
        """获取检索器"""
        return self.vector_store.as_retriever()

    @property
    def vector_store(self) -> WeaviateVectorStore:
        return WeaviateVectorStore(
            client=self.weaviate.client,
            index_name=COLLECTION_NAME,
            text_key="text",
            embedding=self.embedding_service.cache_backed_embeddings
        )


    @property
    def collection(self) -> Collection:
        return self.weaviate.client.collections.get(COLLECTION_NAME)
