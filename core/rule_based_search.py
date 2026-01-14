"""
基于规则的多国教育资源搜索引擎

简单、可靠、生产就绪
"""

import yaml
import logging
from typing import Dict, List, Optional, TypedDict
from pathlib import Path
from dataclasses import dataclass

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """配置错误"""
    pass


@dataclass
class LocalizedTerms:
    """本地化术语"""
    grade: str
    subject: str
    curriculum: str


@dataclass
class GradeSubjectConfig:
    """年级学科配置"""
    localized_terms: LocalizedTerms
    queries: List[str]
    trusted_domains: Dict[str, float]


class SearchResult(TypedDict):
    """搜索结果"""
    url: str
    title: str
    snippet: str
    score: float
    score_reason: str


class LocalizedInfo(TypedDict):
    """本地化信息"""
    country: str
    grade: str
    subject: str
    curriculum: str
    supported: bool


class SearchMetadata(TypedDict):
    """搜索元数据"""
    queries_used: List[str]
    total_found: int
    top_score: float
    search_method: str


class SearchResponse(TypedDict):
    """搜索响应"""
    results: List[SearchResult]
    localized_info: LocalizedInfo
    search_metadata: SearchMetadata


class RuleBasedSearchEngine:
    """基于规则的教育搜索引擎"""

    # 默认分数
    DEFAULT_SCORE = 5.0

    def __init__(self, config_path: str = "config/country_search_config.yaml"):
        """初始化搜索引擎

        Args:
            config_path: 配置文件路径

        Raises:
            ConfigError: 配置文件缺失或无效
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()

        # 延迟加载search_engine（避免循环导入）
        self.search_engine = None

        logger.info(
            "RuleBasedSearchEngine initialized",
            extra={
                "config_path": str(config_path),
                "supported_countries": list(self.config.keys())
            }
        )

    def _load_config(self) -> Dict:
        """加载配置文件

        Returns:
            配置字典

        Raises:
            ConfigError: 配置文件不存在或格式错误
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if not config:
                raise ConfigError(f"Config file is empty: {self.config_path}")

            # 验证必要结构
            if 'DEFAULT' not in config:
                logger.warning("DEFAULT configuration missing")

            return config

        except FileNotFoundError:
            raise ConfigError(f"Config file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ConfigError(f"Failed to parse config: {e}")

    def _get_search_engine(self):
        """延迟加载搜索引擎"""
        if self.search_engine is None:
            # 注意：规则搜索引擎本身不需要外部搜索引擎
            # search_engine 属性由外部注入（如在web_app.py中设置）
            # 这里只是为了兼容性保留
            logger.warning("No external search engine provided, using mock results")
            self.search_engine = MockSearchEngine()

    def search(
        self,
        country: str,
        grade: str,
        subject: str,
        max_results: int = 20
    ) -> SearchResponse:
        """执行搜索

        Args:
            country: 国家代码（ID, SA, CN, US等）
            grade: 年级（1, 2, 3... 或 Grade 1, 一年级）
            subject: 学科（math, 数学, Mathematics等）
            max_results: 返回结果数

        Returns:
            SearchResponse字典

        Raises:
            ConfigError: 配置无效
        """
        logger.info(f"Search started: {country} - {grade} - {subject}")

        # 延迟加载搜索引擎
        if self.search_engine is None:
            self._get_search_engine()

        # 步骤1：获取配置
        try:
            country_config = self._get_country_config(country)
        except ConfigError as e:
            logger.error(f"Config error: {e}")
            return self._empty_result(f"Configuration error: {e}")

        # 标准化年级和学科
        normalized_grade = self._normalize_grade(grade, country)
        normalized_subject = self._normalize_subject(subject, country)

        grade_subject_config = country_config.get(
            f"grade_{normalized_grade}", {}
        ).get(normalized_subject, {})

        if not grade_subject_config:
            logger.warning(f"No config for {country}-{normalized_grade}-{normalized_subject}")
            return self._empty_result(
                f"Not configured: {country} - {normalized_grade} - {normalized_subject}"
            )

        # 验证配置结构
        try:
            self._validate_config(grade_subject_config, country, normalized_grade, normalized_subject)
        except ConfigError as e:
            logger.error(f"Config validation failed: {e}")
            return self._empty_result(f"Configuration error: {e}")

        # 步骤2：生成查询
        localized_terms_dict = grade_subject_config['localized_terms']
        localized_terms = LocalizedTerms(
            grade=localized_terms_dict['grade'],
            subject=localized_terms_dict['subject'],
            curriculum=localized_terms_dict['curriculum']
        )
        queries = self._generate_queries(
            grade_subject_config.get('queries', []),
            localized_terms.grade,
            localized_terms.subject,
            localized_terms.curriculum
        )

        logger.info(f"Generated {len(queries)} queries for {country}")
        for i, q in enumerate(queries[:3], 1):
            logger.debug(f"  Query {i}: {q}")

        # 步骤3：执行搜索
        logger.info("Executing searches...")
        all_results = []

        for query in queries:
            try:
                results = self.search_engine.search(query, country=country)
                all_results.extend(results)
                logger.debug(f"Query '{query[:50]}...' returned {len(results)} results")
            except Exception as e:
                logger.warning(f"Search failed for query '{query[:50]}...': {e}")
                continue

        # 去重
        all_results = self._deduplicate_results(all_results)
        logger.info(f"Total results after deduplication: {len(all_results)}")

        # 步骤4：评分
        scored_results = self._score_results(
            all_results,
            grade_subject_config.get('trusted_domains', {})
        )

        # 排序并返回前N个
        final_results = scored_results[:max_results]

        if final_results:
            logger.info(
                f"Returning {len(final_results)} results, "
                f"top score: {final_results[0]['score']:.1f}"
            )
        else:
            logger.warning(f"No results found for {country}-{grade}-{subject}")

        # 返回完整结果
        return {
            'results': final_results,
            'localized_info': {
                'country': country,
                'grade': localized_terms.grade,
                'subject': localized_terms.subject,
                'curriculum': localized_terms.curriculum,
                'supported': True
            },
            'search_metadata': {
                'queries_used': queries,
                'total_found': len(all_results),
                'top_score': final_results[0]['score'] if final_results else 0,
                'search_method': 'rule_based'
            }
        }

    def _get_country_config(self, country: str) -> Dict:
        """获取国家配置

        Args:
            country: 国家代码

        Returns:
            国家配置字典

        Raises:
            ConfigError: 国家未配置
        """
        # 尝试直接获取
        if country in self.config:
            return self.config[country]

        # 尝试大写
        country_upper = country.upper()
        if country_upper in self.config:
            return self.config[country_upper]

        # 使用DEFAULT配置
        if 'DEFAULT' in self.config:
            logger.warning(f"Country {country} not configured, using DEFAULT")
            return self.config['DEFAULT']

        raise ConfigError(f"Country {country} not configured and no DEFAULT available")

    def _normalize_grade(self, grade: str, country: str) -> str:
        """标准化年级

        Args:
            grade: 年级字符串
            country: 国家代码

        Returns:
            标准化后的年级
        """
        grade = grade.strip().lower()

        # 年级映射表
        grade_map = {
            '1': '1', 'grade 1': '1', 'grade1': '1',
            '一年级': '1', '小学一年级': '1',
            'kelas 1': '1', 'sd kelas 1': '1',
            'الصف الأول': '1', 'class 1': '1',
            'year 1': '1',
        }

        return grade_map.get(grade, grade)

    def _normalize_subject(self, subject: str, country: str) -> str:
        """标准化学科

        Args:
            subject: 学科字符串
            country: 国家代码

        Returns:
            标准化后的学科
        """
        subject = subject.strip().lower()

        # 学科映射表
        subject_map = {
            'math': 'math', 'mathematics': 'math',
            '数学': 'math', 'matematika': 'math',
            'الرياضيات': 'math',
        }

        return subject_map.get(subject, subject)

    def _validate_config(
        self,
        config: Dict,
        country: str,
        grade: str,
        subject: str
    ) -> None:
        """验证配置结构

        Args:
            config: 配置字典
            country: 国家代码
            grade: 年级
            subject: 学科

        Raises:
            ConfigError: 配置无效
        """
        if 'queries' not in config:
            raise ConfigError(
                f"Missing 'queries' in config for {country}-{grade}-{subject}"
            )

        if not isinstance(config['queries'], list):
            raise ConfigError(
                f"'queries' must be a list for {country}-{grade}-{subject}"
            )

        if 'trusted_domains' in config and not isinstance(config['trusted_domains'], dict):
            raise ConfigError(
                f"'trusted_domains' must be a dict for {country}-{grade}-{subject}"
            )

    def _generate_queries(
        self,
        query_templates: List[str],
        grade: str,
        subject: str,
        curriculum: str
    ) -> List[str]:
        """生成查询列表

        Args:
            query_templates: 查询模板列表
            grade: 年级
            subject: 学科
            curriculum: 课程标准

        Returns:
            查询列表
        """
        queries = []

        for template in query_templates:
            try:
                query = template.format(
                    grade=grade,
                    subject=subject.title(),
                    curriculum=curriculum
                )
                queries.append(query)
            except KeyError as e:
                logger.warning(f"Template '{template}' missing variable: {e}")
                continue

        return queries

    def _score_results(
        self,
        results: List[Dict],
        trusted_domains: Dict[str, float]
    ) -> List[Dict]:
        """根据域名评分

        Args:
            results: 搜索结果列表
            trusted_domains: 可信域名评分字典

        Returns:
            评分后的结果列表（按分数降序）
        """
        scored_results = []

        for result in results:
            url = result.get('url', '').lower()

            # 查找域名分数
            score = self.DEFAULT_SCORE
            score_reason = f"Default score ({self.DEFAULT_SCORE})"

            for domain, domain_score in trusted_domains.items():
                if domain in url:
                    score = domain_score
                    score_reason = f"Trusted domain: {domain} ({domain_score})"
                    break

            result['score'] = score
            result['score_reason'] = score_reason
            scored_results.append(result)

        # 按分数降序排序
        scored_results.sort(key=lambda x: x['score'], reverse=True)

        return scored_results

    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """去重（基于URL）

        Args:
            results: 搜索结果列表

        Returns:
        去重后的结果列表
        """
        seen_urls = set()
        unique_results = []

        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)

        return unique_results

    def _empty_result(self, error_message: str) -> SearchResponse:
        """返回空结果

        Args:
            error_message: 错误信息

        Returns:
            空的SearchResponse
        """
        return {
            'results': [],
            'localized_info': {
                'supported': False,
                'error': error_message
            },
            'search_metadata': {
                'queries_used': [],
                'total_found': 0,
                'top_score': 0,
                'search_method': 'rule_based'
            }
        }


