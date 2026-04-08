from pydantic import BaseModel, field_validator

from internal.exception import FailException


class CategoryEntity(BaseModel):
    """分类实体"""
    category: str
    name: str
    icon: str

    @field_validator("icon")
    def check_icon_extension(cls, v):
        """校验icon 拓展名 是否为svg"""
        if not v.endswith(".svg"):
            raise FailException("icon 拓展名必须是 svg")

        return  v