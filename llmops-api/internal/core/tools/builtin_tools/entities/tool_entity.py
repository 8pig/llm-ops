from typing import Optional, Any

from pydantic import BaseModel, Field
from enum import Enum


class ToolParamType(str, Enum):
    """工具参数类型"""
    STRING = "string"
    NUMBER = "number" # int float
    BOOLEAN = "boolean"
    SELECT = "select"



class ToolParams(BaseModel):
    """工具参数类"""
    name: str  # 名字
    label: str #标签
    description: str
    type: ToolParamType # 参数类型
    required: bool = False
    default: Optional[Any] = None
    min: Optional[float] = None
    max: Optional[float] = None
    options: list[dict[str, Any]] = Field(default_factory=list)  #下拉菜单列表


class ToolEntity(BaseModel):
    """工具实体类  存储的信息是   工具名:yaml数据"""
    name: str
    label:  str
    description: str

    params: list[ToolParams] = Field(default_factory=list)  # 参数信息