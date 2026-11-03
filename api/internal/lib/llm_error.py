"""LLM 服务商异常识别与友好降级工具

将模型服务商（OpenAI 兼容 / DashScope 等）返回的配额不足、鉴权失败、
超时、限流等异常统一映射为面向用户的中文提示，避免直接以 500 / 中断的形式
暴露给前端。同时提供 SSE 流的保护包装器，把可识别的模型错误转成
`event: error` 事件正常结束流式响应。
"""
import json
import logging
from typing import Any, Generator, Optional, Union


def friendly_llm_error(exc: Exception) -> Optional[str]:
    """识别模型服务商异常并返回友好的中文提示，无法识别时返回 None"""
    if not isinstance(exc, Exception):
        return None

    name = exc.__class__.__name__.lower()
    text = str(exc).lower()
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)

    # 1.额度不足：403 AllocationQuota / FreeTierOnly / InsufficientBalance 等
    if (
        "quota" in text
        or "insufficient_balance" in text
        or "allocation" in text
        or "free tier" in text
        or "balance" in text
        or "额度" in text
    ):
        return (
            "模型调用额度不足（免费额度可能已用完）。请在模型服务商控制台充值，"
            "或关闭“仅使用免费额度”后重试。"
        )

    # 2.超时/连接异常
    if (
        isinstance(exc, TimeoutError)
        or "timeout" in name
        or "timed out" in text
        or "connection" in name
    ):
        return "模型服务响应超时或连接失败，请稍后重试。"

    # 3.鉴权失败
    if "authentication" in name or status == 401 or "401" in text:
        return "模型 API Key 无效或已失效，请检查模型配置。"

    # 4.限流
    if "ratelimit" in name or status == 429 or "429" in text:
        return "模型调用过于频繁，请稍后重试。"

    # 5.服务端 5xx
    if (
        "internal" in name
        or "server" in name
        or (isinstance(status, int) and status >= 500)
    ):
        return "模型服务暂时不可用，请稍后重试。"

    # 6.其它 403 拒绝
    if (
        "permission" in name
        or "forbidden" in name
        or status == 403
    ):
        return "模型服务拒绝了本次请求（403），请检查模型 API Key 与调用权限。"

    return None


def safe_sse_stream(response: Union[Any, Generator]) -> Union[Any, Generator]:
    """包装 SSE 生成器：可识别的模型异常转成 error 事件并正常结束，其余异常原样抛出"""
    if not isinstance(response, Generator):
        return response

    def _guard() -> Generator[str, None, None]:
        try:
            yield from response
        except Exception as e:  # noqa: BLE001 - 统一在流边界兜底
            message = friendly_llm_error(e)
            if message is None:
                raise
            logging.exception("模型服务调用异常，已降级为错误事件: %s", e)
            payload = {"event": "error", "message": message}
            yield f"event: error\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

    return _guard()
