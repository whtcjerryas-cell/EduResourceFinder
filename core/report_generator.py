#!/usr/bin/env python3
"""
自动报告生成器
生成多维度教育资源报告，支持PDF和Excel导出
"""

import os
import sys
import json
import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from jinja2 import Template

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_manager import ConfigManager
from utils.logger_utils import get_logger
from core.analytics import DataAnalyzer

logger = get_logger('report_generator')

# 设置中文字体（避免中文显示问题）
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


@dataclass
class ReportConfig:
    """报告配置"""
    title: str = "K12教育资源分析报告"
    include_charts: bool = True
    include_details: bool = True
    time_range_days: int = 30


class ReportGenerator:
    """报告生成器"""

    def __init__(self):
        """初始化报告生成器"""
        self.config_manager = ConfigManager()
        self.data_analyzer = DataAnalyzer()
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')

        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)

        logger.info("✅ 报告生成器初始化完成")

    def generate_comprehensive_report(self, config: ReportConfig = None) -> Dict[str, Any]:
        """
        生成综合报告

        Args:
            config: 报告配置

        Returns:
            报告数据
        """
        if config is None:
            config = ReportConfig()

        logger.info("=" * 80)
        logger.info(f"📊 开始生成综合报告: {config.title}")
        logger.info(f"⏰ 时间范围: 最近{config.time_range_days}天")
        logger.info("=" * 80)

        start_time = datetime.now()

        report_data = {
            'metadata': {
                'title': config.title,
                'generated_at': datetime.now().isoformat(),
                'time_range_days': config.time_range_days,
                'generator_version': '1.0.0'
            },
            'sections': []
        }

        # 1. 全球教育资源概览
        logger.info("\n📊 生成全球教育资源概览...")
        global_overview = self._generate_global_overview()
        report_data['sections'].append({
            'id': 'global_overview',
            'title': '全球教育资源概览',
            'content': global_overview
        })

        # 2. 各国教育资源详情
        logger.info("\n📊 生成各国教育资源详情...")
        country_details = self._generate_country_details()
        report_data['sections'].append({
            'id': 'country_details',
            'title': '各国教育资源详情',
            'content': country_details
        })

        # 3. 知识点覆盖率分析
        logger.info("\n📊 生成知识点覆盖率分析...")
        knowledge_coverage = self._generate_knowledge_coverage()
        report_data['sections'].append({
            'id': 'knowledge_coverage',
            'title': '知识点覆盖率分析',
            'content': knowledge_coverage
        })

        # 4. 搜索行为分析
        logger.info("\n📊 生成搜索行为分析...")
        search_behavior = self._generate_search_behavior(config.time_range_days)
        report_data['sections'].append({
            'id': 'search_behavior',
            'title': '搜索行为分析',
            'content': search_behavior
        })

        # 5. 系统性能报告
        logger.info("\n📊 生成系统性能报告...")
        system_performance = self._generate_system_performance()
        report_data['sections'].append({
            'id': 'system_performance',
            'title': '系统性能报告',
            'content': system_performance
        })

        elapsed_time = (datetime.now() - start_time).total_seconds()

        report_data['metadata']['generation_time'] = elapsed_time

        logger.info("=" * 80)
        logger.info(f"✅ 报告生成完成 - 耗时: {elapsed_time:.2f}秒")
        logger.info("=" * 80)

        return report_data

    def _generate_global_overview(self) -> Dict[str, Any]:
        """生成全球教育资源概览"""
        global_stats = self.data_analyzer.get_global_stats()

        overview = {
            'total_countries': global_stats['total_countries'],
            'total_videos': global_stats['total_videos'],
            'total_evaluations': global_stats['total_evaluations'],
            'total_grades': global_stats['total_grades'],
            'total_subjects': global_stats['total_subjects'],
            'average_quality_score': global_stats['average_quality_score'],
            'countries': global_stats['countries']
        }

        return overview

    def _generate_country_details(self) -> List[Dict[str, Any]]:
        """生成各国教育资源详情"""
        countries = self.config_manager.get_all_countries()
        country_details = []

        for country in countries:
            country_code = country.get('country_code', '')
            country_name = country.get('country_name', '')
            grades = country.get('grades', [])

            # 统计该国家的数据
            total_subjects = 0
            for grade in grades:
                subjects = grade.get('subjects', [])
                total_subjects += len(subjects)

            detail = {
                'country_code': country_code,
                'country_name': country_name,
                'total_grades': len(grades),
                'total_subjects': total_subjects,
                'grades': grades
            }

            country_details.append(detail)

        # 按国家代码排序
        country_details.sort(key=lambda x: x['country_code'])

        return country_details

    def _generate_knowledge_coverage(self) -> Dict[str, Any]:
        """生成知识点覆盖率分析"""
        countries = self.config_manager.get_all_countries()
        coverage_data = {
            'countries': []
        }

        for country in countries:
            country_code = country.get('country_code', '')
            country_name = country.get('country_name', '')

            # 统计知识点覆盖情况
            grades_coverage = []

            for grade in country.get('grades', []):
                grade_name = grade.get('grade_name', '')
                subjects_coverage = []

                for subject in grade.get('subjects', []):
                    subject_name = subject.get('subject_name', '')

                    # 获取知识点覆盖数据
                    try:
                        coverage = self.data_analyzer.get_knowledge_point_coverage(
                            country_code,
                            grade_name,
                            subject_name
                        )

                        subjects_coverage.append({
                            'subject_name': subject_name,
                            'total_points': coverage.get('total_knowledge_points', 0),
                            'covered_points': coverage.get('covered_points', 0),
                            'coverage_rate': coverage.get('coverage_rate', 0),
                            'average_quality': coverage.get('average_quality_score', 0)
                        })
                    except Exception as e:
                        logger.warning(f"获取{country_name}-{grade_name}-{subject_name}覆盖数据失败: {str(e)}")

                grades_coverage.append({
                    'grade_name': grade_name,
                    'subjects': subjects_coverage
                })

            coverage_data['countries'].append({
                'country_code': country_code,
                'country_name': country_name,
                'grades': grades_coverage
            })

        return coverage_data

    def _generate_search_behavior(self, days: int) -> Dict[str, Any]:
        """生成搜索行为分析"""
        try:
            search_stats = self.data_analyzer.get_search_stats(days=days)

            behavior = {
                'time_range_days': days,
                'total_searches': search_stats.get('total_searches', 0),
                'successful_searches': search_stats.get('successful_searches', 0),
                'success_rate': search_stats.get('success_rate', 0),
                'average_response_time': search_stats.get('average_response_time', 0),
                'searches_by_country': search_stats.get('searches_by_country', {}),
                'searches_by_subject': search_stats.get('searches_by_subject', {}),
                'daily_trends': search_stats.get('daily_trends', [])
            }

            return behavior
        except Exception as e:
            logger.warning(f"获取搜索行为数据失败: {str(e)}")
            return {
                'time_range_days': days,
                'error': str(e)
            }

    def _generate_system_performance(self) -> Dict[str, Any]:
        """生成系统性能报告"""
        try:
            from performance_monitor import get_performance_monitor

            perf_monitor = get_performance_monitor()
            stats = perf_monitor.get_all_stats()

            performance = {
                'total_searches': stats.get('total_searches', 0),
                'cache_hits': stats.get('cache_hits', 0),
                'cache_misses': stats.get('cache_misses', 0),
                'cache_hit_rate': stats.get('cache_hit_rate', 0),
                'average_response_time': stats.get('average_response_time', 0),
                'engine_performance': stats.get('engine_performance', {})
            }

            return performance
        except Exception as e:
            logger.warning(f"获取系统性能数据失败: {str(e)}")
            return {
                'error': str(e)
            }

    def generate_markdown_report(self, report_data: Dict[str, Any]) -> str:
        """
        生成Markdown格式的报告

        Args:
            report_data: 报告数据

        Returns:
            Markdown格式的报告文本
        """
        lines = []

        # 标题
        lines.append(f"# {report_data['metadata']['title']}")
        lines.append("")
        lines.append(f"**生成时间**: {datetime.fromisoformat(report_data['metadata']['generated_at']).strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**生成耗时**: {report_data['metadata']['generation_time']:.2f}秒")
        lines.append(f"**报告版本**: {report_data['metadata']['generator_version']}")
        lines.append("")

        # 各个章节
        for section in report_data['sections']:
            lines.append(f"## {section['title']}")
            lines.append("")

            content = section['content']

            if section['id'] == 'global_overview':
                # 全球概览
                lines.append(f"- **支持国家数**: {content['total_countries']}")
                lines.append(f"- **总视频数**: {content['total_videos']:,}")
                lines.append(f"- **总评估数**: {content['total_evaluations']:,}")
                lines.append(f"- **总年级数**: {content['total_grades']}")
                lines.append(f"- **总学科数**: {content['total_subjects']}")
                lines.append(f"- **平均质量分**: {content['average_quality_score']:.2f}")
                lines.append("")

                # 各国统计表格
                lines.append("| 国家 | 代码 | 视频数 | 评估数 | 平均质量 |")
                lines.append("|------|------|--------|--------|----------|")

                for country in content['countries']:
                    lines.append(f"| {country['country_name']} | {country['country_code']} | {country['video_count']:,} | {country['evaluation_count']:,} | {country['average_quality']:.2f} |")

                lines.append("")

            elif section['id'] == 'country_details':
                # 各国详情
                for country in content:
                    lines.append(f"### {country['country_name']} ({country['country_code']})")
                    lines.append("")
                    lines.append(f"- **年级数**: {country['total_grades']}")
                    lines.append(f"- **学科总数**: {country['total_subjects']}")
                    lines.append("")

            elif section['id'] == 'knowledge_coverage':
                # 知识点覆盖
                for country in content['countries']:
                    lines.append(f"### {country['country_name']}")
                    lines.append("")

                    for grade in country['grades']:
                        lines.append(f"#### {grade['grade_name']}")
                        lines.append("")

                        if grade['subjects']:
                            lines.append("| 学科 | 知识点总数 | 已覆盖 | 覆盖率 | 平均质量 |")
                            lines.append("|------|-----------|--------|--------|----------|")

                            for subject in grade['subjects']:
                                coverage_rate = subject['coverage_rate'] * 100
                                lines.append(f"| {subject['subject_name']} | {subject['total_points']} | {subject['covered_points']} | {coverage_rate:.1f}% | {subject['average_quality']:.2f} |")

                            lines.append("")

            elif section['id'] == 'search_behavior':
                # 搜索行为
                if 'error' not in content:
                    lines.append(f"- **时间范围**: 最近{content['time_range_days']}天")
                    lines.append(f"- **总搜索次数**: {content['total_searches']:,}")
                    lines.append(f"- **成功搜索**: {content['successful_searches']:,}")
                    lines.append(f"- **成功率**: {content['success_rate']:.1f}%")
                    lines.append(f"- **平均响应时间**: {content['average_response_time']:.2f}秒")
                    lines.append("")

                    # 按国家分布
                    if content['searches_by_country']:
                        lines.append("#### 按国家分布")
                        lines.append("")

                        for country_code, count in sorted(content['searches_by_country'].items(), key=lambda x: x[1], reverse=True):
                            lines.append(f"- **{country_code}**: {count:,}次搜索")

                        lines.append("")

            elif section['id'] == 'system_performance':
                # 系统性能
                if 'error' not in content:
                    lines.append(f"- **总搜索次数**: {content['total_searches']:,}")
                    lines.append(f"- **缓存命中**: {content['cache_hits']:,}")
                    lines.append(f"- **缓存未命中**: {content['cache_misses']:,}")
                    lines.append(f"- **缓存命中率**: {content['cache_hit_rate']:.1f}%")
                    lines.append(f"- **平均响应时间**: {content['average_response_time']:.2f}秒")
                    lines.append("")

                    # 搜索引擎性能
                    if content['engine_performance']:
                        lines.append("#### 搜索引擎性能")
                        lines.append("")

                        for engine, perf in content['engine_performance'].items():
                            lines.append(f"- **{engine}**:")
                            lines.append(f"  - 搜索次数: {perf.get('search_count', 0):,}")
                            lines.append(f"  - 平均响应时间: {perf.get('avg_response_time', 0):.2f}秒")
                            lines.append(f"  - 成功率: {perf.get('success_rate', 0):.1f}%")

                        lines.append("")

        return '\n'.join(lines)

    def save_markdown_report(self, report_data: Dict[str, Any], filename: str = None) -> str:
        """
        保存Markdown报告到文件

        Args:
            report_data: 报告数据
            filename: 文件名（可选）

        Returns:
            保存的文件路径
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'education_report_{timestamp}.md'

        filepath = os.path.join(self.output_dir, filename)

        markdown_content = self.generate_markdown_report(report_data)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        logger.info(f"✅ Markdown报告已保存: {filepath}")

        return filepath

    def generate_json_report(self, report_data: Dict[str, Any], filename: str = None) -> str:
        """
        生成JSON格式的报告

        Args:
            report_data: 报告数据
            filename: 文件名（可选）

        Returns:
            保存的文件路径
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'education_report_{timestamp}.json'

        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ JSON报告已保存: {filepath}")

        return filepath


