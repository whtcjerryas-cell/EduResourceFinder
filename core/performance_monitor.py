#!/usr/bin/env python3
"""
性能监控模块
用于追踪和报告系统性能指标
"""

import time
import json
from typing import Dict, List, Optional, Any, Callable
from functools import wraps
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from threading import Lock
from logger_utils import get_logger

logger = get_logger('performance_monitor')


class PerformanceMonitor:
    """
    性能监控类

    功能:
    1. 记录函数执行时间
    2. 按类别统计性能数据
    3. 生成性能报告
    4. 持久化性能数据
    """

    def __init__(self, data_dir: str = "data/performance"):
        """
        初始化性能监控器

        Args:
            data_dir: 性能数据存储目录
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 性能数据存储
        self.metrics: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.lock = Lock()

        # 统计数据
        self.stats = {
            "total_calls": 0,
            "total_errors": 0,
            "start_time": datetime.now().isoformat()
        }

        logger.info(f"✅ 性能监控器初始化完成: {self.data_dir}")

    def record_metric(self,
                     operation: str,
                     duration: float,
                     success: bool = True,
                     metadata: Optional[Dict[str, Any]] = None):
        """
        记录性能指标

        Args:
            operation: 操作名称（如: search_indonesia, cache_get）
            duration: 执行时间（秒）
            success: 是否成功
            metadata: 额外的元数据（如: country, engine, result_count）
        """
        with self.lock:
            metric = {
                "operation": operation,
                "duration": duration,
                "success": success,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }

            self.metrics[operation].append(metric)
            self.stats["total_calls"] += 1

            if not success:
                self.stats["total_errors"] += 1

            logger.debug(f"记录指标: {operation} - {duration:.3f}s")

    def get_stats(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        获取统计信息

        Args:
            operation: 操作名称，如果为None则返回所有操作的统计

        Returns:
            统计信息字典
        """
        with self.lock:
            if operation:
                return self._get_operation_stats(operation)

            # 返回所有操作的统计
            all_stats = {}
            for op in self.metrics.keys():
                all_stats[op] = self._get_operation_stats(op)

            return {
                "operations": all_stats,
                "total_calls": self.stats["total_calls"],
                "total_errors": self.stats["total_errors"],
                "error_rate": self.stats["total_errors"] / max(1, self.stats["total_calls"]),
                "start_time": self.stats["start_time"]
            }

    def _get_operation_stats(self, operation: str) -> Dict[str, Any]:
        """
        获取单个操作的统计信息
        """
        if operation not in self.metrics or not self.metrics[operation]:
            return {
                "count": 0,
                "avg_duration": 0,
                "min_duration": 0,
                "max_duration": 0,
                "p50_duration": 0,
                "p95_duration": 0,
                "p99_duration": 0,
                "success_rate": 0
            }

        records = self.metrics[operation]
        durations = [r["duration"] for r in records]
        durations.sort()

        count = len(durations)
        total = sum(durations)
        avg = total / count

        # 计算百分位数
        def percentile(p: float) -> float:
            idx = int(len(durations) * p / 100)
            return durations[idx] if durations else 0

        success_count = sum(1 for r in records if r["success"])

        return {
            "count": count,
            "avg_duration": round(avg, 3),
            "min_duration": round(min(durations), 3),
            "max_duration": round(max(durations), 3),
            "p50_duration": round(percentile(50), 3),
            "p95_duration": round(percentile(95), 3),
            "p99_duration": round(percentile(99), 3),
            "success_rate": success_count / count if count > 0 else 0
        }

    def get_stats_by_country(self) -> Dict[str, Any]:
        """
        获取按国家分组的统计信息
        """
        with self.lock:
            country_stats: Dict[str, List[float]] = defaultdict(list)

            for op, records in self.metrics.items():
                for record in records:
                    country = record["metadata"].get("country", "unknown")
                    if country != "unknown":
                        country_stats[country].append(record["duration"])

            result = {}
            for country, durations in country_stats.items():
                durations.sort()
                result[country] = {
                    "count": len(durations),
                    "avg_duration": round(sum(durations) / len(durations), 3),
                    "min_duration": round(min(durations), 3),
                    "max_duration": round(max(durations), 3),
                    "p95_duration": round(durations[int(len(durations) * 0.95)] if durations else 0, 3)
                }

            return result

    def get_slow_queries(self, threshold: float = 5.0, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取慢查询列表

        Args:
            threshold: 慢查询阈值（秒）
            limit: 返回的最大数量

        Returns:
            慢查询列表
        """
        with self.lock:
            slow_queries = []

            for op, records in self.metrics.items():
                for record in records:
                    if record["duration"] >= threshold:
                        slow_queries.append({
                            "operation": op,
                            "duration": record["duration"],
                            "timestamp": record["timestamp"],
                            "metadata": record["metadata"]
                        })

            # 按持续时间排序
            slow_queries.sort(key=lambda x: x["duration"], reverse=True)
            return slow_queries[:limit]

    def get_stats_by_engine(self) -> Dict[str, Any]:
        """
        获取按搜索引擎分组的统计信息
        """
        with self.lock:
            engine_stats: Dict[str, List[float]] = defaultdict(list)

            for op, records in self.metrics.items():
                for record in records:
                    engine = record["metadata"].get("engine", "unknown")
                    if engine != "unknown":
                        engine_stats[engine].append(record["duration"])

            result = {}
            for engine, durations in engine_stats.items():
                durations.sort()
                result[engine] = {
                    "count": len(durations),
                    "avg_duration": round(sum(durations) / len(durations), 3),
                    "min_duration": round(min(durations), 3),
                    "max_duration": round(max(durations), 3)
                }

            return result

    def save_metrics(self):
        """保存性能指标到文件"""
        with self.lock:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = self.data_dir / f"metrics_{timestamp}.json"

            data = {
                "timestamp": timestamp,
                "stats": self.stats,
                "metrics": dict(self.metrics)
            }

            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                logger.info(f"性能指标已保存: {file_path}")
            except Exception as e:
                logger.error(f"保存性能指标失败: {str(e)}")

    def cleanup_old_metrics(self, days: int = 7):
        """
        清理旧的性能数据文件

        Args:
            days: 保留天数
        """
        cutoff_time = datetime.now() - timedelta(days=days)

        for file_path in self.data_dir.glob("metrics_*.json"):
            try:
                # 从文件名提取时间
                parts = file_path.stem.split("_")
                if len(parts) >= 3:
                    date_str = f"{parts[1]}{parts[2]}"
                    file_time = datetime.strptime(date_str, "%Y%m%d%H%M%S")

                    if file_time < cutoff_time:
                        file_path.unlink()
                        logger.info(f"已删除旧指标文件: {file_path}")
            except Exception as e:
                logger.warning(f"清理文件失败 {file_path}: {str(e)}")

    def generate_report(self) -> str:
        """
        生成性能报告

        Returns:
            报告文本
        """
        stats = self.get_stats()
        country_stats = self.get_stats_by_country()
        engine_stats = self.get_stats_by_engine()
        slow_queries = self.get_slow_queries(threshold=5.0, limit=10)

        report = []
        report.append("=" * 70)
        report.append("性能监控报告")
        report.append("=" * 70)
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"总调用次数: {stats['total_calls']}")
        report.append(f"总错误次数: {stats['total_errors']}")
        report.append(f"错误率: {stats['error_rate']:.2%}")
        report.append("")

        # 按国家统计
        if country_stats:
            report.append("-" * 70)
            report.append("按国家统计:")
            report.append("-" * 70)
            report.append(f"{'国家':<15} {'次数':<8} {'平均':<10} {'最小':<10} {'最大':<10} {'P95':<10}")
            report.append("-" * 70)

            for country, stat in sorted(country_stats.items(), key=lambda x: x[1]['avg_duration']):
                report.append(
                    f"{country:<15} {stat['count']:<8} {stat['avg_duration']:<10} "
                    f"{stat['min_duration']:<10} {stat['max_duration']:<10} {stat['p95_duration']:<10}"
                )
            report.append("")

        # 按搜索引擎统计
        if engine_stats:
            report.append("-" * 70)
            report.append("按搜索引擎统计:")
            report.append("-" * 70)
            report.append(f"{'引擎':<15} {'次数':<8} {'平均':<10} {'最小':<10} {'最大':<10}")
            report.append("-" * 70)

            for engine, stat in sorted(engine_stats.items(), key=lambda x: x[1]['avg_duration']):
                report.append(
                    f"{engine:<15} {stat['count']:<8} {stat['avg_duration']:<10} "
                    f"{stat['min_duration']:<10} {stat['max_duration']:<10}"
                )
            report.append("")

        # 慢查询
        if slow_queries:
            report.append("-" * 70)
            report.append(f"慢查询 (>5.0s) - Top {len(slow_queries)}:")
            report.append("-" * 70)

            for i, query in enumerate(slow_queries, 1):
                country = query['metadata'].get('country', 'N/A')
                grade = query['metadata'].get('grade', 'N/A')
                subject = query['metadata'].get('subject', 'N/A')
                report.append(
                    f"{i}. {query['operation']}: {query['duration']:.3f}s - "
                    f"{country} / {grade} / {subject}"
                )
            report.append("")

        report.append("=" * 70)

        return "\n".join(report)


# 全局单例
_global_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """
    获取全局性能监控器实例

    Returns:
        PerformanceMonitor实例
    """
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def monitor_performance(operation_name: Optional[str] = None):
    """
    性能监控装饰器

    Args:
        operation_name: 操作名称，如果为None则使用函数名

    Usage:
        @monitor_performance("search_indonesia")
        def search(country, grade, subject):
            # 搜索逻辑
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            op_name = operation_name or func.__name__

            start_time = time.time()
            success = True
            metadata = {}

            try:
                result = func(*args, **kwargs)

                # 尝试从参数中提取元数据
                if args and len(args) >= 3:
                    metadata = {
                        "country": args[0] if isinstance(args[0], str) else "unknown",
                        "grade": args[1] if len(args) > 1 and isinstance(args[1], str) else "unknown",
                        "subject": args[2] if len(args) > 2 and isinstance(args[2], str) else "unknown"
                    }

                # 从结果中提取元数据
                if hasattr(result, '__dict__'):
                    if hasattr(result, 'total_count'):
                        metadata['result_count'] = result.total_count
                    if hasattr(result, 'query'):
                        metadata['query'] = result.query

                return result

            except Exception as e:
                success = False
                metadata['error'] = str(e)
                logger.error(f"操作失败: {op_name} - {str(e)}")
                raise

            finally:
                duration = time.time() - start_time
                monitor.record_metric(op_name, duration, success, metadata)

        return wrapper
    return decorator


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("性能监控测试")
    print("=" * 50)

    monitor = PerformanceMonitor()

    # 模拟一些操作
    print("\n测试1: 记录指标")
    monitor.record_metric("search_indonesia", 1.5, True, {"country": "Indonesia", "result_count": 10})
    monitor.record_metric("search_indonesia", 2.3, True, {"country": "Indonesia", "result_count": 8})
    monitor.record_metric("search_china", 3.7, True, {"country": "China", "result_count": 10})
    monitor.record_metric("search_russia", 16.89, True, {"country": "Russia", "result_count": 5})
    monitor.record_metric("cache_get", 0.001, True, {"hit": True})

    print("\n测试2: 获取统计")
    print(f"所有统计: {json.dumps(monitor.get_stats(), indent=2)}")

    print("\n测试3: 按国家统计")
    print(f"国家统计: {json.dumps(monitor.get_stats_by_country(), indent=2)}")

    print("\n测试4: 慢查询")
    print(f"慢查询: {json.dumps(monitor.get_slow_queries(threshold=2.0), indent=2)}")

    print("\n测试5: 生成报告")
    print(monitor.generate_report())

    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
