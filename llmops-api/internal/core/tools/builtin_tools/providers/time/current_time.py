import datetime
from typing import Any

from langchain_core.tools import BaseTool


class CurrentTimeTool(BaseTool):
    """获取当前时间的工具"""
    name: str = "current_time"
    description: str = "获取当前时间"


    def _run(self, *args: Any, **kwargs: Any) -> Any:

        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")



def current_time(**kwargs: Any) -> BaseTool:
    """返回获取当前时间的langchain的工具"""
    return  CurrentTimeTool()