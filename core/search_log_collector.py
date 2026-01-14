#!/usr/bin/env python3
"""
搜索日志收集器 - 记录搜索过程中的所有详细信息
用于生成详细的分析报告
"""
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LLMCall:
    """LLM调用记录"""
    model_name: str
    function: str  # 模型功能
    provider: str  # 提供商
    timestamp: str
    prompt: str
    input_data: str  # 输入信息摘要
    output_data: str  # 输出结果
    execution_time: float  # 执行时间（秒）
    tokens_used: Optional[int] = None
    cost: Optional[float] = None


@dataclass
class SearchResult:
    """搜索结果记录"""
    search_engine: str  # 搜索引擎
    query: str  # 查询关键词
    url: str
    title: str
    snippet: str
    score: float
    recommendation_reason: str
    resource_type: str
    additional_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchLog:
    """搜索日志"""
    search_id: str
    timestamp: str
    country: str
    grade: str
    subject: str
    semester: Optional[str]
    
    # 搜索引擎调用记录
    search_engine_calls: List[Dict[str, Any]] = field(default_factory=list)
    
    # LLM调用记录
    llm_calls: List[LLMCall] = field(default_factory=list)
    
    # 搜索结果记录
    search_results: List[SearchResult] = field(default_factory=list)
    
    # 性能统计
    total_time: float = 0.0
    search_time: float = 0.0
    scoring_time: float = 0.0
    
    # 结果统计
    total_results: int = 0
    playlist_count: int = 0
    video_count: int = 0
    average_score: float = 0.0
    
    # 其他信息
    metadata: Dict[str, Any] = field(default_factory=dict)


class SearchLogCollector:
    """搜索日志收集器"""
    
    def __init__(self):
        """初始化日志收集器"""
        self.current_log: Optional[SearchLog] = None
        self.logs_history: List[SearchLog] = []
    
    def start_search(self, country: str, grade: str, subject: str, semester: Optional[str] = None) -> str:
        """开始一个新的搜索记录"""
        search_id = f"search_{int(time.time())}"
        
        self.current_log = SearchLog(
            search_id=search_id,
            timestamp=datetime.now().isoformat(),
            country=country,
            grade=grade,
            subject=subject,
            semester=semester
        )
        
        return search_id
    
    def record_search_engine_call(
        self,
        engine: str,
        query: str,
        results_count: int,
        execution_time: float,
        success: bool = True,
        error: Optional[str] = None,
        additional_info: Optional[Dict[str, Any]] = None
    ):
        """记录搜索引擎调用"""
        if not self.current_log:
            return
        
        call_record = {
            "engine": engine,
            "query": query,
            "results_count": results_count,
            "execution_time": execution_time,
            "success": success,
            "error": error,
            "timestamp": datetime.now().isoformat(),
            "additional_info": additional_info or {}
        }
        
        self.current_log.search_engine_calls.append(call_record)
    
    def record_llm_call(
        self,
        model_name: str,
        function: str,
        provider: str,
        prompt: str,
        input_data: str,
        output_data: str,
        execution_time: float,
        tokens_used: Optional[int] = None,
        cost: Optional[float] = None
    ):
        """记录LLM调用"""
        if not self.current_log:
            return
        
        llm_call = LLMCall(
            model_name=model_name,
            function=function,
            provider=provider,
            timestamp=datetime.now().isoformat(),
            prompt=prompt,
            input_data=input_data,
            output_data=output_data,
            execution_time=execution_time,
            tokens_used=tokens_used,
            cost=cost
        )
        
        self.current_log.llm_calls.append(llm_call)
    
    def record_search_result(
        self,
        engine: str,
        query: str,
        url: str,
        title: str,
        snippet: str,
        score: float,
        recommendation_reason: str,
        resource_type: str,
        **kwargs
    ):
        """记录搜索结果"""
        if not self.current_log:
            return
        
        result = SearchResult(
            search_engine=engine,
            query=query,
            url=url,
            title=title,
            snippet=snippet,
            score=score,
            recommendation_reason=recommendation_reason,
            resource_type=resource_type,
            additional_info=kwargs
        )
        
        self.current_log.search_results.append(result)
    
    def finish_search(self, total_time: float, search_time: float, scoring_time: float):
        """完成搜索记录"""
        if not self.current_log:
            return
        
        self.current_log.total_time = total_time
        self.current_log.search_time = search_time
        self.current_log.scoring_time = scoring_time
        
        # 计算统计信息
        self.current_log.total_results = len(self.current_log.search_results)
        self.current_log.playlist_count = sum(
            1 for r in self.current_log.search_results 
            if r.resource_type == '播放列表'
        )
        self.current_log.video_count = sum(
            1 for r in self.current_log.search_results 
            if r.resource_type == '视频'
        )
        
        if self.current_log.search_results:
            scores = [r.score for r in self.current_log.search_results]
            self.current_log.average_score = sum(scores) / len(scores)
        
        # 保存到历史记录
        self.logs_history.append(self.current_log)
        
        # 返回当前日志
        log = self.current_log
        self.current_log = None
        
        return log
    
    def get_current_log(self) -> Optional[SearchLog]:
        """获取当前搜索日志"""
        return self.current_log
    
    def get_log_by_id(self, search_id: str) -> Optional[SearchLog]:
        """根据搜索ID获取日志"""
        for log in self.logs_history:
            if log.search_id == search_id:
                return log
        return None
    
    def get_recent_logs(self, count: int = 10) -> List[SearchLog]:
        """获取最近的搜索日志"""
        return self.logs_history[-count:]


# 全局单例
_collector_instance = None

def get_log_collector() -> SearchLogCollector:
    """获取日志收集器单例"""
    global _collector_instance
    if _collector_instance is None:
        _collector_instance = SearchLogCollector()
    return _collector_instance
