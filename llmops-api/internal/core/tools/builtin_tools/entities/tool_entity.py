from pydantic import BaseModel


class ToolEntity(BaseModel):
    """工具实体类  存储的信息是   工具名:yaml数据"""
    name: str
    label:  str
    description: str

    params: list = [] # 参数信息