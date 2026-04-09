from pkg.sqlalchemy import SQLAlchemy
from injector import Injector
from config import Config
from internal.router import Router
from internal.server import Http
from internal.model.module import ExtensionModule
from flask_migrate import Migrate
import dotenv
import logging
import sys
dotenv.load_dotenv()

conf = Config()



injector = Injector([
    ExtensionModule
])


def setup_flask_logging(app):
    """配置 Flask 应用的日志系统"""
    if app.debug:
        # 设置日志级别为 DEBUG
        app.logger.setLevel(logging.DEBUG)

        # 确保有控制台处理器
        if not app.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.DEBUG)

            app.logger.addHandler(handler)

        app.logger.info("🚀 日志系统已初始化 (DEBUG 模式)")


app = Http(
    __name__,
    conf=conf,
    db=injector.get(SQLAlchemy),
    migrate=injector.get(Migrate),
    router=injector.get(Router)
)
setup_flask_logging(app)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)