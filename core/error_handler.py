#!/usr/bin/env python3
"""
统一错误处理模块

提供装饰器和工具函数，简化错误处理逻辑，
减少代码重复，提升错误处理的一致性。
"""

import functools
import logging
import traceback
from typing import Optional, Callable, Any, Type, Tuple
import time

logger = logging.getLogger(__name__)


def handle_errors(
    *,
    default_return: Any = None,
    log_level: int = logging.ERROR,
    raise_on: Optional[Tuple[Type[Exception], ...]] = None,
    silence: bool = False,
    max_retries: int = 0,
    retry_delay: float = 0.0,
    context: Optional[dict] = None
) -> Callable:
    """
    统一错误处理装饰器

    Args:
        default_return: 发生异常时的默认返回值
        log_level: 日志级别（logging.ERROR, logging.WARNING等）
        raise_on: 指定哪些异常需要重新抛出（元组形式）
        silence: 是否完全静默（不记录日志）
        max_retries: 最大重试次数（0表示不重试）
        retry_delay: 重试延迟（秒）
        context: 额外的上下文信息（会记录到日志中）

    Returns:
        装饰器函数

    Examples:
        >>> @handle_errors(default_return=[], raise_on=ValueError)
        >>> def fetch_data():
        ...     # 可能抛出异常的代码
        ...     return data

        >>> @handle_errors(max_retries=3, retry_delay=1.0)
        >>> def unstable_api_call():
        ...     # 不稳定的API调用
        ...     return response
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            # 尝试执行（包含重试逻辑）
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    # 检查是否需要重新抛出
                    if raise_on and isinstance(e, raise_on):
                        logger.error(f"❌ {func.__name__}() 抛出指定异常: {type(e).__name__}: {str(e)[:200]}")
                        raise

                    # 如果还有重试次数
                    if attempt < max_retries:
                        logger.warning(
                            f"⚠️ {func.__name__}() 第 {attempt + 1} 次尝试失败: {str(e)[:200]}，"
                            f"{retry_delay}秒后重试..."
                        )
                        time.sleep(retry_delay)
                        continue

                    # 最后一次尝试也失败了，记录错误
                    if not silence:
                        context_str = f"Context: {context}" if context else ""
                        logger.log(
                            log_level,
                            f"❌ {func.__name__}() 执行失败: {type(e).__name__}: {str(e)[:200]}\n{context_str}"
                        )
                        if logger.isEnabledFor(logging.DEBUG):
                            logger.debug(f"Stack trace: {traceback.format_exc()[-500:]}")

                    # 返回默认值
                    if default_return is not None:
                        if callable(default_return):
                            return default_return()
                        return default_return

                    # 如果没有默认值，返回None
                    return None

        return wrapper
    return decorator


def async_handle_errors(
    *,
    default_return: Any = None,
    log_level: int = logging.ERROR,
    raise_on: Optional[Tuple[Type[Exception], ...]] = None,
    silence: bool = False,
    context: Optional[dict] = None
) -> Callable:
    """
    异步函数的统一错误处理装饰器

    Args:
        default_return: 发生异常时的默认返回值
        log_level: 日志级别
        raise_on: 指定哪些异常需要重新抛出
        silence: 是否完全静默
        context: 额外的上下文信息

    Returns:
        异步装饰器函数

    Examples:
        >>> @async_handle_errors(default_return=[])
        >>> async def fetch_async_data():
        ...     # 可能抛出异常的异步代码
        ...     return data
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)

            except Exception as e:
                # 检查是否需要重新抛出
                if raise_on and isinstance(e, raise_on):
                    logger.error(f"❌ {func.__name__}() 抛出指定异常: {type(e).__name__}: {str(e)[:200]}")
                    raise

                # 记录错误
                if not silence:
                    context_str = f"Context: {context}" if context else ""
                    logger.log(
                        log_level,
                        f"❌ {func.__name__}() 执行失败: {type(e).__name__}: {str(e)[:200]}\n{context_str}"
                    )
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"Stack trace: {traceback.format_exc()[-500:]}")

                # 返回默认值
                if default_return is not None:
                    if callable(default_return):
                        return default_return()
                    return default_return

                return None

        return wrapper
    return decorator


def log_execution_time(log_level: int = logging.INFO, threshold: Optional[float] = None) -> Callable:
    """
    记录函数执行时间的装饰器

    Args:
        log_level: 日志级别
        threshold: 仅当执行时间超过此阈值（秒）时才记录

    Returns:
        装饰器函数

    Examples:
        >>> @log_execution_time(threshold=1.0)
        >>> def slow_function():
        ...     # 耗时操作
        ...     pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time
                if threshold is None or elapsed > threshold:
                    logger.log(
                        log_level,
                        f"⏱️ {func.__name__}() 执行时间: {elapsed:.2f}秒"
                    )
        return wrapper
    return decorator


def validate_args(**validators) -> Callable:
    """
    参数验证装饰器

    Args:
        validators: 参数名到验证函数的映射

    Returns:
        装饰器函数

    Examples:
        >>> @validate_args(query=lambda x: len(x) > 0, max_results=lambda x: x > 0)
        >>> def search(query: str, max_results: int):
        ...     # query非空，max_results为正数
        ...     pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 获取函数签名
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # 验证每个参数
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not validator(value):
                        raise ValueError(
                            f"参数验证失败: {param_name}={value} "
                            f"(验证函数: {validator.__name__ if hasattr(validator, '__name__') else validator})"
                        )

            return func(*args, **kwargs)
        return wrapper
    return decorator


# 便捷装饰器（预设配置）
def safe(default_return: Any = None) -> Callable:
    """安全执行装饰器：捕获所有异常，返回默认值"""
    return handle_errors(default_return=default_return, silence=True)


def retry(max_retries: int = 3, retry_delay: float = 1.0) -> Callable:
    """重试装饰器：失败时自动重试"""
    return handle_errors(max_retries=max_retries, retry_delay=retry_delay)


def timed(threshold: Optional[float] = None) -> Callable:
    """计时装饰器：记录函数执行时间"""
    return log_execution_time(threshold=threshold)


if __name__ == "__main__":
    print("=" * 60)
    print("错误处理模块测试")
    print("=" * 60)

    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # 测试1: 基本错误处理
    print("\n测试1 - 基本错误处理:")
    @handle_errors(default_return=[])
    def test_function():
        raise ValueError("测试异常")

    result = test_function()
    print(f"  结果: {result} (默认返回值)")

    # 测试2: 重试机制
    print("\n测试2 - 重试机制:")
    attempt_count = [0]

    @handle_errors(max_retries=3, retry_delay=0.1, default_return="success")
    def test_retry():
        attempt_count[0] += 1
        if attempt_count[0] < 3:
            raise ValueError("还没准备好")
        return "success"

    result = test_retry()
    print(f"  结果: {result} (尝试了 {attempt_count[0]} 次)")

    # 测试3: 执行时间记录
    print("\n测试3 - 执行时间记录:")
    @log_execution_time(threshold=0.001)
    def test_slow_function():
        time.sleep(0.01)
        return "done"

    result = test_slow_function()

    # 测试4: 参数验证
    print("\n测试4 - 参数验证:")
    try:
        @validate_args(query=lambda x: len(x) > 0, count=lambda x: x > 0)
        def test_validation(query: str, count: int):
            return f"查询: {query}, 数量: {count}"

        result = test_validation("", 10)  # 应该抛出异常
    except ValueError as e:
        print(f"  ✅ 参数验证正常工作: {e}")

    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)
