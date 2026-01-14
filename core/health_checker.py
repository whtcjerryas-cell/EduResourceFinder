#!/usr/bin/env python3
"""
自动化健康检查模块
用于监控系统健康状态，包括搜索引擎、API响应、数据一致性等
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_manager import ConfigManager
from logger_utils import get_logger
from search_strategist import SearchHunter
from tools.discovery_agent import CountryDiscoveryAgent

logger = get_logger('health_checker')


class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """单项健康检查结果"""
    name: str
    status: HealthStatus
    message: str
    response_time: float = 0.0
    details: Dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'name': self.name,
            'status': self.status.value,
            'message': self.message,
            'response_time': self.response_time,
            'details': self.details,
            'timestamp': self.timestamp
        }


class HealthChecker:
    """自动化健康检查器"""

    def __init__(self):
        """初始化健康检查器"""
        self.config_manager = ConfigManager()
        self.discovery_agent = CountryDiscoveryAgent()

        # 健康阈值配置
        self.thresholds = {
            'api_response_time': 5.0,  # API响应时间阈值（秒）
            'search_response_time': 10.0,  # 搜索响应时间阈值（秒）
            'min_success_rate': 0.7,  # 最低成功率
            'max_degraded_engines': 1,  # 最多允许的降级搜索引擎数量
        }

        logger.info("✅ 健康检查器初始化完成")

    def run_all_checks(self) -> Dict[str, any]:
        """
        运行所有健康检查

        Returns:
            包含所有检查结果的字典
        """
        logger.info("=" * 80)
        logger.info("🔍 开始系统健康检查")
        logger.info("=" * 80)

        start_time = time.time()
        results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': HealthStatus.UNKNOWN,
            'total_checks': 0,
            'passed_checks': 0,
            'failed_checks': 0,
            'degraded_checks': 0,
            'checks': []
        }

        # 1. 搜索引擎健康检查
        search_engine_result = self._check_search_engines()
        results['checks'].append(search_engine_result.to_dict())

        # 2. API健康检查
        api_result = self._check_apis()
        results['checks'].append(api_result.to_dict())

        # 3. 数据一致性检查
        data_consistency_result = self._check_data_consistency()
        results['checks'].append(data_consistency_result.to_dict())

        # 4. 配置文件检查
        config_result = self._check_configurations()
        results['checks'].append(config_result.to_dict())

        # 5. 磁盘空间检查
        disk_result = self._check_disk_space()
        results['checks'].append(disk_result.to_dict())

        # 统计结果
        results['total_checks'] = len(results['checks'])
        results['passed_checks'] = sum(1 for c in results['checks'] if c['status'] == HealthStatus.HEALTHY.value)
        results['failed_checks'] = sum(1 for c in results['checks'] if c['status'] == HealthStatus.UNHEALTHY.value)
        results['degraded_checks'] = sum(1 for c in results['checks'] if c['status'] == HealthStatus.DEGRADED.value)

        # 计算总体状态
        if results['failed_checks'] > 0:
            results['overall_status'] = HealthStatus.UNHEALTHY.value
        elif results['degraded_checks'] > 0:
            results['overall_status'] = HealthStatus.DEGRADED.value
        else:
            results['overall_status'] = HealthStatus.HEALTHY.value

        elapsed_time = time.time() - start_time
        results['elapsed_time'] = round(elapsed_time, 2)

        logger.info("=" * 80)
        logger.info(f"✅ 健康检查完成 - 总体状态: {results['overall_status']}")
        logger.info(f"📊 通过: {results['passed_checks']}/{results['total_checks']}")
        logger.info(f"⏱️ 耗时: {elapsed_time:.2f}秒")
        logger.info("=" * 80)

        return results

    def _check_search_engines(self) -> HealthCheckResult:
        """
        检查搜索引擎健康状态（简化版，不实际调用API）

        Returns:
            搜索引擎健康检查结果
        """
        logger.info("\n🔍 检查搜索引擎配置...")

        start_time = time.time()

        # 检查搜索引擎配置是否存在
        try:
            from search_strategist import SearchHunter
            has_search_hunter = True
        except ImportError:
            has_search_hunter = False

        # 检查环境变量配置
        google_api_key = bool(os.getenv("GOOGLE_API_KEY"))
        google_cx = bool(os.getenv("GOOGLE_CX"))
        baidu_api_key = bool(os.getenv("BAIDU_API_KEY"))

        elapsed_time = time.time() - start_time

        # 计算状态
        if has_search_hunter and (google_api_key or baidu_api_key):
            status = HealthStatus.HEALTHY
            message = "搜索引擎配置正常"
        elif has_search_hunter:
            status = HealthStatus.DEGRADED
            message = "搜索引擎模块存在但缺少API密钥"
        else:
            status = HealthStatus.DEGRADED
            message = "搜索引擎配置不完整"

        return HealthCheckResult(
            name="搜索引擎配置检查",
            status=status,
            message=message,
            response_time=round(elapsed_time, 2),
            details={
                'has_search_hunter': has_search_hunter,
                'google_configured': google_api_key and google_cx,
                'baidu_configured': baidu_api_key
            }
        )

    def _check_apis(self) -> HealthCheckResult:
        """
        检查API健康状态

        Returns:
            API健康检查结果
        """
        logger.info("\n🔍 检查API健康...")

        start_time = time.time()
        api_status = {}
        failed_apis = []

        # 检查LLM API
        try:
            api_start_time = time.time()

            # 简单的API测试调用
            test_response = self.discovery_agent.llm_client.generate_response(
                "Hello, this is a health check test. Please respond with 'OK'."
            )

            api_time = time.time() - api_start_time

            if test_response and len(test_response) > 0:
                api_status['llm_api'] = {
                    'status': 'healthy',
                    'response_time': round(api_time, 2),
                    'response_length': len(test_response)
                }
                logger.info(f"  ✅ LLM API: healthy ({api_time:.2f}s)")
            else:
                api_status['llm_api'] = {
                    'status': 'failed',
                    'response_time': round(api_time, 2)
                }
                failed_apis.append('llm_api')
                logger.warning(f"  ⚠️ LLM API: failed (empty response)")

        except Exception as e:
            api_time = time.time() - api_start_time
            api_status['llm_api'] = {
                'status': 'error',
                'error': str(e)
            }
            failed_apis.append('llm_api')
            logger.error(f"  ❌ LLM API: error - {str(e)}")

        # 计算总体状态
        elapsed_time = time.time() - start_time

        if len(failed_apis) > 0:
            status = HealthStatus.UNHEALTHY
            message = f"API检查失败: {', '.join(failed_apis)}"
        else:
            status = HealthStatus.HEALTHY
            message = "所有API正常"

        return HealthCheckResult(
            name="API健康检查",
            status=status,
            message=message,
            response_time=round(elapsed_time, 2),
            details={
                'apis': api_status,
                'failed_apis': failed_apis
            }
        )

    def _check_data_consistency(self) -> HealthCheckResult:
        """
        检查数据一致性

        Returns:
            数据一致性检查结果
        """
        logger.info("\n🔍 检查数据一致性...")

        start_time = time.time()
        issues = []

        try:
            # 1. 检查国家配置文件
            countries = self.config_manager.get_all_countries()
            if not countries or len(countries) == 0:
                issues.append("国家配置文件为空")
            else:
                logger.info(f"  ✅ 国家配置: {len(countries)}个国家")

            # 2. 检查每个国家的数据完整性
            for country in countries:
                country_code = country.get('country_code', '')
                country_name = country.get('country_name', '')

                if not country_code:
                    issues.append(f"国家缺少代码: {country_name}")
                    continue

                # 检查必需字段
                required_fields = ['country_code', 'country_name', 'grades']
                missing_fields = [f for f in required_fields if f not in country or not country[f]]

                if missing_fields:
                    issues.append(f"{country_name} 缺少字段: {', '.join(missing_fields)}")

                # 检查年级和学科
                if 'grades' in country and country['grades']:
                    logger.info(f"  ✅ {country_name}: {len(country['grades'])}个年级")

                    for grade in country['grades']:
                        if 'subjects' not in grade or not grade['subjects']:
                            issues.append(f"{country_name} - {grade.get('grade_name', 'Unknown')}: 缺少学科")

            # 3. 检查评估数据目录
            eval_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'evaluations')
            if os.path.exists(eval_dir):
                eval_files = [f for f in os.listdir(eval_dir) if f.endswith('.json')]
                logger.info(f"  ✅ 评估数据: {len(eval_files)}个文件")
            else:
                issues.append("评估数据目录不存在")

            # 4. 检查搜索历史
            history_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'search_history.json')
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    try:
                        history = json.load(f)
                        if isinstance(history, list) and len(history) > 0:
                            logger.info(f"  ✅ 搜索历史: {len(history)}条记录")
                    except json.JSONDecodeError:
                        issues.append("搜索历史文件格式错误")

        except Exception as e:
            issues.append(f"数据一致性检查异常: {str(e)}")
            logger.error(f"  ❌ 检查异常: {str(e)}")

        # 计算总体状态
        elapsed_time = time.time() - start_time

        if len(issues) >= 3:
            status = HealthStatus.UNHEALTHY
            message = f"发现{len(issues)}个严重问题"
        elif len(issues) > 0:
            status = HealthStatus.DEGRADED
            message = f"发现{len(issues)}个问题"
        else:
            status = HealthStatus.HEALTHY
            message = "数据一致性良好"

        return HealthCheckResult(
            name="数据一致性检查",
            status=status,
            message=message,
            response_time=round(elapsed_time, 2),
            details={
                'issues': issues,
                'issues_count': len(issues)
            }
        )

    def _check_configurations(self) -> HealthCheckResult:
        """
        检查配置文件

        Returns:
            配置文件检查结果
        """
        logger.info("\n🔍 检查配置文件...")

        start_time = time.time()
        config_issues = []

        try:
            # 检查必需的配置文件
            base_dir = os.path.dirname(os.path.dirname(__file__))
            required_configs = [
                'data/config/countries_config.json',
                'data/config/grades_config.json',
                'data/config/subjects_config.json'
            ]

            for config_path in required_configs:
                full_path = os.path.join(base_dir, config_path)
                if not os.path.exists(full_path):
                    config_issues.append(f"配置文件缺失: {config_path}")
                else:
                    # 验证JSON格式
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            json.load(f)
                            logger.info(f"  ✅ {config_path}")
                    except json.JSONDecodeError as e:
                        config_issues.append(f"配置文件格式错误: {config_path}")

            # 检查日志目录
            log_dir = os.path.join(base_dir, 'logs')
            if not os.path.exists(log_dir):
                config_issues.append("日志目录不存在")
            else:
                logger.info(f"  ✅ 日志目录存在")

        except Exception as e:
            config_issues.append(f"配置检查异常: {str(e)}")
            logger.error(f"  ❌ 检查异常: {str(e)}")

        # 计算总体状态
        elapsed_time = time.time() - start_time

        if len(config_issues) > 0:
            status = HealthStatus.UNHEALTHY
            message = f"配置文件问题: {len(config_issues)}个"
        else:
            status = HealthStatus.HEALTHY
            message = "所有配置文件正常"

        return HealthCheckResult(
            name="配置文件检查",
            status=status,
            message=message,
            response_time=round(elapsed_time, 2),
            details={
                'issues': config_issues,
                'issues_count': len(config_issues)
            }
        )

    def _check_disk_space(self) -> HealthCheckResult:
        """
        检查磁盘空间

        Returns:
            磁盘空间检查结果
        """
        logger.info("\n🔍 检查磁盘空间...")

        start_time = time.time()

        try:
            import shutil

            # 检查数据目录的磁盘使用情况
            base_dir = os.path.dirname(os.path.dirname(__file__))
            data_dir = os.path.join(base_dir, 'data')

            total, used, free = shutil.disk_usage(data_dir)

            total_gb = total / (1024**3)
            used_gb = used / (1024**3)
            free_gb = free / (1024**3)
            used_percent = (used / total) * 100

            logger.info(f"  💾 总空间: {total_gb:.2f}GB")
            logger.info(f"  💾 已使用: {used_gb:.2f}GB ({used_percent:.1f}%)")
            logger.info(f"  💾 可用: {free_gb:.2f}GB")

            # 判断状态
            if used_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"磁盘空间不足: 仅剩{free_gb:.2f}GB"
            elif used_percent > 75:
                status = HealthStatus.DEGRADED
                message = f"磁盘空间告警: 剩余{free_gb:.2f}GB"
            else:
                status = HealthStatus.HEALTHY
                message = "磁盘空间充足"

        except Exception as e:
            status = HealthStatus.UNKNOWN
            message = f"无法检查磁盘空间: {str(e)}"
            logger.error(f"  ❌ 检查异常: {str(e)}")

        elapsed_time = time.time() - start_time

        return HealthCheckResult(
            name="磁盘空间检查",
            status=status,
            message=message,
            response_time=round(elapsed_time, 2),
            details={
                'total_gb': round(total_gb, 2),
                'used_gb': round(used_gb, 2),
                'free_gb': round(free_gb, 2),
                'used_percent': round(used_percent, 1)
            }
        )

    def generate_health_report(self, results: Dict[str, any]) -> str:
        """
        生成健康检查报告（Markdown格式）

        Args:
            results: 健康检查结果

        Returns:
            Markdown格式的报告
        """
        lines = []
        lines.append("# 系统健康检查报告")
        lines.append(f"\n**检查时间**: {results['timestamp']}")
        lines.append(f"**总体状态**: {self._get_status_emoji(results['overall_status'])} {results['overall_status'].upper()}")
        lines.append(f"**总耗时**: {results.get('elapsed_time', 0):.2f}秒")

        # 总体统计
        lines.append(f"\n## 📊 总体统计")
        lines.append(f"- **总检查项**: {results['total_checks']}")
        lines.append(f"- **通过**: ✅ {results['passed_checks']}")
        lines.append(f"- **降级**: ⚠️ {results['degraded_checks']}")
        lines.append(f"- **失败**: ❌ {results['failed_checks']}")

        # 详细结果
        lines.append(f"\n## 📋 详细结果")

        for check in results['checks']:
            status_emoji = self._get_status_emoji(check['status'])
            lines.append(f"\n### {status_emoji} {check['name']}")
            lines.append(f"- **状态**: {check['status'].upper()}")
            lines.append(f"- **消息**: {check['message']}")
            lines.append(f"- **响应时间**: {check['response_time']:.2f}秒")

            # 显示详细信息
            if check.get('details'):
                details = check['details']

                # 搜索引擎详情
                if 'engines' in details:
                    lines.append(f"\n**搜索引擎状态**:")
                    for engine, info in details['engines'].items():
                        engine_status = info['status']
                        emoji = "✅" if engine_status == "healthy" else "⚠️" if engine_status == "slow" else "❌"
                        lines.append(f"- {emoji} **{engine}**: {engine_status} ({info['response_time']}s)")

                # API详情
                if 'apis' in details:
                    lines.append(f"\n**API状态**:")
                    for api, info in details['apis'].items():
                        api_status = info.get('status', 'unknown')
                        emoji = "✅" if api_status == "healthy" else "❌"
                        lines.append(f"- {emoji} **{api}**: {api_status}")

                # 问题列表
                if 'issues' in details and details['issues']:
                    lines.append(f"\n**发现的问题**:")
                    for issue in details['issues']:
                        lines.append(f"- ❌ {issue}")

                # 磁盘空间详情
                if 'total_gb' in details:
                    lines.append(f"\n**磁盘使用情况**:")
                    lines.append(f"- 总空间: {details['total_gb']}GB")
                    lines.append(f"- 已使用: {details['used_gb']}GB ({details['used_percent']}%)")
                    lines.append(f"- 可用: {details['free_gb']}GB")

        return '\n'.join(lines)

    def _get_status_emoji(self, status: str) -> str:
        """获取状态对应的emoji"""
        status_map = {
            'healthy': '✅',
            'degraded': '⚠️',
            'unhealthy': '❌',
            'unknown': '❓'
        }
        return status_map.get(status, '❓')


# ============================================================================
# 单例模式
# ============================================================================

_health_checker_instance = None
_health_checker_lock = threading.Lock()


def get_health_checker() -> HealthChecker:
    """获取健康检查器单例"""
    global _health_checker_instance
    with _health_checker_lock:
        if _health_checker_instance is None:
            _health_checker_instance = HealthChecker()
        return _health_checker_instance


# ============================================================================
# 命令行接口
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='系统健康检查')
    parser.add_argument('--output', '-o', help='输出报告文件路径（Markdown格式）')

    args = parser.parse_args()

    # 创建健康检查器
    checker = HealthChecker()

    # 运行检查
    results = checker.run_all_checks()

    # 生成报告
    report = checker.generate_health_report(results)

    # 打印报告
    print("\n" + "=" * 80)
    print("📋 健康检查报告")
    print("=" * 80)
    print(report)
    print("\n" + "=" * 80)

    # 保存报告
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ 报告已保存: {args.output}")
        print("=" * 80)

    # 返回退出码
    exit_code = 0 if results['overall_status'] in [HealthStatus.HEALTHY.value, HealthStatus.DEGRADED.value] else 1
    sys.exit(exit_code)
