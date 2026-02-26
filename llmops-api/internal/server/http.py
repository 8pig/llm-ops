
from flask import Flask
from internal.router import Router

class Http(Flask):

    def __init__(self, *args,router: Router, **kwargs):
        super(Http, self).__init__(*args, **kwargs)

        # 注册应用路由
        router.register_router(self)



