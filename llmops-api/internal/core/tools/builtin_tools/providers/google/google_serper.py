from langchain_community.tools import GoogleSerperRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.tools import BaseTool
from pydantic.v1 import Field, BaseModel


class GoogleSerperArgsSchema(BaseModel):
    query: str = Field(description="执行谷歌搜索的查询语句")

def google_serper(**kwargs) -> BaseTool:
    """"""
    return GoogleSerperRun(
        name="google_serper",
        description=(
            "根据传入的搜索内容，返回搜索结果"
            "谷歌搜索工具"
        ),
        args_schema=GoogleSerperArgsSchema,
        api_wrapper=GoogleSerperAPIWrapper(),
    )