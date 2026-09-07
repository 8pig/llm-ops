
from typing import Any, Type

from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from internal.lib.helper import add_attribute


class EsignServiceArgsSchema(BaseModel):
    """e签宝电子签章参数描述"""
    action: str = Field(description="操作类型：创建签署、查询状态、下载合同等")
    contract_id: str = Field(default="", description="合同ID，查询或下载时必填")


class EsignServiceTool(BaseTool):
    """e签宝电子签章服务工具"""
    name: str = "esign_service"
    description: str = "电子签章服务，支持合同签署、印章管理、签署流程管理等电子签章相关功能"
    args_schema: Type[BaseModel] = EsignServiceArgsSchema

    def _run(self, *args: Any, **kwargs: Any) -> str:
        """执行电子签章操作"""
        action = kwargs.get("action", "")
        contract_id = kwargs.get("contract_id", "")
        return f"e签宝服务结果（mock）：操作「{action}」，合同ID「{contract_id}」的功能待接入实际API"


@add_attribute("args_schema", EsignServiceArgsSchema)
def esign_service(**kwargs) -> BaseTool:
    """获取e签宝电子签章工具"""
    return EsignServiceTool()
