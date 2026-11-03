"""gunicorn 配置：把应用预热推迟到 worker fork 之后

## 背景

``docker/entrypoint.sh`` 启动 gunicorn 时带了 ``--preload``：主进程先 import
``app.http.app``，再 fork 出 N 个 worker。而 ``app/http/app.py`` 里的预热是
import 阶段起一个后台守护线程。

这两件事放在一起有两个问题：

1. **线程不会被 fork 继承**。worker 里根本没有预热线程，等于预热白做，
   每个 worker 的第一个请求仍要各自付出初始化成本。
2. **更危险的是锁**。fork 只会复制调用线程，其它线程持有的锁在子进程中依然
   处于"已锁定"状态且永远不会有线程来释放。预热线程当时若正持有
   ``ConcurrentTimedRotatingFileHandler`` 的写锁、httpx 连接池锁或 FAISS
   内部锁，worker 起来后第一次写日志/发请求就会永久卡死。

## 做法

``on_starting`` 打一个环境变量标记，主进程 import 应用时据此跳过预热；
``post_fork`` 在每个 worker 内各自启动预热。

gunicorn 会自动加载当前工作目录下的 ``gunicorn.conf.py``（WORKDIR 为
``/app/api``），因此 entrypoint 无需额外传 ``-c``。
"""
import os


def on_starting(server):  # noqa: ARG001 - gunicorn 钩子签名固定
    """主进程启动时打标记，让应用 import 阶段跳过预热

    on_starting 在 preload 之前执行，因此标记能被应用代码读到。
    """
    os.environ["WARMUP_DEFERRED"] = "1"


def post_fork(server, worker):  # noqa: ARG001 - gunicorn 钩子签名固定
    """worker fork 完成后，在各自进程内启动预热

    此时应用模块已由 preload 加载好（未开 preload 时由 load_wsgi 加载），
    直接取用即可。任何异常都只记录，不能让 worker 起不来。
    """
    try:
        from app.http.app import app, injector
        from internal.lib.warmup import start_warmup

        start_warmup(app, injector)
    except Exception as exc:  # pragma: no cover
        import logging

        logging.getLogger(__name__).warning("[warmup] worker %s 预热启动失败: %s", worker.pid, exc)
