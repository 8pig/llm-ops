from pydantic import BaseModel, Field


class ToolEntity(BaseModel):

    id: str = Field(default="", description="工具id")
    name: str = Field(default="", description="工具名称")
    url: str = Field(default="", description="api发起请求的url地址")
    method: str = Field(default="get", description="请求方式 get/post")
    description: str = Field(default="", description="工具描述")
    headers: list[dict] = Field(default_factory=list, description="api请求头")
    parameters: list[dict] = Field(default_factory=list, description="api请求参数")