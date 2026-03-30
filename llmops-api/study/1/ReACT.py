import os

import dotenv
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_community.tools import GoogleSerperRun
from langchain_community.tools.openai_dalle_image_generation import OpenAIDALLEImageGenerationTool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import render_text_description_and_args
from langchain_openai import ChatOpenAI
from pydantic.v1 import Field, BaseModel
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from langchain_community.utilities import GoogleSerperAPIWrapper
dotenv.load_dotenv()

class GoogleSerperArgsSchema(BaseModel):
    query: str = Field(..., description="执行谷歌搜索的查询语句")


class DallEArgsSchema(BaseModel):
    query: str = Field(..., description="输入是生成图像的文本提示(prompt)")

dalle = OpenAIDALLEImageGenerationTool(
    name="openao_dalle",
    description=(
        "根据传入的描述，生成图片"
        "Dalle图片生成工具"
    ),
    args_schema=DallEArgsSchema,
    api_wrapper=DallEAPIWrapper(model="qwen-image-2.0"),

)




google_serper = GoogleSerperRun(
    name="google_serper",
    description=(
        "根据传入的搜索内容，返回搜索结果"
        "谷歌搜索工具"
    ),
    args_schema=GoogleSerperArgsSchema,
    api_wrapper=GoogleSerperAPIWrapper(),
)


tools = [
    google_serper,
    dalle
]


prompt = ChatPromptTemplate.from_template(
    "Answer the following questions as best you can. You have access to the following tools:\n"
    "{tools} \n"
    
    "Use the following format:\n"
    
    "Question: the input question you must answer\n"
    "Thought: you should always think about what to do\n"
    "Action: the action to take, should be one of [{tool_names}]\n"
    "Action Input: the input to the action\n"
    "Observation: the result of the action"
    "... (this Thought/Action/Action Input/Observation can repeat N times)\n"
    "Thought: I now know the final answer\n"
    "Final Answer: the final answer to the original input question\n"
    
    "Begin!\n"
    
    "Question: {input}\n"
    "Thought:{agent_scratchpad}\n"
)

llm = ChatOpenAI(
    model="qwen3-max-2026-01-23",
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE_URL")
)

agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=prompt,
    tools_renderer=render_text_description_and_args
)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

print(agent_executor.invoke({"input": "帮我生成一张老爷爷爬山的图片, 要求是 亚洲脸"}))





