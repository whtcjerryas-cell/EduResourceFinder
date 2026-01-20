#!/usr/bin/env python3
"""
LLM配置统一管理

集中管理所有LLM相关的参数配置，消除代码中的魔法数字。
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMConfig:
    """LLM调用配置"""

    # Token限制配置
    DEFAULT_MAX_TOKENS: int = 8000  # 默认最大token数（批量评估）
    SINGLE_EVALUATION_TOKENS: int = 300  # 单个结果评估
    SMALL_EVALUATION_TOKENS: int = 200  # 小型评估
    VIDEO_EVALUATION_TOKENS: int = 500  # 视频评估
    RECOMMENDATION_TOKENS_PER_RESULT: int = 150  # 推荐生成（每个结果）
    VISION_EVALUATION_TOKENS: int = 800  # 视觉评估

    # Temperature配置
    DEFAULT_TEMPERATURE: float = 0.3  # 默认温度（平衡创造性和确定性）
    DETERMINISTIC_TEMPERATURE: float = 0.0  # 高确定性（输出稳定）
    LOW_TEMPERATURE: float = 0.1  # 低温度（较确定）
    MEDIUM_TEMPERATURE: float = 0.2  # 中等温度
    CREATIVE_TEMPERATURE: float = 0.7  # 创造性温度

    # 场景化配置
    class Scenario:
        """常用场景配置"""

        # 批量结果评分
        BATCH_EVALUATION = {
            'max_tokens': 8000,
            'temperature': 0.3
        }

        # 单个结果评估
        SINGLE_EVALUATION = {
            'max_tokens': 300,
            'temperature': 0.3
        }

        # 视频内容评估
        VIDEO_EVALUATION = {
            'max_tokens': 500,
            'temperature': 0.3
        }

        # 搜索策略生成
        SEARCH_STRATEGY = {
            'max_tokens': 2000,
            'temperature': 0.2
        }

        # 搜索查询生成
        SEARCH_QUERY = {
            'max_tokens': 200,
            'temperature': 0.3
        }

        # 推荐生成
        RECOMMENDATION = {
            'max_tokens': None,  # 动态计算：150 * len(results)
            'temperature': 0.7
        }

        # 视觉评估
        VISION_EVALUATION = {
            'max_tokens': 800,
            'temperature': 0.3
        }

        # 简洁输出（高确定性）
        CONCISE_OUTPUT = {
            'max_tokens': 300,
            'temperature': 0.1
        }


# 默认配置实例
default_config = LLMConfig()


def get_llm_params(scenario: str, **overrides) -> dict:
    """
    获取指定场景的LLM参数

    Args:
        scenario: 场景名称（如 'BATCH_EVALUATION'）
        **overrides: 参数覆盖（如 max_tokens=5000）

    Returns:
        LLM参数字典

    Example:
        >>> params = get_llm_params('BATCH_EVALUATION')
        >>> params = get_llm_params('BATCH_EVALUATION', max_tokens=5000)
    """
    # 从场景类中获取配置
    config = getattr(LLMConfig.Scenario, scenario, {}).copy()

    # 应用覆盖参数
    config.update(overrides)

    # 处理None值（如RECOMMENDATION场景）
    if 'max_tokens' in config and config['max_tokens'] is None:
        config.pop('max_tokens')

    return config


def get_batch_evaluation_params(max_results: int = 10) -> dict:
    """
    获取批量评估的LLM参数

    Args:
        max_results: 最大结果数（用于动态调整token数）

    Returns:
        LLM参数字典
    """
    base_config = LLMConfig.Scenario.BATCH_EVALUATION.copy()

    # 根据结果数动态调整max_tokens
    # 每个结果约需要100 tokens（index + score + reason）
    estimated_tokens = max_results * 100
    base_config['max_tokens'] = min(
        max(estimated_tokens * 2, 1000),  # 至少1000，2倍安全余量
        default_config.DEFAULT_MAX_TOKENS  # 最多使用默认值
    )

    return base_config


def get_recommendation_params(result_count: int) -> dict:
    """
    获取推荐生成的LLM参数

    Args:
        result_count: 结果数量

    Returns:
        LLM参数字典
    """
    return {
        'max_tokens': default_config.RECOMMENDATION_TOKENS_PER_RESULT * result_count,
        'temperature': default_config.CREATIVE_TEMPERATURE
    }


@dataclass
class SearchConfig:
    """
    搜索引擎配置

    集中管理搜索引擎相关的配置参数，消除代码中的魔法数字。
    """

    # 并发配置
    MAX_PLAYLIST_WORKERS: int = 20  # 播放列表信息获取的最大并发数
    SINGLE_TIMEOUT: int = 3  # 单个播放列表获取超时（秒）
    VISUAL_TIMEOUT: int = 30  # 视觉评估超时（秒）

    # 质量阈值
    HIGH_QUALITY_THRESHOLD: float = 7.0  # 高质量阈值
    MEDIUM_QUALITY_THRESHOLD: float = 5.0  # 中等质量阈值
    LOW_QUALITY_THRESHOLD: float = 3.0  # 低质量阈值

    # 搜索结果配置
    MAX_RESULTS_TO_RETURN: int = 20  # 返回的最大结果数
    TOP_N_FOR_QUALITY_CHECK: int = 10  # 用于质量检查的Top N结果数

    # 搜索查询配置
    MAX_SEARCH_QUERIES: int = 5  # 并行搜索使用的最大查询数
    MAX_PRIORITY_DOMAINS: int = 5  # 优先域名数量


# 默认搜索配置实例
default_search_config = SearchConfig()
