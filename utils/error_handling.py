#!/usr/bin/env python3
"""
错误处理工具 - 提供统一的错误处理机制
"""

import traceback
from typing import Callable, Any, Tuple, Optional
from flask import jsonify
from utils.logger_utils import get_logger

logger = get_logger('error_handling')


class APIError(Exception):
    """API错误基类"""

    def __init__(self, message: str, status_code: int = 500, details: Optional[dict] = None):
        """
        初始化API错误

        Args:
            message: 错误消息
            status_code: HTTP状态码
            details: 额外详情
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(APIError):
    """参数验证错误"""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, status_code=400, details=details)


class NotFoundError(APIError):
    """资源未找到错误"""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, status_code=404, details=details)


class ServiceUnavailableError(APIError):
    """服务不可用错误"""

    def __init__(self, message: str = "服务暂时不可用，请稍后重试", details: Optional[dict] = None):
        super().__init__(message, status_code=503, details=details)


def handle_api_error(error: Exception) -> Tuple[dict, int]:
    """
    处理API错误并生成响应

    Args:
        error: 异常对象

    Returns:
        (响应字典, 状态码)
    """
    if isinstance(error, APIError):
        logger.error(f"[API错误] {error.__class__.__name__}: {error.message}")
        response = {
            "success": False,
            "message": error.message,
            **error.details
        }
        return response, error.status_code
    else:
        # 未知错误
        logger.error(f"[未知错误] {str(error)}\n{traceback.format_exc()}")
        return {
            "success": False,
            "message": "服务器内部错误"
        }, 500


def safe_execute(
    func: Callable,
    error_message: str = "操作失败",
    default_return: Any = None,
    raise_on_error: bool = False
) -> Any:
    """
    安全执行函数，捕获异常

    Args:
        func: 要执行的函数
        error_message: 错误消息
        default_return: 默认返回值
        raise_on_error: 是否重新抛出异常

    Returns:
        函数执行结果或默认返回值
    """
    try:
        return func()
    except Exception as e:
        logger.error(f"{error_message}: {str(e)}")
        logger.debug(f"[错误详情] {traceback.format_exc()}")

        if raise_on_error:
            raise

        return default_return


def validate_required_fields(
    data: dict,
    required_fields: list,
    error_message: str = "缺少必填字段"
) -> Tuple[bool, str]:
    """
    验证必填字段

    Args:
        data: 数据字典
        required_fields: 必填字段列表
        error_message: 错误消息

    Returns:
        (is_valid, error_message)
    """
    if not data:
        return False, f"{error_message}: 请求数据为空"

    missing_fields = []
    for field in required_fields:
        if field not in data or not data.get(field):
            missing_fields.append(field)

    if missing_fields:
        return False, f"{error_message}: 缺少必填字段 {', '.join(missing_fields)}"

    return True, ""


def log_exception(
    func: Callable,
    exception: Exception,
    context: str = ""
):
    """
    记录异常详情

    Args:
        func: 发生异常的函数
        exception: 异常对象
        context: 额外上下文信息
    """
    func_name = func.__name__ if callable(func) else str(func)
    exception_type = exception.__class__.__name__
    exception_message = str(exception)

    logger.error(f"[异常] {func_name} - {exception_type}: {exception_message}")
    if context:
        logger.error(f"[上下文] {context}")

    # 记录详细的堆栈跟踪
    logger.debug(f"[堆栈跟踪]\n{traceback.format_exc()}")
