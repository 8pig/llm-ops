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


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)