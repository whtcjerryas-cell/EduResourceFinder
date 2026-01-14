#!/usr/bin/env python3
"""
缓存预热模块
用于预加载常用搜索，提升用户体验
"""

import time
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from search_engine_v2 import SearchEngineV2 as SearchEngine, SearchRequest
from logger_utils import get_logger
from core.search_cache import get_search_cache
from core.performance_monitor import get_performance_monitor

logger = get_logger('cache_warmup')


class CacheWarmup:
    """
    缓存预热类

    功能:
    1. 预加载常用搜索
    2. 定时刷新缓存
    3. 智能选择热门搜索
    4. 监控预热效果
    """

    def __init__(self):
        """初始化缓存预热器"""
        self.search_engine = SearchEngine()
        self.cache = get_search_cache()
        self.monitor = get_performance_monitor()

        # 热门搜索配置
        self.popular_searches = self._load_popular_searches()

        logger.info(f"✅ 缓存预热器初始化完成")

    def _load_popular_searches(self) -> List[Dict[str, str]]:
        """
        加载热门搜索配置

        Returns:
            热门搜索列表
        """
        # 常用搜索组合
        searches = [
            # 印尼
            {"country": "Indonesia", "grade": "Kelas 10", "subject": "Matematika"},
            {"country": "Indonesia", "grade": "Kelas 11", "subject": "Fisika"},
            {"country": "Indonesia", "grade": "Kelas 12", "subject": "Kimia"},

            # 中国
            {"country": "China", "grade": "高中一", "subject": "数学"},
            {"country": "China", "grade": "高中一", "subject": "物理"},
            {"country": "China", "grade": "高中二", "subject": "化学"},

            # 印度
            {"country": "India", "grade": "Class 10", "subject": "Mathematics"},
            {"country": "India", "grade": "Class 12", "subject": "Physics"},

            # 菲律宾
            {"country": "Philippines", "grade": "Grade 10", "subject": "Mathematics"},
            {"country": "Philippines", "grade": "Grade 11", "subject": "Science"},

            # 俄罗斯（优化性能）
            {"country": "Russia", "grade": "10 класс", "subject": "Математика"},
            {"country": "Russia", "grade": "11 класс", "subject": "Физика"},
        ]

        return searches

    def warmup_cache(self, delay: float = 1.0) -> Dict[str, Any]:
        """
        执行缓存预热

        Args:
            delay: 每次搜索之间的延迟（秒）

        Returns:
            预热结果统计
        """
        logger.info("=" * 70)
        logger.info("🔥 开始缓存预热")
        logger.info("=" * 70)

        results = {
            "total": len(self.popular_searches),
            "success": 0,
            "failed": 0,
            "total_time": 0,
            "details": []
        }

        start_time = time.time()

        for i, search_config in enumerate(self.popular_searches, 1):
            country = search_config["country"]
            grade = search_config["grade"]
            subject = search_config["subject"]

            logger.info(f"\n[{i}/{len(self.popular_searches)}] 预热: {country} - {grade} - {subject}")

            try:
                # 创建搜索请求
                request = SearchRequest(
                    country=country,
                    grade=grade,
                    subject=subject
                )

                # 执行搜索
                search_start = time.time()
                response = self.search_engine.search(request)
                search_duration = time.time() - search_start

                if response.success:
                    results["success"] += 1
                    logger.info(f"    ✅ 成功 - {search_duration:.2f}s - {response.total_count}个结果")

                    results["details"].append({
                        "country": country,
                        "grade": grade,
                        "subject": subject,
                        "success": True,
                        "duration": search_duration,
                        "result_count": response.total_count
                    })
                else:
                    results["failed"] += 1
                    logger.warning(f"    ⚠️ 失败 - {response.message}")

                    results["details"].append({
                        "country": country,
                        "grade": grade,
                        "subject": subject,
                        "success": False,
                        "error": response.message
                    })

                # 延迟，避免过载
                if delay > 0 and i < len(self.popular_searches):
                    time.sleep(delay)

            except Exception as e:
                results["failed"] += 1
                logger.error(f"    ❌ 错误: {str(e)}")

                results["details"].append({
                    "country": country,
                    "grade": grade,
                    "subject": subject,
                    "success": False,
                    "error": str(e)
                })

        results["total_time"] = time.time() - start_time

        logger.info("\n" + "=" * 70)
        logger.info("🔥 缓存预热完成")
        logger.info("=" * 70)
        logger.info(f"总计: {results['total']} | 成功: {results['success']} | 失败: {results['failed']}")
        logger.info(f"总耗时: {results['total_time']:.2f}s")
        logger.info(f"平均耗时: {results['total_time'] / results['total']:.2f}s")
        logger.info("=" * 70)

        # 显示缓存统计
        cache_stats = self.cache.get_stats()
        logger.info(f"\n缓存统计:")
        logger.info(f"  命中率: {cache_stats['hit_rate']:.1%}")
        logger.info(f"  缓存文件数: {cache_stats['cache_files_count']}")

        return results

    def warmup_by_country(self, country: str, delay: float = 1.0) -> Dict[str, Any]:
        """
        按国家预热缓存

        Args:
            country: 国家名称
            delay: 每次搜索之间的延迟（秒）

        Returns:
            预热结果统计
        """
        # 过滤出指定国家的搜索
        country_searches = [
            s for s in self.popular_searches
            if s["country"].lower() == country.lower()
        ]

        if not country_searches:
            logger.warning(f"未找到国家 {country} 的热门搜索配置")
            return {"total": 0, "success": 0, "failed": 0}

        # 临时替换搜索列表
        original_searches = self.popular_searches
        self.popular_searches = country_searches

        # 执行预热
        results = self.warmup_cache(delay=delay)

        # 恢复原始搜索列表
        self.popular_searches = original_searches

        return results

    def get_warmup_recommendations(self) -> List[Dict[str, Any]]:
        """
        获取预热建议

        基于性能监控数据，推荐应该预热的搜索

        Returns:
            推荐搜索列表
        """
        # 获取慢查询
        slow_queries = self.monitor.get_slow_queries(threshold=3.0, limit=20)

        recommendations = []

        for query in slow_queries:
            country = query["metadata"].get("country", "unknown")
            grade = query["metadata"].get("grade", "unknown")
            subject = query["metadata"].get("subject", "unknown")
            duration = query["duration"]

            if country != "unknown":
                recommendations.append({
                    "country": country,
                    "grade": grade,
                    "subject": subject,
                    "avg_duration": duration,
                    "reason": "慢查询"
                })

        return recommendations


