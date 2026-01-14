#!/usr/bin/env python3
"""
搜索质量评估Agent

功能:
- 单次搜索质量评估（0-100分）
- 批量质量评估（趋势分析）
- 异常检测
- 优化建议生成
"""

import json
import os
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path


class QualityEvaluator:
    """搜索质量评估器"""

    def __init__(self, llm_client=None):
        """
        初始化质量评估器

        Args:
            llm_client: LLM客户端（用于深度分析）
        """
        self.llm_client = llm_client

        # 质量阈值配置
        self.quality_thresholds = {
            "excellent": 8.5,  # 优秀
            "good": 7.0,       # 良好
            "acceptable": 5.5, # 合格
            "poor": 0.0        # 差
        }

    def evaluate_single_search(
        self,
        results: List[Dict[str, Any]],
        search_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        评估单次搜索的质量

        Args:
            results: 搜索结果列表（包含score等字段）
            search_params: 搜索参数（country, grade, subject等）

        Returns:
            质量评估报告
        """
        if not results:
            return {
                "overall_quality_score": 0,
                "quality_level": "无结果",
                "basic_stats": {
                    "total_results": 0,
                    "avg_score": 0,
                    "high_quality_count": 0,
                    "low_quality_count": 0
                },
                "anomalies": [
                    {
                        "type": "no_results",
                        "severity": "critical",
                        "description": "搜索未返回任何结果",
                        "suggestion": "检查搜索引擎配置和网络连接"
                    }
                ],
                "optimization_suggestions": []
            }

        # 提取分数
        scores = [r.get('score', 0) for r in results if 'score' in r]

        if not scores:
            return {
                "overall_quality_score": 0,
                "quality_level": "无分数",
                "basic_stats": {
                    "total_results": len(results),
                    "avg_score": 0,
                    "high_quality_count": 0,
                    "low_quality_count": 0
                },
                "anomalies": [
                    {
                        "type": "no_scores",
                        "severity": "high",
                        "description": "搜索结果缺少质量分数",
                        "suggestion": "确保评分系统正常运行"
                    }
                ],
                "optimization_suggestions": []
            }

        # 基本统计
        avg_score = statistics.mean(scores)
        median_score = statistics.median(scores)
        std_dev = statistics.stdev(scores) if len(scores) > 1 else 0

        # 质量分布
        high_quality_count = sum(1 for s in scores if s >= 8.0)
        medium_quality_count = sum(1 for s in scores if 6.0 <= s < 8.0)
        low_quality_count = sum(1 for s in scores if s < 6.0)

        # 计算总体质量分数（0-100）
        # 权重: 平均分(60%) + 高质量比例(20%) + 中位数(20%)
        high_quality_ratio = high_quality_count / len(scores)
        overall_score = (avg_score * 0.6 + high_quality_ratio * 15 + median_score * 0.25) * 10

        # 确保分数在0-100范围内
        overall_score = max(0, min(100, overall_score))

        # 质量等级
        quality_level = self._get_quality_level(avg_score)

        # 异常检测
        anomalies = self._detect_anomalies(
            scores, avg_score, results, search_params
        )

        # 生成优化建议
        optimization_suggestions = self._generate_optimization_suggestions(
            avg_score, high_quality_count, low_quality_count, results, anomalies
        )

        return {
            "overall_quality_score": round(overall_score, 1),
            "quality_level": quality_level,
            "basic_stats": {
                "total_results": len(results),
                "avg_score": round(avg_score, 2),
                "median_score": round(median_score, 2),
                "std_dev": round(std_dev, 2),
                "high_quality_count": high_quality_count,
                "medium_quality_count": medium_quality_count,
                "low_quality_count": low_quality_count,
                "min_score": round(min(scores), 2),
                "max_score": round(max(scores), 2)
            },
            "quality_distribution": {
                "high_quality_ratio": round(high_quality_count / len(scores), 2),
                "medium_quality_ratio": round(medium_quality_count / len(scores), 2),
                "low_quality_ratio": round(low_quality_count / len(scores), 2)
            },
            "anomalies": anomalies,
            "optimization_suggestions": optimization_suggestions,
            "search_params": search_params,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def evaluate_batch_quality(
        self,
        search_history_file: str = None,
        days: int = 1
    ) -> Dict[str, Any]:
        """
        批量评估搜索质量（用于优化循环）

        Args:
            search_history_file: 搜索历史文件路径
            days: 评估最近N天

        Returns:
            批量质量报告
        """
        if search_history_file is None:
            # 使用默认路径
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            search_history_file = os.path.join(base_dir, "data", "search_history.jsonl")

        if not os.path.exists(search_history_file):
            return {
                "error": "搜索历史文件不存在",
                "file": search_history_file
            }

        cutoff_time = datetime.utcnow() - timedelta(days=days)

        # 读取搜索历史
        search_records = []
        with open(search_history_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                    if timestamp >= cutoff_time:
                        search_records.append(record)

        if not search_records:
            return {
                "period_days": days,
                "total_searches": 0,
                "message": f"最近{days}天没有搜索记录"
            }

        # 评估每次搜索
        quality_reports = []
        for record in search_records:
            results = record.get('results', [])
            search_params = record.get('search_params', {})
            report = self.evaluate_single_search(results, search_params)
            quality_reports.append(report)

        # 汇总统计
        overall_scores = [r['overall_quality_score'] for r in quality_reports]
        avg_quality_score = statistics.mean(overall_scores)

        # 趋势分析
        trend = self._analyze_trend(quality_reports)

        return {
            "period_days": days,
            "total_searches": len(search_records),
            "avg_quality_score": round(avg_quality_score, 1),
            "quality_trend": trend,
            "quality_distribution": self._get_batch_quality_distribution(quality_reports),
            "top_issues": self._get_top_issues(quality_reports),
            "recommendation": self._generate_batch_recommendation(avg_quality_score, trend),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def _get_quality_level(self, avg_score: float) -> str:
        """获取质量等级"""
        if avg_score >= self.quality_thresholds['excellent']:
            return "优秀"
        elif avg_score >= self.quality_thresholds['good']:
            return "良好"
        elif avg_score >= self.quality_thresholds['acceptable']:
            return "合格"
        else:
            return "差"

    def _detect_anomalies(
        self,
        scores: List[float],
        avg_score: float,
        results: List[Dict],
        search_params: Dict
    ) -> List[Dict[str, Any]]:
        """检测异常情况"""
        anomalies = []

        # 1. 平均分过低
        if avg_score < 5.0:
            anomalies.append({
                "type": "low_avg_score",
                "severity": "high",
                "description": f"平均分数偏低: {avg_score:.2f}",
                "suggestion": "检查搜索引擎选择和提示词配置"
            })

        # 2. 结果过少
        if len(results) < 5:
            anomalies.append({
                "type": "too_few_results",
                "severity": "medium",
                "description": f"结果数量较少: {len(results)}个",
                "suggestion": "考虑调整搜索策略或增加搜索引擎"
            })

        # 3. 低质量结果过多
        low_quality_ratio = sum(1 for s in scores if s < 6.0) / len(scores)
        if low_quality_ratio > 0.5:
            anomalies.append({
                "type": "high_low_quality_ratio",
                "severity": "high",
                "description": f"低质量结果比例过高: {low_quality_ratio*100:.1f}%",
                "suggestion": "建议优化LLM提示词以提高相关性识别"
            })

        # 4. 标准差过大（结果质量不稳定）
        if len(scores) > 1:
            std_dev = statistics.stdev(scores)
            if std_dev > 3.0:
                anomalies.append({
                    "type": "high_variance",
                    "severity": "medium",
                    "description": f"结果质量波动较大（标准差: {std_dev:.2f}）",
                    "suggestion": "可能存在搜索引擎配置问题"
                })

        return anomalies

    def _generate_optimization_suggestions(
        self,
        avg_score: float,
        high_quality_count: int,
        low_quality_count: int,
        results: List[Dict],
        anomalies: List[Dict]
    ) -> List[str]:
        """生成优化建议"""
        suggestions = []

        # 基于基本统计的建议
        if high_quality_count < 3:
            suggestions.append("高质量结果数量较少，建议优化LLM提示词以提高相关性识别")

        if low_quality_count > len(results) * 0.3:
            suggestions.append("低质量结果比例较高，建议调整评分权重配置")

        # 检查播放列表资源
        playlist_count = sum(1 for r in results if r.get('is_playlist', False))
        if playlist_count < len(results) * 0.5:
            suggestions.append("播放列表资源较少，建议在搜索查询中强化'playlist'关键词")

        # 基于异常的建议
        for anomaly in anomalies:
            suggestion = anomaly.get('suggestion')
            if suggestion and suggestion not in suggestions:
                suggestions.append(suggestion)

        return suggestions

    def _analyze_trend(self, quality_reports: List[Dict]) -> str:
        """分析质量趋势"""
        if len(quality_reports) < 2:
            return "数据不足"

        # 简单趋势分析：比较前半部分和后半部分
        mid = len(quality_reports) // 2
        first_half_avg = statistics.mean(
            [r['overall_quality_score'] for r in quality_reports[:mid]]
        )
        second_half_avg = statistics.mean(
            [r['overall_quality_score'] for r in quality_reports[mid:]]
        )

        diff = second_half_avg - first_half_avg
        if diff > 2.0:
            return "提升"
        elif diff < -2.0:
            return "下降"
        else:
            return "稳定"

    def _get_batch_quality_distribution(self, quality_reports: List[Dict]) -> Dict:
        """获取批量质量分布"""
        levels = {"优秀": 0, "良好": 0, "合格": 0, "差": 0}
        for report in quality_reports:
            level = report.get('quality_level', '合格')
            if level in levels:
                levels[level] += 1

        total = len(quality_reports)
        return {
            level: round(count / total, 2)
            for level, count in levels.items()
        }

    def _get_top_issues(self, quality_reports: List[Dict]) -> List[str]:
        """获取最常见的问题"""
        issue_count = {}

        for report in quality_reports:
            for anomaly in report.get('anomalies', []):
                issue_type = anomaly['type']
                issue_count[issue_type] = issue_count.get(issue_type, 0) + 1

        # 排序并返回前3个
        sorted_issues = sorted(issue_count.items(), key=lambda x: x[1], reverse=True)
        return [issue for issue, count in sorted_issues[:3]]

    def _generate_batch_recommendation(
        self,
        avg_quality_score: float,
        trend: str
    ) -> str:
        """生成批量优化建议"""
        if avg_quality_score >= 75:
            return "系统运行良好，无需立即优化"
        elif avg_quality_score >= 60:
            if trend == "下降":
                return "质量有所下降，建议分析低质量案例并优化提示词"
            else:
                return "系统运行尚可，可以继续监控"
        else:
            return "质量偏低，强烈建议运行优化循环"


if __name__ == "__main__":
    # 测试代码
    evaluator = QualityEvaluator()

    # 测试单次搜索评估
    test_results = [
        {"score": 8.5, "title": "Test 1", "is_playlist": True},
        {"score": 7.2, "title": "Test 2", "is_playlist": True},
        {"score": 6.1, "title": "Test 3", "is_playlist": False},
        {"score": 5.5, "title": "Test 4", "is_playlist": False},
        {"score": 4.2, "title": "Test 5", "is_playlist": False},
    ]

    test_params = {
        "country": "伊拉克",
        "grade": "三年级",
        "subject": "数学"
    }

    report = evaluator.evaluate_single_search(test_results, test_params)
    print("单次搜索质量评估报告:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