# ============================================
# 使用示例
# ============================================

if __name__ == "__main__":
    # 初始化搜索引擎
    engine = RuleBasedSearchEngine()

    # 测试印尼搜索
    try:
        result = engine.search(
            country='ID',
            grade='1',
            subject='math',
            max_results=10
        )

        print("\n搜索结果:")
        for i, r in enumerate(result['results'][:5], 1):
            print(f"{i}. [{r['score']:.1f}分] {r.get('title', 'N/A')}")
            print(f"   {r.get('url', 'N/A')}")

    except ConfigError as e:
        print(f"配置错误: {e}")
    except Exception as e:
        print(f"搜索失败: {e}")


class MockSearchEngine:
    """Mock搜索引擎，用于演示和测试

    注意：此引擎返回推荐平台主页，而非假的具体资源链接。
    真实搜索引擎集成后，应返回实际可访问的资源URL。
    """
    def search(self, query, country):
        """返回推荐平台信息

        Args:
            query: 搜索查询字符串
            country: 国家代码

        Returns:
            平台推荐列表，每个平台包含真实可访问的主页URL
        """
        import random

        # 根据国家返回推荐教育平台
        if country.upper() == 'ID':
            # 印尼推荐平台
            platforms = [
                {
                    'url': 'https://www.ruangguru.com/',
                    'title': 'Ruangguru - 印尼最大教育平台',
                    'snippet': f'💡 推荐访问 Ruangguru 搜索 "{query}" 相关资源。印尼领先的在线学习平台，提供K12全科目课程。',
                    'platform': 'Ruangguru',
                    'recommendation': '⭐ 强烈推荐',
                    'usage_hint': '在网站内搜索具体课程'
                },
                {
                    'url': 'https://www.youtube.com/',
                    'title': 'YouTube - 免费教育视频',
                    'snippet': f'💡 在 YouTube 搜索 "{query}" 查找相关课程。海量免费教育内容。',
                    'platform': 'YouTube',
                    'recommendation': '⭐ 推荐',
                    'usage_hint': '搜索印尼语教育频道'
                },
                {
                    'url': 'https://www.zenius.net/',
                    'title': 'Zenius - 印尼在线学习平台',
                    'snippet': f'💡 使用 Zenius 的 "{query}" 资源。高质量印尼课程内容。',
                    'platform': 'Zenius',
                    'recommendation': '⭐ 推荐',
                    'usage_hint': '提供免费和付费课程'
                },
                {
                    'url': 'https://www.khanacademy.org/',
                    'title': 'Khan Academy - 免费国际课程',
                    'snippet': f'💡 Khan Academy 提供 "{query}" 免费课程。支持印尼语界面。',
                    'platform': 'Khan Academy',
                    'recommendation': '⭐ 推荐',
                    'usage_hint': '切换语言到印尼语'
                },
                {
                    'url': 'https://www.kemdikbud.go.id/',
                    'title': '印尼教育部官方资源',
                    'snippet': f'💡 访问教育部官网获取 "{query}" 官方教材和资源。',
                    'platform': 'Kemdikbud',
                    'recommendation': '⭐ 官方权威',
                    'usage_hint': '查看 Kurikulum Merdeka 资源'
                }
            ]
        else:
            # 其他国家/DEFAULT配置
            platforms = [
                {
                    'url': 'https://www.youtube.com/',
                    'title': 'YouTube - 教育内容',
                    'snippet': f'💡 在 YouTube 搜索 "{query}" 相关视频',
                    'platform': 'YouTube',
                    'recommendation': '⭐ 推荐'
                },
                {
                    'url': 'https://www.khanacademy.org/',
                    'title': 'Khan Academy',
                    'snippet': f'💡 "{query}" 免费课程和练习',
                    'platform': 'Khan Academy',
                    'recommendation': '⭐ 推荐'
                },
                {
                    'url': 'https://www.udemy.com/',
                    'title': 'Udemy - 在线课程',
                    'snippet': f'💡 在 Udemy 搜索 "{query}" 相关课程',
                    'platform': 'Udemy',
                    'recommendation': '⭐ 推荐'
                }
            ]

        # 返回前2-4个平台推荐
        return platforms[:random.randint(2, 4)]
