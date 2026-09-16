
from typing import Any

from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessageChunk
from langchain_core.outputs import ChatGenerationChunk, ChatResult

# 推理内容在additional_kwargs中的键名，与OpenAI风格接口(DeepSeek/MiMo等)保持一致
REASONING_CONTENT_KEY = "reasoning_content"


class ReasoningMixin:
    """思维链(reasoning_content)提取增强混入类

    langchain_openai默认只提取标准字段，非标准字段reasoning_content会被直接丢弃，
    该混入类通过覆写响应转换方法将其保留到additional_kwargs中，便于上层获取模型推理过程。
    对于底层SDK已支持提取reasoning_content的provider(tongyi/ollama等)，无需使用该混入类。
    """

    def _convert_chunk_to_generation_chunk(
        self,
        chunk: dict,
        default_chunk_class: type,
        base_generation_info: dict | None,
    ) -> ChatGenerationChunk | None:
        """覆写流式响应转换，额外提取reasoning_content到additional_kwargs"""
        # 1.调用父类完成标准字段(content/tool_calls等)的转换
        generation_chunk = super()._convert_chunk_to_generation_chunk(
            chunk, default_chunk_class, base_generation_info
        )

        # 2.父类未生成chunk时直接返回
        if generation_chunk is None:
            return generation_chunk

        # 3.从原始chunk中提取推理内容
        choices = chunk.get("choices", []) or chunk.get("chunk", {}).get("choices", [])
        if not choices:
            return generation_chunk

        delta = choices[0].get("delta") or {}
        reasoning_content = delta.get(REASONING_CONTENT_KEY)
        if not reasoning_content:
            return generation_chunk

        # 4.将推理内容写入additional_kwargs，交由langchain完成流式累加
        message_chunk = generation_chunk.message
        if isinstance(message_chunk, BaseMessageChunk):
            message_chunk.additional_kwargs[REASONING_CONTENT_KEY] = reasoning_content

        return generation_chunk

    def _create_chat_result(
        self,
        response: dict | Any,
        generation_info: dict | None = None,
    ) -> ChatResult:
        """覆写非流式响应转换，额外提取reasoning_content到additional_kwargs"""
        # 1.调用父类完成标准字段的转换
        chat_result = super()._create_chat_result(response, generation_info)

        # 2.读取原始响应中的推理内容
        response_dict = (
            response
            if isinstance(response, dict)
            else response.model_dump(exclude={"choices": {"__all__": {"message": {"parsed"}}}})
        )

        for generation, raw_choice in zip(chat_result.generations, response_dict.get("choices") or []):
            message = generation.message
            if not isinstance(message, AIMessage):
                continue

            reasoning_content = (raw_choice.get("message") or {}).get(REASONING_CONTENT_KEY)
            if reasoning_content:
                message.additional_kwargs[REASONING_CONTENT_KEY] = reasoning_content

        return chat_result

    @classmethod
    def _extract_reasoning_content(cls, message: AIMessage | AIMessageChunk) -> str:
        """从消息的additional_kwargs中提取推理内容，供上层便捷调用"""
        reasoning_content = (getattr(message, "additional_kwargs", None) or {}).get(REASONING_CONTENT_KEY, "")
        return reasoning_content if isinstance(reasoning_content, str) else ""
