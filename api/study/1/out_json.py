import os
import json

import dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
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

# 创建 JSON 输出解析器
parser = JsonOutputParser(pydantic_object=QAExtra)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个问答助手, 你从用户传递的query中提取假设性的问题+答案\n{format_instructions}"),
    ("human", "{query}"),
]).partial(format_instructions=parser.get_format_instructions())

# type: ignore 抑制类型检查警告
chain = {"query": RunnablePassthrough()} | prompt | llm | parser  # type: ignore

result = chain.invoke({"query": "我叫野猪佩奇, 我喜欢唱跳rap篮球"})

# result 已经是字典类型
print(json.dumps(result, indent=2, ensure_ascii=False))
