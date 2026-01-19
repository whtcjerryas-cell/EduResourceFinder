#!/usr/bin/env python3
"""
评分策略模块

使用策略模式实现各种评分维度，消除God Object问题。
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径（统一在这里设置）
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scoring.base_strategy import BaseScoringStrategy
from scoring.url_strategy import URLScoringStrategy
from scoring.title_strategy import TitleScoringStrategy
from scoring.content_strategy import ContentScoringStrategy
from scoring.source_strategy import SourceScoringStrategy
from scoring.resource_strategy import ResourceScoringStrategy
from scoring.playlist_strategy import PlaylistScoringStrategy
from scoring.language_strategy import LanguageScoringStrategy
from scoring.scorer import IntelligentResultScorer, get_result_scorer, get_result_scorer_with_kb

__all__ = [
    'BaseScoringStrategy',
    'URLScoringStrategy',
    'TitleScoringStrategy',
    'ContentScoringStrategy',
    'SourceScoringStrategy',
    'ResourceScoringStrategy',
    'PlaylistScoringStrategy',
    'LanguageScoringStrategy',
    'IntelligentResultScorer',
    'get_result_scorer',
    'get_result_scorer_with_kb'
]
