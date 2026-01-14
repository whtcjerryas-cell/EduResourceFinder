#!/usr/bin/env python3
"""
智能搜索优化器 - 单次搜索实时优化

实现完整的智能闭环：
- 检测问题（playlist少？质量低？）
- 自动生成优化方案
- 人工确认
- 自动调整策略
- 自动重搜
- 对比并返回更好的结果
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from copy import deepcopy

logger = logging.getLogger(__name__)


class IntelligentSearchOptimizer:
    """智能搜索优化器 - 单次搜索实时优化"""

    def __init__(self, search_engine, llm_client=None):
        """
        初始化智能搜索优化器

        Args:
            search_engine: 搜索引擎实例（用于重搜）
            llm_client: LLM客户端（可选，用于深度分析）
        """
        self.search_engine = search_engine
        self.llm_client = llm_client

        # 优化阈值配置
        self.thresholds = {
            'min_results': 5,           # 最少结果数
            'min_avg_score': 6.5,       # 最低平均分
            'min_playlist_ratio': 0.3,  # 最低播放列表比例
            'min_high_quality_ratio': 0.4  # 最低高质量比例
        }

        # 最大优化迭代次数
        self.max_optimization_rounds = 2

    def should_optimize(
        self,
        results: List[Dict[str, Any]],
        quality_report: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        判断是否需要优化

        Args:
            results: 搜索结果
            quality_report: 质量评估报告

        Returns:
            (是否需要优化, 问题列表)
        """
        if not results:
            return True, ["无搜索结果"]

        issues = []

        # 1. 结果数量不足
        if len(results) < self.thresholds['min_results']:
            issues.append(f"结果数量过少: {len(results)}个 < {self.thresholds['min_results']}个")

        # 2. 平均分过低
        avg_score = quality_report.get('basic_stats', {}).get('avg_score', 0)
        if avg_score < self.thresholds['min_avg_score']:
            issues.append(f"平均分偏低: {avg_score:.2f} < {self.thresholds['min_avg_score']}")

        # 3. 播放列表比例过低
        playlist_count = sum(1 for r in results if r.get('is_playlist', False))
        if len(results) > 0:
            playlist_ratio = playlist_count / len(results)
            if playlist_ratio < self.thresholds['min_playlist_ratio']:
                issues.append(f"播放列表比例过低: {playlist_ratio*100:.1f}% < {self.thresholds['min_playlist_ratio']*100:.1f}%")

        # 4. 高质量结果比例过低
        high_quality_count = quality_report.get('basic_stats', {}).get('high_quality_count', 0)
        if len(results) > 0:
            high_quality_ratio = high_quality_count / len(results)
            if high_quality_ratio < self.thresholds['min_high_quality_ratio']:
                issues.append(f"高质量结果比例过低: {high_quality_ratio*100:.1f}%")

        return len(issues) > 0, issues

    def generate_optimization_plans(
        self,
        results: List[Dict[str, Any]],
        quality_report: Dict[str, Any],
        search_params: Dict[str, Any],
        issues: List[str]
    ) -> List[Dict[str, Any]]:
        """
        生成优化方案

        Args:
            results: 搜索结果
            quality_report: 质量评估报告
            search_params: 搜索参数
            issues: 检测到的问题列表

        Returns:
            优化方案列表
        """
        plans = []
        plan_id = 0

        # 分析问题类型
        has_few_results = any("结果数量过少" in issue for issue in issues)
        has_low_avg_score = any("平均分偏低" in issue for issue in issues)
        has_low_playlist_ratio = any("播放列表比例过低" in issue for issue in issues)
        has_low_high_quality_ratio = any("高质量结果比例过低" in issue for issue in issues)

        # 生成优化方案

        # 方案1: 强化播放列表关键词
        if has_low_playlist_ratio:
            plan_id += 1
            plans.append({
                'plan_id': f'plan_{plan_id}',
                'name': '强化播放列表搜索',
                'description': '在搜索查询中添加"playlist"和"完整课程"关键词，提高播放列表资源覆盖率',
                'strategy': 'add_playlist_keywords',
                'modifications': {
                    'add_keywords': ['playlist', 'full course', '完整课程', 'الكامل']
                },
                'expected_improvement': '+15-25% 播放列表覆盖率',
                'risk': '低 - 仅添加关键词，不改变核心搜索逻辑'
            })

        # 方案2: 扩大搜索范围
        if has_few_results or has_low_avg_score:
            plan_id += 1
            plans.append({
                'plan_id': f'plan_{plan_id}',
                'name': '扩大搜索范围',
                'description': '放宽搜索约束，增加搜索引擎数量，提高结果数量',
                'strategy': 'expand_search_scope',
                'modifications': {
                    'increase_engines': True,
                    'relax_constraints': True
                },
                'expected_improvement': '+50-100% 结果数量',
                'risk': '中 - 可能引入部分低质量结果'
            })

        # 方案3: 提升语言匹配度
        avg_score = quality_report.get('basic_stats', {}).get('avg_score', 0)
        if has_low_avg_score and avg_score < 6.0:
            plan_id += 1
            country = search_params.get('country', '')
            plans.append({
                'plan_id': f'plan_{plan_id}',
                'name': '提升语言和地区匹配度',
                'description': f'强化{country}相关的本地化关键词，提高相关性',
                'strategy': 'enhance_language_matching',
                'modifications': {
                    'add_local_keywords': True,
                    'target_country': country
                },
                'expected_improvement': '+10-20% 相关性分数',
                'risk': '低 - 优化本地化表达'
            })

        # 方案4: 组合优化（如果多个问题同时存在）
        if len(issues) >= 2:
            plan_id += 1
            plans.append({
                'plan_id': f'plan_{plan_id}',
                'name': '组合优化方案',
                'description': '同时应用多项优化策略，全面提升搜索质量',
                'strategy': 'combined_optimization',
                'modifications': {
                    'add_playlist_keywords': has_low_playlist_ratio,
                    'expand_search_scope': has_few_results,
                    'enhance_language_matching': has_low_avg_score
                },
                'expected_improvement': '+20-30% 综合质量分数',
                'risk': '中 - 多项调整可能需要更多时间'
            })

        return plans

    def apply_optimization_strategy(
        self,
        plan: Dict[str, Any],
        original_search_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        应用优化策略到搜索参数

        Args:
            plan: 优化方案
            original_search_params: 原始搜索参数

        Returns:
            修改后的搜索参数
        """
        modified_params = deepcopy(original_search_params)
        strategy = plan['strategy']
        modifications = plan['modifications']

        # 根据策略调整参数
        if strategy == 'add_playlist_keywords':
            # 添加playlist关键词
            country = original_search_params.get('country', '')
            grade = original_search_params.get('grade', '')
            subject = original_search_params.get('subject', '')

            # 在原始查询基础上添加关键词
            modified_params['query_enhancements'] = modifications.get('add_keywords', [])

        elif strategy == 'expand_search_scope':
            # 扩大搜索范围
            modified_params['max_results'] = original_search_params.get('max_results', 10) * 1.5
            modified_params['use_additional_engines'] = True

        elif strategy == 'enhance_language_matching':
            # 提升语言匹配
            country = modifications.get('target_country', '')
            modified_params['enhance_localization'] = True
            modified_params['target_country_specific'] = country

        elif strategy == 'combined_optimization':
            # 组合优化
            if modifications.get('add_playlist_keywords'):
                modified_params['query_enhancements'] = ['playlist', 'full course', '完整课程']
            if modifications.get('expand_search_scope'):
                modified_params['max_results'] = original_search_params.get('max_results', 10) * 1.5
                modified_params['use_additional_engines'] = True
            if modifications.get('enhance_language_matching'):
                modified_params['enhance_localization'] = True

        return modified_params

    def execute_optimization(
        self,
        plan: Dict[str, Any],
        original_search_params: Dict[str, Any],
        original_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        执行优化：应用策略 → 重新搜索 → 对比结果

        Args:
            plan: 选定的优化方案
            original_search_params: 原始搜索参数
            original_results: 原始搜索结果

        Returns:
            优化执行结果
        """
        start_time = datetime.utcnow()

        try:
            # 1. 应用优化策略
            modified_params = self.apply_optimization_strategy(plan, original_search_params)

            # 2. 执行重新搜索
            logger.info(f"🔧 执行优化方案: {plan['name']}")
            logger.info(f"   修改后参数: {json.dumps(modified_params, ensure_ascii=False, indent=2)}")

            # 注意：这里需要调用搜索引擎的search方法
            # 由于search_engine_v2的接口设计，我们需要适配
            if hasattr(self.search_engine, 'search'):
                optimized_results = self.search_engine.search(
                    country=modified_params.get('country', original_search_params.get('country', '')),
                    grade=modified_params.get('grade', original_search_params.get('grade', '')),
                    subject=modified_params.get('subject', original_search_params.get('subject', '')),
                    query_enhancements=modified_params.get('query_enhancements', []),
                    max_results=int(modified_params.get('max_results', original_search_params.get('max_results', 15)))
                )
            else:
                logger.error("❌ 搜索引擎不支持search方法")
                return {
                    'success': False,
                    'error': '搜索引擎不支持search方法',
                    'plan': plan
                }

            # 3. 对比结果
            comparison = self._compare_results(
                original_results,
                optimized_results,
                plan
            )

            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()

            return {
                'success': True,
                'plan': plan,
                'execution_time_seconds': execution_time,
                'original_results_count': len(original_results),
                'optimized_results_count': len(optimized_results),
                'optimized_results': optimized_results,
                'comparison': comparison,
                'recommendation': self._generate_recommendation(comparison),
                'timestamp': end_time.isoformat() + 'Z'
            }

        except Exception as e:
            logger.error(f"❌ 优化执行失败: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'plan': plan
            }

    def _compare_results(
        self,
        original_results: List[Dict[str, Any]],
        optimized_results: List[Dict[str, Any]],
        plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        对比原始结果和优化结果

        Args:
            original_results: 原始搜索结果
            optimized_results: 优化后的搜索结果
            plan: 使用的优化方案

        Returns:
            对比报告
        """
        # 基本统计
        orig_count = len(original_results)
        opt_count = len(optimized_results)

        # 计算平均分
        orig_scores = [r.get('score', 0) for r in original_results if 'score' in r]
        opt_scores = [r.get('score', 0) for r in optimized_results if 'score' in r]

        orig_avg = sum(orig_scores) / len(orig_scores) if orig_scores else 0
        opt_avg = sum(opt_scores) / len(opt_scores) if opt_scores else 0

        # 计算播放列表数量
        orig_playlists = sum(1 for r in original_results if r.get('is_playlist', False))
        opt_playlists = sum(1 for r in optimized_results if r.get('is_playlist', False))

        # 计算高质量结果数量
        orig_high_quality = sum(1 for s in orig_scores if s >= 8.0)
        opt_high_quality = sum(1 for s in opt_scores if s >= 8.0)

        # 判断是否更好
        is_better = False
        reasons = []

        # 评分改善
        if opt_avg > orig_avg + 0.5:
            is_better = True
            reasons.append(f"平均分提升: {orig_avg:.2f} → {opt_avg:.2f}")

        # 播放列表增加
        if opt_playlists > orig_playlists:
            is_better = True
            reasons.append(f"播放列表增加: {orig_playlists} → {opt_playlists}")

        # 高质量结果增加
        if opt_high_quality > orig_high_quality:
            is_better = True
            reasons.append(f"高质量结果增加: {orig_high_quality} → {opt_high_quality}")

        # 如果没有明显改善，检查是否至少没有变差
        if not is_better:
            if opt_avg >= orig_avg - 0.3 and opt_playlists >= orig_playlists - 1:
                reasons.append("结果质量保持稳定")
            else:
                reasons.append("优化效果不明显，建议使用原始结果")

        return {
            'original': {
                'count': orig_count,
                'avg_score': round(orig_avg, 2),
                'playlist_count': orig_playlists,
                'high_quality_count': orig_high_quality
            },
            'optimized': {
                'count': opt_count,
                'avg_score': round(opt_avg, 2),
                'playlist_count': opt_playlists,
                'high_quality_count': opt_high_quality
            },
            'improvements': {
                'avg_score_diff': round(opt_avg - orig_avg, 2),
                'playlist_diff': opt_playlists - orig_playlists,
                'high_quality_diff': opt_high_quality - orig_high_quality
            },
            'is_better': is_better,
            'reasons': reasons
        }

    def _generate_recommendation(self, comparison: Dict[str, Any]) -> str:
        """
        基于对比结果生成建议

        Args:
            comparison: 对比报告

        Returns:
            推荐建议
        """
        if comparison['is_better']:
            return "✅ 建议：使用优化后的结果（质量明显提升）"
        else:
            reasons = comparison.get('reasons', [])
            if "优化效果不明显" in ' '.join(reasons):
                return "⚠️ 建议：使用原始结果（优化效果不明显）"
            else:
                return "ℹ️ 建议：使用原始结果（优化后未超过原始质量）"

    def create_optimization_request(
        self,
        results: List[Dict[str, Any]],
        quality_report: Dict[str, Any],
        search_params: Dict[str, Any],
        issues: List[str]
    ) -> Dict[str, Any]:
        """
        创建优化请求（用于人工确认）

        Args:
            results: 搜索结果
            quality_report: 质量评估报告
            search_params: 搜索参数
            issues: 检测到的问题

        Returns:
            优化请求对象
        """
        # 生成优化方案
        plans = self.generate_optimization_plans(
            results, quality_report, search_params, issues
        )

        return {
            'request_id': f"opt_req_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'detected_issues': issues,
            'quality_summary': {
                'overall_score': quality_report.get('overall_quality_score', 0),
                'quality_level': quality_report.get('quality_level', '未知'),
                'total_results': len(results),
                'avg_score': quality_report.get('basic_stats', {}).get('avg_score', 0),
                'playlist_count': sum(1 for r in results if r.get('is_playlist', False))
            },
            'search_params': search_params,
            'optimization_plans': plans,
            'status': 'pending_approval',  # pending_approval, approved, rejected, executed
            'selected_plan': None,
            'execution_result': None
        }

    def execute_approved_optimization(
        self,
        optimization_request: Dict[str, Any],
        plan_id: str,
        original_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        执行已批准的优化

        Args:
            optimization_request: 优化请求对象
            plan_id: 选定的方案ID
            original_results: 原始搜索结果

        Returns:
            更新后的优化请求对象
        """
        # 查找选定的方案
        selected_plan = None
        for plan in optimization_request['optimization_plans']:
            if plan['plan_id'] == plan_id:
                selected_plan = plan
                break

        if not selected_plan:
            logger.error(f"❌ 未找到方案: {plan_id}")
            optimization_request['status'] = 'failed'
            optimization_request['error'] = f'方案不存在: {plan_id}'
            return optimization_request

        # 更新请求状态
        optimization_request['status'] = 'approved'
        optimization_request['selected_plan'] = selected_plan

        # 执行优化
        execution_result = self.execute_optimization(
            selected_plan,
            optimization_request['search_params'],
            original_results
        )

        optimization_request['execution_result'] = execution_result

        if execution_result['success']:
            optimization_request['status'] = 'executed'
            logger.info(f"✅ 优化执行成功: {selected_plan['name']}")
        else:
            optimization_request['status'] = 'failed'
            logger.error(f"❌ 优化执行失败: {execution_result.get('error', 'Unknown error')}")

        return optimization_request


if __name__ == "__main__":
    # 测试代码
    import sys
    sys.path.append('/Users/shmiwanghao8/Desktop/education/Indonesia')

    from core.quality_evaluator import QualityEvaluator

    # 模拟搜索引擎
    class MockSearchEngine:
        def search(self, country, grade, subject, query_enhancements=None, max_results=15):
            # 模拟返回优化后的结果
            return [
                {'title': f'优化结果 {i}', 'score': 8.5, 'is_playlist': True}
                for i in range(min(10, max_results))
            ]

    # 创建优化器
    optimizer = IntelligentSearchOptimizer(
        search_engine=MockSearchEngine(),
        llm_client=None
    )

    # 测试数据
    test_results = [
        {'score': 6.2, 'title': 'Test 1', 'is_playlist': False},
        {'score': 5.8, 'title': 'Test 2', 'is_playlist': False},
        {'score': 5.1, 'title': 'Test 3', 'is_playlist': True},
        {'score': 4.9, 'title': 'Test 4', 'is_playlist': False},
    ]

    test_params = {
        'country': '伊拉克',
        'grade': '三年级',
        'subject': '数学',
        'max_results': 10
    }

    # 评估质量
    evaluator = QualityEvaluator()
    quality_report = evaluator.evaluate_single_search(test_results, test_params)

    # 判断是否需要优化
    should_opt, issues = optimizer.should_optimize(test_results, quality_report)
    print(f"\n是否需要优化: {should_opt}")
    print(f"检测到的问题: {issues}")

    if should_opt:
        # 创建优化请求
        opt_request = optimizer.create_optimization_request(
            test_results, quality_report, test_params, issues
        )

        print(f"\n优化请求:")
        print(json.dumps(opt_request, ensure_ascii=False, indent=2))

        # 模拟人工批准第一个方案
        if opt_request['optimization_plans']:
            first_plan_id = opt_request['optimization_plans'][0]['plan_id']
            print(f"\n执行方案: {first_plan_id}")

            updated_request = optimizer.execute_approved_optimization(
                opt_request, first_plan_id, test_results
            )

            print(f"\n执行结果:")
            print(json.dumps(updated_request['execution_result'], ensure_ascii=False, indent=2))
