#!/usr/bin/env python3
"""
标题相关性评分策略

评估标题与搜索查询的相关性
"""

from typing import Dict, Any, Optional
from scoring.base_strategy import BaseScoringStrategy


class TitleScoringStrategy(BaseScoringStrategy):
    """
    标题相关性评分策略

    评估维度：
    1. 查询完全匹配
    2. 关键词重叠度
    3. 年级和学科匹配
    """

    def __init__(self, weight: float = 2.0):
        """
        初始化标题评分策略

        Args:
            weight: 策略权重（默认2.0，因为标题相关性最重要）
        """
        super().__init__(name="标题相关性", weight=weight)

        # 年级关键词
        self.grade_keywords = [
            'grade', 'kelas', '年级', 'class', 'primary',
            'secondary', 'elementary', 'middle', 'high'
        ]

        # 学科关键词
        self.subject_keywords = [
            'math', 'science', 'english', 'arabic', '数学', '科学',
            'physics', 'chemistry', 'biology', 'history', 'geography',
            '物理', '化学', '生物', '历史', '地理'
        ]

        self.logger.info(f"✅ 标题相关性评分策略初始化: {len(self.grade_keywords)} 个年级关键词, "
                        f"{len(self.subject_keywords)} 个学科关键词")

    def score(self, result: Dict[str, Any], query: str, metadata: Optional[Dict] = None) -> float:
        """
        评估标题相关性

        Args:
            result: 搜索结果
            query: 搜索查询
            metadata: 额外的元数据

        Returns:
            评分值 (0.0 - 3.0)
        """
        title = result.get('title', '')
        snippet = result.get('snippet', '')

        if not title or not query:
            return 0.0

        score = 0.0
        query_lower = query.lower()
        combined = f"{title} {snippet}".lower()

        # 1. 完全匹配查询 (0-1.5分)
        if query_lower in combined:
            score += 1.5
            self.logger.debug(f"  ✅ 查询完全匹配 (+1.5)")

        # 2. 关键词匹配度 (0-1.0分)
        query_words = set(query_lower.split())
        combined_words = set(combined.split())
        overlap = len(query_words & combined_words)

        if overlap >= 3:
            score += 1.0
            self.logger.debug(f"  ✅ 高关键词重叠: {overlap} 个 (+1.0)")
        elif overlap >= 2:
            score += 0.7
            self.logger.debug(f"  ✅ 中关键词重叠: {overlap} 个 (+0.7)")
        elif overlap >= 1:
            score += 0.4
            self.logger.debug(f"  ✅ 低关键词重叠: {overlap} 个 (+0.4)")

        # 3. 年级和学科匹配 (0-0.5分)
        has_grade = any(kw in combined for kw in self.grade_keywords)
        has_subject = any(kw in combined for kw in self.subject_keywords)

        if has_grade and has_subject:
            score += 0.5
            self.logger.debug(f"  ✅ 年级和学科匹配 (+0.5)")
        elif has_grade or has_subject:
            score += 0.2
            self.logger.debug(f"  ✅ 年级或学科匹配 (+0.2)")

        return min(score, 3.0)

    def validate_result(self, result: Dict[str, Any]) -> bool:
        """
        验证结果是否包含标题

        Args:
            result: 搜索结果

        Returns:
            标题是否存在
        """
        return bool(result.get('title'))

    def extract_keywords(self, text: str) -> set[str]:
        """
        提取文本中的关键词

        Args:
            text: 输入文本

        Returns:
            关键词集合
        """
        if not text:
            return set()

        words = text.lower().split()
        return set(word for word in words if len(word) > 2)

    def calculate_overlap_ratio(self, text1: str, text2: str) -> float:
        """
        计算两个文本的关键词重叠率

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            重叠率 (0.0 - 1.0)
        """
        keywords1 = self.extract_keywords(text1)
        keywords2 = self.extract_keywords(text2)

        if not keywords1 or not keywords2:
            return 0.0

        overlap = len(keywords1 & keywords2)
        total = len(keywords1 | keywords2)

        return overlap / total if total > 0 else 0.0
