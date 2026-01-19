#!/usr/bin/env python3
"""
评分策略基类

定义所有评分策略的统一接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from logger_utils import get_logger

logger = get_logger('base_strategy')


class BaseScoringStrategy(ABC):
    """
    评分策略抽象基类

    所有具体评分策略应该继承此类并实现score方法
    """

    def __init__(self, name: str, weight: float = 1.0):
        """
        初始化评分策略

        Args:
            name: 策略名称
            weight: 策略权重（用于加权总分计算）
        """
        self.name = name
        self.weight = weight
        self.logger = get_logger(f'scoring.{name}')

    @abstractmethod
    def score(self, result: Dict[str, Any], query: str, metadata: Optional[Dict] = None) -> float:
        """
        计算评分（子类必须实现）

        Args:
            result: 搜索结果字典
            query: 搜索查询
            metadata: 额外的元数据（如年级、学科等）

        Returns:
            评分值（通常在0-10之间）
        """
        pass

    def get_weighted_score(self, result: Dict[str, Any], query: str, metadata: Optional[Dict] = None) -> float:
        """
        获取加权评分

        Args:
            result: 搜索结果
            query: 搜索查询
            metadata: 额外的元数据

        Returns:
            加权后的评分值
        """
        base_score = self.score(result, query, metadata)
        return base_score * self.weight

    def validate_result(self, result: Dict[str, Any]) -> bool:
        """
        验证结果是否包含必要字段（可重写）

        Args:
            result: 搜索结果

        Returns:
            是否有效
        """
        return True  # 默认总是有效

    def normalize_score(self, score: float, min_score: float = 0.0, max_score: float = 10.0) -> float:
        """
        标准化评分到指定范围（可重写）

        Args:
            score: 原始评分
            min_score: 最小值
            max_score: 最大值

        Returns:
            标准化后的评分
        """
        return max(min_score, min(max_score, score))


class StrategyComposition:
    """
    策略组合器

    管理多个评分策略，计算综合评分
    """

    def __init__(self):
        """初始化策略组合器"""
        self.strategies: list[BaseScoringStrategy] = []
        self.logger = get_logger('strategy_composition')

    def add_strategy(self, strategy: BaseScoringStrategy):
        """
        添加评分策略

        Args:
            strategy: 评分策略实例
        """
        self.strategies.append(strategy)
        self.logger.info(f"✅ 已添加评分策略: {strategy.name} (权重: {strategy.weight})")

    def remove_strategy(self, strategy_name: str):
        """
        移除评分策略

        Args:
            strategy_name: 策略名称
        """
        self.strategies = [s for s in self.strategies if s.name != strategy_name]
        self.logger.info(f"❌ 已移除评分策略: {strategy_name}")

    def get_strategy(self, strategy_name: str) -> Optional[BaseScoringStrategy]:
        """
        获取指定策略

        Args:
            strategy_name: 策略名称

        Returns:
            策略实例（如果存在）
        """
        for strategy in self.strategies:
            if strategy.name == strategy_name:
                return strategy
        return None

    def calculate_composite_score(self, result: Dict[str, Any], query: str,
                                 metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        计算综合评分

        Args:
            result: 搜索结果
            query: 搜索查询
            metadata: 额外的元数据

        Returns:
            包含总评分和各策略分项评分的字典
            {
                'total_score': float,
                'strategy_scores': {
                    'strategy_name': float,
                    ...
                }
            }
        """
        strategy_scores = {}
        total_weighted_score = 0.0
        total_weight = 0.0

        for strategy in self.strategies:
            try:
                if strategy.validate_result(result):
                    weighted_score = strategy.get_weighted_score(result, query, metadata)
                    strategy_scores[strategy.name] = weighted_score
                    total_weighted_score += weighted_score
                    total_weight += strategy.weight
                else:
                    strategy_scores[strategy.name] = 0.0
            except Exception as e:
                self.logger.error(f"策略 {strategy.name} 评分失败: {str(e)[:200]}")
                strategy_scores[strategy.name] = 0.0

        # 计算平均加权分
        average_score = total_weighted_score / total_weight if total_weight > 0 else 0.0

        return {
            'total_score': average_score,
            'strategy_scores': strategy_scores,
            'num_strategies': len(self.strategies),
            'active_strategies': sum(1 for s in strategy_scores.values() if s > 0)
        }

    def get_all_strategies(self) -> list[str]:
        """
        获取所有策略名称

        Returns:
            策略名称列表
        """
        return [s.name for s in self.strategies]
