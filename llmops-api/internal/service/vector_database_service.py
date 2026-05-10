
import os

import weaviate
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
class VectorDatabaseService:
    """向量数据库服务"""
    client: WeaviateClient
    vector_store: WeaviateVectorStore
    embedding_service: EmbeddingsService

    def __init__(self, embedding_service: EmbeddingsService):
        """构造函数，完成向量数据库服务的客户端+LangChain向量数据库实例的创建"""

        self.embedding_service = embedding_service

        # 1.创建/连接weaviate向量数据库
        self.client = weaviate.connect_to_local(
            host=os.getenv("WEAVIATE_HOST"),
            port=int(os.getenv("WEAVIATE_PORT"))
        )

        # 2.确保集合存在，如果不存在则创建
        self._ensure_collection()

        # 3.创建LangChain向量数据库
        self.vector_store = WeaviateVectorStore(
            client=self.client,
            index_name=COLLECTION_NAME,
            text_key="text",
            embedding=self.embedding_service.embeddings
        )

    def _ensure_collection(self) -> None:
        """确保向量集合存在，如果不存在则创建"""
        try:
            if not self.client.collections.exists(COLLECTION_NAME):
                test_embedding = self.embedding_service.embeddings.embed_query("test")
                vector_dim = len(test_embedding)

                print(f"Creating collection '{COLLECTION_NAME}' with vector dimension: {vector_dim}")

                self.client.collections.create(
                    name=COLLECTION_NAME,
                    vectorizer_config=Configure.Vectorizer.none(),
                    properties=[
                        Property(name="text", data_type=DataType.TEXT),
                        Property(name="dataset_id", data_type=DataType.UUID),
                        Property(name="document_id", data_type=DataType.UUID),
                        Property(name="segment_id", data_type=DataType.UUID),
                        Property(name="enabled", data_type=DataType.BOOL),
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

    @classmethod
    def combine_documents(cls, documents: list[Document]) -> str:
        """将对应的文档列表使用换行符进行合并"""
        return "\n\n".join([document.page_content for document in documents])


    @property
    def collection(self) -> Collection:
        return self.client.collections.get(COLLECTION_NAME)