def warmup_on_startup():
    """
    应用启动时执行缓存预热
    """
    print("\n" + "=" * 70)
    print("🔥 执行启动时缓存预热...")
    print("=" * 70)

    warmup = CacheWarmup()
    results = warmup.warmup_cache(delay=0.5)

    print(f"\n✅ 预热完成:")
    print(f"  成功: {results['success']}/{results['total']}")
    print(f"  失败: {results['failed']}/{results['total']}")
    print(f"  耗时: {results['total_time']:.2f}s")
    print("=" * 70 + "\n")


# ============================================================================
# 命令行工具
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="缓存预热工具")
    parser.add_argument(
        "--country",
        type=str,
        help="指定国家（如: Indonesia, China, India）"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="每次搜索之间的延迟（秒），默认: 1.0"
    )
    parser.add_argument(
        "--recommendations",
        action="store_true",
        help="显示预热建议"
    )

    args = parser.parse_args()

    warmup = CacheWarmup()

    if args.recommendations:
        # 显示预热建议
        print("\n" + "=" * 70)
        print("📋 缓存预热建议")
        print("=" * 70)

        recommendations = warmup.get_warmup_recommendations()

        if recommendations:
            print(f"\n基于性能数据，推荐预热以下 {len(recommendations)} 个搜索:\n")
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec['country']} - {rec['grade']} - {rec['subject']}")
                print(f"   平均耗时: {rec['avg_duration']:.2f}s | 原因: {rec['reason']}")
        else:
            print("\n暂无预热建议（系统可能还没有足够的性能数据）")

        print("=" * 70 + "\n")

    elif args.country:
        # 按国家预热
        print(f"\n预热国家: {args.country}")
        results = warmup.warmup_by_country(args.country, delay=args.delay)

    else:
        # 全部预热
        results = warmup.warmup_cache(delay=args.delay)
