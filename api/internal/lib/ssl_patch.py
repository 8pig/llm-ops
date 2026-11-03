"""SSL 默认上下文构建加速补丁

## 问题

Windows 上 ``ssl.create_default_context(cafile=certifi.where())`` 单次耗时实测
**1.264s**，而无参的 ``ssl.create_default_context()``（走 Windows 证书存储）仅
**0.019s**，相差 66 倍。原因是 certifi 的 cacert.pem 有 266KB、140+ 张证书，
CPython 在 Windows 上逐张解析 PEM 并做 X509 校验的开销极高。

httpx 0.28.1 的 ``_config.create_ssl_context`` 在 ``verify=True`` 时固定走：

    ctx = ssl.create_default_context(cafile=certifi.where())

而每个 ``httpx.HTTPTransport`` / ``AsyncHTTPTransport`` 构造时都会调一次。
本项目启动阶段实测创建了 **81 次** transport（42 次同步 + 39 次异步），
累计约 **155s**，这才是 "import app.http.app 要 136 秒" 的真正原因。

## 方案

在进程级包装 ``ssl.create_default_context``：仅当传入的 ``cafile`` 恰好是
certifi 自带的 CA 束时，把 ``cafile`` 置空，改为加载 Windows 系统证书存储。

系统存储里本就包含 Mozilla 根证书（以及企业内网私有根证书），
对公网与内网服务的校验结果与 certifi 一致，而加载速度快两个数量级。

## 为什么不缓存 SSLContext

缓存会让多个 client 共享同一个 ctx 对象，任一调用方修改 ``verify_mode`` /
``check_hostname`` 就会污染其他调用方，属于隐蔽的并发缺陷。
本补丁每次仍返回**全新**的 ctx，只更换证书来源，没有共享风险。

## 安全兜底

``install()`` 会先构建一次系统证书上下文并检查证书数量，
若系统存储不可用（容器、精简系统等）则自动放弃补丁，回退 certifi，
不会出现"打了补丁反而所有 HTTPS 请求校验证书失败"的情况。

设置环境变量 ``SSL_PATCH_DISABLED=1`` 可完全跳过本补丁。
"""
import logging
import os
import ssl
from os.path import abspath, normcase

logger = logging.getLogger(__name__)

# 原始实现，用于回滚与兜底
_original_create_default_context = ssl.create_default_context

# certifi CA 束的规范化绝对路径，未安装 certifi 时为 None
_certifi_path: str | None = None
_installed = False

# 统计信息，便于验证补丁是否生效
_stats = {"total": 0, "redirected": 0}

# 系统证书存储至少要有的证书数量，低于该值视为不可用
_MIN_SYSTEM_CA_COUNT = 10


def _resolve_certifi_path() -> str | None:
    """获取 certifi 自带 CA 束的规范化路径"""
    try:
        import certifi
    except ImportError:  # pragma: no cover - 正常环境必有 certifi
        return None
    try:
        return normcase(abspath(certifi.where()))
    except Exception:  # pragma: no cover
        return None


def _system_store_usable() -> bool:
    """探测系统证书存储是否可用

    用 ``cert_store_stats()`` 统计已加载的证书数量，比 ``get_ca_certs()`` 轻量得多。
    """
    try:
        ctx = _original_create_default_context()
        return ctx.cert_store_stats().get("x509", 0) >= _MIN_SYSTEM_CA_COUNT
    except Exception as exc:  # pragma: no cover
        logger.warning("[ssl_patch] 系统证书存储探测失败: %s", exc)
        return False


def _patched_create_default_context(
    purpose=ssl.Purpose.SERVER_AUTH,
    *,
    cafile=None,
    capath=None,
    cadata=None,
):
    """替换版 create_default_context

    仅当 ``cafile`` 指向 certifi 默认 CA 束时改走系统证书存储，
    其他调用（自定义证书、capath、cadata）原样透传，行为不变。
    """
    _stats["total"] += 1
    if cafile is not None and _certifi_path is not None:
        try:
            if normcase(abspath(str(cafile))) == _certifi_path:
                cafile = None
                _stats["redirected"] += 1
                # 首次命中时提示一次，之后静默，避免刷日志
                if _stats["redirected"] == 1:
                    logger.info(
                        "[ssl_patch] certifi CA 束已重定向至系统证书存储 (单次 1.26s -> 0.02s)"
                    )
        except (OSError, ValueError):  # pragma: no cover - 非法路径原样透传
            pass
    return _original_create_default_context(
        purpose, cafile=cafile, capath=capath, cadata=cadata
    )


def install() -> bool:
    """安装补丁，返回是否实际生效

    必须在任何 httpx/openai 客户端构造之前调用。重复调用无副作用。
    """
    global _certifi_path, _installed

    if _installed:
        return True

    if os.getenv("SSL_PATCH_DISABLED") == "1":
        logger.info("[ssl_patch] 已通过 SSL_PATCH_DISABLED=1 关闭")
        return False

    _certifi_path = _resolve_certifi_path()
    if _certifi_path is None:
        logger.info("[ssl_patch] 未找到 certifi CA 束，跳过")
        return False

    if not _system_store_usable():
        logger.warning("[ssl_patch] 系统证书存储不可用，保留 certifi（启动会较慢）")
        return False

    ssl.create_default_context = _patched_create_default_context
    _installed = True
    logger.info("[ssl_patch] 已安装，httpx 将复用系统证书存储")
    return True


def uninstall() -> None:
    """还原原始实现，仅用于测试"""
    global _installed
    ssl.create_default_context = _original_create_default_context
    _installed = False


def get_stats() -> dict:
    """返回调用统计：total 为总调用次数，redirected 为被重定向次数"""
    return dict(_stats)
