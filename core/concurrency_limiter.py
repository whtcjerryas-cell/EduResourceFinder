#!/usr/bin/env python3
"""
并发限制器模块
用于控制系统并发请求，防止资源耗尽
"""

import time
import threading
from typing import Optional, Callable, Any
from queue import Queue, Empty, Full
from datetime import datetime, timedelta
from functools import wraps
from utils.logger_utils import get_logger

logger = get_logger('concurrency_limiter')


class ConcurrencyLimiter:
    """
    并发限制器

    功能:
    1. 限制最大并发数
    2. 请求队列管理
    3. 超时处理
    4. 统计信息
    """

    def __init__(self, max_concurrent: int = 2, queue_size: int = 50, timeout: float = 120.0):
        """
        初始化并发限制器

        Args:
            max_concurrent: 最大并发数
            queue_size: 队列大小
            timeout: 请求超时时间（秒）
        """
        self.max_concurrent = max_concurrent
        self.queue_size = queue_size
        self.timeout = timeout

        # 信号量（控制并发数）
        self.semaphore = threading.Semaphore(max_concurrent)

        # 当前活跃请求
        self.active_requests: set = set()
        self.active_lock = threading.Lock()

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "completed_requests": 0,
            "rejected_requests": 0,
            "timeout_requests": 0,
            "start_time": datetime.now().isoformat()
        }

        # 峰值并发数
        self.peak_concurrent = 0

        logger.info(f"✅ 并发限制器初始化完成: max_concurrent={max_concurrent}, queue_size={queue_size}, timeout={timeout}s")

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        获取执行许可

        Args:
            timeout: 超时时间（秒），如果为None则使用默认超时

        Returns:
            是否成功获取许可
        """
        timeout = timeout or self.timeout
        self.stats["total_requests"] += 1

        # 尝试获取信号量
        acquired = self.semaphore.acquire(timeout=timeout)

        if acquired:
            # 记录活跃请求
            with self.active_lock:
                request_id = threading.get_ident()
                self.active_requests.add(request_id)
                current_concurrent = len(self.active_requests)

                # 更新峰值
                if current_concurrent > self.peak_concurrent:
                    self.peak_concurrent = current_concurrent

            logger.debug(f"获取许可成功: 当前并发={current_concurrent}/{self.max_concurrent}")
            return True
        else:
            # 超时
            self.stats["timeout_requests"] += 1
            logger.warning(f"获取许可超时: 超时时间={timeout}s")
            return False

    def release(self):
        """释放执行许可"""
        with self.active_lock:
            request_id = threading.get_ident()
            if request_id in self.active_requests:
                self.active_requests.remove(request_id)
                self.stats["completed_requests"] += 1
                # 只有在成功获取许可的情况下才释放semaphore
                self.semaphore.release()
                logger.debug(f"释放许可: 当前并发={len(self.active_requests)}/{self.max_concurrent}")
            else:
                # 如果request_id不在active_requests中，说明没有成功获取许可，不应该释放semaphore
                logger.warning(f"尝试释放未获取的许可: request_id={request_id}, 当前活跃请求={list(self.active_requests)}")

    def get_stats(self) -> dict:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        with self.active_lock:
            current_concurrent = len(self.active_requests)

        return {
            "max_concurrent": self.max_concurrent,
            "current_concurrent": current_concurrent,
            "peak_concurrent": self.peak_concurrent,
            "total_requests": self.stats["total_requests"],
            "completed_requests": self.stats["completed_requests"],
            "rejected_requests": self.stats["rejected_requests"],
            "timeout_requests": self.stats["timeout_requests"],
            "success_rate": (
                self.stats["completed_requests"] / max(1, self.stats["total_requests"])
            ),
            "start_time": self.stats["start_time"]
        }

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_requests": 0,
            "completed_requests": 0,
            "rejected_requests": 0,
            "timeout_requests": 0,
            "start_time": datetime.now().isoformat()
        }
        self.peak_concurrent = 0
        logger.info("统计信息已重置")

    def __enter__(self):
        """上下文管理器入口"""
        if not self.acquire():
            raise TimeoutError("无法获取执行许可（超时）")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.release()


# 全局单例
_global_limiter: Optional[ConcurrencyLimiter] = None


def get_concurrency_limiter() -> ConcurrencyLimiter:
    """
    获取全局并发限制器实例

    Returns:
        ConcurrencyLimiter实例
    """
    global _global_limiter
    if _global_limiter is None:
        # 从环境变量读取配置
        import os
        max_concurrent = int(os.getenv("MAX_CONCURRENT_SEARCHES", "2"))  # 降低默认并发数，减少内存压力
        queue_size = int(os.getenv("SEARCH_QUEUE_SIZE", "50"))
        timeout = float(os.getenv("SEARCH_TIMEOUT", "120"))

        _global_limiter = ConcurrencyLimiter(
            max_concurrent=max_concurrent,
            queue_size=queue_size,
            timeout=timeout
        )
    return _global_limiter


def limit_concurrency(limiter: Optional[ConcurrencyLimiter] = None):
    """
    并发限制装饰器

    Args:
        limiter: 并发限制器实例，如果为None则使用全局实例

    Usage:
        @limit_concurrency()
        def expensive_function():
            # 函数逻辑
            pass
    """
    if limiter is None:
        limiter = get_concurrency_limiter()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 尝试获取许可
            if not limiter.acquire():
                logger.warning(f"函数 {func.__name__} 被限流: 无法获取许可")
                raise TimeoutError(f"函数 {func.__name__} 执行超时（并发限制）")

            try:
                # 执行函数
                return func(*args, **kwargs)
            finally:
                # 释放许可
                limiter.release()

        return wrapper
    return decorator


# ============================================================================
# Flask 集成
# ============================================================================

class FlaskConcurrencyMiddleware:
    """
    Flask 并发限制中间件
    """

    def __init__(self, app=None, limiter: Optional[ConcurrencyLimiter] = None):
        """
        初始化中间件

        Args:
            app: Flask 应用实例
            limiter: 并发限制器实例
        """
        self.limiter = limiter or get_concurrency_limiter()
        self.app = app

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        初始化 Flask 应用

        Args:
            app: Flask 应用实例
        """
        self.app = app

        # 添加 before_request 处理
        @app.before_request
        def limit_concurrent_requests():
            # 只对搜索 API 进行限制
            if request.path == '/api/search' and request.method == 'POST':
                if not self.limiter.acquire(timeout=5.0):
                    return jsonify({
                        "success": False,
                        "message": "服务器繁忙，请稍后重试"
                    }), 503

        # 添加 teardown_request 处理
        @app.teardown_request
        def release_concurrent_requests(exception):
            if request.path == '/api/search' and request.method == 'POST':
                self.limiter.release()


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("并发限制器测试")
    print("=" * 50)

    limiter = ConcurrencyLimiter(max_concurrent=3, timeout=2.0)

    def test_task(task_id: int, duration: float):
        """测试任务"""
        print(f"[任务 {task_id}] 尝试获取许可...")
        if limiter.acquire():
            print(f"[任务 {task_id}] ✅ 获取许可成功")
            time.sleep(duration)
            print(f"[任务 {task_id}] 完成任务")
            limiter.release()
        else:
            print(f"[任务 {task_id}] ❌ 获取许可超时")

    # 测试1: 正常并发
    print("\n测试1: 正常并发（3个并发）")
    import threading

    threads = []
    for i in range(3):
        t = threading.Thread(target=test_task, args=(i, 1.0))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print(f"\n统计信息: {limiter.get_stats()}")

    # 测试2: 超过限制
    print("\n测试2: 超过限制（5个任务，最大3并发）")
    threads = []
    for i in range(5):
        t = threading.Thread(target=test_task, args=(i, 1.0))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print(f"\n统计信息: {limiter.get_stats()}")

    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
