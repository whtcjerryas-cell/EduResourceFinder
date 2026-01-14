#!/usr/bin/env python3
"""
搜索处理器 - 拆分 web_app.py 中的超长 search() 函数
"""

import time
import gc
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Dict, Any, List, Optional, Tuple
from logger_utils import get_logger
from utils.constants import (
    SEARCH_TIMEOUT_SECONDS,
    CONCURRENCY_LIMITER_TIMEOUT,
    HTTP_SUCCESS,
    HTTP_BAD_REQUEST,
    HTTP_SERVER_ERROR,
    HTTP_SERVICE_UNAVAILABLE
)

logger = get_logger('search_handler')


class SearchHandler:
    """搜索处理器 - 封装搜索的完整流程"""

    def __init__(self, concurrency_limiter=None):
        """
        初始化搜索处理器

        Args:
            concurrency_limiter: 并发限制器
        """
        self.concurrency_limiter = concurrency_limiter
        self.SEARCH_TIMEOUT = SEARCH_TIMEOUT_SECONDS

    def handle_search_request(
        self,
        request_data: Dict[str, Any],
        concurrency_limiter=None
    ) -> Tuple[Dict[str, Any], int]:
        """
        处理搜索请求（主入口）

        Args:
            request_data: 请求数据
            concurrency_limiter: 并发限制器

        Returns:
            (响应字典, 状态码)
        """
        # 生成请求ID
        request_id = str(uuid.uuid4())[:8]
        logger.info(f"[搜索请求] 开始处理搜索请求 [ID: {request_id}]")

        # 1. 参数验证
        is_valid, error_message, params = self._validate_and_parse_params(request_data)
        if not is_valid:
            logger.warning(f"[搜索请求] 参数不完整: {error_message}")
            return self._create_error_response(error_message, HTTP_BAD_REQUEST)

        # 2. 并发限制检查
        if not self._acquire_concurrency_slot():
            logger.warning(f"搜索请求被限流: 超过最大并发数")
            return self._create_error_response("服务器繁忙，请稍后重试", HTTP_SERVICE_UNAVAILABLE)

        try:
            # 3. 初始化搜索组件
            if not self._initialize_search_engine():
                return self._create_error_response("搜索引擎模块不可用", HTTP_SERVER_ERROR)

            # 4. 创建搜索请求
            search_request = self._create_search_request(params)

            # 5. 启动日志收集
            from core.search_log_collector import get_log_collector
            log_collector = get_log_collector()
            search_id = log_collector.start_search(
                params['country'],
                params['grade'],
                params['subject'],
                params.get('semester')
            )
            logger.info(f"[日志收集] 已启动搜索日志: {search_id}")

            # 6. 执行搜索（带超时）
            response, search_elapsed = self._execute_search_with_timeout(
                search_request,
                request_id
            )

            # 7. 记录搜索结果
            if response and response.success:
                self._record_search_results(
                    log_collector,
                    response,
                    search_elapsed
                )

            # 8. 格式化响应
            result_data = self._format_search_response(response, search_id)

            # 9. 应用资源类型过滤
            if params.get('resource_type') and params['resource_type'] != 'all':
                result_data = self._filter_by_resource_type(
                    result_data,
                    params['resource_type']
                )

            return result_data, HTTP_SUCCESS

        except Exception as e:
            logger.error(f"[搜索请求] 处理失败: {str(e)}")
            return self._create_error_response(f"搜索失败: {str(e)}", HTTP_SERVER_ERROR)

    def _validate_and_parse_params(self, data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        验证并解析请求参数

        Returns:
            (is_valid, error_message, parsed_params)
        """
        if not data:
            return False, "请求数据为空", {}

        country = (data.get('country') or '').strip()
        grade = (data.get('grade') or '').strip()
        subject = (data.get('subject') or '').strip()

        if not country or not grade or not subject:
            return False, "请提供国家、年级和学科", {}

        semester_val = data.get('semester')
        semester = (semester_val.strip() if semester_val and isinstance(semester_val, str) else '') or None

        language_val = data.get('language')
        language = (language_val.strip() if language_val and isinstance(language_val, str) else '') or None

        resource_type = data.get('resourceType', 'all').strip()

        params = {
            'country': country,
            'grade': grade,
            'subject': subject,
            'semester': semester,
            'language': language,
            'resource_type': resource_type
        }

        logger.info(f"[搜索参数] {params}")
        return True, "", params

    def _acquire_concurrency_slot(self) -> bool:
        """
        获取并发槽位

        Returns:
            是否成功获取
        """
        if self.concurrency_limiter is None:
            return True

        return self.concurrency_limiter.acquire(timeout=CONCURRENCY_LIMITER_TIMEOUT)

    def _initialize_search_engine(self) -> bool:
        """
        初始化搜索引擎

        Returns:
            是否成功
        """
        try:
            logger.debug("[搜索请求] 开始加载搜索引擎模块...")
            import importlib
            import search_engine_v2
            importlib.reload(search_engine_v2)
            from search_engine_v2 import SearchEngineV2
            self.SearchEngineV2 = SearchEngineV2
            logger.debug("[搜索请求] 搜索引擎模块加载完成")
            return True
        except Exception as e:
            logger.error(f"[搜索请求] 搜索引擎模块加载失败: {str(e)}")
            return False

    def _create_search_request(self, params: Dict[str, Any]):
        """创建搜索请求对象"""
        from search_engine_v2 import SearchRequest
        return SearchRequest(
            country=params['country'],
            grade=params['grade'],
            semester=params.get('semester'),
            subject=params['subject'],
            language=params.get('language')
        )

    def _execute_search_with_timeout(
        self,
        search_request,
        request_id: str
    ) -> Tuple[Any, float]:
        """
        执行搜索（带超时保护）

        Returns:
            (搜索响应, 耗时)
        """
        search_start_time = time.time()
        response = None
        search_engine_instance = None

        def execute_search():
            """在独立线程中执行搜索"""
            nonlocal search_engine_instance
            search_engine_instance = self.SearchEngineV2()
            try:
                result = search_engine_instance.search(search_request)
                return result
            finally:
                try:
                    if search_engine_instance is not None:
                        del search_engine_instance
                        gc.collect()
                except:
                    pass

        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(execute_search)
                try:
                    response = future.result(timeout=self.SEARCH_TIMEOUT)
                    search_elapsed = time.time() - search_start_time
                    logger.info(f"[搜索执行] 搜索完成，耗时: {search_elapsed:.2f}秒，结果数: {len(response.results)}")
                    return response, search_elapsed
                except FuturesTimeoutError:
                    logger.error(f"[搜索执行] 搜索超时（超过{self.SEARCH_TIMEOUT}秒）")
                    future.cancel()
                    from search_engine_v2 import SearchResponse
                    response = SearchResponse(
                        success=False,
                        query="",
                        results=[],
                        message=f"搜索超时（超过{self.SEARCH_TIMEOUT}秒），请稍后重试或减少搜索条件",
                        total_count=0,
                        playlist_count=0,
                        video_count=0
                    )
                    return response, self.SEARCH_TIMEOUT
        except Exception as e:
            logger.error(f"[搜索执行] 搜索异常: {str(e)}")
            from search_engine_v2 import SearchResponse
            return SearchResponse(
                success=False,
                query="",
                results=[],
                message=str(e),
                total_count=0,
                playlist_count=0,
                video_count=0
            ), 0

    def _record_search_results(self, log_collector, response, search_elapsed: float):
        """记录搜索结果到日志"""
        try:
            for result in response.results:
                search_engine_name = getattr(result, 'search_engine', None) or (
                    result.model_dump().get('search_engine') if hasattr(result, 'model_dump') else None
                ) or "Unknown"

                log_collector.record_search_result(
                    engine=search_engine_name,
                    query=response.query,
                    url=result.url or "",
                    title=result.title or "",
                    snippet=result.snippet or "",
                    score=result.score or 0,
                    recommendation_reason=result.recommendation_reason or "",
                    resource_type=result.resource_type or "未知",
                )

            # 完成日志收集
            log_collector.finish_search(
                total_time=search_elapsed,
                search_time=search_elapsed * 0.7,
                result_count=len(response.results),
                playlist_count=response.playlist_count if hasattr(response, 'playlist_count') else 0,
                video_count=response.video_count if hasattr(response, 'video_count') else 0
            )
            logger.info(f"[日志收集] 搜索日志已记录")
        except Exception as e:
            logger.warning(f"[日志收集] 记录失败: {str(e)}")

    def _format_search_response(self, response, search_id: str) -> Dict[str, Any]:
        """格式化搜索响应"""
        if not response:
            return {
                "success": False,
                "query": "",
                "results": [],
                "message": "搜索结果为空",
                "total_count": 0,
                "playlist_count": 0,
                "video_count": 0,
                "search_id": search_id
            }

        return {
            "success": response.success,
            "query": response.query,
            "results": [self._format_result(r) for r in (response.results if response else [])],
            "message": response.message or "",
            "total_count": response.total_count if response else 0,
            "playlist_count": response.playlist_count if response else 0,
            "video_count": response.video_count if response else 0,
            "search_id": search_id
        }

    def _format_result(self, result) -> Dict[str, Any]:
        """格式化单个搜索结果"""
        return {
            "title": result.title,
            "url": result.url,
            "snippet": result.snippet,
            "score": result.score,
            "recommendation_reason": result.recommendation_reason,
            "resource_type": result.resource_type,
            "search_engine": getattr(result, 'search_engine', 'Unknown')
        }

    def _filter_by_resource_type(
        self,
        response_data: Dict[str, Any],
        resource_type: str
    ) -> Dict[str, Any]:
        """
        按资源类型过滤结果

        Args:
            response_data: 响应数据
            resource_type: 资源类型

        Returns:
            过滤后的响应数据
        """
        if not response_data.get('results'):
            return response_data

        filtered_results = []
        for result in response_data['results']:
            result_type = result.get('resource_type', '').lower()
            if resource_type.lower() in result_type or result_type == '未知':
                filtered_results.append(result)

        response_data['results'] = filtered_results
        response_data['total_count'] = len(filtered_results)
        return response_data

    def _create_error_response(
        self,
        message: str,
        status_code: int
    ) -> Tuple[Dict[str, Any], int]:
        """创建错误响应"""
        error_response = {
            "success": False,
            "message": message,
            "results": []
        }
        if status_code == 400:
            error_response.update({
                "query": "",
                "total_count": 0,
                "playlist_count": 0,
                "video_count": 0
            })
        return error_response, status_code
