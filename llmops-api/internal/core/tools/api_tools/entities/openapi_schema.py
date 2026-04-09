from pydantic import BaseModel, Field, field_validator


class OpenAPISchema(BaseModel):
    """ openapi 规范 """

    description: str = Field(default="", description="工具的描述", validate_default= True)
    server: str = Field(default="", description="地址", validate_default= True)
    paths: dict[str,dict]  = Field(default_factory=dict, description="参数字典", validate_default= True)

    @field_validator("server", mode="before")
    def validate_server(cls, v):
        """ 验证server """
        if not v.startswith("http://") and not v.startswith("https://"):
            raise ValueError("server must start with http:// or https://")
        return v