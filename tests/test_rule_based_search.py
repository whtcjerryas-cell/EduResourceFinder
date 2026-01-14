"""
测试规则搜索引擎

基于Kieran的评审要求，添加边界测试用例
"""

import pytest
import yaml
from pathlib import Path
from core.rule_based_search import (
    RuleBasedSearchEngine,
    ConfigError
)


class TestRuleBasedSearchEngine:
    """测试规则搜索引擎"""

    @pytest.fixture
    def config_path(self, tmp_path):
        """创建临时配置文件"""
        config_file = tmp_path / "test_config.yaml"
        config_data = {
            'ID': {
                'grade_1': {
                    'math': {
                        'localized_terms': {
                            'grade': 'SD Kelas 1',
                            'subject': 'Matematika',
                            'curriculum': 'Kurikulum Merdeka'
                        },
                        'queries': [
                            'Matematika SD Kelas 1'
                        ],
                        'trusted_domains': {
                            'ruangguru.com': 9.5,
                            'youtube.com': 7.5
                        }
                    }
                }
            },
            'DEFAULT': {
                'grade_1': {
                    'math': {
                        'localized_terms': {
                            'grade': 'Grade 1',
                            'subject': 'Mathematics',
                            'curriculum': 'National Curriculum'
                        },
                        'queries': ['Grade 1 Mathematics'],
                        'trusted_domains': {
                            'youtube.com': 7.5
                        }
                    }
                }
            }
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)

        return str(config_file)

    @pytest.fixture
    def engine(self, config_path):
        """创建搜索引擎实例"""
        return RuleBasedSearchEngine(config_path=config_path)

    def test_indonesia_grade_1_math(self, engine):
        """测试印尼一年级数学搜索"""
        # Mock search engine
        class MockSearchEngine:
            def search(self, query, country):
                return [
                    {'url': 'https://ruangguru.com/math1', 'title': 'Ruangguru Math'},
                    {'url': 'https://youtube.com/math1', 'title': 'YouTube Math'},
                ]

        engine.search_engine = MockSearchEngine()

        result = engine.search(
            country='ID',
            grade='1',
            subject='math',
            max_results=10
        )

        # 验证
        assert result['localized_info']['supported'] == True
        assert result['localized_info']['grade'] == 'SD Kelas 1'
        assert result['localized_info']['subject'] == 'Matematika'
        assert len(result['results']) == 2
        assert result['results'][0]['score'] >= 7.0  # 至少是中等质量

    def test_config_file_not_found(self):
        """测试配置文件不存在"""
        with pytest.raises(ConfigError) as exc_info:
            RuleBasedSearchEngine(config_path="nonexistent.yaml")

        assert "not found" in str(exc_info.value).lower()

    def test_malformed_yaml(self, tmp_path):
        """测试格式错误的YAML"""
        config_file = tmp_path / "malformed.yaml"

        with open(config_file, 'w') as f:
            f.write("invalid: yaml: content:\n  - broken")

        with pytest.raises(ConfigError) as exc_info:
            RuleBasedSearchEngine(config_path=str(config_file))

        assert "parse" in str(exc_info.value).lower() or "format" in str(exc_info.value).lower()

    def test_empty_yaml(self, tmp_path):
        """测试空配置文件"""
        config_file = tmp_path / "empty.yaml"

        with open(config_file, 'w') as f:
            f.write("")

        with pytest.raises(ConfigError) as exc_info:
            RuleBasedSearchEngine(config_path=str(config_file))

        assert "empty" in str(exc_info.value).lower()

    def test_missing_required_fields(self, tmp_path):
        """测试缺少必需字段"""
        config_file = tmp_path / "incomplete.yaml"
        config_data = {
            'ID': {
                'grade_1': {
                    'math': {
                        # 缺少 'queries' 字段
                        'trusted_domains': {}
                    }
                }
            }
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        # Mock search engine
        class MockSearchEngine:
            def search(self, query, country):
                return [{'url': 'https://youtube.com/math', 'title': 'Math'}]

        engine = RuleBasedSearchEngine(config_path=str(config_file))
        engine.search_engine = MockSearchEngine()

        result = engine.search('ID', '1', 'math')

        # 应该返回错误结果
        assert result['localized_info']['supported'] == False
        assert 'Configuration error' in result['localized_info'].get('error', '')

    def test_query_template_with_invalid_placeholder(self, engine):
        """测试查询模板有无效占位符"""
        # 修改配置，添加无效占位符
        engine.config['ID']['grade_1']['math']['queries'] = [
            '{subject} {invalid_placeholder}'
        ]

        # 应该跳过无效模板，但不崩溃
        queries = engine._generate_queries(
            engine.config['ID']['grade_1']['math']['queries'],
            'SD Kelas 1',
            'Matematika',
            'Kurikulum Merdeka'
        )

        # 应该返回空列表（因为模板无效）
        assert len(queries) == 0

    def test_grade_normalization(self, engine):
        """测试年级标准化"""
        grades = ['1', 'Grade 1', '一年级']

        for grade in grades:
            normalized = engine._normalize_grade(grade, 'ID')
            assert normalized == '1'

    def test_subject_normalization(self, engine):
        """测试学科标准化"""
        subjects = ['math', 'Mathematics', '数学', 'Matematika']

        for subject in subjects:
            normalized = engine._normalize_subject(subject, 'ID')
            assert normalized == 'math'

    def test_deduplication(self, engine):
        """测试去重"""
        results = [
            {'url': 'https://example.com/1'},
            {'url': 'https://example.com/1'},  # 重复
            {'url': 'https://example.com/2'},
            {'url': 'https://example.com/2?foo=bar'},  # 同域不同参数
        ]

        unique = engine._deduplicate_results(results)

        assert len(unique) == 3  # 2个不同URL + 1个带参数的
        assert unique[0]['url'] == 'https://example.com/1'
        assert unique[1]['url'] == 'https://example.com/2'

    def test_scoring(self, engine):
        """测试评分"""
        results = [
            {'url': 'https://ruangguru.com/math1'},
            {'url': 'https://unknown.com/math1'},
        ]

        trusted_domains = {
            'ruangguru.com': 9.5
        }

        scored = engine._score_results(results, trusted_domains)

        assert scored[0]['score'] == 9.5
        assert scored[1]['score'] == 5.0  # 默认分数

    def test_domain_scoring_with_subdomain(self, engine):
        """测试子域名评分（如m.youtube.com）"""
        results = [
            {'url': 'https://www.youtube.com/math1'},
            {'url': 'https://m.youtube.com/math2'},
            {'url': 'https://youtube.com/math3'},
        ]

        trusted_domains = {
            'youtube.com': 7.5
        }

        scored = engine._score_results(results, trusted_domains)

        # 所有YouTube子域名都应该得分
        assert all(r['score'] == 7.5 for r in scored)

    def test_unsupported_country_falls_back_to_default(self, engine):
        """测试不支持的国家使用DEFAULT配置"""
        # Mock search engine
        class MockSearchEngine:
            def search(self, query, country):
                return [{'url': 'https://youtube.com/math', 'title': 'Math'}]

        engine.search_engine = MockSearchEngine()

        result = engine.search(
            country='ZZ',  # 不存在的国家
            grade='1',
            subject='math'
        )

        # 应该使用DEFAULT配置
        assert result['localized_info']['supported'] == True
        assert result['localized_info']['grade'] == 'Grade 1'
        assert result['localized_info']['subject'] == 'Mathematics'

    def test_config_structure_validation_queries_type(self, engine):
        """测试配置结构验证 - queries必须是list"""
        config = {
            'queries': 'not_a_list',  # 错误：应该是list
            'trusted_domains': {}
        }

        with pytest.raises(ConfigError) as exc_info:
            engine._validate_config(config, 'ID', '1', 'math')

        assert 'list' in str(exc_info.value).lower()

    def test_config_structure_validation_domains_type(self, engine):
        """测试配置结构验证 - trusted_domains必须是dict"""
        config = {
            'queries': [],
            'trusted_domains': 'not_a_dict'  # 错误：应该是dict
        }

        with pytest.raises(ConfigError) as exc_info:
            engine._validate_config(config, 'ID', '1', 'math')

        assert 'dict' in str(exc_info.value).lower()

    def test_scoring_results_sorted(self, engine):
        """测试评分结果按分数降序排列"""
        results = [
            {'url': 'https://low.com'},
            {'url': 'https://high.com'},
            {'url': 'https://medium.com'},
        ]

        trusted_domains = {
            'high.com': 9.0,
            'medium.com': 7.0,
            'low.com': 5.0
        }

        scored = engine._score_results(results, trusted_domains)

        # 验证降序排列
        scores = [r['score'] for r in scored]
        assert scores == sorted(scores, reverse=True)
        assert scored[0]['url'] == 'https://high.com'
