#!/usr/bin/env python3
"""
播放列表评分策略

评估播放列表和完整课程的额外价值
"""

from typing import Dict, Any, Optional
from scoring.base_strategy import BaseScoringStrategy


class PlaylistScoringStrategy(BaseScoringStrategy):
    """
    播放列表评分策略

    评估维度：
    1. 明确的播放列表URL
    2. 完整课程关键词
    3. 播放列表关键词
    4. 播放列表丰富度
    """

    def __init__(self, weight: float = 1.0):
        """
        初始化播放列表评分策略

        Args:
            weight: 策略权重
        """
        super().__init__(name="播放列表", weight=weight)

        # 播放列表URL指示器
        self.playlist_url_indicators = [
            'playlist?',
            'list=',
            '/videos'
        ]

        # 完整课程关键词
        self.complete_keywords = [
            'complete course', 'full course', 'all lessons',
            'كامل', 'شامل', 'دورة كاملة',  # 阿拉伯语
            '完整', '全套', '全部',
            'lengkap', 'daftar putar lengkap',  # 印尼语
            'полный курс', 'все уроки',  # 俄语
        ]

        # 播放列表关键词
        self.playlist_keywords = [
            'playlist', 'series', 'collection',
            'قائمة التشغيل', 'سلسلة',  # 阿拉伯语
            '播放列表', '系列',
            'daftar putar', 'seri',  # 印尼语
            'плейлист', 'серия',  # 俄语
        ]

        self.logger.info(f"✅ 播放列表评分策略初始化: {len(self.playlist_url_indicators)} 个URL指示器, "
                        f"{len(self.complete_keywords)} 个完整关键词, {len(self.playlist_keywords)} 个播放列表关键词")

    def score(self, result: Dict[str, Any], query: str, metadata: Optional[Dict] = None) -> float:
        """
        评估播放列表价值

        Args:
            result: 搜索结果
            query: 搜索查询
            metadata: 额外的元数据

        Returns:
            评分值 (0.0 - 1.0)
        """
        url = result.get('url', '')
        title = result.get('title', '')
        snippet = result.get('snippet', '')

        combined = f"{url} {title} {snippet}".lower()

        # 1. 明确的播放列表URL（最高分）
        if any(indicator in url.lower() for indicator in self.playlist_url_indicators):
            self.logger.debug(f"  ✅ 明确的播放列表URL (+1.0)")
            return 1.0

        # 2. 标题包含完整课程关键词
        if any(kw in combined for kw in self.complete_keywords):
            self.logger.debug(f"  ✅ 完整课程关键词 (+0.8)")
            return 0.8

        # 3. 标题包含播放列表关键词
        if any(kw in combined for kw in self.playlist_keywords):
            self.logger.debug(f"  ✅ 播放列表关键词 (+0.5)")
            return 0.5

        return 0.0

    def score_playlist_richness(self, playlist_info: Dict[str, Any]) -> float:
        """
        评估播放列表丰富度

        Args:
            playlist_info: 播放列表信息

        Returns:
            丰富度评分 (0.0 - 2.0)
        """
        if not playlist_info:
            return 0.0

        score = 0.0

        # 1. 视频数量评分 (0-1.0分)
        video_count = playlist_info.get('video_count', 0)
        if video_count >= 50:
            score += 1.0
            self.logger.debug(f"  ✅ 播放列表视频数: {video_count} (+1.0)")
        elif video_count >= 20:
            score += 0.7
            self.logger.debug(f"  ✅ 播放列表视频数: {video_count} (+0.7)")
        elif video_count >= 10:
            score += 0.4
            self.logger.debug(f"  ✅ 播放列表视频数: {video_count} (+0.4)")

        # 2. 有描述/元数据 (0-1.0分)
        has_title = bool(playlist_info.get('title'))
        has_description = bool(playlist_info.get('description'))
        has_author = bool(playlist_info.get('author'))

        metadata_score = sum([has_title, has_description, has_author]) / 3.0

        if metadata_score > 0:
            score += metadata_score
            self.logger.debug(f"  ✅ 播放列表元数据完整度: {metadata_score:.1%} (+{metadata_score:.1f})")

        return score

    def validate_result(self, result: Dict[str, Any]) -> bool:
        """
        验证结果是否包含必要字段

        Args:
            result: 搜索结果

        Returns:
            是否有效
        """
        return bool(result.get('url') or result.get('title'))

    def is_playlist(self, result: Dict[str, Any]) -> bool:
        """
        判断是否为播放列表

        Args:
            result: 搜索结果

        Returns:
            是否为播放列表
        """
        url = result.get('url', '')
        title = result.get('title', '')
        combined = f"{url} {title}".lower()

        # 检查URL指示器
        if any(indicator in url.lower() for indicator in self.playlist_url_indicators):
            return True

        # 检查关键词
        if any(kw in combined for kw in self.complete_keywords + self.playlist_keywords):
            return True

        return False

    def is_complete_course(self, result: Dict[str, Any]) -> bool:
        """
        判断是否为完整课程

        Args:
            result: 搜索结果

        Returns:
            是否为完整课程
        """
        url = result.get('url', '')
        title = result.get('title', '')
        snippet = result.get('snippet', '')
        combined = f"{url} {title} {snippet}".lower()

        return any(kw in combined for kw in self.complete_keywords)
