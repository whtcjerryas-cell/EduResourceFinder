#!/usr/bin/env python3
"""
搜索服务 - 封装搜索相关的业务逻辑
"""

import time
import gc
import uuid
import importlib
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Optional, Dict, Any
from logger_utils import get_logger

logger = get_logger('search_service')


class SearchService:
    """搜索服务类"""

    def __init__(self, concurrency_limiter=None):
        """
        初始化搜索服务

        Args:
            concurrency_limiter: 并发限制器（可选）
        """
        self.concurrency_limiter = concurrency_limiter
        self.SEARCH_TIMEOUT = 150  # 搜索超时时间（秒）

    def execute_search(
        self,
        country: str,
        grade: str,
        subject: str,
        semester: Optional[str] = None,
        language: Optional[str] = None,
        resource_type: str = 'all'
    ) -> Dict[str, Any]:
        """
        执行搜索

        Args:
            country: 国家
            grade: 年级
            subject: 学科
            semester: 学期（可选）
            language: 语言（可选）
            resource_type: 资源类型

        Returns:
            搜索结果字典
        """
        request_id = str(uuid.uuid4())[:8]
        logger.info(f"[搜索请求] 开始处理搜索请求 [ID: {request_id}]")

        # 并发限制检查
        if self.concurrency_limiter is not None:
            if not self.concurrency_limiter.acquire(timeout=5.0):
                logger.warning(f"搜索请求被限流: 超过最大并发数")
                return {
                    "success": False,
                    "message": "服务器繁忙，请稍后重试",
                    "status_code": 503
                }

        try:
            # 强制重新加载模块（确保获取最新代码）
            logger.debug("[搜索请求] 开始加载搜索引擎模块...")
            import search_engine_v2
            importlib.reload(search_engine_v2)
            from search_engine_v2 import SearchRequest, SearchEngineV2, SearchResponse

            search_request = SearchRequest(
                country=country,
                grade=grade,
                semester=semester,
                subject=subject,
                language=language
            )

            logger.info(f"[搜索执行] 开始执行搜索 [ID: {request_id}]")

            # 📊 启动日志收集
            from core.search_log_collector import get_log_collector
            log_collector = get_log_collector()
            search_id = log_collector.start_search(country, grade, subject, semester)
            logger.info(f"[日志收集] 已启动搜索日志: {search_id}")

            search_start_time = time.time()
            response = None
            search_engine_instance = None

            def execute_search_in_thread():
                """在独立线程中执行搜索"""
                nonlocal search_engine_instance
                search_engine_instance = SearchEngineV2()
                try:
                    result = search_engine_instance.search(search_request)
                    return result
                finally:
                    # 在线程内部清理资源
                    try:
                        if search_engine_instance is not None:
                            del search_engine_instance
                            gc.collect()
                    except:
                        pass

            try:
                # 使用ThreadPoolExecutor执行搜索，支持真正的超时中断
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(execute_search_in_thread)
                    try:
                        response = future.result(timeout=self.SEARCH_TIMEOUT)
                        search_elapsed = time.time() - search_start_time
                        logger.info(f"[搜索执行] 搜索完成，耗时: {search_elapsed:.2f}秒，结果数: {len(response.results)}")
                    except FuturesTimeoutError:
                        logger.error(f"[搜索执行] 搜索超时（超过{self.SEARCH_TIMEOUT}秒）[ID: {request_id}]")
                        future.cancel()
                        # 返回超时响应
                        response = SearchResponse(
                            success=False,
                            query="",
                            results=[],
                            message=f"搜索超时（超过{self.SEARCH_TIMEOUT}秒），请稍后重试或减少搜索条件",
                            total_count=0,
                            playlist_count=0,
                            video_count=0
                        )

                # 📊 记录搜索结果到日志
                search_elapsed = time.time() - search_start_time
                if response and response.success:
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
                        search_time=search_elapsed * 0.7,  # 估算搜索时间
                        result_count=len(response.results),
                        playlist_count=response.playlist_count if hasattr(response, 'playlist_count') else 0,
                        video_count=response.video_count if hasattr(response, 'video_count') else 0
                    )
                    logger.info(f"[日志收集] 搜索日志已记录: {search_id}")

                # 构建响应
                return {
                    "success": response.success if response else False,
                    "query": response.query if response else "",
                    "results": [self._format_result(r) for r in (response.results if response else [])],
                    "message": response.message if response else "",
                    "total_count": response.total_count if response else 0,
                    "playlist_count": response.playlist_count if response else 0,
                    "video_count": response.video_count if response else 0,
                    "search_id": search_id,
                    "status_code": 200
                }

            except Exception as e:
                logger.error(f"[搜索执行] 搜索异常: {str(e)}")
                return {
                    "success": False,
                    "message": f"搜索执行异常: {str(e)}",
                    "results": [],
                    "status_code": 500
                }

        except Exception as e:
            logger.error(f"[搜索请求] 处理失败: {str(e)}")
            return {
                "success": False,
                "message": str(e),
                "results": [],
                "status_code": 500
            }

    def _format_result(self, result) -> Dict[str, Any]:
        """格式化搜索结果"""
        return {
            "title": result.title,
            "url": result.url,
            "snippet": result.snippet,
            "score": result.score,
            "recommendation_reason": result.recommendation_reason,
            "resource_type": result.resource_type,
            "search_engine": getattr(result, 'search_engine', 'Unknown')
        }
