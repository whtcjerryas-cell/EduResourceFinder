#!/usr/bin/env python3
"""
搜索引擎策略模式实现

此模块实现了策略模式来简化 search() 方法的复杂度。
将搜索引擎选择逻辑封装到独立的策略类中。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path
from utils.logger_utils import get_logger

logger = get_logger(__name__)


# ========================================
# 1. 定义搜索上下文
# ========================================

@dataclass
class SearchContext:
    """
    搜索上下文（包含使用量统计）

    Attributes:
        google_remaining: Google 剩余免费额度
        metaso_remaining: Metaso 剩余免费额度
        tavily_remaining: Tavily 剩余免费额度
        baidu_remaining: Baidu 剩余免费额度
    """
    google_remaining: int
    metaso_remaining: int
    tavily_remaining: int
    baidu_remaining: int

    def is_available(self, engine_name: str) -> bool:
        """
        检查搜索引擎是否可用

        Args:
            engine_name: 搜索引擎名称 ('google', 'metaso', 'tavily', 'baidu')

        Returns:
            True 如果额度 > 0
        """
        return getattr(self, f"{engine_name}_remaining", 0) > 0


# ========================================
# 2. 定义策略接口
# ========================================

class SearchStrategy(ABC):
    """搜索引擎策略接口"""

    @abstractmethod
    def can_handle(self, query: str, context: SearchContext) -> bool:
        """
        判断是否可以处理此查询

        Args:
            query: 搜索查询
            context: 搜索上下文

        Returns:
            True 如果此策略可以处理该查询
        """
        pass

    @abstractmethod
    def search(self, client, query: str, max_results: int,
               include_domains: Optional[List[str]] = None,
               country_code: str = "CN") -> List[Dict[str, Any]]:
        """
        执行搜索

        Args:
            client: UnifiedLLMClient 实例
            query: 搜索查询
            max_results: 最大结果数
            include_domains: 包含的域名列表
            country_code: 国家代码

        Returns:
            搜索结果列表
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass

    @property
    def priority(self) -> int:
        """策略优先级（数字越小优先级越高）"""
        pass


# ========================================
# 3. 实现具体策略
# ========================================

class ChineseGoogleStrategy(SearchStrategy):
    """
    中文内容优先使用 Google 搜索

    优先级: 1（最高）
    语言: 中文
    搜索引擎: Google
    """

    def can_handle(self, query: str, context: SearchContext) -> bool:
        """中文内容且 Google 可用时使用"""
        is_chinese = any('\u4e00' <= c <= '\u9fff' for c in query)
        return is_chinese and context.is_available('google')

    def search(self, client, query: str, max_results: int,
               include_domains: Optional[List[str]] = None,
               country_code: str = "CN") -> List[Dict[str, Any]]:
        """执行 Google 搜索"""
        return client._search_with_google(
            query, max_results, country_code,
            reason=f"中文内容（Google优先，剩余免费: {context.google_remaining:,}）"
        )

    @property
    def name(self) -> str:
        return "中文Google搜索"

    @property
    def priority(self) -> int:
        return 1


class ChineseMetasoStrategy(SearchStrategy):
    """
    中文内容备用 Metaso 搜索

    优先级: 2
    语言: 中文
    搜索引擎: Metaso
    """

    def can_handle(self, query: str, context: SearchContext) -> bool:
        """中文内容且 Metaso 可用时使用"""
        is_chinese = any('\u4e00' <= c <= '\u9fff' for c in query)
        return is_chinese and context.is_available('metaso')

    def search(self, client, query: str, max_results: int,
               include_domains: Optional[List[str]] = None,
               country_code: str = "CN") -> List[Dict[str, Any]]:
        """执行 Metaso 搜索"""
        return client._search_with_metaso(
            query, max_results, include_domains,
            reason=f"中文内容（剩余免费: {context.metaso_remaining:,}）"
        )

    @property
    def name(self) -> str:
        return "中文Metaso搜索"

    @property
    def priority(self) -> int:
        return 2


