#!/usr/bin/env python3
"""
来源可信度评分策略

评估资源来源的可信度和权威性
"""

from typing import Dict, Any, Optional
from urllib.parse import urlparse
from scoring.base_strategy import BaseScoringStrategy


class SourceScoringStrategy(BaseScoringStrategy):
    """
    来源可信度评分策略

    评估维度：
    1. 官方教育平台
    2. 教育机构域名
    3. 政府网站
    4. 视频平台
    """

    # 官方教育平台（最高可信度）
    OFFICIAL_EDUCATION_PLATFORMS = [
        'khanacademy.org',
        'kemdikbud.go.id',
        'moe.gov',
        'education.gov',
    ]

    # 知名教育平台（高可信度）
    REPUTABLE_EDUCATION_PLATFORMS = [
        'ruangguru',
        'zenius',
        'uchi.ru',
        'byju',
        'coursera.org',
        'edx.org',
        'udemy.com',
    ]

    def __init__(self, weight: float = 1.5):
        """
        初始化来源可信度评分策略

        Args:
            weight: 策略权重（默认1.5）
        """
        super().__init__(name="来源可信度", weight=weight)
        self.logger.info("✅ 来源可信度评分策略初始化")

    def score(self, result: Dict[str, Any], query: str, metadata: Optional[Dict] = None) -> float:
        """
        评估来源可信度

        Args:
            result: 搜索结果
            query: 搜索查询
            metadata: 额外的元数据

        Returns:
            评分值 (0.0 - 2.0)
        """
        url = result.get('url', '')

        if not url:
            return 0.0

        score = 0.0

        try:
            domain = urlparse(url).netloc.lower()

            # 1. 官方教育平台 (2.0分)
            if any(platform in domain for platform in self.OFFICIAL_EDUCATION_PLATFORMS):
                score = 2.0
                self.logger.debug(f"  ✅ 官方教育平台: {domain} (+2.0)")
                return score

            # 2. 知名教育平台 (1.8分)
            if any(platform in domain for platform in self.REPUTABLE_EDUCATION_PLATFORMS):
                score = 1.8
                self.logger.debug(f"  ✅ 知名教育平台: {domain} (+1.8)")
                return score

            # 3. 教育机构域名 (1.5分)
            if '.edu' in domain:
                score = 1.5
                self.logger.debug(f"  ✅ 教育机构: {domain} (+1.5)")
                return score

            # 4. 政府网站 (1.5分)
            if '.gov.' in domain:
                score = 1.5
                self.logger.debug(f"  ✅ 政府网站: {domain} (+1.5)")
                return score

            # 5. YouTube视频 (1.0分)
            if 'youtube.com' in domain:
                score = 1.0
                self.logger.debug(f"  ⚠️ YouTube: {domain} (+1.0)")
                return score

            # 6. 其他来源 (0.5分)
            score = 0.5
            self.logger.debug(f"  ℹ️ 其他来源: {domain} (+0.5)")

        except Exception as e:
            self.logger.error(f"  ❌ 解析URL失败: {str(e)[:100]}")
            score = 0.0

        return score

    def validate_result(self, result: Dict[str, Any]) -> bool:
        """
        验证结果是否包含URL

        Args:
            result: 搜索结果

        Returns:
            URL是否存在
        """
        return bool(result.get('url'))

    def get_credibility_level(self, url: str) -> str:
        """
        获取URL的可信度级别

        Args:
            url: URL

        Returns:
            级别: 'official', 'reputable', 'educational', 'government', 'video', 'other'
        """
        if not url:
            return 'none'

        try:
            domain = urlparse(url).netloc.lower()

            if any(platform in domain for platform in self.OFFICIAL_EDUCATION_PLATFORMS):
                return 'official'
            elif any(platform in domain for platform in self.REPUTABLE_EDUCATION_PLATFORMS):
                return 'reputable'
            elif '.edu' in domain:
                return 'educational'
            elif '.gov.' in domain:
                return 'government'
            elif 'youtube.com' in domain:
                return 'video'
            else:
                return 'other'
        except Exception:
            return 'none'
