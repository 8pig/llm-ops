import warnings
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
    migrate=injector.get(Migrate),
    router=injector.get(Router)
)

celery = app.extensions["celery"]


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)