class ChineseBaiduStrategy(SearchStrategy):
    """
    中文内容备用 Baidu 搜索

    优先级: 3
    语言: 中文
    搜索引擎: Baidu
    """

    def can_handle(self, query: str, context: SearchContext) -> bool:
        """中文内容且 Baidu 可用时使用"""
        is_chinese = any('\u4e00' <= c <= '\u9fff' for c in query)
        return is_chinese and context.is_available('baidu')

    def search(self, client, query: str, max_results: int,
               include_domains: Optional[List[str]] = None,
               country_code: str = "CN") -> List[Dict[str, Any]]:
        """执行 Baidu 搜索"""
        return client._search_with_baidu(
            query, max_results,
            reason=f"中文内容（剩余免费: {context.baidu_remaining:,}）"
        )

    @property
    def name(self) -> str:
        return "中文Baidu搜索"

    @property
    def priority(self) -> int:
        return 3


class EnglishGoogleStrategy(SearchStrategy):
    """
    英语内容优先使用 Google 搜索

    优先级: 1
    语言: 英语
    搜索引擎: Google
    """

    def can_handle(self, query: str, context: SearchContext) -> bool:
        """英语内容且 Google 可用时使用"""
        if not query:
            return False
        english_chars = sum(1 for c in query if c.isalpha() and c.isascii())
        total_chars = sum(1 for c in query if c.isalpha())
        is_english = total_chars > 0 and (english_chars / total_chars) > 0.7
        return is_english and context.is_available('google')

    def search(self, client, query: str, max_results: int,
               include_domains: Optional[List[str]] = None,
               country_code: str = "CN") -> List[Dict[str, Any]]:
        """执行 Google 搜索"""
        return client._search_with_google(
            query, max_results, country_code,
            reason=f"英语内容（Google优先，剩余免费: {context.google_remaining:,}）"
        )

    @property
    def name(self) -> str:
        return "英语Google搜索"

    @property
    def priority(self) -> int:
        return 1


class EnglishMetasoStrategy(SearchStrategy):
    """
    英语内容备用 Metaso 搜索

    优先级: 2
    语言: 英语
    搜索引擎: Metaso
    """

    def can_handle(self, query: str, context: SearchContext) -> bool:
        """英语内容且 Metaso 可用时使用"""
        if not query:
            return False
        english_chars = sum(1 for c in query if c.isalpha() and c.isascii())
        total_chars = sum(1 for c in query if c.isalpha())
        is_english = total_chars > 0 and (english_chars / total_chars) > 0.7
        return is_english and context.is_available('metaso')

    def search(self, client, query: str, max_results: int,
               include_domains: Optional[List[str]] = None,
               country_code: str = "CN") -> List[Dict[str, Any]]:
        """执行 Metaso 搜索"""
        return client._search_with_metaso(
            query, max_results, include_domains,
            reason=f"英语内容（剩余免费: {context.metaso_remaining:,}）"
        )

    @property
    def name(self) -> str:
        return "英语Metaso搜索"

    @property
    def priority(self) -> int:
        return 2


class DefaultGoogleStrategy(SearchStrategy):
    """
    默认使用 Google 搜索（适用于非中英语）

    优先级: 1
    语言: 其他
    搜索引擎: Google
    """

    def can_handle(self, query: str, context: SearchContext) -> bool:
        """总是优先尝试 Google"""
        return context.is_available('google')

    def search(self, client, query: str, max_results: int,
               include_domains: Optional[List[str]] = None,
               country_code: str = "CN") -> List[Dict[str, Any]]:
        """执行 Google 搜索"""
        return client._search_with_google(
            query, max_results, country_code,
            reason=f"非英语内容（Google优先，剩余免费: {context.google_remaining:,}）"
        )

    @property
    def name(self) -> str:
        return "默认Google搜索"

    @property
    def priority(self) -> int:
        return 1


