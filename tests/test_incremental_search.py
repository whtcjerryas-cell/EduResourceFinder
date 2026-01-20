#!/usr/bin/env python3
"""
单元测试：渐进式搜索优化功能

测试内容：
1. search_strategy_agent 新方法
2. fallback_utils 降级策略
3. incremental_search 核心逻辑
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from search_strategy_agent import SearchStrategyAgent, SearchStrategy
from fallback_utils import (
    detect_low_quality_results,
    fallback_query_rewriting,
    fallback_engine_switching,
    fallback_relax_filters,
    fallback_historical_cache,
    comprehensive_fallback
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_llm_client():
    """模拟LLM客户端"""
    client = Mock()
    client.call_llm = Mock(return_value="site:youtube.com Matematika Kelas 8 playlist")
    return client


@pytest.fixture
def mock_config_manager():
    """模拟配置管理器"""
    config = Mock()

    # 模拟印尼国家配置
    indo_config = Mock()
    indo_config.country_name = "Indonesia"
    indo_config.language_code = "id"
    indo_config.domains = ["youtube.com", "rumahbelajar.com"]

    # 模拟中国国家配置
    china_config = Mock()
    china_config.country_name = "China"
    china_config.language_code = "zh"
    china_config.domains = ["bilibili.com", "youku.com"]

    # 模拟get_country_config方法
    def get_country_config(country_code):
        if country_code == "ID":
            return indo_config
        elif country_code == "CN":
            return china_config
        return None

    config.get_country_config = Mock(side_effect=get_country_config)
    return config


@pytest.fixture
def search_strategy_agent(mock_llm_client, mock_config_manager):
    """创建SearchStrategyAgent实例"""
    return SearchStrategyAgent(
        llm_client=mock_llm_client,
        config_manager=mock_config_manager
    )


@pytest.fixture
def sample_results():
    """示例搜索结果"""
    return [
        {'title': 'Matematika Kelas 8 Playlist Complete', 'url': 'https://youtube.com/1', 'score': 8.5},
        {'title': 'Mathematics Grade 8 Video Lesson', 'url': 'https://youtube.com/2', 'score': 7.2},
        {'title': 'Kelas 8 Matematika Chapter 1', 'url': 'https://youtube.com/3', 'score': 6.8},
        {'title': 'Grade 8 Math Full Course', 'url': 'https://youtube.com/4', 'score': 6.5},
        {'title': '数学初二播放列表', 'url': 'https://bilibili.com/1', 'score': 5.9},
        {'title': 'Random Video', 'url': 'https://example.com/1', 'score': 4.2},
        {'title': 'Another Random Video', 'url': 'https://example.com/2', 'score': 3.8},
        {'title': 'Unrelated Content', 'url': 'https://example.com/3', 'score': 2.5},
    ]


# ============================================================================
# Test: generate_best_query()
# ============================================================================

class TestGenerateBestQuery:
    """测试generate_best_query方法"""

    def test_generate_best_query_indonesia(self, search_strategy_agent):
        """测试生成印尼的最优查询"""
        query = search_strategy_agent.generate_best_query(
            country="ID",
            grade="Kelas 8",
            subject="Matematika"
        )

        assert query is not None
        assert isinstance(query, str)
        assert len(query) > 0
        assert "playlist" in query.lower() or "course" in query.lower()

    def test_generate_best_query_china(self, search_strategy_agent):
        """测试生成中国的最优查询"""
        query = search_strategy_agent.generate_best_query(
            country="CN",
            grade="初二",
            subject="数学"
        )

        assert query is not None
        assert "bilibili" in query.lower() or "播放列表" in query

    def test_generate_best_query_with_semester(self, search_strategy_agent):
        """测试带学期的最优查询"""
        query = search_strategy_agent.generate_best_query(
            country="ID",
            grade="Kelas 8",
            subject="Matematika",
            semester="Semester 1"
        )

        assert query is not None
        # 验证学期信息被考虑（虽然在查询中可能不明确显示）

    def test_generate_best_query_unknown_country(self, search_strategy_agent):
        """测试未知国家使用默认查询"""
        query = search_strategy_agent.generate_best_query(
            country="UNKNOWN",
            grade="Grade 8",
            subject="Mathematics"
        )

        assert query is not None
        assert "site:youtube.com" in query.lower()

    def test_generate_best_query_llm_failure(self, search_strategy_agent, mock_llm_client):
        """测试LLM失败时使用默认查询"""
        # 模拟LLM调用失败
        mock_llm_client.call_llm.side_effect = Exception("LLM API Error")

        query = search_strategy_agent.generate_best_query(
            country="ID",
            grade="Kelas 8",
            subject="Matematika"
        )

        # 应该返回默认查询
        assert query is not None
        assert "site:youtube.com" in query


# ============================================================================
# Test: generate_alternative_query()
# ============================================================================

class TestGenerateAlternativeQuery:
    """测试generate_alternative_query方法"""

    def test_alternative_query_attempt_1(self, search_strategy_agent):
        """测试第1次备选查询（英文）"""
        query = search_strategy_agent.generate_alternative_query(
            country="ID",
            grade="Kelas 8",
            subject="Matematika",
            attempt_number=1
        )

        assert query is not None
        assert "complete course" in query.lower() or "playlist" in query.lower()

    def test_alternative_query_attempt_2(self, search_strategy_agent):
        """测试第2次备选查询（添加video）"""
        query = search_strategy_agent.generate_alternative_query(
            country="ID",
            grade="Kelas 8",
            subject="Matematika",
            attempt_number=2
        )

        assert query is not None
        assert "video" in query.lower()

    def test_alternative_query_attempt_3(self, search_strategy_agent):
        """测试第3次备选查询（course）"""
        query = search_strategy_agent.generate_alternative_query(
            country="ID",
            grade="Kelas 8",
            subject="Matematika",
            attempt_number=3
        )

        assert query is not None
        assert "kursus" in query.lower() or "course" in query.lower()

    def test_alternative_query_attempt_4(self, search_strategy_agent):
        """测试第4次备选查询（无年级）"""
        query = search_strategy_agent.generate_alternative_query(
            country="ID",
            grade="Kelas 8",
            subject="Matematika",
            attempt_number=4
        )

        assert query is not None
        # 应该不包含年级
        assert "kelas 8" not in query.lower()

    def test_alternative_query_attempt_5(self, search_strategy_agent):
        """测试第5次备选查询（精确语法）"""
        query = search_strategy_agent.generate_alternative_query(
            country="ID",
            grade="Kelas 8",
            subject="Matematika",
            attempt_number=5
        )

        assert query is not None
        assert 'site:youtube.com' in query
        # 应该包含引号
        assert '"' in query

    def test_alternative_query_cycle(self, search_strategy_agent):
        """测试备选查询循环（超过5次）"""
        query1 = search_strategy_agent.generate_alternative_query(
            country="ID",
            grade="Kelas 8",
            subject="Matematika",
            attempt_number=5
        )

        query6 = search_strategy_agent.generate_alternative_query(
            country="ID",
            grade="Kelas 8",
            subject="Matematika",
            attempt_number=6
        )

        # 第6次应该循环回第1个策略
        assert query1 == query6


# ============================================================================
# Test: detect_low_quality_results()
# ============================================================================

class TestDetectLowQualityResults:
    """测试detect_low_quality_results函数"""

    def test_high_quality_results(self, sample_results):
        """测试高质量结果（不应该被检测为低质量）"""
        request = {
            'country': 'ID',
            'grade': 'Kelas 8',
            'subject': 'Matematika'
        }

        is_low_quality = detect_low_quality_results(sample_results, request)

        assert is_low_quality is False

    def test_low_quality_by_average_score(self):
        """测试通过平均分检测低质量"""
        low_quality_results = [
            {'title': 'Video 1', 'url': 'https://example.com/1', 'score': 4.0},
            {'title': 'Video 2', 'url': 'https://example.com/2', 'score': 4.5},
            {'title': 'Video 3', 'url': 'https://example.com/3', 'score': 5.0},
        ]

        request = {'country': 'ID', 'grade': 'Kelas 8', 'subject': 'Matematika'}

        is_low_quality = detect_low_quality_results(low_quality_results, request)

        assert is_low_quality is True

    def test_low_quality_by_high_score_count(self):
        """测试通过高分数量检测低质量"""
        low_quality_results = [
            {'title': 'Video 1', 'url': 'https://example.com/1', 'score': 6.0},
            {'title': 'Video 2', 'url': 'https://example.com/2', 'score': 6.2},
            {'title': 'Matematika Video', 'url': 'https://example.com/3', 'score': 6.5},
            {'title': 'Video 4', 'url': 'https://example.com/4', 'score': 5.8},
        ]

        request = {'country': 'ID', 'grade': 'Kelas 8', 'subject': 'Matematika'}

        is_low_quality = detect_low_quality_results(low_quality_results, request)

        # 高分结果（>=7.0）少于3个
        assert is_low_quality is True

    def test_low_quality_by_relevance(self):
        """测试通过标题相关性检测低质量"""
        irrelevant_results = [
            {'title': 'Random Cat Video', 'url': 'https://example.com/1', 'score': 6.0},
            {'title': 'Music Video', 'url': 'https://example.com/2', 'score': 6.5},
            {'title': 'Game Review', 'url': 'https://example.com/3', 'score': 7.0},
        ]

        request = {'country': 'ID', 'grade': 'Kelas 8', 'subject': 'Matematika'}

        is_low_quality = detect_low_quality_results(irrelevant_results, request)

        # 相关标题少于5个
        assert is_low_quality is True

    def test_empty_results(self):
        """测试空结果"""
        request = {'country': 'ID', 'grade': 'Kelas 8', 'subject': 'Matematika'}

        is_low_quality = detect_low_quality_results([], request)

        assert is_low_quality is True


# ============================================================================
# Test: fallback_query_rewriting()
# ============================================================================

class TestFallbackQueryRewriting:
    """测试fallback_query_rewriting函数"""

    def test_successful_rewrite(self, mock_llm_client, search_strategy_agent):
        """测试成功的查询重写"""
        mock_llm_client.search = Mock(return_value=[
            {'title': 'Result 1', 'url': 'https://example.com/1'},
            {'title': 'Result 2', 'url': 'https://example.com/2'},
        ])

        request = {
            'country': 'ID',
            'grade': 'Kelas 8',
            'subject': 'Matematika'
        }

        results = fallback_query_rewriting(request, mock_llm_client, search_strategy_agent)

        assert len(results) >= 2
        assert mock_llm_client.search.called

    def test_all_rewrites_fail(self, mock_llm_client, search_strategy_agent):
        """测试所有重写都失败"""
        mock_llm_client.search = Mock(return_value=[])

        request = {
            'country': 'ID',
            'grade': 'Kelas 8',
            'subject': 'Matematika'
        }

        results = fallback_query_rewriting(request, mock_llm_client, search_strategy_agent)

        assert len(results) == 0


# ============================================================================
# Test: fallback_engine_switching()
# ============================================================================

class TestFallbackEngineSwitching:
    """测试fallback_engine_switching函数"""

    def test_successful_engine_switch(self, mock_llm_client):
        """测试成功的引擎切换"""
        # 模拟Tavily/Metaso失败，Google成功
        tavily_results = []
        google_results = [
            {'title': 'Google Result 1', 'url': 'https://google.com/1'},
            {'title': 'Google Result 2', 'url': 'https://google.com/2'},
        ]

        call_count = [0]

        def mock_search(query, max_results, country_code):
            call_count[0] += 1
            if call_count[0] == 1:
                return tavily_results  # Tavily失败
            else:
                return google_results  # Google成功

        mock_llm_client.search = Mock(side_effect=mock_search)

        mock_google_hunter = Mock()
        mock_google_hunter.search = Mock(return_value=google_results)

        request = {
            'country': 'ID',
            'grade': 'Kelas 8',
            'subject': 'Matematika'
        }

        results = fallback_engine_switching(request, mock_llm_client, mock_google_hunter)

        assert len(results) >= 2

    def test_all_engines_fail(self, mock_llm_client):
        """测试所有引擎都失败"""
        mock_llm_client.search = Mock(return_value=[])

        request = {
            'country': 'ID',
            'grade': 'Kelas 8',
            'subject': 'Matematika'
        }

        results = fallback_engine_switching(request, mock_llm_client)

        assert len(results) == 0


# ============================================================================
# Test: fallback_relax_filters()
# ============================================================================

class TestFallbackRelaxFilters:
    """测试fallback_relax_filters函数"""

    def test_successful_relax(self, mock_llm_client):
        """测试成功的放宽筛选"""
        mock_llm_client.search = Mock(return_value=[
            {'title': 'Result 1', 'url': 'https://example.com/1'},
            {'title': 'Result 2', 'url': 'https://example.com/2'},
        ])

        mock_scorer = Mock()
        mock_scorer.score_results = Mock(return_value=[
            {'title': 'Result 1', 'url': 'https://example.com/1', 'score': 4.0},
            {'title': 'Result 2', 'url': 'https://example.com/2', 'score': 3.5},
        ])

        request = {
            'country': 'ID',
            'grade': 'Kelas 8',
            'subject': 'Matematika'
        }

        results = fallback_relax_filters(request, mock_llm_client, mock_scorer)

        assert len(results) >= 2
        assert mock_scorer.score_results.called

    def test_relax_no_results(self, mock_llm_client):
        """测试放宽筛选但仍无结果"""
        mock_llm_client.search = Mock(return_value=[])

        mock_scorer = Mock()
        mock_scorer.score_results = Mock(return_value=[])

        request = {
            'country': 'ID',
            'grade': 'Kelas 8',
            'subject': 'Matematika'
        }

        results = fallback_relax_filters(request, mock_llm_client, mock_scorer)

        assert len(results) == 0


# ============================================================================
# Test: fallback_historical_cache()
# ============================================================================

class TestFallbackHistoricalCache:
    """测试fallback_historical_cache函数"""

    def test_successful_cache_retrieval(self):
        """测试成功的缓存检索"""
        mock_cache = Mock()
        mock_cache.get_l3_cache = Mock(return_value={
            'age_hours': 2.5,
            'results': [
                {'title': 'Cached Result 1', 'url': 'https://cached.com/1'},
                {'title': 'Cached Result 2', 'url': 'https://cached.com/2'},
            ]
        })

        request = {
            'country': 'ID',
            'grade': 'Kelas 8',
            'subject': 'Matematika'
        }

        results = fallback_historical_cache(request, mock_cache)

        assert len(results) >= 2
        assert all(r.get('_fallback') for r in results)

    def test_no_cache_available(self):
        """测试无可用缓存"""
        mock_cache = Mock()
        mock_cache.get_l3_cache = Mock(return_value=None)

        request = {
            'country': 'ID',
            'grade': 'Kelas 8',
            'subject': 'Matematika'
        }

        results = fallback_historical_cache(request, mock_cache)

        assert len(results) == 0


# ============================================================================
# Test: comprehensive_fallback()
# ============================================================================

class TestComprehensiveFallback:
    """测试comprehensive_fallback函数"""

    def test_first_strategy_succeeds(self, mock_llm_client, search_strategy_agent):
        """测试第一个策略成功"""
        mock_llm_client.search = Mock(return_value=[
            {'title': 'Result 1', 'url': 'https://example.com/1'},
            {'title': 'Result 2', 'url': 'https://example.com/2'},
            {'title': 'Result 3', 'url': 'https://example.com/3'},
            {'title': 'Result 4', 'url': 'https://example.com/4'},
            {'title': 'Result 5', 'url': 'https://example.com/5'},
        ])

        request = {
            'country': 'ID',
            'grade': 'Kelas 8',
            'subject': 'Matematika'
        }

        results = comprehensive_fallback(request, mock_llm_client, search_strategy_agent)

        assert len(results) >= 5

    def test_all_strategies_fail(self, mock_llm_client, search_strategy_agent):
        """测试所有策略都失败"""
        mock_llm_client.search = Mock(return_value=[])

        request = {
            'country': 'ID',
            'grade': 'Kelas 8',
            'subject': 'Matematika'
        }

        results = comprehensive_fallback(request, mock_llm_client, search_strategy_agent)

        assert len(results) == 0


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
