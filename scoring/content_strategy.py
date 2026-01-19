#!/usr/bin/env python3
"""
内容完整性评分策略

评估内容描述的详细程度和完整性
"""

from typing import Dict, Any, Optional
from scoring.base_strategy import BaseScoringStrategy


class ContentScoringStrategy(BaseScoringStrategy):
    """
    内容完整性评分策略

    评估维度：
    1. 描述长度
    2. 内容详细程度
    3. 信息完整性
    """

    def __init__(self, weight: float = 1.0, min_length: int = 50):
        """
        初始化内容评分策略

        Args:
            weight: 策略权重
            min_length: 最小有效长度
        """
        super().__init__(name="内容完整性", weight=weight)
        self.min_length = min_length
        self.logger.info(f"✅ 内容完整性评分策略初始化: 最小长度={min_length}")

    def score(self, result: Dict[str, Any], query: str, metadata: Optional[Dict] = None) -> float:
        """
        评估内容完整性

        Args:
            result: 搜索结果
            query: 搜索查询
            metadata: 额外的元数据

        Returns:
            评分值 (0.0 - 1.0)
        """
        snippet = result.get('snippet', '')

        if not snippet:
            return 0.0

        # 根据描述长度评分
        length = len(snippet)

        if length >= 200:
            score = 1.0
            self.logger.debug(f"  ✅ 内容长度优秀: {length} 字符 (+1.0)")
        elif length >= 150:
            score = 0.8
            self.logger.debug(f"  ✅ 内容长度良好: {length} 字符 (+0.8)")
        elif length >= 100:
            score = 0.6
            self.logger.debug(f"  ✅ 内容长度中等: {length} 字符 (+0.6)")
        elif length >= self.min_length:
            score = 0.3
            self.logger.debug(f"  ⚠️ 内容长度较短: {length} 字符 (+0.3)")
        else:
            score = 0.0
            self.logger.debug(f"  ❌ 内容长度不足: {length} 字符")

        return score

    def validate_result(self, result: Dict[str, Any]) -> bool:
        """
        验证结果是否包含内容描述

        Args:
            result: 搜索结果

        Returns:
            内容是否存在
        """
        snippet = result.get('snippet', '')
        return len(snippet) >= self.min_length

    def get_length_category(self, text: str) -> str:
        """
        获取文本长度分类

        Args:
            text: 输入文本

        Returns:
            分类: 'excellent', 'good', 'medium', 'poor', 'insufficient'
        """
        if not text:
            return 'insufficient'

        length = len(text)

        if length >= 200:
            return 'excellent'
        elif length >= 150:
            return 'good'
        elif length >= 100:
            return 'medium'
        elif length >= self.min_length:
            return 'poor'
        else:
            return 'insufficient'
