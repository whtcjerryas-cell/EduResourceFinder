#!/usr/bin/env python3
"""
服务容器 - 依赖注入模式
替代全局单例模式，提升可测试性和并发安全性
"""

from typing import Dict, Any, Optional, TypeVar, Type, Callable
from dataclasses import dataclass
import threading


T = TypeVar('T')


@dataclass
class ServiceDescriptor:
    """服务描述符"""
    service_type: Type[Any]
    factory: Optional[Callable[[], Any]] = None
    singleton: bool = True
    instance: Optional[Any] = None


class ServiceContainer:
    """
    依赖注入容器

    使用方法：
        container = ServiceContainer()

        # 注册服务
        container.register(SearchEngine)

        # 注册带工厂函数的服务
        container.register(Cache, lambda: MultiLevelCache())

        # 获取服务
        search_engine = container.get(SearchEngine)
    """

    def __init__(self):
        self._services: Dict[str, ServiceDescriptor] = {}
        self._lock = threading.Lock()

    def register(
        self,
        service_type: Type[T],
        factory: Optional[Callable[[], T]] = None,
        singleton: bool = True,
        override: bool = False
    ) -> None:
        """
        注册服务到容器

        Args:
            service_type: 服务类型
            factory: 工厂函数（可选）
            singleton: 是否单例（默认True）
            override: 是否覆盖已存在的服务
        """
        service_name = service_type.__name__

        with self._lock:
            if service_name in self._services and not override:
                raise ValueError(f"服务 {service_name} 已注册，使用 override=True 覆盖")

            descriptor = ServiceDescriptor(
                service_type=service_type,
                factory=factory,
                singleton=singleton,
                instance=None
            )

            self._services[service_name] = descriptor

    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """
        注册服务实例

        Args:
            service_type: 服务类型
            instance: 服务实例
        """
        service_name = service_type.__name__

        with self._lock:
            descriptor = ServiceDescriptor(
                service_type=service_type,
                factory=None,
                singleton=True,
                instance=instance
            )

            self._services[service_name] = descriptor

    def get(self, service_type: Type[T]) -> T:
        """
        从容器获取服务

        Args:
            service_type: 服务类型

        Returns:
            服务实例
        """
        service_name = service_type.__name__

        if service_name not in self._services:
            # 自动注册
            self.register(service_type)
            descriptor = self._services[service_name]
        else:
            descriptor = self._services[service_name]

        # 单例模式
        if descriptor.singleton:
            if descriptor.instance is None:
                with self._lock:
                    # 双重检查锁定
                    if descriptor.instance is None:
                        if descriptor.factory:
                            descriptor.instance = descriptor.factory()
                        else:
                            descriptor.instance = service_type()
            return descriptor.instance
        else:
            # 非单例，每次创建新实例
            if descriptor.factory:
                return descriptor.factory()
            else:
                return service_type()

    def has(self, service_type: Type[T]) -> bool:
        """
        检查服务是否已注册

        Args:
            service_type: 服务类型

        Returns:
            是否已注册
        """
        service_name = service_type.__name__
        return service_name in self._services

    def clear(self) -> None:
        """清除所有服务（主要用于测试）"""
        with self._lock:
            for descriptor in self._services.values():
                descriptor.instance = None


# 全局容器实例（可以替换为每个线程一个容器）
_global_container: Optional[ServiceContainer] = None
_container_lock = threading.Lock()


def get_container() -> ServiceContainer:
    """
    获取全局服务容器

    Returns:
        服务容器实例
    """
    global _global_container

    if _global_container is None:
        with _container_lock:
            if _global_container is None:
                _global_container = ServiceContainer()

    return _global_container


def init_container() -> ServiceContainer:
    """
    初始化全局容器并注册所有核心服务

    Returns:
        初始化好的容器
    """
    container = get_container()

    # 注册核心服务
    from core.multi_level_cache import MultiLevelCache
    from core.performance_monitor import PerformanceMonitor
    from core.result_scorer import IntelligentResultScorer

    # 多级缓存
    container.register(MultiLevelCache, factory=lambda: MultiLevelCache())

    # 性能监控
    container.register(PerformanceMonitor, factory=lambda: PerformanceMonitor())

    # 评分器（需要知识库，延迟初始化）
    container.register(IntelligentResultScorer, singleton=False)

    return container


# 便捷函数
def get_service(service_type: Type[T]) -> T:
    """
    从容器获取服务（便捷函数）

    Args:
        service_type: 服务类型

    Returns:
        服务实例
    """
    container = get_container()
    return container.get(service_type)
