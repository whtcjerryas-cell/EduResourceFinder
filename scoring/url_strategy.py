#!/usr/bin/env python3
"""
URL质量评分策略

评估URL的可信度、安全性和教育相关性
"""

from typing import Dict, Any, Optional
from scoring.base_strategy import BaseScoringStrategy


class URLScoringStrategy(BaseScoringStrategy):
    """
    URL质量评分策略

    评估维度：
    1. HTTPS安全性
    2. 可信教育域名
    3. 低质量域名（短链接等）
    4. 教育机构域名
    """

    def __init__(self, weight: float = 1.0, trusted_domains: Optional[Dict[str, float]] = None,
                 low_quality_domains: Optional[Dict[str, float]] = None):
        """
        初始化URL评分策略

        Args:
            weight: 策略权重
            trusted_domains: 可信域名列表 {domain: bonus_score}
            low_quality_domains: 低质量域名列表 {domain: penalty_score}
        """
        super().__init__(name="URL质量", weight=weight)

        # 默认可信域名配置
        self.trusted_domains = trusted_domains or {
            # 国际教育平台
            'khanacademy.org': 3.0,
            'coursera.org': 2.5,
            'edx.org': 2.5,
            'udemy.com': 2.0,

            # 视频平台
            'youtube.com': 2.0,
            'youtube-nocookie.com': 2.0,
            'vimeo.com': 1.5,

            # 印尼教育平台
            'kemdikbud.go.id': 3.0,
            'ruangguru.com': 2.5,
            'zenius.net': 2.5,
            'quipper.com': 2.0,
            'brainly.co.id': 1.5,

            # 俄罗斯教育平台
            'uchi.ru': 2.5,
            'znaika.ru': 2.5,
            'interneturok.ru': 2.5,
            'infourok.ru': 2.0,
            'videouroki.net': 2.0,
            'reshuege.ru': 2.0,

            # 中国教育平台
            'bilibili.com': 2.0,
            'icourse163.org': 2.5,

            # 印度教育平台
            'byju.com': 2.5,
            'vedantu.com': 2.0,
            'unacademy.com': 2.0,
        }

        # 默认低质量域名配置
        self.low_quality_domains = low_quality_domains or {
            'bit.ly': -1.0,
            'tinyurl.com': -1.0,
            'short.link': -1.0,
        }

        self.logger.info(f"✅ URL评分策略初始化: {len(self.trusted_domains)} 个可信域名, "
                        f"{len(self.low_quality_domains)} 个低质量域名")

    def score(self, result: Dict[str, Any], query: str, metadata: Optional[Dict] = None) -> float:
        """
        评估URL质量

        Args:
            result: 搜索结果
            query: 搜索查询
            metadata: 额外的元数据

        Returns:
            评分值 (0.0 - 5.0)
        """
        url = result.get('url', '')
        if not url:
            return 0.0

        score = 0.0

        # 1. HTTPS 加分 (0.3分)
        if url.startswith('https://'):
            score += 0.3

        # 2. 检查可信域名 (最多3.0分)
        for domain, bonus in self.trusted_domains.items():
            if domain in url:
                score += bonus
                self.logger.debug(f"  ✅ 可信域名: {domain} (+{bonus})")
                break

        # 3. 检查低质量域名 (最多-1.0分)
        for domain, penalty in self.low_quality_domains.items():
            if domain in url:
                score += penalty
                self.logger.warning(f"  ⚠️ 低质量域名: {domain} ({penalty})")
                break

        # 4. 检查教育域名 (0.5分)
        if '.edu' in url or '.ac.' in url or '.gov.' in url:
            score += 0.5
            self.logger.debug(f"  ✅ 教育/政府域名 (+0.5)")

        return self.normalize_score(score, 0.0, 5.0)

    def validate_result(self, result: Dict[str, Any]) -> bool:
        """
        验证结果是否包含URL

        Args:
            result: 搜索结果

        Returns:
            URL是否存在
        """
        return bool(result.get('url'))

    def add_trusted_domain(self, domain: str, bonus: float = 2.0):
        """
        添加可信域名

        Args:
            domain: 域名
            bonus: 加分值
        """
        self.trusted_domains[domain] = bonus
        self.logger.info(f"✅ 已添加可信域名: {domain} (+{bonus})")

    def add_low_quality_domain(self, domain: str, penalty: float = -1.0):
        """
        添加低质量域名

        Args:
            domain: 域名
            penalty: 减分值
        """
        self.low_quality_domains[domain] = penalty
        self.logger.warning(f"⚠️ 已添加低质量域名: {domain} ({penalty})")

    def is_trusted_domain(self, url: str) -> bool:
        """
        检查是否为可信域名

        Args:
            url: URL

        Returns:
            是否可信
        """
        return any(domain in url for domain in self.trusted_domains.keys())

    def is_low_quality_domain(self, url: str) -> bool:
        """
        检查是否为低质量域名

        Args:
            url: URL

        Returns:
            是否低质量
        """
        return any(domain in url for domain in self.low_quality_domains.keys())
