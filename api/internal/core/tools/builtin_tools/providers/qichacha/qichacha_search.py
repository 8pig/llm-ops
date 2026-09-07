
from typing import Any, Type

from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from internal.lib.helper import add_attribute


class QichachaSearchArgsSchema(BaseModel):
    """企查查企业查询参数描述"""
    keyword: str = Field(description="企业名称、法人姓名或统一社会信用代码")


class QichachaSearchTool(BaseTool):
    """企查查企业信息查询工具"""
    name: str = "qichacha_search"
    description: str = "企业信息查询工具，可查询工商注册、股东信息、法人信息、经营范围等企业公开信息"
    args_schema: Type[BaseModel] = QichachaSearchArgsSchema

    def _run(self, *args: Any, **kwargs: Any) -> str:
        """查询企业信息"""
        keyword = kwargs.get("keyword", "")
        return f"企查查查询结果（mock）：关键词「{keyword}」的查询功能待接入实际API"


@add_attribute("args_schema", QichachaSearchArgsSchema)
def qichacha_search(**kwargs) -> BaseTool:
    """获取企查查企业查询工具"""
    return QichachaSearchTool()
