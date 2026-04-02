

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from internal.lib.helper import add_attribute


class DDGoInput(BaseModel):
    query: str = Field(description="执行DuckDuckGo搜索的查询语句")


@add_attribute("args_schema", DDGoInput)
def duckduckgo_search(**kwargs) -> BaseTool:
    """返回一个langchain的工具，该工具用于调用DuckDuckGo搜索API"""
    return DuckDuckGoSearchRun(
        name="duckduckgo_search",
        description=
            "一个注重隐私的搜索工具, 工具的输入是一个查询语句，返回搜索结果",
        args_schema=DDGoInput,
    )