# ============================================================================
# 单例模式
# ============================================================================

_report_generator_instance = None


def get_report_generator() -> ReportGenerator:
    """获取报告生成器单例"""
    global _report_generator_instance
    if _report_generator_instance is None:
        _report_generator_instance = ReportGenerator()
    return _report_generator_instance


# ============================================================================
# 命令行接口
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='教育资源报告生成器')
    parser.add_argument('--output', '-o', help='输出文件名（不含扩展名）')
    parser.add_argument('--format', '-f', choices=['markdown', 'json', 'both'], default='both',
                       help='输出格式（默认: both）')
    parser.add_argument('--days', '-d', type=int, default=30,
                       help='统计时间范围（天），默认30天')

    args = parser.parse_args()

    # 创建报告生成器
    generator = ReportGenerator()

    # 配置报告
    config = ReportConfig(time_range_days=args.days)

    # 生成报告
    print("📊 正在生成报告...")
    report_data = generator.generate_comprehensive_report(config)

    # 保存报告
    if args.format in ['markdown', 'both']:
        md_file = generator.save_markdown_report(report_data, args.output + '.md' if args.output else None)
        print(f"✅ Markdown报告: {md_file}")

    if args.format in ['json', 'both']:
        json_file = generator.generate_json_report(report_data, args.output + '.json' if args.output else None)
        print(f"✅ JSON报告: {json_file}")

    print("\n📊 报告生成完成！")
