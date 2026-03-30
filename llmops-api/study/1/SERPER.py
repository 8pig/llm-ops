import os
import pprint

import dotenv
from langchain_community.tools import GoogleSerperRun
from pydantic.v1 import Field, BaseModel


from langchain_community.utilities import GoogleSerperAPIWrapper


class GoogleSerperArgsSchema(BaseModel):
    query: str = Field(..., description="执行谷歌搜索的查询语句")


dotenv.load_dotenv()

google_serper = GoogleSerperRun(
    name="google_serper",
    description=(
        "根据传入的搜索内容，返回搜索结果"
        "谷歌搜索工具"
    ),
    args_schema=GoogleSerperArgsSchema,
    api_wrapper=GoogleSerperAPIWrapper(),
)

print(google_serper.invoke("美福特号航母被全员隔离审查，"
                           "美军向福特号航母派出8个调查员, "
                           "调查员的结局会是什么?"))
