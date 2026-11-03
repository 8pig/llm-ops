# [必须最先执行] httpx 每构造一个 transport 都会走 ssl.create_default_context(cafile=certifi)
# Windows 上单次约 1.26s，启动期共触发 81 次(约 155s)，是 import 本模块耗时的主因。
# 此处提前把 certifi CA 束重定向到系统证书存储(单次 0.02s)。
# 必须在所有会构造 httpx 客户端的 import 之前，否则补丁来不及生效。
from internal.lib.ssl_patch import install as _install_ssl_patch

_install_ssl_patch()

import warnings
import os
#
# if os.environ.get("FLASK_DEBUG") == "0" or os.environ.get("FLASK_ENV") == "production":
#     from gevent import monkey
#
#     monkey.patch_all()
#
#     import grpc.experimental.gevent
#     grpc.experimental.gevent.init_gevent()

from flask_login import LoginManager

from internal.middleware import Middleware
from flask_weaviate import FlaskWeaviate
# 忽略第三方库的警告
warnings.filterwarnings("ignore", category=SyntaxWarning, module="jieba")
warnings.filterwarnings("ignore", category=UserWarning, module="jieba")
warnings.filterwarnings("ignore", category=ResourceWarning)



from config import Config
from internal.router import Router
from internal.server import Http
from flask_migrate import Migrate
from pkg.db import SQLAlchemy
from internal.model.module import injector
import dotenv
dotenv.load_dotenv()

conf = Config()


app = Http(
    __name__,
    conf=conf,
    db=injector.get(SQLAlchemy),
    weaviate=injector.get(FlaskWeaviate),
    migrate=injector.get(Migrate),
    login_manager=injector.get(LoginManager),
    middleware=injector.get(Middleware),
    router=injector.get(Router)
)
celery = app.extensions["celery"]

# 应用预热：首次对话请求需要一次性付出LLM客户端构建、FAISS索引加载、langgraph图编译等
# 初始化成本(实测20秒级)，这里在启动后由后台守护线程提前完成，避免"第一次聊天要等半天"。
#
# 注意：不要用 FLASK_DEBUG 判断是否 reloader 父进程。本项目启动命令是
# `uv run python app/http/app.py`(debug=False，不启用热重载)，而 .env 里写着
# FLASK_DEBUG=1，按环境变量判断会误判为"父进程"从而整个跳过预热。
# 这里只在显式设置 WARMUP_DISABLED=1 时才跳过；若用 flask CLI 执行 db migrate 等
# 一次性命令，预热线程会随之启动并在进程退出时被销毁，属于可接受的少量浪费。
#
# 生产环境用 gunicorn --preload 启动时，主进程先 import 本模块再 fork worker。
# 此时**不能**在这里起预热线程：线程不被 fork 继承，且 fork 瞬间它持有的锁会在
# 子进程中永久锁死，导致 worker 首个请求卡住。这种情况由 gunicorn.conf.py 的
# post_fork 钩子在每个 worker 内各自预热（on_starting 会设置 WARMUP_DEFERRED=1）。
if os.getenv("WARMUP_DISABLED") != "1" and os.getenv("WARMUP_DEFERRED") != "1":
    from internal.lib.warmup import start_warmup
    start_warmup(app, injector)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)