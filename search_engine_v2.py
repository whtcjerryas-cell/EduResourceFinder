#!/usr/bin/env python3
"""
新版搜索引擎 - 基于国家/年级/学期搜索
使用 AI 生成本地语言的搜索词

TODO 重构任务（P1 - 代码质量改进）:
- [008] 超长函数：search()方法需要拆分为多个小函数（当前约1000+行）
- [009] 全局变量：减少global关键字使用，改用依赖注入模式
- [010] 硬编码路径：创建PathManager统一管理路径配置
"""

import os
import json
import time
import re
from typing import Dict, List, Optional, Any, Callable
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
import concurrent.futures
from config_manager import ConfigManager
from logger_utils import get_logger
from json_utils import extract_json_array
from search_strategy_agent import SearchStrategyAgent
from core.search_cache import get_search_cache
from core.config_loader import get_config
from core.performance_monitor import get_performance_monitor
from core.result_scorer import get_result_scorer
from core.recommendation_generator import get_recommendation_generator
from core.grade_subject_validator import GradeSubjectValidator
from core.text_utils import clean_title, clean_snippet, extract_video_info
from core.quality_evaluator import QualityEvaluator
from core.intelligent_search_optimizer import IntelligentSearchOptimizer
# from core.optimization_approval import get_approval_manager  # 已禁用 - SIS功能
# 日志脱敏工具（安全修复：P1 - 防止敏感信息泄露）
from utils.log_sanitizer import safe_log, safe_log_json

# 初始化日志记录器
logger = get_logger('search_engine')

# 初始化性能监控器
perf_monitor = get_performance_monitor()

# 支持从 .env 文件读取环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    def load_dotenv():
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip().strip('"').strip("'")
    load_dotenv()


# ============================================================================
# 数据模型定义
# ============================================================================

class SearchRequest(BaseModel):
    """搜索请求"""
    country: str = Field(description="国家代码（如：ID, CN, US）")
    grade: str = Field(description="年级（如：1, 2, 3 或 Kelas 1, Grade 1）")
    semester: Optional[str] = Field(description="学期（如：1, 2 或 Semester 1）", default=None)
    subject: str = Field(description="学科（如：Matematika, Mathematics, 数学）")
    language: Optional[str] = Field(description="搜索语言（如：id, en, zh）", default=None)


class SearchResult(BaseModel):
    """单个搜索结果"""
    title: str = Field(description="搜索结果标题")
    url: str = Field(description="结果URL")
    snippet: str = Field(description="结果摘要", default="")
    source: str = Field(description="来源（规则/LLM）", default="规则")
    search_engine: str = Field(description="搜索引擎来源（Tavily/Google/Baidu）", default="Unknown")
    score: float = Field(description="评估分数（0-10分）", default=0.0)
    recommendation_reason: str = Field(description="推荐理由", default="")
    evaluation_method: Optional[str] = Field(description="评估方法（MCP Tools/Rule-based/LLM）", default=None)
    resource_type: Optional[str] = Field(description="资源类型（视频、教材、教辅、学习资料、练习题等）", default=None)
    is_selected: bool = Field(description="是否被人工选中", default=False)
    evaluation_status: Optional[str] = Field(description="评估状态（pending/evaluating/completed/failed）", default=None)
    evaluation_result: Optional[Dict[str, Any]] = Field(description="视频评估结果（如果已评估）", default=None)


class SearchResponse(BaseModel):
    """搜索响应"""
    success: bool = Field(description="是否成功")
    query: str = Field(description="使用的搜索词")
    results: List[SearchResult] = Field(description="搜索结果列表", default_factory=list)
    total_count: int = Field(description="结果总数", default=0)
    playlist_count: int = Field(description="播放列表数量", default=0)
    video_count: int = Field(description="视频数量", default=0)
    message: str = Field(description="消息", default="")
    timestamp: str = Field(description="时间戳", default_factory=lambda: datetime.now(timezone.utc).isoformat())
    quality_report: Optional[Dict[str, Any]] = Field(description="质量评估报告", default=None)
    optimization_request: Optional[Dict[str, Any]] = Field(description="优化请求（如果检测到质量问题）", default=None)


# ============================================================================
# AI Builders 客户端 (使用统一LLM客户端，支持双API系统)
# ============================================================================

# 导入统一LLM客户端
try:
    from llm_client import UnifiedLLMClient, AIBuildersAPIClient
    HAS_UNIFIED_CLIENT = True
except ImportError:
    HAS_UNIFIED_CLIENT = False
    print("[⚠️] 警告: 无法导入统一LLM客户端，将使用原有实现")

