#!/usr/bin/env python3
"""
资源类型评分策略

评估资源类型（视频、播放列表、教育内容等）的匹配度
"""

from typing import Dict, Any, Optional
from scoring.base_strategy import BaseScoringStrategy


class ResourceScoringStrategy(BaseScoringStrategy):
    """
    资源类型评分策略

    评估维度：
    1. 视频资源识别
    2. 教育内容关键词
    3. 资源类型匹配度
    """

    def __init__(self, weight: float = 1.0):
        """
        初始化资源类型评分策略

        Args:
            weight: 策略权重
        """
        super().__init__(name="资源类型", weight=weight)

        # 视频相关关键词
        self.video_keywords = [
            'video', 'youtube', 'watch', 'vimeo',
            '视频', '影片',
            'видео',  # 俄语
            'video',  # 印尼语
        ]

        # 教育关键词（加分）
        self.educational_keywords = [
            'lesson', 'tutorial', 'course', 'lecture', 'education',
            'learn', 'study', 'school', 'class', 'teacher',
            '课程', '教程', '学习', '教学', '课程',
            'урок', 'обучение', 'лекция',  # 俄语
            'pelajaran', 'pembelajaran', 'belajar',  # 印尼语
        ]

        self.logger.info(f"✅ 资源类型评分策略初始化: {len(self.video_keywords)} 个视频关键词, "
                        f"{len(self.educational_keywords)} 个教育关键词")

    def score(self, result: Dict[str, Any], query: str, metadata: Optional[Dict] = None) -> float:
        """
        评估资源类型匹配度

        Args:
            result: 搜索结果
            query: 搜索查询
            metadata: 额外的元数据

        Returns:
            评分值 (0.0 - 1.5)
        """
        url = result.get('url', '')
        title = result.get('title', '')
        snippet = result.get('snippet', '')

        score = 0.0
        combined = f"{url} {title} {snippet}".lower()

        # 1. 视频资源加分 (0-0.5分)
        for keyword in self.video_keywords:
            if keyword in combined:
                score += 0.5
                self.logger.debug(f"  ✅ 视频资源: {keyword} (+0.5)")
                break

        # 2. 教育内容加分 (0-1.0分)
        matches = sum(1 for kw in self.educational_keywords if kw in combined)

        if matches >= 3:
            score += 1.0
            self.logger.debug(f"  ✅ 高教育相关: {matches} 个关键词 (+1.0)")
        elif matches >= 2:
            score += 0.5
            self.logger.debug(f"  ✅ 中教育相关: {matches} 个关键词 (+0.5)")
        elif matches >= 1:
            score += 0.2
            self.logger.debug(f"  ✅ 低教育相关: {matches} 个关键词 (+0.2)")

        return score

    def validate_result(self, result: Dict[str, Any]) -> bool:
        """
        验证结果是否包含基本字段

        Args:
            result: 搜索结果

        Returns:
            是否有效
        """
        return bool(result.get('url') or result.get('title'))

    def is_video_resource(self, result: Dict[str, Any]) -> bool:
        """
        判断是否为视频资源

        Args:
            result: 搜索结果

        Returns:
            是否为视频资源
        """
        url = result.get('url', '')
        title = result.get('title', '')
        combined = f"{url} {title}".lower()

        return any(kw in combined for kw in self.video_keywords)

    def is_educational_content(self, result: Dict[str, Any]) -> bool:
        """
        判断是否为教育内容

        Args:
            result: 搜索结果

        Returns:
            是否为教育内容
        """
        title = result.get('title', '')
        snippet = result.get('snippet', '')
        combined = f"{title} {snippet}".lower()

        matches = sum(1 for kw in self.educational_keywords if kw in combined)
        return matches >= 1

    def get_educational_score(self, result: Dict[str, Any]) -> float:
        """
        获取教育内容评分

        Args:
            result: 搜索结果

        Returns:
            教育评分 (0.0 - 1.0)
        """
        title = result.get('title', '')
        snippet = result.get('snippet', '')
        combined = f"{title} {snippet}".lower()

        matches = sum(1 for kw in self.educational_keywords if kw in combined)

        if matches >= 3:
            return 1.0
        elif matches >= 2:
            return 0.5
        elif matches >= 1:
            return 0.2
        else:
            return 0.0
