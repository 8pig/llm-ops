from dataclasses import field, dataclass
from typing import Any
from flask import jsonify

from .http_code import HttpCode

@dataclass
class Response:
    """基础 http 响应格式"""
    code: HttpCode = HttpCode.SUCCESS
    message: str = ""
    data: Any = field(default_factory=dict)




def json(data: Response = None):
    return jsonify(data), 200

def success_json(data: Any = None):
    """成功响应"""
    return json(Response(code=HttpCode.SUCCESS, data=data, message=""))


def fail_json(data: Any = None):
    """失败响应"""
    return json(Response(code=HttpCode.FAIL, data=data, message=""))

def validate_error_json(errors: dict = None):
    """参数验证错误"""
    first_key = next(iter(errors))
    if first_key is not None:
        msg = errors.get(first_key)[0]
    else:
        msg = ""
    return json(Response(code=HttpCode.VALIDATE_ERROR, message=msg, data=errors))

def message(code: HttpCode = None, msg: str = ""):
    return json(Response(code=code, message=msg, data={}))

def success_message( msg: str = ""):
    """success"""
    return message(code=HttpCode.SUCCESS, msg=msg)


def fail_message( msg: str = ""):
    """fail"""
    return message(code=HttpCode.FAIL, msg=msg)



def not_found_message(msg: str = ""):
    """未找到消息响应"""
    return message(code=HttpCode.NOT_FOUND, msg=msg)


def unauthorized_message(msg: str = ""):
    """未授权"""
    return message(code=HttpCode.UNAUTHORIZED, msg=msg)


def forbidden_message(msg: str = ""):
    """无权限"""
    return message(code=HttpCode.FORBIDDEN, msg=msg)