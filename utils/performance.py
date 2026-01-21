#!/usr/bin/env python3
"""
性能监控工具 - 提供性能监控装饰器
"""

import time
import functools
from typing import Callable, Any
from utils.logger_utils import get_logger

logger = get_logger('performance')


def monitor_performance(func: Callable) -> Callable:
    """
    性能监控装饰器 - 监控函数执行时间

    Args:
        func: 要监控的函数

    Returns:
        包装后的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        func_name = func.__name__

        try:
            # 执行函数
            result = func(*args, **kwargs)

            # 计算耗时
            elapsed = time.time() - start_time

            # 记录性能日志
            if elapsed > 1.0:  # 超过1秒记录警告
                logger.warning(f"[性能] {func_name} 执行较慢: {elapsed:.2f}秒")
            elif elapsed > 5.0:  # 超过5秒记录错误
                logger.error(f"[性能] {func_name} 执行很慢: {elapsed:.2f}秒")
            else:
                logger.debug(f"[性能] {func_name} 执行时间: {elapsed:.2f}秒")

            return result

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"[性能] {func_name} 执行失败 (耗时{elapsed:.2f}秒): {str(e)}")
            raise

    return wrapper


def monitor_async_performance(func: Callable) -> Callable:
    """
    异步函数性能监控装饰器

    Args:
        func: 要监控的异步函数

    Returns:
        包装后的异步函数
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        func_name = func.__name__

        try:
            # 执行异步函数
            result = await func(*args, **kwargs)

            # 计算耗时
            elapsed = time.time() - start_time

            # 记录性能日志
            if elapsed > 1.0:
                logger.warning(f"[性能] {func_name} 执行较慢: {elapsed:.2f}秒")
            else:
                logger.debug(f"[性能] {func_name} 执行时间: {elapsed:.2f}秒")

            return result

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"[性能] {func_name} 执行失败 (耗时{elapsed:.2f}秒): {str(e)}")
            raise

    return wrapper


class PerformanceTimer:
    """性能计时器 - 用于代码块的性能监控"""

    def __init__(self, name: str, threshold: float = 1.0):
        """
        初始化计时器

        Args:
            name: 计时器名称
            threshold: 警告阈值（秒）
        """
        self.name = name
        self.threshold = threshold
        self.start_time = None

    def __enter__(self):
        """进入上下文"""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        if self.start_time is None:
            return

        elapsed = time.time() - self.start_time

        if elapsed > self.threshold:
            logger.warning(f"[性能] {self.name} 执行较慢: {elapsed:.2f}秒")
        else:
            logger.debug(f"[性能] {self.name} 执行时间: {elapsed:.2f}秒")

    def start(self):
        """启动计时器"""
        self.start_time = time.time()

    def stop(self) -> float:
        """
        停止计时器并返回耗时

        Returns:
            耗时（秒）
        """
        if self.start_time is None:
            return 0

        elapsed = time.time() - self.start_time
        self.start_time = None
        return elapsed


def log_execution_time(threshold: float = 1.0):
    """
    执行时间日志装饰器（可配置阈值）

    Args:
        threshold: 警告阈值（秒）

    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = func.__name__

            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time

                if elapsed > threshold:
                    logger.warning(f"[性能] {func_name} 执行较慢: {elapsed:.2f}秒")
                else:
                    logger.debug(f"[性能] {func_name} 执行时间: {elapsed:.2f}秒")

                return result

            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"[性能] {func_name} 失败 (耗时{elapsed:.2f}秒): {str(e)}")
                raise

        return wrapper
    return decorator
