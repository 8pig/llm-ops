from enum import Enum


class HttpCode(str, Enum):
    """http状态码"""
    SUCCESS = "success"
    FAIL = "fail"
    NOT_FOUND = "not_found"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    VALIDATE_ERROR = "validate_error"
    SERVER_ERROR = "server_error"