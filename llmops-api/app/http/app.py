import dotenv
from pkg.sqlalchemy import SQLAlchemy
from injector import Injector
from config import Config
from internal.router import Router
from internal.server import Http
from internal.model.module import ExtensionModule
from flask_migrate import Migrate

dotenv.load_dotenv()

conf = Config()



injector = Injector([
    ExtensionModule
])


app = Http(
    __name__,
    conf=conf,
    db=injector.get(SQLAlchemy),
    migrate=injector.get(Migrate),
    router=injector.get(Router)
)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=3000, debug=True)