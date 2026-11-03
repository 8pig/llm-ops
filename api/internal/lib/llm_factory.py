"""LLM 客户端工厂

统一创建并复用 LangChain 聊天模型实例，解决两个问题：

1. 性能：原先每个请求都会重新构建 ``Chat``/``ChatOpenAI``，进而在 Windows
   上重建一次完整的 httpx 连接（含 SSLContext 构建，实测约 2.5s），
   主链路 + 会话摘要 + 会话命名共 3 次，单个请求白等 5~7s。
   这里用 ``lru_cache`` 按参数复用实例，httpx 连接池得以跨请求复用。

2. 稳定性：原先未设置 ``timeout``（httpx 默认无限等待）且 ``max_retries``
   取默认值 2，底层连接一旦挂住，请求会静默卡住直到对端超时。
   这里统一设置超时与重试次数，把"无限干等"变成可预期的失败。

注意：环境变量在**调用时**读取，而非模块导入时。因为 ``app/http/app.py``
中 ``dotenv.load_dotenv()`` 发生在业务模块 import 之后，模块级读 env 会拿到空值。
"""
import os
from functools import lru_cache
from typing import Optional, Tuple

from internal.core.language_model.entities.model_entity import ModelFeature
from internal.core.language_model.providers.openai.chat import Chat

# 单次读超时（秒）。流式场景下 httpx 按 chunk 间隔计时，不影响长文本输出，
# 只用于终止"连接已建立但迟迟没有数据"的悬挂状态。
DEFAULT_TIMEOUT = 60
# 失败重试次数。langchain-openai 默认 2，连接异常时会额外等待两个完整超时周期。
DEFAULT_MAX_RETRIES = 1


def _get_env_int(key: str, default: int) -> int:
    """读取整型环境变量，缺失或非法值时回退默认值"""
    try:
        return int(os.getenv(key) or default)
    except (TypeError, ValueError):
        return default


@lru_cache(maxsize=8)
def _build_chat(
    model: Optional[str],
    temperature: float,
    api_key: Optional[str],
    base_url: Optional[str],
    reasoning_effort: Optional[str],
    features: Tuple[ModelFeature, ...],
    timeout: int,
    max_retries: int,
) -> Chat:
    """按参数构建 Chat 实例，相同参数只构建一次

    缓存键包含全部构造参数（含从环境变量读取的模型名/地址），
    因此修改 .env 并重启后会自然生成新实例，不会读到过期配置。
    """
    # 不同 langchain-openai 版本对超时字段的命名不一致：
    # 旧版/新版为 request_timeout，部分版本用 timeout 作为别名。
    # 模型配置为 extra="ignore"，传错名字会被静默丢弃，故此处按实际字段名适配。
    chat_fields = Chat.model_fields
    timeout_kwargs = {}
    if "request_timeout" in chat_fields:
        timeout_kwargs["request_timeout"] = timeout
    elif "timeout" in chat_fields:
        timeout_kwargs["timeout"] = timeout

    return Chat(
        model=model,
        temperature=temperature,
        api_key=api_key,
        base_url=base_url,
        reasoning_effort=reasoning_effort,
        features=list(features),
        metadata={},
        max_retries=max_retries,
        **timeout_kwargs,
    )


def get_assistant_chat() -> Chat:
    """辅助Agent主链路使用的LLM客户端（工具调用 + 思维链 + 图片输入）"""
    return _build_chat(
        os.getenv("LLM_MODEL"),
        0.5,
        os.getenv("OPENAI_API_KEY"),
        os.getenv("OPENAI_API_BASE_URL"),
        os.getenv("REASONING_EFFORT"),
        (ModelFeature.TOOL_CALL, ModelFeature.AGENT_THOUGHT, ModelFeature.IMAGE_INPUT),
        _get_env_int("LLM_TIMEOUT", DEFAULT_TIMEOUT),
        _get_env_int("LLM_MAX_RETRIES", DEFAULT_MAX_RETRIES),
    )


def get_text_chat(temperature: float = 0.0) -> Chat:
    """纯文本场景使用的LLM客户端（会话摘要、会话命名、建议问题等）"""
    return _build_chat(
        os.getenv("LLM_MODEL"),
        temperature,
        os.getenv("OPENAI_API_KEY"),
        os.getenv("OPENAI_API_BASE_URL"),
        os.getenv("REASONING_EFFORT"),
        (),
        _get_env_int("LLM_TIMEOUT", DEFAULT_TIMEOUT),
        _get_env_int("LLM_MAX_RETRIES", DEFAULT_MAX_RETRIES),
    )
