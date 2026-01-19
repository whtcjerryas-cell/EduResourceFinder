#!/usr/bin/env python3
"""
搜索引擎抽象基类

定义所有搜索引擎的统一接口，消除代码重复，
提供搜索引擎的通用功能实现。
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from logger_utils import get_logger

logger = get_logger('base_search_engine')


class SearchResult:
    """
    统一的搜索结果数据结构

    Attributes:
        title: 结果标题
        url: 结果URL
        snippet: 结果摘要
        source: 结果来源
        score: 评分（可选）
        metadata: 额外的元数据（可选）
    """

    def __init__(
        self,
        title: str,
        url: str,
        snippet: str = "",
        source: str = "",
        score: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.source = source
        self.score = score
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'title': self.title,
            'url': self.url,
            'snippet': self.snippet,
            'source': self.source,
            'score': self.score,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchResult':
        """从字典创建SearchResult对象"""
        return cls(
            title=data.get('title', ''),
            url=data.get('url', ''),
            snippet=data.get('snippet', ''),
            source=data.get('source', ''),
            score=data.get('score', 0.0),
            metadata=data.get('metadata', {})
        )


class SearchRequest:
    """
    统一的搜索请求数据结构

    Attributes:
        query: 搜索查询
        country_code: 国家代码
        grade: 年级
        subject: 学科
        max_results: 最大结果数
        filters: 额外的过滤条件
    """

    def __init__(
        self,
        query: str,
        country_code: str = "",
        grade: str = "",
        subject: str = "",
        max_results: int = 15,
        filters: Optional[Dict[str, Any]] = None
    ):
        self.query = query
        self.country_code = country_code
        self.grade = grade
        self.subject = subject
        self.max_results = max_results
        self.filters = filters or {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'query': self.query,
            'country_code': self.country_code,
            'grade': self.grade,
            'subject': self.subject,
            'max_results': self.max_results,
            'filters': self.filters
        }


class BaseSearchEngine(ABC):
    """
    搜索引擎抽象基类

    所有具体搜索引擎类应该继承此类并实现search方法。
    提供搜索引擎的通用功能和接口定义。
    """

    def __init__(self, name: str = "BaseSearchEngine"):
        """
        初始化搜索引擎

        Args:
            name: 搜索引擎名称
        """
        self.name = name
        self.logger = get_logger(f'search_engine.{name}')
        self._stats = {
            'total_searches': 0,
            'successful_searches': 0,
            'failed_searches': 0,
            'total_results': 0
        }

    @abstractmethod
    def search(self, request: SearchRequest) -> Dict[str, Any]:
        """
        执行搜索（子类必须实现）

        Args:
            request: 搜索请求对象

        Returns:
            搜索结果字典，格式为：
            {
                'results': List[SearchResult],
                'total': int,
                'metadata': Dict[str, Any]
            }
        """
        pass

    def validate_request(self, request: SearchRequest) -> bool:
        """
        验证搜索请求（可重写）

        Args:
            request: 搜索请求

        Returns:
            验证是否通过
        """
        if not request.query or not request.query.strip():
            self.logger.warning("搜索查询为空")
            return False

        if request.max_results <= 0:
            self.logger.warning(f"无效的max_results: {request.max_results}")
            return False

        return True

    def preprocess_query(self, query: str) -> str:
        """
        预处理查询字符串（可重写）

        Args:
            query: 原始查询

        Returns:
            处理后的查询
        """
        # 基础预处理：去除多余空格，转换为小写
        return ' '.join(query.strip().split())

    def postprocess_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        后处理搜索结果（可重写）

        Args:
            results: 原始结果列表

        Returns:
            处理后的结果列表
        """
        # 基础后处理：按评分排序
        return sorted(results, key=lambda x: x.score, reverse=True)

    def execute_search(self, request: SearchRequest) -> Dict[str, Any]:
        """
        执行搜索的完整流程（模板方法）

        Args:
            request: 搜索请求

        Returns:
            搜索结果字典
        """
        self._stats['total_searches'] += 1

        try:
            # 1. 验证请求
            if not self.validate_request(request):
                self._stats['failed_searches'] += 1
                return self._error_response("请求验证失败")

            # 2. 预处理查询
            processed_query = self.preprocess_query(request.query)

            # 3. 创建修改后的请求
            processed_request = SearchRequest(
                query=processed_query,
                country_code=request.country_code,
                grade=request.grade,
                subject=request.subject,
                max_results=request.max_results,
                filters=request.filters
            )

            # 4. 调用子类实现的搜索方法
            response = self.search(processed_request)

            # 5. 后处理结果
            if 'results' in response:
                results = [SearchResult.from_dict(r) if isinstance(r, dict) else r
                           for r in response['results']]
                response['results'] = self.postprocess_results(results)
                response['results'] = [r.to_dict() for r in response['results']]

            # 6. 更新统计信息
            self._stats['successful_searches'] += 1
            self._stats['total_results'] += len(response.get('results', []))

            return response

        except Exception as e:
            self._stats['failed_searches'] += 1
            self.logger.error(f"搜索执行失败: {str(e)[:200]}")
            return self._error_response(f"搜索失败: {str(e)[:100]}")

    def _error_response(self, message: str) -> Dict[str, Any]:
        """
        生成错误响应

        Args:
            message: 错误消息

        Returns:
            错误响应字典
        """
        return {
            'results': [],
            'total': 0,
            'error': message,
            'metadata': {
                'engine': self.name,
                'success': False
            }
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        获取搜索引擎统计信息

        Returns:
            统计信息字典
        """
        return {
            'engine': self.name,
            'total_searches': self._stats['total_searches'],
            'successful_searches': self._stats['successful_searches'],
            'failed_searches': self._stats['failed_searches'],
            'success_rate': (
                self._stats['successful_searches'] / self._stats['total_searches']
                if self._stats['total_searches'] > 0 else 0
            ),
            'total_results': self._stats['total_results'],
            'avg_results_per_search': (
                self._stats['total_results'] / self._stats['successful_searches']
                if self._stats['successful_searches'] > 0 else 0
            )
        }

    def reset_stats(self):
        """重置统计信息"""
        self._stats = {
            'total_searches': 0,
            'successful_searches': 0,
            'failed_searches': 0,
            'total_results': 0
        }
        self.logger.info(f"统计信息已重置")


class GoogleSearchEngine(BaseSearchEngine):
    """
    Google搜索引擎实现（示例）
    """

    def __init__(self):
        super().__init__(name="GoogleSearch")

    def search(self, request: SearchRequest) -> Dict[str, Any]:
        """
        使用Google搜索API执行搜索

        注：这是一个示例实现，实际使用时需要集成真实的搜索API
        """
        # TODO: 集成Google Custom Search API
        self.logger.info(f"执行Google搜索: {request.query}")

        # 返回模拟数据
        return {
            'results': [],
            'total': 0,
            'metadata': {
                'engine': self.name,
                'query': request.query,
                'success': True
            }
        }


if __name__ == "__main__":
    print("=" * 60)
    print("搜索引擎抽象基类测试")
    print("=" * 60)

    # 测试1: 创建搜索请求
    print("\n测试1 - 创建搜索请求:")
    request = SearchRequest(
        query="mathematics grade 1",
        country_code="ID",
        grade="1",
        subject="Mathematics",
        max_results=10
    )
    print(f"  查询: {request.query}")
    print(f"  国家: {request.country_code}")
    print(f"  最大结果数: {request.max_results}")

    # 测试2: 使用搜索引擎
    print("\n测试2 - 使用搜索引擎:")
    engine = GoogleSearchEngine()
    response = engine.execute_search(request)
    print(f"  引擎: {response['metadata']['engine']}")
    print(f"  成功: {response['metadata']['success']}")

    # 测试3: 获取统计信息
    print("\n测试3 - 统计信息:")
    stats = engine.get_stats()
    print(f"  总搜索次数: {stats['total_searches']}")
    print(f"  成功率: {stats['success_rate']:.1%}")

    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)
