from flask import Flask

from internal.server import Http
from injector import Injector
from internal.router import Router

import dotenv
dotenv.load_dotenv()

injector = Injector()


app = Http(__name__, router=injector.get(Router))


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=3000, debug=True)