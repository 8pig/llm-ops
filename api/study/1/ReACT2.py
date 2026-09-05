import os
from dashscope import MultiModalConversation

import dotenv
from langchain_classic.agents import AgentExecutor, create_react_agent, create_tool_calling_agent
from langchain_community.tools import GoogleSerperRun
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import render_text_description_and_args, Tool
from langchain_openai import ChatOpenAI
from pydantic.v1 import Field, BaseModel
from langchain_community.utilities import GoogleSerperAPIWrapper

dotenv.load_dotenv()


class GoogleSerperArgsSchema(BaseModel):
    query: str = Field(..., description="执行谷歌搜索的查询语句")


class DallEArgsSchema(BaseModel):
    query: str = Field(..., description="输入是生成图像的文本提示(prompt)")




def generate_image(prompt: str) -> str:
    """使用阿里云通义万相生成图片"""
    messages = [
        {
            "role": "user",
            "content": [
                {"text": prompt}
            ]
        }
    ]

    try:
        response = MultiModalConversation.call(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="qwen-image-2.0-pro",
            messages=messages,
            result_format='message',
            stream=False,
            watermark=False,
            prompt_extend=True,
            negative_prompt="低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，蜡像感，人脸无细节，过度光滑，画面具有 AI 感。构图混乱。文字模糊，扭曲。",
            size='2048*2048'
        )

        print("API 响应:", response)

        # ✅ 正确的解析方式 - 从 output.choices 中获取图片
        # {"status_code": 200, "request_id": "6ab051b0-6c8f-4675-974f-919143e91d98", "code": "", "message": "", "output": {"text": null, "finish_reason": null, "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": [{"image": "https://dashscope-7c2c.oss-accelerate.aliyuncs.com/7d/c3/20260326/e74037e8/2d748881-31a4-4e0a-b2c3-1508ee17a3f1.png?Expires=1775104234&OSSAccessKeyId=LTAI5tPxpiCM2hjmWrFXrym1&Signature=4t53r7bOV3%2Fg01L%2FUPvouMgqKeQ%3D"}]}}], "audio": null}, "usage": {"input_tokens": 0, "output_tokens": 0, "characters": 0, "height": 2048, "image_count": 1, "width": 2048}}
        if response.output and response.output.get('choices'):
            choices = response.output['choices']
            if len(choices) > 0:
                message = choices[0].get('message', {})
                content = message.get('content', [])

                if isinstance(content, list) and len(content) > 0:
                    # 查找包含 image 的内容
                    for item in content:
                        if isinstance(item, dict) and 'image' in item:
                            image_url = item['image']
                            return f"图片已生成成功！\n图片链接：{image_url}"

                    # 如果没有找到 image，返回文本内容
                    text_content = content[0].get('text', '')
                    if text_content:
                        return f"生成结果：{text_content}"

        # 备用方案：尝试从 output.text 获取
        if response.output and response.output.get('text'):
            return f"生成结果：{response.output['text']}"

        return "图片生成失败，无法解析响应数据"

    except Exception as e:
        print(f"异常详情：{str(e)}")
        return f"图片生成出错：{str(e)}"





google_serper = GoogleSerperRun(
    name="google_serper",
    description=(
        "根据传入的搜索内容，返回搜索结果"
        "谷歌搜索工具"
    ),
    args_schema=GoogleSerperArgsSchema,
    api_wrapper=GoogleSerperAPIWrapper(),
)

dalle = Tool(
    name="openai_dalle",
    description="根据传入的描述生成图片。当用户要求生成图像、创建图片、画图时使用此工具。输入应该是详细的图像描述。",
    func=generate_image,
    args_schema=DallEArgsSchema,
)
tools = [
    google_serper,
    dalle
]

prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer the following questions as best you can. You have access to the following tools:"),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

llm = ChatOpenAI(
    model="qwen3-max-2026-01-23",
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE_URL")
)
# ✅ 绑定工具到 LLM
agent = create_tool_calling_agent(
    llm=llm,
    tools=tools,
    prompt=prompt
)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

print(agent_executor.invoke({"input": "帮我照一张吉泽明步年轻的照片"}))