class DefaultTavilyStrategy(SearchStrategy):
    """
    默认使用 Tavily 搜索（适用于非中英语）

    优先级: 2
    语言: 其他
    搜索引擎: Tavily
    """

    def can_handle(self, query: str, context: SearchContext) -> bool:
        """总是可用（作为后备）"""
        return True  # 总是可用作为最后的选择

    def search(self, client, query: str, max_results: int,
               include_domains: Optional[List[str]] = None,
               country_code: str = "CN") -> List[Dict[str, Any]]:
        """执行 Tavily 搜索"""
        return client._search_with_tavily(
            query, max_results, include_domains,
            reason=f"非英语内容（Tavily优先，剩余免费: {context.tavily_remaining:,}）"
        )

    @property
    def name(self) -> str:
        return "Tavily搜索（默认）"

    @property
    def priority(self) -> int:
        return 10  # 最低优先级


class FallbackTavilyStrategy(SearchStrategy):
    """
    Tavily 作为后备策略（当其他引擎失败时使用）

    优先级: 99（最低）
    搜索引擎: Tavily
    """

    def can_handle(self, query: str, context: SearchContext) -> bool:
        """总是可用（作为后备）"""
        return True

    def search(self, client, query: str, max_results: int,
               include_domains: Optional[List[str]] = None,
               country_code: str = "CN") -> List[Dict[str, Any]]:
        """执行 Tavily 搜索"""
        return client._search_with_tavily(
            query, max_results, include_domains,
            reason="其他引擎额度用尽"
        )

    @property
    def name(self) -> str:
        return "Tavily搜索（后备）"

    @property
    def priority(self) -> int:
        return 99


# ========================================
# 4. 实现搜索引擎编排器
# ========================================

class SearchOrchestrator:
    """
    搜索引擎编排器

    使用策略模式管理多个搜索引擎策略，
    根据查询内容和可用额度自动选择最合适的搜索引擎。
    """

    def __init__(self):
        """初始化编排器，定义策略优先级"""
        self.strategies = [
            # 中文策略（优先级 1-3）
            ChineseGoogleStrategy(),
            ChineseMetasoStrategy(),
            ChineseBaiduStrategy(),
            # 英语策略（优先级 1-2）
            EnglishGoogleStrategy(),
            EnglishMetasoStrategy(),
            # 默认策略（优先级 1-99）
            DefaultGoogleStrategy(),
            DefaultTavilyStrategy(),
            # 后备策略（优先级 99）
            FallbackTavilyStrategy(),
        ]

        # 按优先级排序
        self.strategies.sort(key=lambda s: s.priority)

    def search(self, client, query: str, max_results: int = 20,
               include_domains: Optional[List[str]] = None,
               country_code: str = "CN",
               context: Optional[SearchContext] = None) -> List[Dict[str, Any]]:
        """
        使用策略模式执行搜索

        Args:
            client: UnifiedLLMClient 实例
            query: 搜索查询
            max_results: 最大结果数
            include_domains: 包含的域名列表
            country_code: 国家代码
            context: 搜索上下文（如果为 None 则自动创建）

        Returns:
            搜索结果列表

        Raises:
            ValueError: 所有搜索引擎都失败
        """
        # 创建默认上下文（如果未提供）
        if context is None:
            context = SearchContext(
                google_remaining=10000 - client.google_usage if client.google_hunter else 0,
                metaso_remaining=5000 - client.metaso_client.usage_count if client.metaso_client else 0,
                tavily_remaining=1000 - client.tavily_usage,
                baidu_remaining=100 - client.baidu_usage if client.baidu_hunter else 0
            )

        # 遍历策略，找到第一个可以处理的
        for strategy in self.strategies:
            if strategy.can_handle(query, context):
                logger.info(f"搜索策略] 使用: {strategy.name}")

                try:
                    results = strategy.search(client, query, max_results, include_domains, country_code)

                    if results:
                        logger.info(f"搜索成功] {strategy.name} 返回 {len(results)} 个结果")
                        return results
                    else:
                        logger.warning(f"搜索无结果] {strategy.name} 未返回结果，尝试下一个策略")
                        continue

                except Exception as e:
                    logger.error(f"搜索失败] {strategy.name}: {str(e)}，尝试下一个策略")
                    continue

        # 所有策略都失败
        logger.error("所有搜索策略失败]")
        return []
