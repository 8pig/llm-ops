from langchain_community.tools.openai_dalle_image_generation import OpenAIDALLEImageGenerationTool
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from langchain_core.tools import BaseTool
from pydantic import Field, BaseModel


class Dall3EArgsSchema(BaseModel):
    query: str = Field(..., description="输入是生成图像的文本提示(prompt)")


def dalle3(**kwargs) -> BaseTool:
    return OpenAIDALLEImageGenerationTool(
        description=(
            "根据传入的描述，生成图片. Dalle3图片生成工具"
        ),
        args_schema=Dall3EArgsSchema,
        api_wrapper=DallEAPIWrapper(**kwargs),
    )
