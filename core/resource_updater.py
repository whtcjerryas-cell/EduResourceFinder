#!/usr/bin/env python3
"""
资源更新模块
自动检测和更新教育资源，包括新视频检测、评分更新等
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_manager import ConfigManager
from utils.logger_utils import get_logger
from video_evaluator import VideoEvaluator

logger = get_logger('resource_updater')


@dataclass
class UpdateProgress:
    """更新进度"""
    total_countries: int = 0
    updated_countries: int = 0
    failed_countries: int = 0
    start_time: float = field(default_factory=time.time)
    results: List[Dict] = field(default_factory=list)
    errors: List[Dict] = field(default_factory=list)

    @property
    def progress_percent(self) -> float:
        """进度百分比"""
        if self.total_countries == 0:
            return 0.0
        return (self.updated_countries / self.total_countries) * 100


class ResourceUpdater:
    """资源更新器"""

    def __init__(self):
        """初始化资源更新器"""
        self.config_manager = ConfigManager()
        self.evaluator = VideoEvaluator()
        self.progress = UpdateProgress()
        self.lock = threading.Lock()

        logger.info("✅ 资源更新器初始化完成")

    def update_all_resources(self, max_workers: int = 2):
        """
        更新所有国家的教育资源

        Args:
            max_workers: 最大并发数
        """
        logger.info("=" * 80)
        logger.info("🔄 开始批量更新教育资源")
        logger.info("=" * 80)

        # 重置进度
        with self.lock:
            self.progress = UpdateProgress(start_time=time.time())

        # 获取所有国家
        countries = self.config_manager.get_all_countries()

        if not countries:
            logger.warning("⚠️ 没有找到国家配置")
            return

        # 更新总数
        with self.lock:
            self.progress.total_countries = len(countries)

        logger.info(f"📊 需要更新的国家数: {len(countries)}")

        # 并发更新
        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                future_to_country = {}
                for country in countries:
                    country_code = country.get('country_code', '')
                    future = executor.submit(
                        self._update_single_country,
                        country_code,
                        country
                    )
                    future_to_country[future] = country_code

                # 处理完成的任务
                for future in as_completed(future_to_country):
                    country_code = future_to_country[future]

                    try:
                        result = future.result()
                        self._handle_success(country_code, result)
                    except Exception as e:
                        self._handle_failure(country_code, str(e))

        except Exception as e:
            logger.error(f"批量更新失败: {str(e)}")
            import traceback
            traceback.print_exc()

        # 生成报告
        elapsed_time = time.time() - self.progress.start_time

        logger.info("=" * 80)
        logger.info(f"✅ 批量更新完成")
        logger.info(f"⏱️ 总耗时: {elapsed_time:.2f}秒")
        logger.info(f"📊 成功率: {self.progress.updated_countries}/{self.progress.total_countries}")
        logger.info("=" * 80)

    def _update_single_country(self, country_code: str, country_config: Dict) -> Dict:
        """
        更新单个国家的资源

        Args:
            country_code: 国家代码
            country_config: 国家配置

        Returns:
            更新结果
        """
        country_name = country_config.get('country_name', '')
        logger.info(f"\n{'='*60}")
        logger.info(f"🔄 开始更新: {country_name} ({country_code})")
        logger.info(f"{'='*60}")

        start_time = time.time()

        result = {
            'country_code': country_code,
            'country_name': country_name,
            'updated_grades': 0,
            'updated_subjects': 0,
            'new_videos_found': 0,
            'updated_evaluations': 0,
            'errors': []
        }

        try:
            grades = country_config.get('grades', [])

            for grade in grades:
                grade_name = grade.get('grade_name', '')

                for subject in grade.get('subjects', []):
                    subject_name = subject.get('subject_name', '')

                    try:
                        # 检查该学科的搜索历史
                        search_stats = self._get_subject_search_stats(
                            country_code,
                            grade_name,
                            subject_name
                        )

                        # 如果最近7天有搜索，更新评估数据
                        if search_stats.get('recent_searches', 0) > 0:
                            logger.info(f"  📊 {grade_name} - {subject_name}: 发现{search_stats['recent_searches']}次最近搜索")

                            # 重新评估最近的视频
                            updated_count = self._update_recent_evaluations(
                                country_code,
                                grade_name,
                                subject_name
                            )

                            if updated_count > 0:
                                result['updated_evaluations'] += updated_count
                                result['updated_subjects'] += 1

                                logger.info(f"  ✅ {grade_name} - {subject_name}: 更新了{updated_count}个评估")

                    except Exception as e:
                        error_msg = f"{grade_name}-{subject_name}: {str(e)}"
                        result['errors'].append(error_msg)
                        logger.warning(f"  ⚠️ 更新失败: {error_msg}")

                result['updated_grades'] += 1

            elapsed_time = time.time() - start_time
            logger.info(f"✅ {country_name} 更新成功 (耗时: {elapsed_time:.2f}秒)")
            logger.info(f"   - 更新年级: {result['updated_grades']}")
            logger.info(f"   - 更新学科: {result['updated_subjects']}")
            logger.info(f"   - 更新评估: {result['updated_evaluations']}")

            result['success'] = True
            result['elapsed_time'] = elapsed_time

        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"❌ {country_name} 更新失败 (耗时: {elapsed_time:.2f}秒): {str(e)}")

            result['success'] = False
            result['error'] = str(e)
            result['elapsed_time'] = elapsed_time

        return result

    def _get_subject_search_stats(self, country_code: str, grade_name: str, subject_name: str) -> Dict:
        """
        获取学科搜索统计

        Args:
            country_code: 国家代码
            grade_name: 年级名称
            subject_name: 学科名称

        Returns:
            搜索统计字典
        """
        try:
            history_file = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'data',
                'search_history.json'
            )

            if not os.path.exists(history_file):
                return {'recent_searches': 0}

            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)

            # 统计最近7天的搜索
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent_count = 0

            for record in history:
                if record.get('country_code') == country_code and \
                   record.get('grade') == grade_name and \
                   record.get('subject') == subject_name:

                    search_time = datetime.fromisoformat(record.get('timestamp', ''))
                    if search_time > seven_days_ago:
                        recent_count += 1

            return {'recent_searches': recent_count}

        except Exception as e:
            logger.warning(f"获取搜索统计失败: {str(e)}")
            return {'recent_searches': 0}

    def _update_recent_evaluations(
        self,
        country_code: str,
        grade_name: str,
        subject_name: str,
        limit: int = 10
    ) -> int:
        """
        更新最近的评估数据

        Args:
            country_code: 国家代码
            grade_name: 年级名称
            subject_name: 学科名称
            limit: 处理数量限制

        Returns:
            更新的评估数量
        """
        updated_count = 0

        try:
            eval_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'data',
                'evaluations',
                country_code,
                grade_name.replace(' ', '_'),
                subject_name.replace(' ', '_')
            )

            if not os.path.exists(eval_dir):
                return 0

            # 获取最近的评估文件
            eval_files = []
            for file_name in os.listdir(eval_dir):
                if file_name.endswith('.json'):
                    file_path = os.path.join(eval_dir, file_name)
                    stat = os.stat(file_path)
                    eval_files.append({
                        'path': file_path,
                        'mtime': stat.st_mtime
                    })

            # 按修改时间排序，取最近的
            eval_files.sort(key=lambda x: x['mtime'], reverse=True)
            recent_files = eval_files[:limit]

            for file_info in recent_files:
                try:
                    with open(file_info['path'], 'r', encoding='utf-8') as f:
                        eval_data = json.load(f)

                    # 检查评估是否需要更新（超过7天）
                    eval_time = datetime.fromisoformat(eval_data.get('evaluated_at', ''))
                    if datetime.now() - eval_time > timedelta(days=7):
                        # 重新评估
                        video_url = eval_data.get('video_url', '')
                        knowledge_points = eval_data.get('knowledge_points', [])

                        if video_url:
                            logger.info(f"    🔄 重新评估: {os.path.basename(file_info['path'])}")

                            # 重新评估视频
                            new_eval = self.evaluator.evaluate_video(
                                video_url=video_url,
                                knowledge_points=knowledge_points,
                                country_code=country_code
                            )

                            # 更新文件
                            new_eval['evaluated_at'] = datetime.now().isoformat()
                            new_eval['updated'] = True

                            with open(file_info['path'], 'w', encoding='utf-8') as f:
                                json.dump(new_eval, f, ensure_ascii=False, indent=2)

                            updated_count += 1

                except Exception as e:
                    logger.warning(f"    ⚠️ 更新评估失败: {str(e)}")

        except Exception as e:
            logger.warning(f"更新评估数据失败: {str(e)}")

        return updated_count

    def _handle_success(self, country_code: str, result: Dict):
        """处理成功"""
        with self.lock:
            self.progress.updated_countries += 1
            self.progress.results.append({
                'country_code': country_code,
                'status': 'success',
                'elapsed_time': result.get('elapsed_time', 0),
                'updated_grades': result.get('updated_grades', 0),
                'updated_subjects': result.get('updated_subjects', 0),
                'updated_evaluations': result.get('updated_evaluations', 0)
            })

    def _handle_failure(self, country_code: str, error_msg: str):
        """处理失败"""
        logger.error(f"❌ {country_code} 更新失败: {error_msg}")

        with self.lock:
            self.progress.failed_countries += 1
            self.progress.errors.append({
                'country_code': country_code,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            })

    def generate_update_report(self) -> str:
        """
        生成更新报告（Markdown格式）

        Returns:
            Markdown格式的报告
        """
        lines = []
        lines.append("# 资源更新报告")
        lines.append(f"\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"\n## 📊 总体统计")
        lines.append(f"- **总国家数**: {self.progress.total_countries}")
        lines.append(f"- **成功更新**: {self.progress.updated_countries}")
        lines.append(f"- **更新失败**: {self.progress.failed_countries}")
        lines.append(f"- **总耗时**: {self.progress.elapsed_time:.2f}秒")

        # 成功的国家
        if self.progress.results:
            lines.append(f"\n## ✅ 成功更新的国家")
            for result in self.progress.results:
                lines.append(f"\n### {result['country_code']}")
                lines.append(f"- **更新年级**: {result['updated_grades']}")
                lines.append(f"- **更新学科**: {result['updated_subjects']}")
                lines.append(f"- **更新评估**: {result['updated_evaluations']}")
                lines.append(f"- **耗时**: {result['elapsed_time']:.2f}秒")

        # 失败的国家
        if self.progress.errors:
            lines.append(f"\n## ❌ 更新失败的国家")
            for error in self.progress.errors:
                lines.append(f"\n### {error['country_code']}")
                lines.append(f"- **错误**: {error['error']}")
                lines.append(f"- **时间**: {error['timestamp']}")

        return '\n'.join(lines)


# ============================================================================
# 单例模式
# ============================================================================

_resource_updater_instance = None


def get_resource_updater() -> ResourceUpdater:
    """获取资源更新器单例"""
    global _resource_updater_instance
    if _resource_updater_instance is None:
        _resource_updater_instance = ResourceUpdater()
    return _resource_updater_instance


# ============================================================================
# 命令行接口
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='教育资源更新器')
    parser.add_argument('--max-workers', type=int, default=2, help='最大并发数（默认2）')

    args = parser.parse_args()

    # 创建更新器
    updater = get_resource_updater()

    # 执行更新
    updater.update_all_resources(max_workers=args.max_workers)

    # 生成报告
    report = updater.generate_update_report()

    print("\n" + "=" * 80)
    print("📋 更新报告")
    print("=" * 80)
    print(report)
    print("\n" + "=" * 80)

    # 保存报告
    report_file = f"resource_update_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
    os.makedirs(reports_dir, exist_ok=True)

    report_path = os.path.join(reports_dir, report_file)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✅ 报告已保存: {report_path}")
    print("=" * 80)
