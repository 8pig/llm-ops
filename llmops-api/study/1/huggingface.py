from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings()


query_vector = embeddings.embed_query("你好")