class AIBuildersClient:
    """
    AI Builders API 客户端（兼容性包装器）
    内部使用统一LLM客户端，支持公司内部API和AI Builders API的fallback机制
    """
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.getenv("AI_BUILDER_TOKEN")
        
        # 尝试使用统一LLM客户端
        if HAS_UNIFIED_CLIENT:
            try:
                # 获取公司内部API密钥（可选）
                internal_api_key = os.getenv("INTERNAL_API_KEY")
                self.unified_client = UnifiedLLMClient(
                    internal_api_key=internal_api_key,
                    ai_builder_token=self.api_token
                )
                self.use_unified_client = True
                print("[✅] 使用统一LLM客户端（支持双API系统）")
            except Exception as e:
                print(f"[⚠️] 统一LLM客户端初始化失败: {str(e)}，回退到原有实现")
                self.use_unified_client = False
                # 回退到原有实现
                if not self.api_token:
                    raise ValueError("请设置 AI_BUILDER_TOKEN 环境变量")
        else:
            self.use_unified_client = False
            if not self.api_token:
                raise ValueError("请设置 AI_BUILDER_TOKEN 环境变量")
        
        # 保留原有属性以保持兼容性
        self.base_url = "https://space.ai-builders.com/backend"
        self.headers = {
            "Authorization": f"Bearer {self.api_token or ''}",
            "Content-Type": "application/json"
        }
    
    def call_llm(self, prompt: str, system_prompt: Optional[str] = None, 
                 max_tokens: int = 2000, temperature: float = 0.3,
                 model: str = "deepseek") -> str:
        """调用 LLM"""
        # 如果使用统一客户端，直接调用
        if self.use_unified_client:
            return self.unified_client.call_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                model=model
            )
        
        # 否则使用原有实现
        endpoint = f"{self.base_url}/v1/chat/completions"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
            # 不设置 tool_choice 和 tools，让 API 使用默认行为
        }
        
        # 详细日志：LLM调用输入（使用脱敏防止敏感信息泄露）
        print(f"\n{'='*80}")
        print(f"[🤖 LLM调用] 开始调用 {model}")
        print(f"{'='*80}")
        print(f"[📤 输入] Endpoint: {endpoint}")
        print(f"[📤 输入] Model: {model}")
        print(f"[📤 输入] Max Tokens: {max_tokens}")
        print(f"[📤 输入] Temperature: {temperature}")
        print(f"[📤 输入] System Prompt 长度: {len(system_prompt) if system_prompt else 0} 字符")
        print(f"[📤 输入] User Prompt 长度: {len(prompt)} 字符")
        if system_prompt:
            print(f"[📤 输入] System Prompt (前500字符):\n{safe_log(system_prompt[:500])}...")
        print(f"[📤 输入] User Prompt (前500字符):\n{safe_log(prompt[:500])}...")
        print(f"[📤 输入] 完整 User Prompt:\n{safe_log(prompt)}")
        print(f"[📤 输入] Payload (已脱敏):\n{safe_log_json(payload)}")
        
        try:
            import time
            from llm_client import get_proxy_config
            start_time = time.time()
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                params={"debug": "true"},
                timeout=300,
                proxies=get_proxy_config()
            )
            elapsed_time = time.time() - start_time
            
            # 详细日志：API响应（使用脱敏防止敏感信息泄露）
            print(f"\n[📥 响应] HTTP 状态码: {response.status_code}")
            print(f"[📥 响应] 响应时间: {elapsed_time:.2f} 秒")

            if response.status_code == 200:
                result = response.json()
                print(f"[📥 响应] 响应类型: {type(result).__name__}")
                print(f"[📥 响应] 响应键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")

                # 打印完整的API响应（用于调试，已脱敏）
                print(f"[📥 响应] 完整 API 响应 (已脱敏):\n{safe_log_json(result)}")
                
                if "choices" in result and len(result["choices"]) > 0:
                    choice = result["choices"][0]
                    message = choice.get("message", {})
                    content = message.get("content", "")
                    finish_reason = choice.get("finish_reason", "unknown")
                    
                    print(f"[📥 响应] Finish Reason: {finish_reason}")
                    print(f"[📥 响应] Content 长度: {len(content) if content else 0} 字符")
                    
                    # 打印 usage 信息（如果存在）
                    if "usage" in result:
                        usage = result["usage"]
                        print(f"[📥 响应] Token 使用:")
                        print(f"    - Prompt Tokens: {usage.get('prompt_tokens', 'N/A')}")
                        print(f"    - Completion Tokens: {usage.get('completion_tokens', 'N/A')}")
                        print(f"    - Total Tokens: {usage.get('total_tokens', 'N/A')}")
                    
                    # 打印 orchestrator_trace（如果存在，用于调试，已脱敏）
                    if "orchestrator_trace" in result:
                        trace = result["orchestrator_trace"]
                        print(f"[📥 响应] Orchestrator Trace 存在，长度: {len(json.dumps(trace))} 字符")
                        print(f"[📥 响应] Orchestrator Trace (已脱敏):\n{safe_log_json(trace)}")
                    
                    if content and content.strip():
                        print(f"[📥 响应] Content (前1000字符):\n{content[:1000]}...")
                        print(f"[📥 响应] 完整 Content:\n{content}")
                        print(f"{'='*80}\n")
                        return content.strip()
                    else:
                        # 如果 deepseek 失败，尝试 gemini
                        if model == "deepseek":
                            print(f"    [⚠️ 警告] DeepSeek 返回空内容，尝试 Gemini...")
                            return self.call_llm(prompt, system_prompt, max_tokens, temperature, "gemini-2.5-pro")
                        raise ValueError("API 响应中 content 为空字符串")
                else:
                    print(f"[❌ 错误] API 响应格式异常，缺少 choices 字段")
                    raise ValueError(f"API 响应格式异常")
            else:
                error_text = response.text[:500] if hasattr(response, 'text') else 'N/A'
                print(f"[❌ 错误] API 调用失败")
                print(f"[❌ 错误] 状态码: {response.status_code}")
                print(f"[❌ 错误] 错误响应: {error_text}")
                raise ValueError(f"API 调用失败，状态码: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[❌ 错误] API 请求异常: {str(e)}")
            print(f"[❌ 错误] 异常类型: {type(e).__name__}")
            import traceback
            print(f"[❌ 错误] 异常堆栈:\n{traceback.format_exc()}")
            raise ValueError(f"API 请求异常: {str(e)}")
    
    def search(self, query: str, max_results: int = 20, include_domains: Optional[List[str]] = None) -> List[SearchResult]:
        """
        使用 Tavily 搜索
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            include_domains: 可选的域名列表，用于限制搜索范围
        """
        # 如果使用统一客户端，尝试使用其search方法
        if self.use_unified_client:
            try:
                search_results = self.unified_client.search(
                    query=query,
                    max_results=max_results,
                    include_domains=include_domains
                )
                # 转换为SearchResult对象，并清理标题
                results = []
                for item in search_results:
                    original_title = item.get('title', '')
                    url = item.get('url', '')
                    # 清理标题
                    cleaned_title = clean_title(original_title, url)
                    # 清理摘要
                    raw_snippet = item.get('content', item.get('snippet', item.get('description', '')))
                    cleaned_snippet = clean_snippet(raw_snippet)

                    # 🔥 提取search_engine字段
                    search_engine = item.get('search_engine', 'Tavily')

                    results.append(SearchResult(
                        title=cleaned_title,
                        url=url,
                        snippet=cleaned_snippet,
                        source="Tavily",
                        search_engine=search_engine  # 🔥 传递搜索引擎字段
                    ))
                return results
            except Exception as e:
                print(f"[⚠️] 统一客户端搜索失败: {str(e)}，回退到原有实现")
                # 回退到原有实现
        
        # 原有实现
        endpoint = f"{self.base_url}/v1/search/"
        
        print(f"        [🔍 Tavily搜索] 原始查询: \"{query}\"")
        print(f"        [⚙️ 参数] max_results={max_results}, include_domains={include_domains}")
        
        payload = {
            "keywords": [query],
            "max_results": min(max_results, 20)
        }
        
        # 如果提供了域名列表，强制确保查询中包含site:语法
        # 重要：即使查询中已有site:语法，我们也强制重新构建以确保正确性
        if include_domains and len(include_domains) > 0:
            # 检查查询中是否已包含site:语法
            query_lower = query.lower()
            has_site_syntax = any(f"site:{domain.lower()}" in query_lower for domain in include_domains)
            
            print(f"        [🔍 检查] 查询词包含site:语法: {has_site_syntax}")
            print(f"        [🔍 检查] 查询词: \"{query}\"")
            print(f"        [🔍 检查] 目标域名: {include_domains[:5]}")
            
            # 强制添加site:语法（即使查询中已有，也重新构建以确保正确性）
            # 选择前5个最重要的域名（避免查询过长）
            selected_domains = include_domains[:5]
            domain_site_clause = " OR ".join([f"site:{domain}" for domain in selected_domains])
            
            # 如果查询中已有site:语法，先移除旧的site:部分
            if has_site_syntax:
                # 尝试移除旧的site:部分（使用正则表达式）
                # 移除 (site:xxx OR site:yyy) 这样的模式
                query_cleaned = re.sub(r'\s*\(site:[^)]+\)', '', query, flags=re.IGNORECASE)
                query_cleaned = query_cleaned.strip()
                # 如果清理后为空，使用原始查询
                if not query_cleaned:
                    query_cleaned = query
                enhanced_query = f"{query_cleaned} ({domain_site_clause})"
                print(f"        [🔧 处理] 查询中已有site:语法，清理后重新添加")
                print(f"        [🔧 处理] 清理后的查询: \"{query_cleaned}\"")
            else:
                # 如果查询中没有site:语法，直接添加
                enhanced_query = f"{query} ({domain_site_clause})"
                print(f"        [🔧 处理] 查询中缺少site:语法，添加域名限制")
            
            payload["keywords"] = [enhanced_query]
            print(f"        [✅ 确认] 最终查询（强制包含site:语法）: \"{enhanced_query}\"")
            print(f"        [✅ 确认] 使用的域名: {selected_domains}")
            
            # 同时尝试在payload中添加include_domains参数（如果API支持）
            # 注意：这取决于Tavily API的实际实现
            # payload["include_domains"] = include_domains[:5]
        
        print(f"        [📤 请求] Endpoint: {endpoint}")
        print(f"        [📤 请求] Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        try:
            from llm_client import get_proxy_config
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=30,
                proxies=get_proxy_config()
            )
            
            print(f"        [📥 响应] 状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"[📥 响应] 响应类型: {type(result).__name__}")
                print(f"[📥 响应] 响应键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
                print(f"[📥 响应] 完整 API 响应:\n{json.dumps(result, ensure_ascii=False, indent=2)}")
                
                results = []
                
                if isinstance(result, dict) and "queries" in result:
                    queries = result.get("queries", [])
                    print(f"[📥 响应] queries 数量: {len(queries)}")
                    
                    if queries:
                        query_result = queries[0]
                        tavily_response = query_result.get("response", {})
                        tavily_results = tavily_response.get("results", [])
                        print(f"[📥 响应] Tavily 结果数量: {len(tavily_results)}")
                        
                        for idx, item in enumerate(tavily_results[:max_results], 1):
                            # 清理标题和摘要
                            url = item.get('url', '')
                            original_title = item.get('title', '')
                            cleaned_title = clean_title(original_title, url)
                            raw_snippet = item.get('content', item.get('snippet', item.get('description', '')))
                            cleaned_snippet = clean_snippet(raw_snippet)

                            result_obj = SearchResult(
                                title=cleaned_title,
                                url=url,
                                snippet=cleaned_snippet,
                                source="Tavily",
                                search_engine="Tavily"
                            )
                            results.append(result_obj)
                            print(f"[📋 结果{idx}] {result_obj.title[:60]}...")
                            print(f"    URL: {result_obj.url}")
                            print(f"    Snippet 长度: {len(result_obj.snippet)} 字符")
                            print(f"    Snippet (前200字符): {result_obj.snippet[:200]}...")
                            # 检查是否匹配目标域名
                            if include_domains:
                                url_lower = result_obj.url.lower()
                                matched = any(domain.lower() in url_lower for domain in include_domains)
                                if matched:
                                    matched_domain = next((d for d in include_domains if d.lower() in url_lower), None)
                                    print(f"    ✅ 匹配目标域名: {matched_domain}")
                                else:
                                    print(f"    ⚠️ 未匹配目标域名")
                    else:
                        print(f"[⚠️ 响应] queries 为空")
                else:
                    print(f"[⚠️ 响应] 响应格式异常，缺少 queries 字段")
                    print(f"[📥 响应] 响应键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
                
                print(f"[✅ 完成] 返回 {len(results)} 个结果")
                print(f"{'='*80}\n")
                return results
            else:
                error_text = response.text[:500] if hasattr(response, 'text') else 'N/A'
                print(f"[❌ 错误] 搜索 API 调用失败")
                print(f"[❌ 错误] 状态码: {response.status_code}")
                print(f"[❌ 错误] 错误响应: {error_text}")
                raise ValueError(f"搜索 API 调用失败，状态码: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[❌ 错误] 搜索 API 请求异常: {str(e)}")
            print(f"[❌ 错误] 异常类型: {type(e).__name__}")
            import traceback
            print(f"[❌ 错误] 异常堆栈:\n{traceback.format_exc()}")
            raise ValueError(f"搜索 API 请求异常: {str(e)}")


# ============================================================================
# 搜索词生成器
# ============================================================================

# ============================================================================
# 结果评估器（复用规则匹配）
# ============================================================================

class ResultEvaluator:
    """结果评估器 - 🔒 当前已禁用（可重新启用）"""
    
    def __init__(self, llm_client: Optional[AIBuildersClient] = None):
        self.llm_client = llm_client or AIBuildersClient()
        print(f"    [✅ ResultEvaluator] 初始化（评估逻辑已禁用）")
    
    def _classify_resource_type(self, title: str, url: str, snippet: str) -> str:
        """
        基于规则和LLM分类资源类型
        返回：播放列表、视频、教材、教辅、练习题、其他
        """
        title_lower = title.lower()
        url_lower = url.lower()
        snippet_lower = snippet.lower() if snippet else ""
        combined_text = f"{title_lower} {url_lower} {snippet_lower}"

        # 0. 播放列表检查（优先级最高）
        # ⚠️ 排除博主的全部播放列表页面（不是单个视频合集）
        if any(exclude in url_lower for exclude in ['/playlists$', '/channel/', '/c/', '/user/']):
            # 这些是博主的全部播放列表页面，不是单个视频合集
            # 仍然标记为播放列表类型，但会在后续过滤中处理
            return "其他"

        # 检查URL中的播放列表特征（单个具体的播放列表）
        if any(indicator in url_lower for indicator in ['playlist?', 'list=', '/videos']):
            return "播放列表"

        # 检查标题中的播放列表关键词
        playlist_keywords = [
            'playlist', 'play list',
            'complete course', 'full course', 'all lessons',
            'series', 'collection',
            'قائمة التشغيل', 'سلسلة',  # 阿拉伯语
            '播放列表', '系列', '全套', '完整课程'
        ]
        if any(kw in combined_text for kw in playlist_keywords):
            # 如果标题包含播放列表关键词，但URL是/playlists页面，则排除
            if '/playlists' in url_lower and not any(ind in url_lower for ind in ['list=', 'playlist?']):
                return "其他"
            return "播放列表"

        # 1. 视频相关关键词
        video_keywords = [
            'video', 'youtube.com', 'youtu.be', 'watch',
            '播放', '视频', 'video pembelajaran',
            'video lesson', 'tutorial', '课程视频', 'lecture', 'lesson',
            'vimeo.com', 'bilibili.com/video', 'dailymotion.com'
        ]
        if any(keyword in combined_text for keyword in video_keywords):
            return "视频"

        # 2. 练习题相关关键词
        exercise_keywords = [
            'exercise', 'practice', 'quiz', 'test', 'exam', 'worksheet',
            '练习题', '练习', 'latihan', 'soal', 'ujian', 'kuis',
            'lembar kerja', 'lkpd', 'assess', 'assessment'
        ]
        if any(keyword in combined_text for keyword in exercise_keywords):
            return "练习题"

        # 3. 教材相关关键词（优先级高于教辅）
        textbook_keywords = [
            'textbook', 'book', '教材', '教科书', 'buku', 'buku pelajaran',
            'modul', 'module', 'coursebook', 'student book',
            'buku siswa', 'buku guru', 'kurikulum'
        ]
        if any(keyword in combined_text for keyword in textbook_keywords):
            return "教材"

        # 4. 教辅相关关键词
        supplement_keywords = [
            'guide', 'handbook', 'manual', '教辅', '参考书', 'panduan',
            '参考', 'supplement', '辅助材料', 'supplementary material',
            'bahan ajar', 'teaching material'
        ]
        if any(keyword in combined_text for keyword in supplement_keywords):
            return "教辅"

        # 5. PDF文件通常属于教材或教辅
        if '.pdf' in url_lower:
            # 进一步判断
            if any(kw in title_lower for kw in ['modul', 'buku', 'textbook', 'kurikulum']):
                return "教材"
            elif any(kw in title_lower for kw in ['panduan', 'guide', 'handbook']):
                return "教辅"
            else:
                return "教材"

        # 6. 学习资料相关
        learning_keywords = [
            'material', 'resource', 'content', '学习资料', '学习资源',
            'materi', 'bahan ajar', 'learning material', 'study material'
        ]
        if any(keyword in combined_text for keyword in learning_keywords):
            return "其他"

        # 7. 根据URL推断
        if 'slideshare.net' in url_lower or 'scribd.com' in url_lower:
            return "教辅"
        if 'kemdikbud.go.id' in url_lower:
            return "教材"

        # 默认返回"其他"
        return "其他"
    
    def evaluate_results(self, search_results: List[SearchResult],
                         country: str = "", grade: str = "", subject: str = "") -> List[SearchResult]:
        """
        评估搜索结果并分类资源类型

        功能：
        - 为每个结果分类资源类型（视频、教材、教辅、练习题）
        - 设置默认评分
        """
        if not search_results:
            return search_results

        print(f"    [ℹ️ 评估] 开始评估和分类 {len(search_results)} 个结果...")

        for result in search_results:
            # 分类资源类型
            resource_type = self._classify_resource_type(result.title, result.url, result.snippet)
            result.resource_type = resource_type

            # 设置默认评分
            if not result.score or result.score == 0:
                result.score = 7.5
            if not result.recommendation_reason:
                result.recommendation_reason = "默认推荐"
            if not result.source:
                result.source = "规则"

        # 统计分类结果
        type_counts = {}
        for result in search_results:
            rtype = result.resource_type or "未分类"
            type_counts[rtype] = type_counts.get(rtype, 0) + 1

        print(f"    [📊 分类统计] {', '.join([f'{k}:{v}' for k,v in type_counts.items()])}")

        return search_results
    


# ============================================================================
# 主搜索引擎
# ============================================================================

class SearchEngineV2:
    """新版搜索引擎"""

    def __init__(self, llm_client: Optional[AIBuildersClient] = None):
        self.llm_client = llm_client or AIBuildersClient()
        self.config_manager = ConfigManager()  # 用于读取国家配置

        # 初始化搜索策略代理
        self.strategy_agent = SearchStrategyAgent(
            llm_client=self.llm_client,
            config_manager=self.config_manager
        )

        # 初始化结果评估器
        self.evaluator = ResultEvaluator(llm_client=self.llm_client)

        # 🔥 移除 QueryGenerator（已被 IntelligentQueryGenerator 替代，功能重复）
        # IntelligentQueryGenerator 使用更新的模型（gemini-2.5-flash vs deepseek），效果更好
        # self.query_generator = QueryGenerator(
        #     llm_client=self.llm_client,
        #     config_manager=self.config_manager
        # )

        # 简单的配置管理器占位符（用于并行搜索配置）
        class SimpleConfigManager:
            def get_search_config(self):
                return {
                    'edtech_domains': [
                        'khanacademy.org', 'coursera.org', 'edx.org',
                        'youtube.com', 'vimeo.com', 'dailymotion.com'
                    ],
                    'localization': {
                        'ar': 'فيديو تعليمي',
                        'en': 'Video lesson',
                        'id': 'Video pelajaran',
                        'zh': '教学视频'
                    }
                }

        self.app_config = SimpleConfigManager()

        self.search_cache = get_search_cache()  # 搜索结果缓存
        # 评分器将在search方法中根据country_code动态初始化（带知识库）
        self.result_scorer = None  # 将在search时初始化为带知识库的评分器
        self.result_scorer_without_kb = get_result_scorer()  # 无知识库的备用评分器
        self._scorer_cache = {}  # 缓存各国的评分器 {country_code: scorer}
        self.recommendation_generator = get_recommendation_generator()  # LLM推荐理由生成器
        print(f"    [✅] 智能评分器已初始化（将在搜索时加载知识库）")
        print(f"    [✅] LLM推荐理由生成器已初始化")

        # 初始化百度搜索客户端（如果配置了）
        self.baidu_search_enabled = False
        try:
            baidu_api_key = os.getenv("BAIDU_API_KEY")
            if baidu_api_key:
                from search_strategist import SearchHunter
                self.baidu_hunter = SearchHunter(search_engine="baidu", llm_client=None)
                self.baidu_search_enabled = True
                print(f"    [✅] 百度搜索已启用")
            else:
                print(f"    [ℹ️] 百度搜索未配置（BAIDU_API_KEY未设置）")
        except Exception as e:
            print(f"    [⚠️] 百度搜索初始化失败: {str(e)}")
            self.baidu_search_enabled = False

        # 初始化 Google 搜索客户端（如果配置了）
        self.google_search_enabled = False
        try:
            google_api_key = os.getenv("GOOGLE_API_KEY")
            google_cx = os.getenv("GOOGLE_CX")
            if google_api_key and google_cx:
                from search_strategist import SearchHunter
                self.google_hunter = SearchHunter(search_engine="google", llm_client=None)
                self.google_search_enabled = True
                print(f"    [✅] Google 搜索已启用")
            else:
                print(f"    [ℹ️] Google 搜索未配置（需要 GOOGLE_API_KEY 和 GOOGLE_CX）")
        except Exception as e:
            print(f"    [⚠️] Google 搜索初始化失败: {str(e)}")
            self.google_search_enabled = False

    def _get_memory_usage(self) -> str:
        """获取当前内存使用情况"""
        try:
            import resource
            import sys
            rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            if sys.platform == 'darwin':
                rss_mb = rss_kb / 1024 / 1024
            else:
                rss_mb = rss_kb / 1024
            return f"{rss_mb:.1f} MB"
        except:
            return "Unknown"

    def _cached_search(self, query: str, search_func, engine_name: str, max_results: int = 15,
                       include_domains: Optional[List[str]] = None) -> List[SearchResult]:
        """
        带缓存的搜索包装器

        Args:
            query: 搜索查询
            search_func: 实际的搜索函数
            engine_name: 搜索引擎名称（用于缓存键）
            max_results: 最大结果数
            include_domains: 包含的域名列表

        Returns:
            搜索结果列表
        """
        # 尝试从缓存获取
        cache_key = f"{query}_{max_results}_{include_domains}"
        cached_result = self.search_cache.get(cache_key, engine_name)

        if cached_result is not None:
            logger.info(f"✅ 缓存命中 [{engine_name}]: {query[:50]}...")
            # 从缓存数据重建SearchResult对象
            return [SearchResult(**item) for item in cached_result]

        # 缓存未命中，执行实际搜索
        logger.info(f"❌ 缓存未命中 [{engine_name}]: {query[:50]}...")
        results = search_func(query, max_results, include_domains)

        # 将结果存入缓存
        results_dict = [result.model_dump() for result in results]
        self.search_cache.set(cache_key, results_dict, engine_name,
                             metadata={"query": query, "max_results": max_results})

        return results

    def _parallel_search(self, query: str, search_tasks: List[Dict[str, Any]],
                        timeout: int = 30, country_code: str = "CN") -> Dict[str, List[SearchResult]]:
        """
        并行执行多个搜索任务

        Args:
            query: 默认搜索查询（如果任务没有指定查询，则使用此查询）
            search_tasks: 搜索任务列表，每个任务包含:
                - name: 任务名称
                - query: 任务特定的搜索查询（可选，优先级高于默认query）
                - func: 搜索函数
                - engine_name: 搜索引擎名称（用于缓存）
                - max_results: 最大结果数
                - include_domains: 包含的域名（可选）
            timeout: 超时时间（秒）
            country_code: 国家代码（用于免费额度优先策略）

        Returns:
            字典，键为任务名称，值为搜索结果列表
        """
        results = {}
        start_time = time.time()

        print(f"    [⚡ 并行搜索] 启动 {len(search_tasks)} 个并行搜索任务")
        print(f"    [⚙️ 参数] 超时时间: {timeout}秒, 国家代码: {country_code}")

        def execute_search_task(task: Dict[str, Any]) -> tuple:
            """执行单个搜索任务"""
            task_name = task['name']
            search_func = task['func']
            engine_name = task['engine_name']
            max_results = task.get('max_results', 15)
            include_domains = task.get('include_domains', None)
            # 使用任务特定的查询，如果没有则使用默认查询
            task_query = task.get('query', query)

            try:
                task_start = time.time()

                # 判断是否是 llm_client.search（支持 country_code 参数）
                # 检查是否是 UnifiedLLMClient 的方法
                is_llm_client_search = (
                    hasattr(search_func, '__self__') and
                    isinstance(search_func.__self__, UnifiedLLMClient) and
                    search_func.__name__ == 'search'
                )

                if is_llm_client_search:
                    # llm_client.search 支持 country_code 参数（免费额度优先策略）
                    task_results = self._cached_search(
                        query=task_query,
                        search_func=lambda q, mr, id: search_func(q, max_results=mr, include_domains=include_domains, country_code=country_code),
                        engine_name=engine_name,
                        max_results=max_results,
                        include_domains=include_domains
                    )
                else:
                    # 其他搜索函数（google_hunter.search, baidu_hunter.search）不支持 country_code
                    task_results = self._cached_search(
                        query=task_query,
                        search_func=lambda q, mr, id: search_func(q, max_results=mr),
                        engine_name=engine_name,
                        max_results=max_results,
                        include_domains=include_domains
                    )

                task_elapsed = time.time() - task_start
                print(f"    [✅ {task_name}] 完成 ({task_elapsed:.2f}秒, {len(task_results)}个结果)")
                return (task_name, task_results)
            except Exception as e:
                print(f"    [❌ {task_name}] 失败: {str(e)}")
                logger.error(f"并行搜索任务失败 [{task_name}]: {str(e)}")
                return (task_name, [])

        # 使用线程池并行执行搜索（TODO：未来迁移到aiohttp以实现真正的异步I/O）
        # 当前使用ThreadPoolExecutor包装同步requests调用，已可并发执行但仍有改进空间
        # 优化建议：使用aiohttp + asyncio实现异步HTTP请求，性能可提升30%+
        with ThreadPoolExecutor(max_workers=min(len(search_tasks), 10)) as executor:  # 增加并发度（P1修复）
            # 提交所有任务
            future_to_task = {
                executor.submit(execute_search_task, task): task
                for task in search_tasks
            }

            # 收集完成的任务结果（添加超时保护）
            try:
                for future in as_completed(future_to_task, timeout=timeout):
                    try:
                        task_name, task_results = future.result(timeout=1.0)  # 单个future结果获取超时
                        results[task_name] = task_results
                    except concurrent.futures.TimeoutError:
                        logger.warning(f"任务 {future_to_task[future].get('name', 'unknown')} 结果获取超时")
                        results[future_to_task[future].get('name', 'unknown')] = []
                    except Exception as e:
                        logger.error(f"任务结果处理失败: {str(e)}")
                        results[future_to_task[future].get('name', 'unknown')] = []
            except concurrent.futures.TimeoutError:
                logger.warning(f"并行搜索整体超时 ({timeout}秒)，已收集部分结果")
                # 尝试获取已完成的任务结果
                for future in future_to_task:
                    if future.done():
                        try:
                            task_name, task_results = future.result(timeout=0.5)
                            if task_name not in results:
                                results[task_name] = task_results
                        except:
                            pass

        elapsed_time = time.time() - start_time
        total_results = sum(len(r) for r in results.values())
        print(f"    [⚡ 并行搜索] 完成，耗时 {elapsed_time:.2f}秒，共 {total_results} 个结果")

        return results

    def _is_edtech_domain(self, url: str) -> bool:
        """
        检查URL是否来自EdTech平台（知名教育平台）

        Args:
            url: 要检查的URL

        Returns:
            是否来自EdTech平台
        """
        try:
            search_config = self.app_config.get_search_config()
            edtech_domains = search_config.get('edtech_domains', [])

            url_lower = url.lower()
            for domain in edtech_domains:
                if domain.lower() in url_lower:
                    logger.debug(f"检测到EdTech平台: {domain}")
                    return True

            return False
        except Exception as e:
            logger.warning(f"检查EdTech域名失败: {str(e)}")
            return False

    def _generate_fallback_query(self, request: SearchRequest) -> str:
        """
        生成降级搜索词（规则生成，不使用LLM）

        Args:
            request: 搜索请求

        Returns:
            搜索词
        """
        # 规则生成默认搜索词
        default_query = f"{request.subject} {request.grade} playlist"
        if request.semester:
            default_query += f" semester {request.semester}"

        logger.info(f"[🔄 规则生成] 生成默认搜索词: \"{default_query}\"")
        return default_query

    def search(self, request: SearchRequest) -> SearchResponse:
        """
        执行搜索

        Args:
            request: 搜索请求

        Returns:
            搜索响应
        """
        # 性能监控 - 开始计时
        search_start_time = time.time()

        # 🔍 详细日志：搜索开始
        logger.info("="*80)
        logger.info(f"🔍 [搜索开始] {request.country} - {request.grade} - {request.subject}")
        logger.info(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"   内存使用: {self._get_memory_usage()}")
        logger.info("="*80)

        print(f"\n{'='*80}")
        print(f"🔍 开始搜索")
        print(f"{'='*80}")
        print(f"国家: {request.country}")
        print(f"年级: {request.grade}")
        print(f"学期: {request.semester or '不指定'}")
        print(f"学科: {request.subject}")
        print(f"{'='*80}\n")

        # ========== 年级-学科配对验证 ==========
        logger.info(f"[步骤 0] 年级-学科配对验证...")
        print(f"[验证] 检查年级-学科配对...")
        try:
            validator = GradeSubjectValidator()
            validation_result = validator.validate(
                request.country,
                request.grade,
                request.subject
            )

            if not validation_result["valid"]:
                # 配对不合法，显示警告但仍允许搜索
                warning_msg = f"⚠️ {validation_result['reason']}"
                print(f"    {warning_msg}")
                if validation_result.get("suggestions"):
                    print(f"    💡 建议: {', '.join(validation_result['suggestions'][:5])}")
                logger.warning(f"年级-学科配对验证失败: {request.country} {request.grade} {request.subject}")
            else:
                print(f"    ✅ 年级-学科配对验证通过")
                logger.info(f"   ✅ 配对验证通过")
        except Exception as e:
            print(f"    ⚠️ 验证失败，继续搜索: {str(e)}")
            logger.warning(f"配对验证异常: {str(e)}")
        # ========== 验证结束 ==========

        # ========== 📚 初始化带知识库的评分器 ==========
        try:
            from core.result_scorer import IntelligentResultScorer

            # 检查缓存中是否已有该国家的评分器
            country_code = request.country.upper()
            if country_code not in self._scorer_cache:
                # 创建带知识库的评分器
                self.result_scorer = IntelligentResultScorer(country_code=country_code)
                self._scorer_cache[country_code] = self.result_scorer
                logger.info(f"[📚 知识库] 已加载 {country_code} 评分器（带知识库）")
                print(f"    [✅ 知识库] 已加载 {country_code} 搜索知识库")
            else:
                # 使用缓存的评分器
                self.result_scorer = self._scorer_cache[country_code]
                logger.debug(f"[📚 知识库] 使用缓存的 {country_code} 评分器")

        except Exception as e:
            # 如果知识库加载失败，使用不带知识库的评分器
            logger.warning(f"[📚 知识库] 加载失败，使用备用评分器: {str(e)}")
            self.result_scorer = self.result_scorer_without_kb
        # ========== 评分器初始化结束 ==========

        try:
            # Step 0: 生成搜索策略
            step0_start = time.time()
            logger.info(f"[步骤 0] 制定搜索策略...")
            print(f"[步骤 0] 制定搜索策略...")
            strategy = self.strategy_agent.generate_strategy(
                country=request.country,
                grade=request.grade,
                subject=request.subject,
                semester=request.semester
            )
            print(f"    [✅ 策略] 搜索语言: {strategy.search_language}")
            print(f"    [✅ 策略] 使用中文搜索引擎: {strategy.use_chinese_search_engine}")
            print(f"    [✅ 策略] 平台列表: {', '.join(strategy.platforms[:5])}")
            print(f"    [✅ 策略] 优先域名: {', '.join(strategy.priority_domains[:5])}")
            if strategy.notes:
                print(f"    [📝 策略说明] {strategy.notes}")
            
            # Step 1: 生成搜索词（优先使用智能查询生成器）
            print(f"\n[步骤 1] 生成智能搜索词...")

            # 尝试使用IntelligentQueryGenerator
            try:
                from core.intelligent_query_generator import get_intelligent_query_generator
                intelligent_gen = get_intelligent_query_generator()

                query = intelligent_gen.generate_query(
                    country=request.country,
                    grade=request.grade,
                    subject=request.subject,
                    semester=request.semester
                )

                print(f"    [🤖 智能生成] 搜索词: \"{query}\"")
                print(f"    [✅ 优势] LLM自动识别语言和术语，支持多种输入格式")

                # 将智能生成的查询添加到策略中
                strategy.search_queries.insert(0, query)

            except Exception as e:
                print(f"    [⚠️ 智能生成失败，降级到策略生成器] {str(e)}")
                logger.warning(f"IntelligentQueryGenerator失败: {str(e)}，使用策略生成器")

                # 降级：使用策略中的搜索词或规则生成
                if strategy.search_queries:
                    # 使用策略中的第一个搜索词作为主查询
                    query = strategy.search_queries[0]
                    print(f"    [✅ 使用策略搜索词] \"{query}\"")
                else:
                    # 🔥 如果没有策略搜索词，使用规则生成（移除了QueryGenerator）
                    # QueryGenerator 已被 IntelligentQueryGenerator 替代，功能重复
                    query = self._generate_fallback_query(request)
                    print(f"    [✅ 使用规则生成搜索词] \"{query}\"")
                    strategy.search_queries = [query]  # 将生成的查询添加到策略中

            # 显示所有搜索词变体
            if len(strategy.search_queries) > 1:
                print(f"    [🎯 播放列表优化] 共有 {len(strategy.search_queries)} 个搜索词变体")
                for i, q in enumerate(strategy.search_queries, 1):
                    is_playlist_query = any(kw in q.lower() for kw in ['playlist', 'complete course', 'full series', 'koleksi', 'kursus lengkap', '播放列表', '完整课程', '系列'])
                    marker = "🎁 [播放列表]" if is_playlist_query else "📹 [常规]"
                    print(f"      {marker} {i}. \"{q}\"")

            # Step 2: 执行混合搜索（通用搜索 + 本地定向搜索）
            print(f"\n[步骤 2] 执行混合搜索...")

            # ========== 并行搜索实现 (新版本) ==========
            # 检查是否启用并行搜索（默认启用）
            use_parallel_search = os.getenv("ENABLE_PARALLEL_SEARCH", "true").lower() == "true"

            if use_parallel_search:
                print(f"    [⚡ 模式] 使用并行搜索")

                # 准备国家配置
                country_code_upper = request.country.upper()
                country_config = self.config_manager.get_country_config(country_code_upper)

                # 使用策略中的优先域名，如果没有则使用配置中的域名
                if strategy.priority_domains:
                    selected_domains = strategy.priority_domains[:5]
                elif country_config and country_config.domains:
                    selected_domains = country_config.domains[:5]
                else:
                    selected_domains = []

                # 构建并行搜索任务列表
                search_tasks = []

                # 使用策略中的多个搜索词进行搜索（优先播放列表相关查询）
                # 取前3个搜索词，确保至少包含播放列表查询
                queries_to_use = strategy.search_queries[:3] if len(strategy.search_queries) >= 3 else strategy.search_queries
                print(f"    [🎯 多查询搜索] 将使用 {len(queries_to_use)} 个搜索词进行搜索")

                # Google搜索（Google优先策略）- 对每个查询都执行（3次）✅ 主要引擎
                if self.google_search_enabled:
                    for query_idx, search_query in enumerate(queries_to_use, 1):
                        is_playlist_focused = any(kw in search_query.lower() for kw in ['playlist', 'complete course', 'full series', 'koleksi', 'kursus lengkap', '播放列表', '完整课程', '系列'])
                        query_type = "播放列表" if is_playlist_focused else "常规"

                        search_tasks.append({
                            'name': f'Google搜索 [{query_type}] #{query_idx}',
                            'query': search_query,  # 使用特定的搜索词
                            'func': self.google_hunter.search,
                            'engine_name': 'Google',
                            'max_results': 10,  # 减少每个查询的结果数，避免过多重复
                            'include_domains': None
                        })

                # Tavily/Metaso搜索 - 只使用第一个查询（1次）✅ 辅助引擎
                if len(queries_to_use) > 0:
                    search_tasks.append({
                        'name': 'Tavily/Metaso搜索',
                        'query': queries_to_use[0],  # 只用第一个查询
                        'func': self.llm_client.search,  # 内部会根据免费额度优先选择Tavily或Metaso
                        'engine_name': 'Tavily/Metaso',
                        'max_results': 15,
                        'include_domains': None
                    })

                # 任务3: 百度搜索（如果启用且需要中文搜索）
                if strategy.use_chinese_search_engine and self.baidu_search_enabled and len(queries_to_use) > 0:
                    search_tasks.append({
                        'name': '百度搜索',
                        'query': queries_to_use[0],  # 使用第一个查询
                        'func': self.baidu_hunter.search,
                        'engine_name': 'Baidu',
                        'max_results': 15,
                        'include_domains': None
                    })

                # 任务4: 本地定向搜索（如果有域名配置）
                if selected_domains:
                    # 构建本地搜索查询
                    base_query = query.replace("playlist", "").replace("Playlist", "").strip()

                    # 从配置读取本地化关键词
                    try:
                        search_config = self.app_config.get_search_config()
                        localization_keywords = search_config.get('localization', {})
                        country_language = country_config.language_code if country_config else "en"
                        local_keyword = localization_keywords.get(country_language, "Video lesson")
                        logger.debug(f"从配置读取本地化关键词: {country_language} -> {local_keyword}")
                    except Exception as e:
                        # 降级为硬编码映射
                        logger.warning(f"从配置读取本地化关键词失败: {str(e)}，使用硬编码映射")
                        language_map = {
                            "id": "Video pembelajaran",
                            "en": "Video lesson",
                            "zh": "教学视频",
                            "ms": "Video pembelajaran",
                            "ar": "فيديو تعليمي",
                            "ru": "Видео урок",
                        }
                        country_language = country_config.language_code if country_config else "en"
                        local_keyword = language_map.get(country_language, "Video lesson")

                    # 构建纯净查询
                    clean_query_parts = []
                    if request.subject:
                        clean_query_parts.append(request.subject)
                    if request.grade:
                        clean_query_parts.append(request.grade)
                    if request.semester:
                        clean_query_parts.append(request.semester)

                    local_base_query = " ".join(clean_query_parts) if clean_query_parts else base_query
                    local_query = f"{local_base_query} {local_keyword}".strip()

                    search_tasks.append({
                        'name': f'本地定向搜索({country_code_upper})',
                        'func': self.llm_client.search,
                        'engine_name': f'Local-{country_code_upper}',
                        'max_results': 10,
                        'include_domains': selected_domains
                    })

                # 执行并行搜索（传递 country_code 用于免费额度优先策略）
                parallel_results = self._parallel_search(query, search_tasks, timeout=30, country_code=request.country)

                # 合并所有结果
                search_results_a = []
                search_results_b = []

                for task_name, results in parallel_results.items():
                    if '本地' in task_name or 'Local' in task_name:
                        search_results_b.extend(results)
                    else:
                        search_results_a.extend(results)

                # 显示结果详情
                if search_results_a:
                    print(f"    [📋 通用搜索结果] 共 {len(search_results_a)} 个")
                    for idx, result in enumerate(search_results_a[:3], 1):
                        print(f"        {idx}. {result.title[:60]}...")

                if search_results_b:
                    print(f"    [📋 本地搜索结果] 共 {len(search_results_b)} 个")
                    for idx, result in enumerate(search_results_b[:3], 1):
                        print(f"        {idx}. {result.title[:60]}...")

            else:
                # ========== 串行搜索实现 (原版本) ==========
                print(f"    [🔄 模式] 使用串行搜索")

                # 搜索 A: 通用搜索（主要覆盖 YouTube）
            # 如果策略要求使用中文搜索引擎，且百度搜索已配置，则使用百度搜索
            if strategy.use_chinese_search_engine and self.baidu_search_enabled:
                print(f"    [🌐 策略] 检测到需要使用中文搜索引擎，使用百度搜索")
                print(f"    [🔍 搜索A-百度搜索] 查询: \"{query}\"")
                print(f"    [⚙️ 参数] max_results=15")
                try:
                    baidu_results = self.baidu_hunter.search(query, max_results=15)
                    # 转换为SearchResult对象
                    search_results_a = []
                    for item in baidu_results:
                        search_results_a.append(SearchResult(
                            title=item.title,
                            url=item.url,
                            snippet=item.snippet,
                            source="百度搜索",
                            search_engine="Baidu"
                        ))
                    print(f"    [✅ 搜索A-百度] 找到 {len(search_results_a)} 个结果")
                except Exception as e:
                    print(f"    [❌ 错误] 百度搜索失败: {str(e)}")
                    # 降级到 Google 搜索（如果可用）或 Tavily
                    if self.google_search_enabled:
                        print(f"    [🔄 降级] 切换到 Google 搜索...")
                        try:
                            google_results = self.google_hunter.search(query, max_results=15)
                            search_results_a = []
                            for item in google_results:
                                search_results_a.append(SearchResult(
                                    title=item.title,
                                    url=item.url,
                                    snippet=item.snippet,
                                    source="Google搜索",
                                    search_engine="Google"
                                ))
                            print(f"    [✅ 搜索A-Google] 找到 {len(search_results_a)} 个结果")
                        except Exception as e2:
                            print(f"    [❌ 错误] Google 搜索也失败: {str(e2)}")
                            print(f"    [🔄 降级] 切换到 Tavily 搜索...")
                            search_results_a = self.llm_client.search(query, max_results=15)
                            print(f"    [✅ 搜索A-Tavily] 找到 {len(search_results_a)} 个结果")
                    else:
                        print(f"    [🔄 降级] 切换到Tavily搜索...")
                        search_results_a = self.llm_client.search(query, max_results=15)
                        print(f"    [✅ 搜索A-Tavily] 找到 {len(search_results_a)} 个结果")
            else:
                if strategy.use_chinese_search_engine:
                    print(f"    [🌐 策略] 检测到需要使用中文搜索引擎（如百度、搜狗）")
                    if not self.baidu_search_enabled:
                        print(f"    [⚠️ 注意] 百度搜索未配置，使用其他搜索引擎，可能无法完全覆盖中文内容")
                    else:
                        print(f"    [ℹ️] 百度搜索已配置但未启用（可能策略判断不需要）")
                
                # 对于非中文搜索，优先使用 Google（如果配置了），否则使用 Tavily
                if self.google_search_enabled:
                    print(f"    [🔍 搜索A-Google] 查询: \"{query}\"")
                    print(f"    [⚙️ 参数] max_results=15")
                    try:
                        google_results = self.google_hunter.search(query, max_results=15)
                        search_results_a = []
                        for item in google_results:
                            search_results_a.append(SearchResult(
                                title=item.title,
                                url=item.url,
                                snippet=item.snippet,
                                source="Google搜索",
                                search_engine="Google"
                            ))
                        print(f"    [✅ 搜索A-Google] 找到 {len(search_results_a)} 个结果")
                    except Exception as e:
                        print(f"    [❌ 错误] Google 搜索失败: {str(e)}")
                        print(f"    [🔄 降级] 切换到 Tavily 搜索...")
                        # 🔥 从llm_client.search()返回的Dict转换为SearchResult
                        tavily_dicts = self.llm_client.search(query, max_results=15)
                        search_results_a = []
                        for item in tavily_dicts:
                            search_engine = item.get('search_engine', 'Tavily')
                            search_results_a.append(SearchResult(
                                title=item.get('title', ''),
                                url=item.get('url', ''),
                                snippet=item.get('snippet', ''),
                                source=item.get('source', 'Tavily'),
                                search_engine=search_engine
                            ))
                        print(f"    [✅ 搜索A-Tavily] 找到 {len(search_results_a)} 个结果")
                else:
                    print(f"    [🔍 搜索A-通用] 查询: \"{query}\"")
                    print(f"    [⚙️ 参数] max_results=15")
                    # 🔥 从llm_client.search()返回的Dict转换为SearchResult
                    search_dicts = self.llm_client.search(query, max_results=15)
                    search_results_a = []
                    for item in search_dicts:
                        search_engine = item.get('search_engine', 'Tavily')
                        search_results_a.append(SearchResult(
                            title=item.get('title', ''),
                            url=item.get('url', ''),
                            snippet=item.get('snippet', ''),
                            source=item.get('source', 'Tavily'),
                            search_engine=search_engine
                        ))
                    print(f"    [✅ 搜索A-Tavily] 找到 {len(search_results_a)} 个结果")
            if search_results_a:
                print(f"    [📋 搜索A结果详情]")
                for idx, result in enumerate(search_results_a[:5], 1):  # 只显示前5个
                    print(f"        {idx}. {result.title[:60]}...")
                    print(f"           URL: {result.url}")
                if len(search_results_a) > 5:
                    print(f"        ... 还有 {len(search_results_a) - 5} 个结果")
            
            # 搜索 B: 本地定向搜索（如果国家配置中有域名列表）
            print(f"\n    [🔍 搜索B-本地] 开始检查国家配置...")
            search_results_b = []
            country_code_upper = request.country.upper()
            print(f"    [📋 输入] 国家代码: {country_code_upper}")
            country_config = self.config_manager.get_country_config(country_code_upper)
            
            if country_config:
                print(f"    [✅ 配置] 成功读取国家配置: {country_config.country_name}")
                print(f"    [📋 配置] 域名数量: {len(country_config.domains)}")
                if country_config.domains:
                    print(f"    [📋 配置] 域名列表:")
                    for idx, domain in enumerate(country_config.domains, 1):
                        print(f"        {idx}. {domain}")
            else:
                print(f"    [⚠️ 配置] 国家配置不存在，跳过本地搜索")
            
            # 使用策略中的优先域名，如果没有则使用配置中的域名
            if strategy.priority_domains:
                selected_domains = strategy.priority_domains[:5]
                print(f"\n    [✅ 策略] 使用策略中的优先域名: {', '.join(selected_domains)}")
            elif country_config and country_config.domains:
                selected_domains = country_config.domains[:5]
                print(f"\n    [✅ 配置] 使用配置中的域名: {', '.join(selected_domains)}")
            else:
                selected_domains = []
            
            if selected_domains:
                # 使用策略中的优先域名或配置中的域名
                print(f"\n    [🔧 准备] 准备平台特定搜索...")
                print(f"    [📋 域名列表] 共 {len(selected_domains)} 个域名:")
                for idx, domain in enumerate(selected_domains, 1):
                    print(f"        {idx}. {domain}")
                
                if selected_domains:
                    
                    # 构建本地搜索词（移除playlist关键词，使用本地化词汇）
                    print(f"\n    [🔧 构建] 构建本地搜索词...")
                    print(f"    [📋 原始查询] \"{query}\"")
                    
                    # 移除playlist关键词（如果存在）
                    base_query = query.replace("playlist", "").replace("Playlist", "").strip()
                    
                    # 根据语言添加本地化关键词
                    language_map = {
                        "id": "Video pembelajaran",  # 印尼语
                        "en": "Video lesson",  # 英语
                        "zh": "教学视频",  # 中文
                        "ms": "Video pembelajaran",  # 马来语
                        "ar": "فيديو تعليمي",  # 阿拉伯语
                        "ru": "Видео урок",  # 俄语
                    }
                    country_language = country_config.language_code or "en"
                    local_keyword = language_map.get(country_language, "Video lesson")
                    
                    # 构建纯净的搜索词（学科 + 年级 + 学期）
                    clean_query_parts = []
                    if request.subject:
                        clean_query_parts.append(request.subject)
                    if request.grade:
                        clean_query_parts.append(request.grade)
                    if request.semester:
                        clean_query_parts.append(request.semester)
                    
                    # 使用纯净查询 + 本地化关键词
                    local_base_query = " ".join(clean_query_parts) if clean_query_parts else base_query
                    local_base_query = f"{local_base_query} {local_keyword}".strip()
                    
                    # 添加site:语法到查询末尾
                    domain_site_clause = " OR ".join([f"site:{domain}" for domain in selected_domains])
                    local_query = f"{local_base_query} ({domain_site_clause})"
                    
                    print(f"    [🔧 处理] 移除playlist关键词后的基础查询: \"{base_query}\"")
                    print(f"    [🔧 处理] 本地化关键词: \"{local_keyword}\"")
                    print(f"    [🔧 处理] 纯净查询: \"{local_base_query}\"")
                    print(f"    [🔧 处理] 添加site:语法后的最终查询: \"{local_query}\"")
                    print(f"\n    [🔍 搜索B-本地] 查询: \"{local_query}\"")
                    print(f"    [📍 目标平台] {', '.join(selected_domains)}")
                    print(f"    [⚙️ 参数] max_results=10, include_domains={selected_domains}")
                    search_results_b = self.llm_client.search(local_query, max_results=10, include_domains=selected_domains)
                    print(f"    [✅ 搜索B] 找到 {len(search_results_b)} 个结果")
                    if search_results_b:
                        print(f"    [📋 搜索B结果详情]")
                        for idx, result in enumerate(search_results_b, 1):
                            print(f"        {idx}. {result.title[:60]}...")
                            print(f"           URL: {result.url}")
                            # 检查 URL 是否来自目标平台
                            url_lower = result.url.lower()
                            matched_platform = None
                            for domain in selected_domains:
                                if domain.lower() in url_lower:
                                    matched_platform = domain
                                    break
                            if matched_platform:
                                print(f"           ✅ 匹配平台: {matched_platform}")
                            else:
                                print(f"           ⚠️ 未匹配到目标平台")
                    else:
                        print(f"    [⚠️ 搜索B] 未找到任何结果")
                else:
                    print(f"    [⚠️ 配置] 域名列表为空，跳过本地搜索")
            
            # 合并结果并去重（基于 URL）
            print(f"\n    [🔧 合并] 开始合并和去重...")
            all_results = search_results_a + search_results_b
            print(f"    [📊 合并前] 通用: {len(search_results_a)} 个, 本地: {len(search_results_b)} 个, 总计: {len(all_results)} 个")
            
            seen_urls = set()
            unique_results = []
            duplicate_count = 0
            
            for result in all_results:
                if result.url not in seen_urls:
                    seen_urls.add(result.url)
                    unique_results.append(result)
                else:
                    duplicate_count += 1
                    print(f"        [-] 去重: {result.url[:80]}...")
            
            search_results = unique_results
            print(f"    [📊 合并后] 去重: {duplicate_count} 个, 保留: {len(search_results)} 个")
            print(f"    [📊 统计] 通用: {len(search_results_a)}, 本地: {len(search_results_b)}, 最终: {len(search_results)}")
            
            # Step 3: 评估结果
            step3_start = time.time()
            logger.info(f"[步骤 3] 评估结果... (内存: {self._get_memory_usage()})")
            print(f"\n[步骤 3] 评估结果...")
            evaluated_results = self.evaluator.evaluate_results(
                search_results,
                country=request.country,
                grade=request.grade,
                subject=request.subject
            )
            step3_elapsed = time.time() - step3_start
            logger.info(f"   ✅ 步骤3完成: {step3_elapsed:.2f}秒, {len(evaluated_results)}个结果 (内存: {self._get_memory_usage()})")

            # Step 3.5: 智能评分和生成推荐理由
            step35_start = time.time()
            logger.info(f"[步骤 3.5] 智能评分开始... (内存: {self._get_memory_usage()})")
            print(f"\n[步骤 3.5] 智能评分...")

            # 快速获取播放列表信息（用于评分）
            def get_playlist_info_fast(url: str) -> Optional[Dict[str, Any]]:
                """快速获取播放列表信息（视频数量和总时长）"""
                if not url or 'list=' not in url:
                    return None

                try:
                    import yt_dlp

                    ydl_opts = {
                        'quiet': True,
                        'no_warnings': True,
                        'extract_flat': True,  # 快速提取
                        'http_headers': {
                            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)',
                        },
                        'extractor_args': {
                            'youtube': {
                                'player_client': ['ios'],
                            }
                        },
                    }

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)

                    if not info:
                        return None

                    entries = info.get('entries', [])
                    if not entries:
                        return None

                    video_count = len(entries)

                    # 计算总时长（分钟）
                    total_duration_seconds = 0
                    for entry in entries:
                        duration = entry.get('duration', 0)
                        if duration:
                            total_duration_seconds += duration

                    total_duration_minutes = total_duration_seconds / 60 if total_duration_seconds > 0 else 0

                    return {
                        'video_count': video_count,
                        'total_duration_minutes': total_duration_minutes
                    }

                except Exception as e:
                    logger.warning(f"获取播放列表信息失败: {str(e)[:100]}")
                    return None

            # 🚀 并发获取播放列表信息（优化性能）
            print(f"\n[步骤 3.5.1] 并发获取播放列表信息...")

            # 第一步：将SearchResult对象转换为字典，并识别播放列表
            results_dicts = []
            playlist_results = []  # 存储需要获取播放列表信息的结果

            for result in evaluated_results:
                result_dict = {
                    'title': result.title,
                    'url': result.url,
                    'snippet': result.snippet,
                    'source': result.source,
                    'resource_type': getattr(result, 'resource_type', 'unknown')
                }

                # 如果是播放列表URL，标记为需要获取信息
                if 'list=' in result.url:
                    playlist_results.append(result_dict)
                else:
                    # 非播放列表，直接添加
                    results_dicts.append(result_dict)

            # 第二步：并发获取所有播放列表信息
            if playlist_results:
                import concurrent.futures

                print(f"    [⚡ 并发] 发现 {len(playlist_results)} 个播放列表，开始并发获取信息...")

                # 设置并发参数
                MAX_PLAYLIST_WORKERS = 20  # 最多20个并发（修复：P1 - N+1查询优化）
                SINGLE_TIMEOUT = 8  # 单个播放列表8秒超时

                success_count = 0
                fail_count = 0

                with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_PLAYLIST_WORKERS) as executor:
                    # 提交所有任务
                    future_to_result = {
                        executor.submit(get_playlist_info_fast, r['url']): r
                        for r in playlist_results
                    }

                    # 🔧 修复：移除整体超时，避免部分超时导致整个搜索失败
                    # 收集结果（等待所有future完成）
                    for future in concurrent.futures.as_completed(future_to_result):
                        result_dict = future_to_result[future]

                        try:
                            # 单个超时控制
                            playlist_info = future.result(timeout=SINGLE_TIMEOUT)

                            if playlist_info:
                                result_dict['playlist_info'] = playlist_info
                                print(f"    [✅ 成功] {result_dict['title'][:40]}... - {playlist_info['video_count']}个视频, {playlist_info['total_duration_minutes']:.0f}分钟")
                                success_count += 1
                            else:
                                print(f"    [⚠️ 失败] {result_dict['title'][:40]}... - 无法获取信息")
                                fail_count += 1

                        except concurrent.futures.TimeoutError:
                            print(f"    [⏱️ 超时] {result_dict['title'][:40]}... - 获取超时({SINGLE_TIMEOUT}秒)")
                            fail_count += 1
                        except Exception as e:
                            print(f"    [❌ 异常] {result_dict['title'][:40]}... - {str(e)[:50]}")
                            fail_count += 1

                        # 无论如何都添加到结果列表
                        results_dicts.append(result_dict)

                print(f"    [📊 统计] 成功: {success_count}, 失败: {fail_count}, 总计: {len(playlist_results)}")
            else:
                print(f"    [ℹ️ 跳过] 没有播放列表需要获取信息")

            # ========== Step 3.5: 视觉快速评估（TOP 20） ==========
            # ⚠️ 临时禁用：视觉评估会导致请求超时（错误代码5）
            # 原因：TOP 20个结果串行处理需要5-10分钟，超过HTTP请求超时限制
            # TODO: 需要改为后台异步处理或大幅减少评估数量（TOP 5）

            # 读取环境变量控制是否启用（默认禁用）
            ENABLE_VISUAL_EVALUATION = os.getenv('ENABLE_VISUAL_EVALUATION', 'false').lower() == 'true'

            # 读取环境变量控制LLM评分数量（默认TOP 10，避免超时）
            LLM_SCORE_TOP_N = int(os.getenv('LLM_SCORE_TOP_N', '10'))

            if not ENABLE_VISUAL_EVALUATION:
                print(f"\n[步骤 3.5] 视觉评估已禁用（使用快速LLM评分模式）")
                print(f"    [ℹ️  提示] 如需启用视觉评估，设置环境变量: ENABLE_VISUAL_EVALUATION=true")
                print(f"    [⚡ 性能优化] 只对TOP {LLM_SCORE_TOP_N}个结果进行LLM评分")

                # ⚡ 优化：只对TOP N个结果进行LLM评分，避免超时
                if len(results_dicts) > LLM_SCORE_TOP_N:
                    top_n_results = results_dicts[:LLM_SCORE_TOP_N]
                    remaining_results = results_dicts[LLM_SCORE_TOP_N:]

                    # 对TOP N进行LLM评分
                    print(f"    [📊] TOP {len(top_n_results)} 个结果将进行LLM评分")
                    quickly_scored_results = top_n_results
                    # 剩余结果使用默认分数（不进行LLM评分）
                    quickly_scored_results.extend([{
                        **r,
                        'score': 5.0,  # 默认中等分数
                        'recommendation_reason': '未评分（超出TOP N限制）'
                    } for r in remaining_results])
                else:
                    # 结果数少于TOP N，全部评分
                    quickly_scored_results = results_dicts.copy()

                visually_scored_results = []
            else:
                print(f"\n[步骤 3.5] 视觉快速评估（TOP 5）...")

                # 提取TOP 5个结果进行视觉评估（减少数量避免超时）
                TOP_N = 5
                top_results = results_dicts[:TOP_N]
                remaining_results = results_dicts[TOP_N:]

                print(f"    [📊] TOP {len(top_results)} 个结果将进行视觉评估")
                print(f"    [📊] 剩余 {len(remaining_results)} 个结果将使用快速评分")

                # 并发截图TOP 5
                screenshot_results = {}
                successful_screenshots = 0

                if top_results:
                    try:
                        # 导入截图服务
                        import asyncio
                        from core.screenshot_service import get_screenshot_service

                        # 准备URL列表
                        urls_to_screenshot = [r['url'] for r in top_results]

                        print(f"    [📸] 开始并发截图 {len(urls_to_screenshot)} 个URL...")

                        # 异步批量截图（增加超时保护 + 自动资源释放 + 多层保险）
                        async def capture_screenshots_async():
                            service = None
                            browser = None
                            try:
                                # 创建截图服务
                                service = await get_screenshot_service()
                                browser = service.browser if hasattr(service, 'browser') else None

                                # 添加60秒总超时保护
                                result = await asyncio.wait_for(
                                    service.capture_batch(
                                        urls=urls_to_screenshot,
                                        wait_for='domcontentloaded',  # 使用更快的等待策略，避免YouTube超时
                                        full_page=False
                                    ),
                                    timeout=60.0  # 最多等待60秒
                                )
                                return result
                            except asyncio.TimeoutError:
                                logger.warning("截图超时(60秒)，部分截图可能失败")
                                return {}
                            except Exception as e:
                                logger.warning(f"截图服务异常: {str(e)[:100]}")
                                return {}
                            finally:
                                # 🔥 关键：多层保险确保资源释放（修复：P1 - 内存泄漏）
                                # 1. 关闭浏览器实例
                                if browser is not None:
                                    try:
                                        await browser.close()
                                        logger.debug("🗑️ 浏览器实例已关闭")
                                    except Exception as e:
                                        logger.debug(f"关闭浏览器实例失败（可忽略）: {str(e)[:50]}")

                                # 2. 停止截图服务
                                if service is not None:
                                    try:
                                        await service.stop()
                                        logger.debug("🗑️ 截图服务已关闭")
                                    except Exception as e:
                                        logger.debug(f"关闭截图服务失败（可忽略）: {str(e)[:50]}")

                                # 3. 强制垃圾回收，确保内存释放
                                try:
                                    import gc
                                    gc.collect()
                                    logger.debug("♻️ 已强制垃圾回收")
                                except Exception:
                                    pass

                        # 运行异步任务
                        screenshot_results = asyncio.run(capture_screenshots_async())

                        # 统计成功数量
                        successful_screenshots = sum(1 for path in screenshot_results.values() if path is not None)
                        print(f"    [✅ 截图完成] {successful_screenshots}/{len(urls_to_screenshot)} 成功")

                    except Exception as e:
                        logger.error(f"截图流程异常: {str(e)}")
                        print(f"    [❌ 截图失败] {str(e)[:100]}")
                        print(f"    [⚠️ 将降级到快速评分模式")
                        # 确保screenshot_results是字典
                        if 'screenshot_results' not in locals() or not isinstance(screenshot_results, dict):
                            screenshot_results = {}

                # 对有截图的结果使用视觉评估
                visually_scored_results = []
                quickly_scored_results = remaining_results.copy()

                for result_dict in top_results:
                    url = result_dict['url']
                    screenshot_path = screenshot_results.get(url)

                    if screenshot_path:
                        # 有截图，使用视觉评估（添加超时保护）
                        try:
                            import signal

                            # 准备metadata
                            country_config = self.config_manager.get_country_config(request.country.upper()) if self.config_manager else None
                            metadata = {
                                'country_name': country_config.name if country_config else '',
                                'grade_name': request.grade,
                                'subject_name': request.subject,
                                'language_code': country_config.language_code if country_config else 'en'
                            }

                            # 调用视觉评估（超时保护30秒）
                            def timeout_handler(signum, frame):
                                raise TimeoutError("视觉评估超时")

                            # 设置超时（仅Unix系统）
                            if hasattr(signal, 'SIGALRM'):
                                signal.signal(signal.SIGALRM, timeout_handler)
                                signal.alarm(30)  # 30秒超时

                            try:
                                visual_evaluation = self.result_scorer.evaluate_with_visual(
                                    result=result_dict,
                                    screenshot_path=screenshot_path,
                                    query=query,
                                    metadata=metadata
                                )
                            finally:
                                if hasattr(signal, 'SIGALRM'):
                                    signal.alarm(0)  # 取消超时

                            if visual_evaluation:
                                # 视觉评估成功
                                result_dict['score'] = visual_evaluation['score']
                                result_dict['recommendation_reason'] = visual_evaluation['recommendation_reason']
                                result_dict['evaluation_method'] = 'Visual'
                                result_dict['evaluation_details'] = visual_evaluation.get('evaluation_details', {})
                                result_dict['screenshot_path'] = screenshot_path
                                visually_scored_results.append(result_dict)
                                print(f"    [✅ 视觉评估] {result_dict['title'][:40]}... - {visual_evaluation['score']}/10")
                            else:
                                # 视觉评估失败，降级到快速评分
                                quickly_scored_results.append(result_dict)
                                print(f"    [⚠️ 降级] {result_dict['title'][:40]}... - 视觉评估失败，使用快速评分")

                        except TimeoutError:
                            logger.warning(f"视觉评估超时: {result_dict['title'][:40]}...")
                            print(f"    [⏱️ 超时] {result_dict['title'][:40]}... - 视觉评估超时，使用快速评分")
                            quickly_scored_results.append(result_dict)
                        except Exception as e:
                            logger.warning(f"视觉评估异常: {str(e)[:100]}")
                            quickly_scored_results.append(result_dict)
                    else:
                        # 没有截图，使用快速评分
                        quickly_scored_results.append(result_dict)

            # 对快速评分结果使用原有的LLM/规则评分
            if quickly_scored_results:
                llm_start = time.time()
                logger.info(f"[LLM评分] 开始: {len(quickly_scored_results)}个结果 (内存: {self._get_memory_usage()})")
                print(f"    [📊] 对 {len(quickly_scored_results)} 个结果进行快速评分（LLM/规则）...")

                # 获取国家语言代码
                language_code = None
                if self.config_manager:
                    country_config = self.config_manager.get_country_config(request.country.upper())
                    if country_config:
                        language_code = country_config.language_code

                quickly_scored = self.result_scorer.score_results(
                    results=quickly_scored_results,
                    query=query,
                    metadata={
                        'country': request.country,
                        'grade': request.grade,
                        'subject': request.subject,
                        'language_code': language_code
                    }
                )

                # 合并结果
                results_dicts = visually_scored_results + quickly_scored

                llm_elapsed = time.time() - llm_start
                logger.info(f"   ✅ LLM评分完成: {llm_elapsed:.2f}秒, {len(quickly_scored)}个结果 (内存: {self._get_memory_usage()})")
            else:
                results_dicts = visually_scored_results

            print(f"    [✅ 评估完成] 总计 {len(results_dicts)} 个结果 (视觉: {len(visually_scored_results)}, 快速: {len(quickly_scored_results)})")

            step35_elapsed = time.time() - step35_start
            logger.info(f"   ✅ 步骤3.5完成: {step35_elapsed:.2f}秒 (内存: {self._get_memory_usage()})")
            logger.info(f"   📊 评分结果: 视觉={len(visually_scored_results)}, 快速={len(quickly_scored_results)}")

            # 显示评分统计
            if results_dicts:
                scores = [r.get('score', 0) for r in results_dicts]
                avg_score = sum(scores) / len(scores) if scores else 0
                high_score_count = sum(1 for s in scores if s >= 8.0)
                visual_count = sum(1 for r in results_dicts if r.get('evaluation_method') == 'Visual')
                print(f"    [📊 评分统计] 平均分: {avg_score:.2f}, 高分(≥8): {high_score_count} 个, 视觉评估: {visual_count} 个")
                print(f"    [📊 前3名评分]:")
                for i, r in enumerate(results_dicts[:3], 1):
                    method = r.get('evaluation_method', 'Unknown')
                    print(f"        {i}. {r.get('score', 0):.1f}/10 [{method}] - {r.get('title', 'N/A')[:50]}...")

            # 将评分信息添加回SearchResult对象
            # ✅ 修复：使用original_index来正确匹配结果和评分（因为results_dicts已被排序）
            final_results = []
            scored_dict_by_index = {r.get('original_index'): r for r in results_dicts}

            for i, result in enumerate(evaluated_results):
                # 使用original_index查找对应的评分结果
                # 如果没有original_index，回退到顺序匹配（可能不准确）
                scored_dict = scored_dict_by_index.get(i, results_dicts[i] if i < len(results_dicts) else None)

                if scored_dict:
                    # 更新SearchResult对象
                    result.score = scored_dict.get('score', 0)
                    result.recommendation_reason = scored_dict.get('recommendation_reason', '')
                    # ✅ 保留evaluation_method（使用model_dump方式避免字段不存在的错误）
                    # 注意：SearchResult可能没有evaluation_method字段，所以我们不直接赋值
                    # 而是在字典中保留这个信息

                # ✅ 将评分信息保存为字典（保留evaluation_method）
                result_dict = result.model_dump()
                result_dict['evaluation_method'] = scored_dict.get('evaluation_method', 'LLM')
                final_results.append(SearchResult(**result_dict))

            evaluated_results = final_results

            # ✅ 在正确匹配分数后，按评分降序排序
            evaluated_results.sort(key=lambda x: x.score, reverse=True)
            logger.info(f"✅ 结果已按评分降序排序 (最高分: {evaluated_results[0].score if evaluated_results else 0:.1f})")

            # Step 4: 统计
            # 播放列表：YouTube播放列表或包含list=的URL
            playlist_count = sum(1 for r in evaluated_results if 
                               "youtube.com/playlist" in r.url.lower() or 
                               ("youtube.com/watch" in r.url.lower() and "list=" in r.url.lower()))
            
            # 视频：YouTube视频、B站视频或其他视频平台
            video_count = sum(1 for r in evaluated_results if 
                            "youtube.com/watch" in r.url.lower() or
                            "bilibili.com/video" in r.url.lower() or
                            "/video/" in r.url.lower())
            
            print(f"\n[步骤 4] 统计结果...")
            print(f"    [📊 统计] 播放列表: {playlist_count} 个")
            print(f"    [📊 统计] 视频: {video_count} 个")
            print(f"    [📊 统计] 总计: {len(evaluated_results)} 个")

            # 显示缓存统计
            cache_stats = self.search_cache.get_stats()
            print(f"\n[💾 缓存统计]")
            print(f"    [📊 统计] 命中次数: {cache_stats['hits']}")
            print(f"    [📊 统计] 未命中次数: {cache_stats['misses']}")
            print(f"    [📊 统计] 总查询次数: {cache_stats['total_queries']}")
            print(f"    [📊 统计] 命中率: {cache_stats['hit_rate']:.1%}")
            print(f"    [📊 统计] 缓存文件数: {cache_stats['cache_files_count']}")

            # 性能监控 - 记录成功的搜索
            search_duration = time.time() - search_start_time
            perf_monitor.record_metric(
                operation=f"search_{request.country.lower()}",
                duration=search_duration,
                success=True,
                metadata={
                    "country": request.country,
                    "grade": request.grade,
                    "subject": request.subject,
                    "result_count": len(evaluated_results),
                    "playlist_count": playlist_count,
                    "video_count": video_count,
                    "query": query
                }
            )

            # 🔧 修复：将SearchResult对象转换为字典（避免Pydantic验证错误）
            results_as_dicts = [r.model_dump() if hasattr(r, 'model_dump') else r.dict() for r in evaluated_results]

            # ========== 🤖 智能优化循环（质量评估 + 优化建议） ==========
            quality_report = None
            optimization_request = None

            try:
                # 检查是否启用智能优化（环境变量控制）
                enable_intelligent_optimization = os.getenv("ENABLE_INTELLIGENT_OPTIMIZATION", "true").lower() == "true"

                if enable_intelligent_optimization:
                    print(f"\n[🤖 智能优化] 开始质量评估...")

                    # 1. 质量评估
                    evaluator = QualityEvaluator()
                    search_params = {
                        'country': request.country,
                        'grade': request.grade,
                        'subject': request.subject,
                        'semester': request.semester
                    }
                    quality_report = evaluator.evaluate_single_search(results_as_dicts, search_params)

                    print(f"    [📊 质量分数] {quality_report['overall_quality_score']:.1f}/100")
                    print(f"    [🎯 质量等级] {quality_report['quality_level']}")
                    print(f"    [📈 平均分] {quality_report['basic_stats']['avg_score']:.2f}/10")

                    # 2. 判断是否需要优化
                    optimizer = IntelligentSearchOptimizer(search_engine=self)
                    should_opt, issues = optimizer.should_optimize(results_as_dicts, quality_report)

                    if should_opt:
                        print(f"    [⚠️ 检测到问题] {len(issues)}个")
                        for i, issue in enumerate(issues, 1):
                            print(f"      {i}. {issue}")

                        # 3. 生成优化方案
                        opt_request = optimizer.create_optimization_request(
                            results_as_dicts, quality_report, search_params, issues
                        )

                        # 4. 存储优化请求到审批管理器 (已禁用 - SIS功能)
                        # approval_manager = get_approval_manager()
                        # stored_request = approval_manager.create_request(opt_request)
                        # print(f"    [✅ 优化请求已创建] ID: {stored_request['request_id']}")
                        # print(f"    [📋 待审批方案] {len(stored_request['optimization_plans'])}个")
                        # optimization_request = stored_request
                        optimization_request = None
                    else:
                        print(f"    [✅ 质量良好] 无需优化")

            except Exception as opt_error:
                print(f"    [⚠️ 智能优化失败] {str(opt_error)}")
                logger.warning(f"智能优化失败: {str(opt_error)}", exc_info=True)
            # ========== 智能优化循环结束 ==========

            # 🔍 详细日志：搜索完成
            total_elapsed = time.time() - search_start_time
            logger.info("="*80)
            logger.info(f"✅ [搜索完成] {request.country} - {request.grade} - {request.subject}")
            logger.info(f"   总耗时: {total_elapsed:.2f}秒")
            logger.info(f"   结果数: {len(evaluated_results)}")
            logger.info(f"   内存使用: {self._get_memory_usage()}")
            logger.info(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            if quality_report:
                logger.info(f"   质量分数: {quality_report['overall_quality_score']:.1f}/100")
            logger.info("="*80)

            return SearchResponse(
                success=True,
                query=query,
                results=results_as_dicts,
                total_count=len(evaluated_results),
                playlist_count=playlist_count,
                video_count=video_count,
                message="搜索成功",
                quality_report=quality_report,
                optimization_request=optimization_request
            )
            
        except Exception as e:
            print(f"\n[❌ 错误] 搜索失败: {str(e)}")
            import traceback
            traceback.print_exc()

            # 性能监控 - 记录失败的搜索
            search_duration = time.time() - search_start_time
            perf_monitor.record_metric(
                operation=f"search_{request.country.lower()}",
                duration=search_duration,
                success=False,
                metadata={
                    "country": request.country,
                    "grade": request.grade,
                    "subject": request.subject,
                    "error": str(e)
                }
            )

            return SearchResponse(
                success=False,
                query="",
                results=[],
                message=f"搜索失败: {str(e)}"
            )

        except Exception as e:
            # 🔍 详细日志：搜索失败
            total_elapsed = time.time() - search_start_time
            logger.error("="*80)
            logger.error(f"❌ [搜索失败] {request.country} - {request.grade} - {request.subject}")
            logger.error(f"   错误类型: {type(e).__name__}")
            logger.error(f"   错误信息: {str(e)[:200]}")
            logger.error(f"   耗时: {total_elapsed:.2f}秒")
            logger.error(f"   内存使用: {self._get_memory_usage()}")
            logger.error(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.error("="*80)
            import traceback
            logger.error(f"堆栈信息:\n{traceback.format_exc()}")