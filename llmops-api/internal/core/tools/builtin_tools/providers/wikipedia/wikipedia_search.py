from langchain_community.tools import WikipediaQueryRun
from langchain_community.tools.wikipedia.tool import WikipediaQueryInput
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import BaseTool

from internal.lib.helper import add_attribute


@add_attribute("args_schema", WikipediaQueryInput)
def wikipedia_search(**kwargs) -> BaseTool:
    """
    根据传入的查询条件，返回wikipedia的搜索结果
    """
    wikipedia_tool = WikipediaQueryRun(
        api_wrapper=WikipediaAPIWrapper()
    )
    return wikipedia_tool