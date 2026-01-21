#!/usr/bin/env python3
"""
Request Context - 请求上下文管理
提供请求ID的上下文变量和访问函数，避免循环导入
"""

import contextvars

# Request ID 上下文变量（用于关联日志）
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar('request_id', default='')

def get_request_id() -> str:
    """获取当前请求的 request_id"""
    return request_id_var.get('')

def set_request_id(request_id: str):
    """设置当前请求的 request_id"""
    request_id_var.set(request_id)
