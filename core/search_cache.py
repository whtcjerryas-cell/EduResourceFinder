#!/usr/bin/env python3
"""
搜索结果缓存模块
用于缓存搜索引擎结果，提升性能
"""

import json
import hashlib
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from logger_utils import get_logger

logger = get_logger('search_cache')


class SearchCache:
    """
    搜索结果缓存类

    功能:
    1. 基于查询哈希的缓存键
    2. TTL（Time To Live）过期机制
    3. 持久化到磁盘
    4. 缓存命中率统计
    """

    def __init__(self, cache_dir: str = "data/cache", ttl_seconds: int = 3600):
        """
        初始化缓存

        Args:
            cache_dir: 缓存目录
            ttl_seconds: 缓存有效期（秒），默认1小时
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds

        # 统计信息
        self.stats = {
            "hits": 0,
            "misses": 0,
            "total_queries": 0
        }

        logger.info(f"✅ 搜索缓存初始化完成: {self.cache_dir}, TTL={ttl_seconds}秒")

    def _generate_cache_key(self, query: str, engine: str = "default") -> str:
        """
        生成缓存键

        Args:
            query: 搜索查询
            engine: 搜索引擎名称

        Returns:
            缓存键（MD5哈希）
        """
        # 组合查询和引擎，生成唯一哈希
        content = f"{engine}:{query}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def get(self, query: str, engine: str = "default") -> Optional[Dict[str, Any]]:
        """
        获取缓存结果

        Args:
            query: 搜索查询
            engine: 搜索引擎名称

        Returns:
            缓存的结果字典，如果不存在或已过期则返回None
        """
        self.stats["total_queries"] += 1
        cache_key = self._generate_cache_key(query, engine)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            self.stats["misses"] += 1
            logger.debug(f"缓存未命中: {query[:50]}...")
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # 检查是否过期
            cached_time = cache_data.get("timestamp", 0)
            current_time = time.time()

            if current_time - cached_time > self.ttl_seconds:
                # 缓存已过期，删除
                cache_file.unlink()
                self.stats["misses"] += 1
                logger.debug(f"缓存已过期: {query[:50]}...")
                return None

            # 缓存命中
            self.stats["hits"] += 1
            logger.info(f"✅ 缓存命中: {query[:50]}... (命中率: {self.get_hit_rate():.1%})")
            return cache_data["data"]

        except Exception as e:
            logger.error(f"读取缓存失败: {str(e)}")
            self.stats["misses"] += 1
            return None

    def set(self, query: str, results: List[Any], engine: str = "default", metadata: Optional[Dict] = None):
        """
        设置缓存结果

        Args:
            query: 搜索查询
            results: 搜索结果列表
            engine: 搜索引擎名称
            metadata: 额外的元数据
        """
        cache_key = self._generate_cache_key(query, engine)
        cache_file = self.cache_dir / f"{cache_key}.json"

        cache_data = {
            "query": query,
            "engine": engine,
            "timestamp": time.time(),
            "data": results,
            "metadata": metadata or {},
            "result_count": len(results)
        }

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            logger.debug(f"缓存已保存: {query[:50]}... ({len(results)}条结果)")
        except Exception as e:
            logger.error(f"保存缓存失败: {str(e)}")

    def invalidate(self, query: str, engine: str = "default"):
        """
        使特定查询的缓存失效

        Args:
            query: 搜索查询
            engine: 搜索引擎名称
        """
        cache_key = self._generate_cache_key(query, engine)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            cache_file.unlink()
            logger.debug(f"缓存已失效: {query[:50]}...")

    def clear_all(self):
        """清空所有缓存"""
        cache_files = list(self.cache_dir.glob("*.json"))
        for cache_file in cache_files:
            cache_file.unlink()
        logger.info(f"已清空所有缓存: {len(cache_files)}个文件")

    def get_hit_rate(self) -> float:
        """
        获取缓存命中率

        Returns:
            命中率（0.0-1.0）
        """
        if self.stats["total_queries"] == 0:
            return 0.0
        return self.stats["hits"] / self.stats["total_queries"]

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "total_queries": self.stats["total_queries"],
            "hit_rate": self.get_hit_rate(),
            "cache_files_count": len(list(self.cache_dir.glob("*.json")))
        }

    def cleanup_expired(self):
        """清理过期的缓存文件"""
        current_time = time.time()
        expired_count = 0

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                cached_time = cache_data.get("timestamp", 0)

                if current_time - cached_time > self.ttl_seconds:
                    cache_file.unlink()
                    expired_count += 1

            except Exception as e:
                # 文件损坏，直接删除
                cache_file.unlink()
                expired_count += 1

        if expired_count > 0:
            logger.info(f"已清理{expired_count}个过期缓存文件")


# 全局单例
_global_cache: Optional[SearchCache] = None


def get_search_cache() -> SearchCache:
    """
    获取全局搜索缓存实例

    Returns:
        SearchCache实例
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = SearchCache()
    return _global_cache


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("搜索缓存测试")
    print("=" * 50)

    cache = SearchCache(ttl_seconds=60)

    # 测试1: 缓存未命中
    print("\n测试1: 缓存未命中")
    result = cache.get("test query", "google")
    print(f"结果: {result}")
    print(f"统计: {cache.get_stats()}")

    # 测试2: 设置缓存
    print("\n测试2: 设置缓存")
    cache.set("test query", [{"title": "Test", "url": "http://test.com"}], "google")
    print(f"统计: {cache.get_stats()}")

    # 测试3: 缓存命中
    print("\n测试3: 缓存命中")
    result = cache.get("test query", "google")
    print(f"结果: {result}")
    print(f"统计: {cache.get_stats()}")

    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
