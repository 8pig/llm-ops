import os

import dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

dotenv.load_dotenv()

class QAExtra(BaseModel):
    question: str = Field(..., description="假设性的问题")
    answer: str = Field(..., description="假设性问题的答案")


llm = ChatOpenAI(
    model="qwen3-max-2026-01-23",
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE_URL"),
)

structured_llm = llm.with_structured_output(QAExtra)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个问答助手, 你从用户传递的query中提取假设性的问题+答案"),
    ("human", "{query}"),
])

chain = {"query": RunnablePassthrough()} | prompt | structured_llm

print(chain.invoke({"query": "我叫野猪佩奇, 我喜欢唱跳rap篮球"}))