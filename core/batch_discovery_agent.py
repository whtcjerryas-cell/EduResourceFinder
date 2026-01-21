#!/usr/bin/env python3
"""
批量国家发现 Agent - AI 驱动的批量国家教育体系调研系统
支持并发调用 discovery_agent 批量调研多个国家
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from dataclasses import dataclass, field
from pydantic import BaseModel

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.discovery_agent import CountryDiscoveryAgent
from config_manager import ConfigManager
from utils.logger_utils import get_logger

logger = get_logger('batch_discovery_agent')


@dataclass
class DiscoveryProgress:
    """发现进度"""
    total_countries: int = 0
    completed_countries: int = 0
    failed_countries: int = 0
    in_progress_countries: int = 0
    start_time: float = field(default_factory=time.time)
    results: List[Dict] = field(default_factory=list)
    errors: List[Dict] = field(default_factory=list)

    @property
    def progress_percent(self) -> float:
        """进度百分比"""
        if self.total_countries == 0:
            return 0.0
        return (self.completed_countries / self.total_countries) * 100

    @property
    def elapsed_time(self) -> float:
        """已用时间（秒）"""
        return time.time() - self.start_time


class BatchDiscoveryAgent:
    """批量国家发现 Agent - 并发处理多个国家的调研"""

    def __init__(self, max_workers: int = 3):
        """
        初始化批量发现 Agent

        Args:
            max_workers: 最大并发数，默认3（避免过多并发导致API限流）
        """
        self.max_workers = max_workers
        self.config_manager = ConfigManager()
        self.progress = DiscoveryProgress()
        self.progress_lock = Lock()
        self.status_callbacks = []

    def add_status_callback(self, callback: Callable[[DiscoveryProgress], None]):
        """
        添加状态回调函数

        Args:
            callback: 回调函数，接收DiscoveryProgress参数
        """
        self.status_callbacks.append(callback)

    def _notify_progress(self):
        """通知所有监听器进度更新"""
        with self.progress_lock:
            # 创建进度副本
            progress_snapshot = DiscoveryProgress(
                total_countries=self.progress.total_countries,
                completed_countries=self.progress.completed_countries,
                failed_countries=self.progress.failed_countries,
                in_progress_countries=self.progress.in_progress_countries,
                start_time=self.progress.start_time,
                results=list(self.progress.results),
                errors=list(self.progress.errors)
            )

        # 调用所有回调
        for callback in self.status_callbacks:
            try:
                callback(progress_snapshot)
            except Exception as e:
                logger.error(f"状态回调失败: {str(e)}")

    def discover_countries_batch(
        self,
        country_names: List[str],
        skip_existing: bool = True
    ) -> Dict[str, any]:
        """
        批量调研多个国家的教育体系

        Args:
            country_names: 国家名称列表（英文）
            skip_existing: 是否跳过已存在的国家配置

        Returns:
            发现结果字典
        """
        logger.info(f"=" * 80)
        logger.info(f"🚀 开始批量国家发现")
        logger.info(f"📋 国家列表: {', '.join(country_names)}")
        logger.info(f"⚙️ 并发数: {self.max_workers}")
        logger.info(f"⏭️ 跳过已存在: {skip_existing}")
        logger.info(f"=" * 80)

        # 重置进度
        with self.progress_lock:
            self.progress = DiscoveryProgress(
                total_countries=len(country_names),
                start_time=time.time()
            )

        # 过滤已存在的国家
        countries_to_discover = []
        for country_name in country_names:
            if skip_existing:
                # 检查是否已存在配置
                existing_codes = self.config_manager.get_all_countries()
                # 简单检查：国家名称是否已存在
                already_exists = any(
                    c.get('country_name', '').lower() == country_name.lower()
                    for c in existing_codes
                )
                if already_exists:
                    logger.info(f"⏭️ 跳过已存在的国家: {country_name}")
                    continue

            countries_to_discover.append(country_name)

        if not countries_to_discover:
            logger.info("✅ 所有国家都已存在，无需调研")
            return self._generate_report()

        # 更新总数
        with self.progress_lock:
            self.progress.total_countries = len(countries_to_discover)

        logger.info(f"📊 实际需要调研的国家数: {len(countries_to_discover)}")

        # 并发调研
        start_time = time.time()

        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有任务
                future_to_country = {}
                for country_name in countries_to_discover:
                    future = executor.submit(self._discover_single_country, country_name)
                    future_to_country[future] = country_name

                # 处理完成的任务
                for future in as_completed(future_to_country):
                    country_name = future_to_country[future]

                    try:
                        result = future.result()
                        self._handle_success(country_name, result)
                    except Exception as e:
                        self._handle_failure(country_name, str(e))

        except Exception as e:
            logger.error(f"批量发现失败: {str(e)}")
            import traceback
            traceback.print_exc()

        end_time = time.time()
        elapsed_time = end_time - start_time

        logger.info(f"=" * 80)
        logger.info(f"✅ 批量国家发现完成")
        logger.info(f"⏱️ 总耗时: {elapsed_time:.2f}秒 ({elapsed_time/60:.2f}分钟)")
        logger.info(f"📊 成功率: {self.progress.completed_countries}/{self.progress.total_countries}")
        logger.info(f"=" * 80)

        # 生成报告
        return self._generate_report()

    def _discover_single_country(self, country_name: str) -> Dict:
        """
        调研单个国家

        Args:
            country_name: 国家名称

        Returns:
            调研结果
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🔍 开始调研: {country_name}")
        logger.info(f"{'='*60}")

        start_time = time.time()

        try:
            # 创建发现 Agent
            agent = CountryDiscoveryAgent()

            # 调研国家
            profile = agent.discover_country_profile(country_name)

            elapsed_time = time.time() - start_time

            logger.info(f"✅ {country_name} 调研成功 (耗时: {elapsed_time:.2f}秒)")

            return {
                'country_name': country_name,
                'profile': profile.dict(),
                'success': True,
                'elapsed_time': elapsed_time
            }

        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"❌ {country_name} 调研失败 (耗时: {elapsed_time:.2f}秒): {str(e)}")

            raise

    def _handle_success(self, country_name: str, result: Dict):
        """处理成功"""
        profile = result['profile']

        # 保存到配置
        try:
            # 使用Pydantic模型验证并保存
            from tools.discovery_agent import CountryProfile
            country_profile = CountryProfile(**profile)
            self.config_manager.update_country_config(country_profile)

            logger.info(f"💾 {country_name} 配置已保存")
        except Exception as e:
            logger.warning(f"⚠️ {country_name} 配置保存失败: {str(e)}")

        # 更新进度
        with self.progress_lock:
            self.progress.completed_countries += 1
            self.progress.results.append({
                'country_name': country_name,
                'status': 'success',
                'elapsed_time': result['elapsed_time'],
                'country_code': profile.get('country_code', ''),
                'grades_count': len(profile.get('grades', [])),
                'subjects_count': len(profile.get('subjects', []))
            })

        # 通知进度更新
        self._notify_progress()

    def _handle_failure(self, country_name: str, error_msg: str):
        """处理失败"""
        logger.error(f"❌ {country_name} 调研失败: {error_msg}")

        # 更新进度
        with self.progress_lock:
            self.progress.failed_countries += 1
            self.progress.errors.append({
                'country_name': country_name,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            })

        # 通知进度更新
        self._notify_progress()

    def _generate_report(self) -> Dict[str, any]:
        """生成发现报告"""
        elapsed_time = self.progress.elapsed_time
        success_count = self.progress.completed_countries
        failed_count = self.progress.failed_countries
        total_count = self.progress.total_countries

        # 统计信息
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0

        # 成功的国家
        successful_countries = [
            r for r in self.progress.results
            if r['status'] == 'success'
        ]

        # 失败的国家
        failed_countries_list = [
            r for r in self.progress.errors
        ]

        # 生成Markdown报告
        markdown_report = self._generate_markdown_report()

        return {
            'success': True,
            'total_countries': total_count,
            'successful_countries': success_count,
            'failed_countries': failed_count,
            'success_rate': round(success_rate, 2),
            'elapsed_time': round(elapsed_time, 2),
            'results': self.progress.results,
            'errors': self.progress.errors,
            'markdown_report': markdown_report,
            'timestamp': datetime.now().isoformat()
        }

    def _generate_markdown_report(self) -> str:
        """生成Markdown格式的报告"""
        lines = []
        lines.append("# 批量国家发现报告")
        lines.append(f"\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"\n## 📊 总体统计")
        lines.append(f"- **总国家数**: {self.progress.total_countries}")
        lines.append(f"- **成功**: {self.progress.completed_countries}")
        lines.append(f"- **失败**: {self.progress.failed_countries}")
        lines.append(f"- **成功率**: {(self.progress.completed_countries / self.progress.total_countries * 100) if self.progress.total_countries > 0 else 0:.1f}%")
        lines.append(f"- **总耗时**: {self.progress.elapsed_time:.2f}秒")

        # 成功的国家
        if self.progress.results:
            lines.append(f"\n## ✅ 成功的国家")
            for result in self.progress.results:
                lines.append(f"\n### {result['country_name']}")
                lines.append(f"- **国家代码**: {result.get('country_code', 'N/A')}")
                lines.append(f"- **年级数**: {result.get('grades_count', 0)}")
                lines.append(f"- **学科数**: {result.get('subjects_count', 0)}")
                lines.append(f"- **耗时**: {result.get('elapsed_time', 0):.2f}秒")

        # 失败的国家
        if self.progress.errors:
            lines.append(f"\n## ❌ 失败的国家")
            for error in self.progress.errors:
                lines.append(f"\n### {error['country_name']}")
                lines.append(f"- **错误**: {error['error']}")
                lines.append(f"- **时间**: {error['timestamp']}")

        return '\n'.join(lines)


# ============================================================================
# 单例模式
# ============================================================================

_batch_discovery_instance = None

def get_batch_discovery_agent() -> BatchDiscoveryAgent:
    """获取批量发现Agent单例"""
    global _batch_discovery_instance
    if _batch_discovery_instance is None:
        _batch_discovery_instance = BatchDiscoveryAgent()
    return _batch_discovery_instance


# ============================================================================
# 命令行接口
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='批量国家发现 Agent')
    parser.add_argument('countries', nargs='+', help='国家名称列表（英文），用空格分隔')
    parser.add_argument('--skip-existing', action='store_true', help='跳过已存在的国家配置')
    parser.add_argument('--max-workers', type=int, default=3, help='最大并发数（默认3）')

    args = parser.parse_args()

    # 创建批量发现Agent
    agent = BatchDiscoveryAgent(max_workers=args.max_workers)

    # 执行批量发现
    result = agent.discover_countries_batch(
        country_names=args.countries,
        skip_existing=args.skip_existing
    )

    # 打印报告
    print("\n" + "=" * 80)
    print("📋 发现报告")
    print("=" * 80)
    print(result['markdown_report'])
    print("\n" + "=" * 80)

    # 保存报告到文件
    report_file = f"batch_discovery_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(result['markdown_report'])

    print(f"✅ 报告已保存: {report_file}")
    print("=" * 80)
