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
import threading  # 🔒 P1线程安全: 添加线程锁支持
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
import concurrent.futures
from utils.config_manager import ConfigManager
from utils.logger_utils import get_logger
from utils.json_utils import extract_json_array
from search_strategy_agent import SearchStrategyAgent
from core.search_cache import get_search_cache
from core.multi_level_cache import get_cache as get_multi_level_cache
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
# 配置常量
# ============================================================================
DEFAULT_MAX_RESULTS = 50  # 🔧 P0-2: 默认返回50个结果（原20个）
MIN_SCORE_THRESHOLD = 5.0  # 🔧 P0-3: 最低评分阈值（原6.0）

# ============================================================================
# 安全工具函数 (P1 - SSRF防护)
# ============================================================================
import ipaddress
from urllib.parse import urlparse

def is_safe_url(url: str) -> bool:
    """
    验证URL以防止SSRF攻击

    Args:
        url: 待验证的URL字符串

    Returns:
        bool: True表示URL安全，False表示URL不安全
    """
    try:
        parsed = urlparse(url)

        # 检查协议 - 只允许HTTP和HTTPS
        if parsed.scheme not in ['http', 'https']:
            logger.warning(f"Blocked URL with unsafe scheme: {parsed.scheme}")
            return False

        # 解析主机名
        hostname = parsed.hostname
        if not hostname:
            logger.warning(f"Blocked URL with no hostname: {url}")
            return False

        # 阻止私有/内部IP地址
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private:
                logger.warning(f"Blocked private IP: {hostname}")
                return False
            if ip.is_loopback:
                logger.warning(f"Blocked loopback IP: {hostname}")
                return False
            if ip.is_link_local:
                logger.warning(f"Blocked link-local IP: {hostname}")
                return False
            if ip.is_reserved:
                logger.warning(f"Blocked reserved IP: {hostname}")
                return False
        except ValueError:
            # 不是IP地址，继续检查主机名
            pass

        # 阻止localhost和本地域名
        blocked_domains = [
            'localhost', '127.0.0.1', '0.0.0.0',
            'metadata.google.internal',  # GCP
            '169.254.169.254',           # AWS/Azure元数据端点
            'instance-data',             # AWS元数据域名
        ]

        if hostname.lower() in blocked_domains:
            logger.warning(f"Blocked internal domain: {hostname}")
            return False

        # 阻止内部主机名模式
        if hostname.endswith('.local') or hostname.endswith('.internal'):
            logger.warning(f"Blocked internal hostname pattern: {hostname}")
            return False

        return True

    except Exception as e:
        logger.warning(f"URL validation error for {url}: {str(e)}")
        return False


def sanitize_search_query(query: str) -> str:
    """
    清理搜索查询以防止注入攻击

    Args:
        query: 原始搜索查询字符串

    Returns:
        str: 清理后的安全查询字符串
    """
    if not query:
        return ""

    # 移除危险的搜索运算符（可能被用于SSRF或信息泄露）
    dangerous_patterns = [
        r'site:\s*[^\s\)]+',      # site: 运算符（可能用于SSRF）
        r'filetype:\s*\w+',        # filetype: 运算符
        r'cache:\s*[^\s\)]+',      # cache: 运算符
        r'link:\s*[^\s\)]+',       # link: 运算符
        r'info:\s*[^\s\)]+',       # info: 运算符
        r'loc:\s*[^\s\)]+',        # location 运算符
    ]

    original_query = query
    for pattern in dangerous_patterns:
        query = re.sub(pattern, '', query, flags=re.IGNORECASE)

    # 如果查询被修改，记录日志
    if query != original_query:
        logger.info(f"Sanitized search query (removed dangerous operators): {original_query[:100]} -> {query[:100]}")

    # 限制查询长度（防止DoS）
    query = query[:500]

    # 移除多余的空格
    query = ' '.join(query.split())

    return query.strip()


def validate_api_key(api_key: Optional[str], key_name: str = "API Key") -> str:
    """
    验证API密钥的有效性

    Args:
        api_key: 待验证的API密钥
        key_name: 密钥名称（用于错误消息）

    Returns:
        str: 验证后的API密钥

    Raises:
        ValueError: 如果API密钥无效
    """
    if not api_key:
        raise ValueError(f"{key_name} cannot be empty or None")

    api_key = api_key.strip()

    # 检查最小长度（防止空字符串或过短的密钥）
    if len(api_key) < 10:
        raise ValueError(f"{key_name} is too short (minimum 10 characters)")

    # 检查最大长度（防止DoS）
    if len(api_key) > 500:
        raise ValueError(f"{key_name} is too long (maximum 500 characters)")

    # 检查是否包含空白字符（API密钥不应该有空白）
    if ' ' in api_key or '\t' in api_key or '\n' in api_key:
        raise ValueError(f"{key_name} contains whitespace characters")

    # 检查是否是常见的占位符或示例值
    placeholders = [
        'your_api_key', 'your-key-here', 'replace_with_key',
        'example_key', 'test_key', 'xxx', 'placeholder',
        'api_key_here', 'secret_key_here'
    ]
    if api_key.lower() in placeholders:
        raise ValueError(f"{key_name} appears to be a placeholder value")

    return api_key


def validate_env_bool(env_var: Optional[str], var_name: str, default: bool = False) -> bool:
    """
    验证并解析布尔型环境变量

    Args:
        env_var: 环境变量的值
        var_name: 变量名称（用于错误消息）
        default: 默认值

    Returns:
        bool: 解析后的布尔值
    """
    if not env_var:
        return default

    env_var = env_var.strip().lower()

    if env_var in ('true', '1', 'yes', 'on', 'enabled'):
        return True
    elif env_var in ('false', '0', 'no', 'off', 'disabled'):
        return False
    else:
        logger.warning(f"Invalid boolean value for {var_name}: '{env_var}', using default: {default}")
        return default


def validate_env_int(env_var: Optional[str], var_name: str, default: int,
                    min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
    """
    验证并解析整数型环境变量

    Args:
        env_var: 环境变量的值
        var_name: 变量名称（用于错误消息）
        default: 默认值
        min_val: 最小值（可选）
        max_val: 最大值（可选）

    Returns:
        int: 解析后的整数值
    """
    if not env_var:
        return default

    try:
        value = int(env_var)

        # 检查范围
        if min_val is not None and value < min_val:
            logger.warning(f"{var_name} value {value} is below minimum {min_val}, using {min_val}")
            return min_val

        if max_val is not None and value > max_val:
            logger.warning(f"{var_name} value {value} is above maximum {max_val}, using {max_val}")
            return max_val

        return value

    except ValueError:
        logger.warning(f"Invalid integer value for {var_name}: '{env_var}', using default: {default}")
        return default


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


class SearchQueryMetadata(BaseModel):
    """单个搜索查询的元数据"""
    query: str = Field(description="搜索词")
    engine: str = Field(description="搜索引擎（Tavily/Google/Baidu）")
    result_count: int = Field(description="该搜索返回的结果数量")
    timestamp: str = Field(description="搜索时间")
    duration_ms: float = Field(description="搜索耗时（毫秒）")
    reasoning: str = Field(description="生成此搜索词的理由", default="")


class SearchTransparencyMetadata(BaseModel):
    """搜索透明度元数据"""
    # 搜索策略信息
    search_strategy: Dict[str, Any] = Field(description="搜索策略详情", default_factory=dict)

    # 搜索执行记录（包含所有执行的搜索）
    search_executions: List[Dict[str, Any]] = Field(description="所有执行的搜索查询", default_factory=list)

    # 搜索执行统计
    total_raw_results: int = Field(description="原始搜索结果总数", default=0)
    total_searches: int = Field(description="执行的搜索次数", default=0)
    total_duration_ms: float = Field(description="总搜索耗时（毫秒）", default=0.0)

    # 过滤流水线
    filtering_pipeline: List[Dict[str, Any]] = Field(description="过滤流水线各阶段", default_factory=list)
    filtered_samples: List[Dict[str, Any]] = Field(description="被过滤的结果样本", default_factory=list)

    # 评分分布
    score_distribution: Dict[str, int] = Field(description="分数分布（如{'8-10': 15, '6-8': 30}）", default_factory=dict)


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

    # 🔍 透明度元数据（新增）
    transparency: Optional[SearchTransparencyMetadata] = Field(description="搜索透明度信息", default=None)


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
        # 🔒 P1 环境变量验证: 获取并验证API token
        api_token_raw = api_token or os.getenv("AI_BUILDER_TOKEN")

        # 只有在提供了token时才验证（允许None用于某些场景）
        if api_token_raw:
            try:
                self.api_token = validate_api_key(api_token_raw, "AI_BUILDER_TOKEN")
            except ValueError as e:
                logger.error(f"Invalid AI_BUILDER_TOKEN: {str(e)}")
                raise ValueError(f"Invalid AI_BUILDER_TOKEN: {str(e)}")
        else:
            self.api_token = None

        # 尝试使用统一LLM客户端
        if HAS_UNIFIED_CLIENT:
            try:
                # 获取公司内部API密钥（可选）
                internal_api_key_raw = os.getenv("INTERNAL_API_KEY")
                internal_api_key = None
                if internal_api_key_raw:
                    try:
                        internal_api_key = validate_api_key(internal_api_key_raw, "INTERNAL_API_KEY")
                    except ValueError as e:
                        logger.warning(f"Invalid INTERNAL_API_KEY, will not use internal API: {str(e)}")

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
                 max_tokens: int = 8000, temperature: float = 0.3,  # [修复] 2026-01-20: 从2000增加到8000
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
                proxies=None  # [修复] 2026-01-20: AI Builders 是内网 API，不需要代理
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
                # 🔒 P1安全修复：使用logger和脱敏，避免暴露敏感错误信息
                error_text = response.text[:200] if hasattr(response, 'text') else 'N/A'  # 减少到200字符
                sanitized_error = safe_log(error_text)  # 脱敏错误信息
                logger.error(f"API call failed: {response.status_code}, error: {sanitized_error}")
                print(f"[❌ 错误] API 调用失败，状态码: {response.status_code}")
                raise ValueError(f"API 调用失败，状态码: {response.status_code}")
        except requests.exceptions.RequestException as e:
            # 🔒 P1 安全修复: 不暴露详细的异常信息和堆栈跟踪
            logger.error(f"API request failed: {type(e).__name__}")
            print(f"[❌ 错误] API 请求异常，请检查网络连接或联系管理员")
            raise ValueError(f"API 请求异常，请稍后重试")
            
    def search(self, query: str, max_results: int = 10, include_domains: list = None, country_code: str = None) -> list:
        """
        执行搜索 (适配 Tavily/Metaso)
        [修复] 2026-01-20: 添加 country_code 参数支持
        """
        # 1. 优先使用 UnifiedClient 的 search 方法（支持 Google/Tavily/Metaso）
        if self.use_unified_client:
            try:
                # 使用统一客户端的 search 方法，它会自动选择最佳的搜索引擎
                results_dicts = self.unified_client.search(
                    query=query,
                    max_results=max_results,
                    include_domains=include_domains,
                    country_code=country_code or "CN"  # 默认使用中国，可以传入其他代码
                )
                # Convert dicts to SearchResult objects
                results = []
                for item in results_dicts:
                    url = item.get('url', '')
                    # 🔒 P1 SSRF防护: 验证URL安全性
                    if not is_safe_url(url):
                        logger.warning(f"Blocked unsafe URL from search results: {url}")
                        continue  # 跳过不安全的URL

                    results.append(SearchResult(
                        title=item.get('title', ''),
                        url=url,
                        snippet=item.get('snippet', item.get('content', '')),
                        source=item.get('search_engine', 'Unknown'),
                        search_engine=item.get('search_engine', 'Unknown')
                    ))
                return results
            except Exception as e:
                # 🔒 P1 安全修复: 不暴露详细的异常信息和堆栈跟踪
                logger.error(f"UnifiedClient search failed: {type(e).__name__}")
                print(f"[⚠️ 搜索失败] UnifiedClient 搜索失败，请稍后重试")
        # 2. Fallback：返回空列表
        print(f"[❌ 搜索失败] 无可用的搜索引擎")
        return []


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

            # 设置默认评分 (修复: 移除虚假的默认评分)
            # if not result.score or result.score == 0:
            #     result.score = 7.5
            # if not result.recommendation_reason:
            #     result.recommendation_reason = "默认推荐"
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

@dataclass
class CountrySearchContext:
    """
    国家搜索上下文

    封装国家相关的搜索配置信息，消除重复的国家配置获取代码
    """
    country_code: str  # 国家代码（大写，如 "ID", "CN"）
    language_code: str  # 语言代码（如 "id", "zh"）
    domains: List[str]  # 优先域名列表
    config: Any  # 国家配置对象（可选）


class SearchEngineV2:
    """新版搜索引擎"""

    def __init__(self, llm_client: Optional[AIBuildersClient] = None, log_collector=None):
        self.llm_client = llm_client or AIBuildersClient()
        self.log_collector = log_collector  # 保存日志收集器引用
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

        self.search_cache = get_search_cache()  # 旧版单级缓存（兼容保留）
        self.multi_cache = get_multi_level_cache()  # 新版三级缓存（L1内存+L2Redis+L3磁盘）
        # 评分器将在search方法中根据country_code动态初始化（带知识库）
        self.result_scorer = None  # 将在search时初始化为带知识库的评分器
        self.result_scorer_without_kb = get_result_scorer()  # 无知识库的备用评分器
        self._scorer_cache = {}  # 缓存各国的评分器 {country_code: scorer}
        self._scorer_cache_lock = threading.Lock()  # 🔒 P1线程安全: 评分器缓存的线程锁
        self._playlist_cache = {}  # 🚀 P1性能优化: 缓存播放列表信息 {playlist_url: {video_count, duration}}
        self.recommendation_generator = get_recommendation_generator()  # LLM推荐理由生成器
        print(f"    [✅] 智能评分器已初始化（将在搜索时加载知识库）")
        print(f"    [✅] LLM推荐理由生成器已初始化")
        print(f"    [✅] 三级缓存系统已启用 (L1:内存100条/5分钟 + L2:Redis/1小时 + L3:磁盘/24小时)")

        # 🔍 初始化搜索透明度收集器
        from core.search_transparency_collector import get_transparency_collector
        self.transparency_collector = get_transparency_collector()
        logger.debug("    [✅] 搜索透明度收集器已初始化")

        # 初始化百度搜索客户端（如果配置了）
        self.baidu_search_enabled = False
        try:
            baidu_api_key_raw = os.getenv("BAIDU_API_KEY")
            if baidu_api_key_raw:
                # 🔒 P1 环境变量验证: 验证百度API密钥
                try:
                    baidu_api_key = validate_api_key(baidu_api_key_raw, "BAIDU_API_KEY")
                    from search_strategist import SearchHunter
                    self.baidu_hunter = SearchHunter(search_engine="baidu", llm_client=None)
                    self.baidu_search_enabled = True
                    print(f"    [✅] 百度搜索已启用")
                except ValueError as e:
                    logger.warning(f"BAIDU_API_KEY validation failed, skipping Baidu search: {str(e)}")
                    print(f"    [⚠️] 百度API密钥验证失败，跳过百度搜索: {str(e)}")
            else:
                print(f"    [ℹ️] 百度搜索未配置（BAIDU_API_KEY未设置）")
        except Exception as e:
            print(f"    [⚠️] 百度搜索初始化失败: {str(e)}")
            self.baidu_search_enabled = False

        # 初始化 Google 搜索客户端（如果配置了）
        self.google_search_enabled = False
        try:
            google_api_key_raw = os.getenv("GOOGLE_API_KEY")
            google_cx_raw = os.getenv("GOOGLE_CX")
            if google_api_key_raw and google_cx_raw:
                # 🔒 P1 环境变量验证: 验证Google API密钥和CX
                try:
                    google_api_key = validate_api_key(google_api_key_raw, "GOOGLE_API_KEY")
                    # CX需要特殊验证（通常较短）
                    if len(google_cx_raw.strip()) < 5:
                        raise ValueError("GOOGLE_CX is too short")
                    google_cx = google_cx_raw.strip()

                    from search_strategist import SearchHunter
                    self.google_hunter = SearchHunter(search_engine="google", llm_client=None)
                    self.google_search_enabled = True
                    print(f"    [✅] Google 搜索已启用")
                except ValueError as e:
                    logger.warning(f"Google API credentials validation failed: {str(e)}")
                    print(f"    [⚠️] Google API凭证验证失败，跳过Google搜索: {str(e)}")
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

    def _log_step(self, message: str, level: str = "info", emoji: str = "✅") -> None:
        """
        统一的步骤日志输出

        同时输出到控制台和日志文件，消除重复代码

        Args:
            message: 日志消息
            level: 日志级别
            emoji: 表情符号
        """
        formatted_msg = f"    [{emoji} {message}]"
        print(formatted_msg)

        logger_func = getattr(logger, level.lower(), logger.info)
        logger_func(f"[{message}]")

    def _get_country_context(self, country: str) -> CountrySearchContext:
        """
        获取国家搜索上下文

        封装重复的国家配置获取逻辑

        Args:
            country: 国家名称或代码

        Returns:
            CountrySearchContext 对象
        """
        country_code = country.upper()
        config = self.config_manager.get_country_config(country_code)

        return CountrySearchContext(
            country_code=country_code,
            language_code=config.language_code if config else "en",
            domains=config.domains[:5] if config else [],
            config=config
        )

    def _setup_visual_evaluation_timeout(self, timeout_seconds: int = 30) -> None:
        """
        设置视觉评估超时

        Args:
            timeout_seconds: 超时时间（秒）
        """
        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError("视觉评估超时")

        if hasattr(signal, 'SIGALRM'):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)

    def _clear_visual_evaluation_timeout(self) -> None:
        """清除视觉评估超时"""
        import signal
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)

    def _evaluate_with_visual_timeout(
        self,
        result_dict: dict,
        screenshot_path: str,
        query: str,
        metadata: dict,
        timeout_seconds: int = 30
    ) -> Optional[dict]:
        """
        带超时保护的视觉评估

        Args:
            result_dict: 结果字典
            screenshot_path: 截图路径
            query: 搜索查询
            metadata: 元数据
            timeout_seconds: 超时时间（秒）

        Returns:
            视觉评估结果字典，失败返回 None
        """
        try:
            # 设置超时
            self._setup_visual_evaluation_timeout(timeout_seconds)

            try:
                visual_evaluation = self.result_scorer.evaluate_with_visual(
                    result=result_dict,
                    screenshot_path=screenshot_path,
                    query=query,
                    metadata=metadata
                )
                return visual_evaluation
            finally:
                # 清除超时
                self._clear_visual_evaluation_timeout()

        except TimeoutError:
            logger.warning(f"视觉评估超时: {result_dict.get('title', '')[:40]}...")
            return None
        except Exception as e:
            logger.warning(f"视觉评估异常: {str(e)[:100]}")
            return None

    def _validate_grade_subject_pair(self, request: SearchRequest) -> None:
        """
        验证年级-学科配对

        Args:
            request: 搜索请求
        """
        from core.grade_subject_validator import GradeSubjectValidator

        logger.info("[步骤 0] 年级-学科配对验证...")
        print("[验证] 检查年级-学科配对...")
        try:
            validator = GradeSubjectValidator()
            validation_result = validator.validate(
                request.country,
                request.grade,
                request.subject
            )

            if not validation_result["valid"]:
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

    def _initialize_scorer_for_search(self, request: SearchRequest) -> None:
        """
        为搜索初始化评分器

        Args:
            request: 搜索请求
        """
        from core.result_scorer import IntelligentResultScorer

        country_code = request.country.upper()
        if country_code not in self._scorer_cache:
            self.result_scorer = IntelligentResultScorer(
                country_code=country_code,
                log_collector=self.log_collector
            )
            self._scorer_cache[country_code] = self.result_scorer
            logger.info(f"[📚 知识库] 已加载 {country_code} 评分器（带知识库和日志记录）")
            print(f"    [✅ 知识库] 已加载 {country_code} 搜索知识库")
        else:
            self.result_scorer = self._scorer_cache[country_code]
            if self.log_collector:
                self.result_scorer.log_collector = self.log_collector
            logger.debug(f"[📚 知识库] 使用缓存的 {country_code} 评分器")

    def _generate_default_search_queries(
        self,
        request: SearchRequest,
        language_code: str
    ) -> List[str]:
        """
        生成默认搜索查询

        Args:
            request: 搜索请求
            language_code: 语言代码

        Returns:
            搜索查询列表
        """
        playlist_keywords_map = {
            "id": ["playlist", "complete course", "full series", "koleksi lengkap", "kursus lengkap"],
            "en": ["playlist", "complete course", "full series", "video collection"],
            "zh": ["播放列表", "完整课程", "系列教程"],
            "ms": ["playlist", "kursus lengkap", "siri lengkap"],
            "ar": ["قائمة التشغيل", "دورة كاملة"],
            "ru": ["плейлист", "полный курс"],
        }
        playlist_keywords = playlist_keywords_map.get(language_code, ["playlist", "complete course"])

        return [
            f"site:youtube.com {request.subject} {request.grade} {playlist_keywords[0]}",
            f"{request.subject} {request.grade} {playlist_keywords[1] if len(playlist_keywords) > 1 else 'complete course'}",
            f"site:youtube.com \"{request.subject}\" \"{request.grade}\" playlist",
            f"{request.subject} {request.grade} video lesson chapter",
            f"{request.grade} {request.subject} full course curriculum",
            f"{request.subject} for {request.grade} students tutorial",
            f"{request.grade} {request.subject} learning series complete"
        ]

    def _get_default_search_strategy(self, request: SearchRequest) -> 'SearchStrategy':
        """
        生成默认搜索策略

        Args:
            request: 搜索请求

        Returns:
            SearchStrategy 对象
        """
        from search_strategy_agent import SearchStrategy

        ctx = self._get_country_context(request.country)

        search_queries = self._generate_default_search_queries(request, ctx.language_code)

        strategy = SearchStrategy(
            search_language=ctx.language_code,
            use_chinese_search_engine=(ctx.country_code == "CN"),
            platforms=["youtube.com"] + ctx.domains[:3],
            search_queries=search_queries,
            priority_domains=ctx.domains[:5],
            notes=f"默认搜索策略（规则生成）：使用{ctx.language_code}语言，优先搜索YouTube播放列表（7个差异化查询）"
        )

        return strategy

    def _cached_search(self, query: str, search_func, engine_name: str, max_results: int = 15,
                       include_domains: Optional[List[str]] = None) -> List[SearchResult]:
        """
        带多级缓存的搜索包装器

        使用三级缓存系统（L1内存+L2Redis+L3磁盘）提升性能
        [修复] 2026-01-20: 添加环境变量 ENABLE_MULTI_CACHE 控制缓存开关

        Args:
            query: 搜索查询
            search_func: 实际的搜索函数
            engine_name: 搜索引擎名称（用于缓存键）
            max_results: 最大结果数
            include_domains: 包含的域名列表

        Returns:
            搜索结果列表
        """
        # 🔒 P1 环境变量验证: 检查是否启用多级缓存
        enable_multi_cache = validate_env_bool(
            os.getenv("ENABLE_MULTI_CACHE"),
            "ENABLE_MULTI_CACHE",
            default=False
        )

        if enable_multi_cache:
            # 使用多级缓存系统（带查询规范化）
            cached_result = self.multi_cache.get(
                query=query,
                engine=engine_name,
                max_results=max_results,
                include_domains=include_domains
            )
        else:
            # 禁用缓存，直接执行搜索
            cached_result = None

        if cached_result is not None:
            cache_stats = self.multi_cache.get_stats()
            logger.info(
                f"✅ 多级缓存命中 [{engine_name}]: {query[:50]}... "
                f"(命中率: {cache_stats['hit_rate']:.1f}%, "
                f"L1:{cache_stats['l1_hit_rate']:.1f}% "
                f"L2:{cache_stats['l2_hit_rate']:.1f}% "
                f"L3:{cache_stats['l3_hit_rate']:.1f}%)"
            )
            # 从缓存数据重建SearchResult对象
            return [SearchResult(**item) for item in cached_result]

        # 缓存未命中，执行实际搜索
        if not enable_multi_cache:
            logger.info(f"⚠️ 多级缓存已禁用 [{engine_name}]: {query[:50]}...")
        else:
            logger.info(f"❌ 多级缓存未命中 [{engine_name}]: {query[:50]}...")
        results = search_func(query, max_results, include_domains)

        # 将结果存入多级缓存（仅在启用时）
        if enable_multi_cache:
            results_dict = [result.model_dump() for result in results]
            self.multi_cache.set(
                query=query,
                engine=engine_name,
                data=results_dict,
                ttl=3600,  # 1小时TTL
                max_results=max_results,
                include_domains=include_domains
            )
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
                    # ✨ 修复：检查搜索函数是否支持 country_code 参数
                    # 只给 Google Hunter 传递 country_code（用于本地化搜索）
                    # Tavily/Metaso/Baidu 不支持此参数
                    import inspect
                    func_name = search_func.__name__ if hasattr(search_func, '__name__') else str(search_func)
                    if hasattr(search_func, '__self__') and 'google_hunter' in str(type(search_func.__self__)):
                        # Google Hunter 支持 country_code 参数
                        task_results = self._cached_search(
                            query=task_query,
                            search_func=lambda q, mr, id: search_func(q, max_results=mr, country_code=country_code),
                            engine_name=engine_name,
                            max_results=max_results,
                            include_domains=include_domains
                        )
                    else:
                        # 其他搜索引擎不支持 country_code 参数
                        task_results = self._cached_search(
                            query=task_query,
                            search_func=lambda q, mr, id: search_func(q, max_results=mr),
                            engine_name=engine_name,
                            max_results=max_results,
                            include_domains=include_domains
                        )

                task_elapsed = time.time() - task_start
                print(f"    [✅ {task_name}] 完成 ({task_elapsed:.2f}秒, {len(task_results)}个结果)")

                # ========== 🔍 记录搜索执行到透明度收集器（P0-1） ==========
                self.transparency_collector.record_search_execution(
                    query=task_query,
                    engine=engine_name,
                    result_count=len(task_results),
                    duration_ms=task_elapsed * 1000,  # 转换为毫秒
                    reasoning=f"任务{task_name}，搜索{task_query}"
                )
                logger.debug(f"[🔍 透明度] 已记录搜索执行: {engine_name} - {len(task_results)}个结果")
                # ========== 搜索执行记录结束 ==========

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

        # 🔒 P1 SSRF防护: 清理搜索查询，移除危险运算符
        sanitized_query = sanitize_search_query(default_query)

        logger.info(f"[🔄 规则生成] 生成默认搜索词: \"{sanitized_query}\"")
        return sanitized_query

    def incremental_search(self, request: SearchRequest) -> SearchResponse:
        """
        渐进式搜索（优化方案一）

        特点：
        - 生成1个最优查询（而非5-7个）
        - 根据质量动态决定是否补充搜索
        - 高质量直接返回，中低质量进行补充搜索或重试
        - 显著降低API调用次数和响应时间

        Args:
            request: 搜索请求

        Returns:
            搜索响应
        """
        search_start_time = time.time()

        logger.info("="*80)
        logger.info(f"🎯 [渐进式搜索] {request.country} - {request.grade} - {request.subject}")
        logger.info("="*80)

        print(f"\n{'='*80}")
        print(f"🎯 渐进式搜索（优化方案一）")
        print(f"{'='*80}\n")

        # ========== Step 1: 生成最优查询 ==========
        print(f"[Step 1] 生成最优查询...")
        logger.info(f"[Step 1] 生成最优查询...")

        try:
            best_query = self.strategy_agent.generate_best_query(
                country=request.country,
                grade=request.grade,
                subject=request.subject,
                semester=request.semester
            )
            print(f"    [✅ 最优查询] \"{best_query}\"")
            logger.info(f"[✅ 最优查询] \"{best_query}\"")
        except Exception as e:
            logger.warning(f"[⚠️ LLM查询生成失败] {str(e)}，使用规则生成")
            best_query = self._generate_fallback_query(request)
            print(f"    [✅ 规则查询] \"{best_query}\"")

        # ========== Step 2: 初始搜索 ==========
        print(f"\n[Step 2] 执行初始搜索...")
        logger.info(f"[Step 2] 执行初始搜索...")

        initial_results = self._perform_initial_search(best_query, request.country)

        if not initial_results:
            logger.warning("[⚠️ 初始搜索无结果]，尝试降级策略")
            return self._handle_empty_results(request, best_query)

        print(f"    [✅ 初始结果] {len(initial_results)} 个")
        logger.info(f"[✅ 初始结果] {len(initial_results)} 个")

        # ========== Step 3: 快速质量评估 ==========
        print(f"\n[Step 3] 快速质量评估...")
        logger.info(f"[Step 3] 快速质量评估...")

        # 使用规则评分进行快速质量评估
        self._ensure_result_scorer(request.country)
        scored_results = self.result_scorer.score_results(
            initial_results,
            best_query,
            metadata={'country': request.country, 'grade': request.grade, 'subject': request.subject}
        )

        # 计算前10个结果的平均分
        top_10 = scored_results[:10]
        avg_score = sum(r.get('score', 0) for r in top_10) / len(top_10) if top_10 else 0.0

        print(f"    [📊 质量评估] 平均分: {avg_score:.2f}")
        logger.info(f"[📊 质量评估] 平均分: {avg_score:.2f}")

        # ========== Step 4-5: 根据质量决定后续策略 ==========
        if avg_score >= 7.0:
            # 高质量：直接返回
            print(f"    [✅ 高质量] 直接返回前20个结果")
            logger.info(f"[✅ 高质量] 直接返回前20个结果")
            return self._build_response(best_query, scored_results[:DEFAULT_MAX_RESULTS], search_start_time, request)

        elif avg_score >= 5.0:
            # 中等质量：补充搜索
            print(f"    [⚠️ 中等质量] 执行补充搜索...")
            logger.info(f"[⚠️ 中等质量] 执行补充搜索...")

            supplementary_results = self._perform_supplementary_search(
                best_query, request.country
            )

            if supplementary_results:
                print(f"    [✅ 补充结果] {len(supplementary_results)} 个")
                logger.info(f"[✅ 补充结果] {len(supplementary_results)} 个")

                # 合并并重新评分
                all_results = self._merge_and_deduplicate(
                    scored_results, supplementary_results, best_query, request
                )
                return self._build_response(best_query, all_results[:DEFAULT_MAX_RESULTS], search_start_time, request)
            else:
                print(f"    [⚠️ 补充搜索无结果]，返回初始结果")
                return self._build_response(best_query, scored_results[:DEFAULT_MAX_RESULTS], search_start_time, request)

        else:
            # 低质量：查询重试
            print(f"    [❌ 低质量] 尝试查询重试...")
            logger.info(f"[❌ 低质量] 尝试查询重试...")

            # 生成备选查询并重试
            for attempt in range(1, 4):  # 最多重试3次
                try:
                    alt_query = self.strategy_agent.generate_alternative_query(
                        country=request.country,
                        grade=request.grade,
                        subject=request.subject,
                        semester=request.semester,
                        attempt_number=attempt
                    )

                    print(f"    [🔄 重试 {attempt}] 使用备选查询: \"{alt_query}\"")
                    logger.info(f"[🔄 重试 {attempt}] 备选查询: \"{alt_query}\"")

                    retry_results = self._perform_initial_search(alt_query, request.country)

                    if retry_results:
                        retry_scored = self.result_scorer.score_results(
                            retry_results,
                            alt_query,
                            metadata={'country': request.country, 'grade': request.grade, 'subject': request.subject}
                        )

                        retry_top_10 = retry_scored[:10]
                        retry_avg = sum(r.get('score', 0) for r in retry_top_10) / len(retry_top_10)

                        print(f"    [📊 重试质量] 平均分: {retry_avg:.2f}")
                        logger.info(f"[📊 重试质量] 平均分: {retry_avg:.2f}")

                        if retry_avg >= 5.0:
                            print(f"    [✅ 重试成功] 返回重试结果")
                            logger.info(f"[✅ 重试成功] 返回重试结果")
                            return self._build_response(alt_query, retry_scored[:DEFAULT_MAX_RESULTS], search_start_time, request)

                except Exception as e:
                    logger.warning(f"[⚠️ 重试 {attempt} 失败]: {str(e)}")
                    continue

            # 所有重试都失败，返回初始结果
            print(f"    [⚠️ 所有重试失败]，返回初始最佳结果")
            logger.warning(f"[⚠️ 所有重试失败]，返回初始最佳结果")
            return self._build_response(best_query, scored_results[:DEFAULT_MAX_RESULTS], search_start_time, request)

    def _perform_initial_search(self, query: str, country_code: str) -> List[Dict]:
        """执行初始搜索（使用Tavily/Metaso）"""
        try:
            results = self.llm_client.search(
                query=query,
                max_results=30,
                country_code=country_code
            )

            # 转换为SearchResult格式
            search_results = []
            for r in results:
                url = r.get('url', '')
                # 🔒 P1 SSRF防护: 验证URL安全性
                if not is_safe_url(url):
                    logger.warning(f"Blocked unsafe URL from initial search: {url}")
                    continue  # 跳过不安全的URL

                search_results.append(SearchResult(
                    title=r.get('title', ''),
                    url=url,
                    snippet=r.get('content', r.get('snippet', '')),
                    source='规则',
                    search_engine=r.get('engine', 'Tavily/Metaso'),
                    score=0.0
                ))

            return search_results

        except Exception as e:
            logger.error(f"[❌ 初始搜索失败]: {str(e)}")
            return []

    def _perform_supplementary_search(self, query: str, country_code: str) -> List[Dict]:
        """执行补充搜索（使用Google）"""
        if not self.google_search_enabled:
            logger.info("[ℹ️ Google搜索未启用，跳过补充搜索]")
            return []

        try:
            results = self.google_hunter.search(
                query=query,
                max_results=20
            )

            # 转换为SearchResult格式
            search_results = []
            for r in results:
                url = r.get('url', '')
                # 🔒 P1 SSRF防护: 验证URL安全性
                if not is_safe_url(url):
                    logger.warning(f"Blocked unsafe URL from supplementary search: {url}")
                    continue  # 跳过不安全的URL

                search_results.append(SearchResult(
                    title=r.get('title', ''),
                    url=url,
                    snippet=r.get('snippet', ''),
                    source='规则',
                    search_engine='Google',
                    score=0.0
                ))

            return search_results

        except Exception as e:
            logger.error(f"[❌ 补充搜索失败]: {str(e)}")
            return []

    def _merge_and_deduplicate(self, initial_results: List[Dict],
                             supplementary_results: List[Dict],
                             query: str, request: SearchRequest) -> List[Dict]:
        """合并结果并去重"""
        seen_urls = {r['url'] for r in initial_results}
        merged = list(initial_results)

        for result in supplementary_results:
            if result['url'] not in seen_urls:
                merged.append(result)
                seen_urls.add(result['url'])

        # 重新评分合并后的结果
        scored = self.result_scorer.score_results(
            merged,
            query,
            metadata={'country': request.country, 'grade': request.grade, 'subject': request.subject}
        )

        # 按分数排序
        scored.sort(key=lambda x: x.get('score', 0), reverse=True)
        return scored

    def _handle_empty_results(self, request: SearchRequest, query: str) -> SearchResponse:
        """处理空结果的情况"""
        logger.warning(f"[⚠️ 空结果] 尝试使用备选查询...")

        # 尝试使用备选查询
        for attempt in range(1, 4):
            try:
                alt_query = self.strategy_agent.generate_alternative_query(
                    country=request.country,
                    grade=request.grade,
                    subject=request.subject,
                    semester=request.semester,
                    attempt_number=attempt
                )

                logger.info(f"[🔄 空结果重试 {attempt}]: \"{alt_query}\"")
                results = self._perform_initial_search(alt_query, request.country)

                if results:
                    scored = self.result_scorer.score_results(
                        results,
                        alt_query,
                        metadata={'country': request.country, 'grade': request.grade, 'subject': request.subject}
                    )
                    return self._build_response(alt_query, scored[:DEFAULT_MAX_RESULTS], time.time(), request)

            except Exception as e:
                logger.warning(f"[⚠️ 空结果重试 {attempt} 失败]: {str(e)}")
                continue

        # 所有尝试都失败，返回空响应
        return SearchResponse(
            success=False,
            query=query,
            results=[],
            total_count=0,
            playlist_count=0,
            video_count=0,
            message="未找到相关搜索结果，请尝试调整搜索关键词"
        )

    def _build_response(self, query: str, results: List[SearchResult],
                       start_time: float, request: SearchRequest) -> SearchResponse:
        """构建搜索响应"""
        elapsed = time.time() - start_time

        # 统计播放列表和视频数量
        playlist_count = sum(1 for r in results if 'playlist' in r.title.lower())
        video_count = len(results) - playlist_count

        logger.info(f"[✅ 搜索完成] 耗时: {elapsed:.2f}秒, 结果: {len(results)}个")
        print(f"    [✅ 完成] 耗时: {elapsed:.2f}秒, 返回: {len(results)}个结果\n")

        return SearchResponse(
            success=True,
            query=query,
            results=results,
            total_count=len(results),
            playlist_count=playlist_count,
            video_count=video_count,
            message=f"搜索完成，耗时 {elapsed:.2f} 秒"
        )

    def _ensure_result_scorer(self, country_code: str):
        """
        确保已初始化带知识库的评分器（线程安全）

        Args:
            country_code: 国家代码
        """
        # 🔒 P1线程安全: 首先检查无锁情况（快速路径）
        if country_code in self._scorer_cache:
            self.result_scorer = self._scorer_cache[country_code]
            return

        # 🔒 P1线程安全: 使用锁防止竞态条件
        with self._scorer_cache_lock:
            # 双重检查：可能在等待锁时其他线程已经初始化
            if country_code in self._scorer_cache:
                self.result_scorer = self._scorer_cache[country_code]
                return

            try:
                from core.result_scorer import get_result_scorer_with_kb
                scorer = get_result_scorer_with_kb(country_code)
                self._scorer_cache[country_code] = scorer
                logger.info(f"[✅ 评分器] 已加载 {country_code} 知识库评分器")
            except Exception as e:
                logger.warning(f"[⚠️ 评分器] 无法加载知识库评分器: {e}")
                self._scorer_cache[country_code] = self.result_scorer_without_kb

            self.result_scorer = self._scorer_cache.get(country_code, self.result_scorer_without_kb)

    def _validate_grade_subject_pair(self, request: SearchRequest) -> None:
        """
        验证年级-学科配对是否合法

        Args:
            request: 搜索请求
        """
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

    def _initialize_transparency_collector(self) -> None:
        """初始化搜索透明度收集器"""
        self.transparency_collector.reset()
        self.transparency_collector.start_search()
        logger.debug("[🔍 透明度] 收集器已重置并开始记录")

    def _initialize_intelligent_scorer(self, country_code: str) -> None:
        """
        初始化带知识库的智能评分器（线程安全）

        Args:
            country_code: 国家代码
        """
        # 🔒 P1线程安全: 首先检查无锁情况（快速路径）
        if country_code in self._scorer_cache:
            self.result_scorer = self._scorer_cache[country_code]
            # 更新 log_collector（可能是新的搜索请求）
            if self.log_collector:
                self.result_scorer.log_collector = self.log_collector
            logger.debug(f"[📚 知识库] 使用缓存的 {country_code} 评分器")
            return

        # 🔒 P1线程安全: 使用锁防止竞态条件
        with self._scorer_cache_lock:
            # 双重检查：可能在等待锁时其他线程已经初始化
            if country_code in self._scorer_cache:
                self.result_scorer = self._scorer_cache[country_code]
                # 更新 log_collector（可能是新的搜索请求）
                if self.log_collector:
                    self.result_scorer.log_collector = self.log_collector
                logger.debug(f"[📚 知识库] 使用缓存的 {country_code} 评分器")
                return

            try:
                from core.result_scorer import IntelligentResultScorer

                # 创建带知识库的评分器（传递 log_collector）
                self.result_scorer = IntelligentResultScorer(
                    country_code=country_code,
                    log_collector=self.log_collector
                )
                self._scorer_cache[country_code] = self.result_scorer
                logger.info(f"[📚 知识库] 已加载 {country_code} 评分器（带知识库和日志记录）")
                print(f"    [✅ 知识库] 已加载 {country_code} 搜索知识库")

            except Exception as e:
                # 如果知识库加载失败，使用不带知识库的评分器
                logger.warning(f"[📚 知识库] 加载失败，使用备用评分器: {str(e)}")
                self.result_scorer = self.result_scorer_without_kb
                self._scorer_cache[country_code] = self.result_scorer_without_kb

            # 也更新 log_collector
            if self.log_collector:
                self.result_scorer.log_collector = self.log_collector

    def get_playlist_info_fast(self, url: str) -> Optional[Dict[str, Any]]:
        """
        快速获取播放列表信息（带缓存）- P1性能优化

        Args:
            url: 播放列表URL

        Returns:
            包含video_count和total_duration_minutes的字典，或None
        """
        if not url or 'list=' not in url:
            return None

        # 🔒 P1 SSRF防护: 验证URL安全性
        if not is_safe_url(url):
            logger.warning(f"Blocked unsafe URL in playlist info extraction: {url}")
            return None

        # 🚀 P1性能优化: 检查缓存
        if url in self._playlist_cache:
            logger.debug(f"Playlist info cache hit for: {url[:50]}...")
            return self._playlist_cache[url]

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

            result = {
                'video_count': video_count,
                'total_duration_minutes': total_duration_minutes
            }

            # 🚀 P1性能优化: 存入缓存
            self._playlist_cache[url] = result
            logger.info(f"Cached playlist info: {video_count} videos, {total_duration_minutes:.1f} minutes")

            return result

        except Exception as e:
            logger.warning(f"获取播放列表信息失败: {str(e)[:100]}")
            return None

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

        # ========== 初始化步骤 ==========
        # 年级-学科配对验证
        logger.info(f"[步骤 0] 年级-学科配对验证...")
        self._validate_grade_subject_pair(request)

        # 初始化透明度收集器
        self._initialize_transparency_collector()

        # 初始化智能评分器
        country_code = request.country.upper()
        self._initialize_intelligent_scorer(country_code)
        # ========== 初始化步骤结束 ==========

        try:
            # Step 0: 获取搜索策略（已跳过LLM生成，直接使用默认策略）
            # [优化] 2026-01-20: 跳过LLM策略生成，直接使用默认规则策略，提升响应速度
            step0_start = time.time()
            logger.info(f"[步骤 0] 获取搜索策略（使用默认规则策略）...")
            print(f"[步骤 0] 获取搜索策略（已跳过LLM生成，使用默认规则策略）...")

            # 直接使用默认策略，跳过LLM生成
            from search_strategy_agent import SearchStrategy
            country_config = self.config_manager.get_country_config(request.country.upper())
            language_code = country_config.language_code if country_config else "en"
            domains = country_config.domains[:5] if country_config else []

            # 构建默认搜索词（规则生成，不使用LLM）
            default_query = f"{request.subject} {request.grade} playlist"
            if request.semester:
                default_query += f" semester {request.semester}"

            # 🔒 P1 SSRF防护: 清理搜索查询，移除危险运算符
            default_query = sanitize_search_query(default_query)

            # 生成多个播放列表优先的搜索查询（7个高度差异化的变体）
            playlist_keywords_map = {
                "id": ["playlist", "complete course", "full series", "koleksi lengkap", "kursus lengkap"],
                "en": ["playlist", "complete course", "full series", "video collection"],
                "zh": ["播放列表", "完整课程", "系列教程"],
                "ms": ["playlist", "kursus lengkap", "siri lengkap"],
                "ar": ["قائمة التشغيل", "دورة كاملة"],
                "ru": ["плейлист", "полный курс"],
            }
            playlist_keywords = playlist_keywords_map.get(language_code, ["playlist", "complete course"])

            # 生成7个差异化搜索查询
            search_queries = [
                f"site:youtube.com {request.subject} {request.grade} {playlist_keywords[0]}",
                f"{request.subject} {request.grade} {playlist_keywords[1] if len(playlist_keywords) > 1 else 'complete course'}",
                f"site:youtube.com \"{request.subject}\" \"{request.grade}\" playlist",
                f"{request.subject} {request.grade} video lesson chapter",
                f"{request.grade} {request.subject} full course curriculum",
                f"{request.subject} for {request.grade} students tutorial",
                f"{request.grade} {request.subject} learning series complete"
            ]

            # 创建策略对象（不使用LLM）
            strategy = SearchStrategy(
                search_language=language_code,
                use_chinese_search_engine=(request.country.upper() == "CN"),
                platforms=["youtube.com"] + domains[:3],
                search_queries=search_queries,
                priority_domains=domains[:5],
                notes=f"默认搜索策略（规则生成）：使用{language_code}语言，优先搜索YouTube播放列表（7个差异化查询）"
            )

            print(f"    [✅ 策略] 搜索语言: {strategy.search_language}")
            print(f"    [✅ 策略] 使用中文搜索引擎: {strategy.use_chinese_search_engine}")
            print(f"    [✅ 策略] 平台列表: {', '.join(strategy.platforms[:5])}")
            print(f"    [✅ 策略] 优先域名: {', '.join(strategy.priority_domains[:5])}")
            print(f"    [⚡ 优化] 跳过LLM生成，使用默认规则策略，提升响应速度")

            # ========== 🔍 记录搜索策略到透明度收集器（P0-1） ==========
            self.transparency_collector.record_strategy({
                "search_language": strategy.search_language,
                "use_chinese_search_engine": strategy.use_chinese_search_engine,
                "platforms": strategy.platforms,
                "search_queries": strategy.search_queries,
                "priority_domains": strategy.priority_domains,
                "notes": strategy.notes
            })
            logger.debug(f"[🔍 透明度] 已记录搜索策略: {len(strategy.search_queries)} 个查询")
            # ========== 策略记录结束 ==========

            # Step 1: 使用搜索策略中的搜索词
            print(f"\n[步骤 1] 使用搜索策略生成的高质量搜索词...")

            # 直接使用策略生成的搜索词（已包含多个变体，包括playlist等优化）
            if strategy.search_queries:
                query = strategy.search_queries[0]
                print(f"    [✅ 使用策略搜索词] \"{query}\"")
                print(f"    [✅ 优势] 策略已生成 {len(strategy.search_queries)} 个高质量变体")
            else:
                # 降级：如果策略中没有搜索词，使用规则生成
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
            # 🔒 P1 环境变量验证: 检查是否启用并行搜索（默认启用）
            use_parallel_search = validate_env_bool(
                os.getenv("ENABLE_PARALLEL_SEARCH"),
                "ENABLE_PARALLEL_SEARCH",
                default=True
            )

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

                # 🚀 P1性能优化：减少API调用次数（从7-8次减少到2-3次）
                # 使用策略中的最优质2-3个搜索词进行搜索
                # 优先级：1) YouTube播放列表搜索 2) 通用播放列表搜索 3) 精确匹配搜索
                queries_to_use = strategy.search_queries[:3] if len(strategy.search_queries) >= 3 else strategy.search_queries
                print(f"    [🎯 优化搜索] 将使用 {len(queries_to_use)} 个高质量搜索词（减少API调用）")

                # Tavily/Metaso搜索 - 只对前2个最佳查询执行（2次）✅ 主要引擎（高质量，avg 4.65）
                # 🚀 P1优化：减少查询数量，从5个降低到2个，减少60%的API调用
                for query_idx, search_query in enumerate(queries_to_use[:2], 1):
                    is_playlist_focused = any(kw in search_query.lower() for kw in ['playlist', 'complete course', 'full series', 'koleksi', 'kursus lengkap', '播放列表', '完整课程', '系列'])
                    query_type = "播放列表" if is_playlist_focused else "常规"

                    search_tasks.append({
                        'name': f'Tavily/Metaso搜索 [{query_type}] #{query_idx}',
                        'query': search_query,  # 使用特定的搜索词
                        'func': self.llm_client.search,  # 内部会根据免费额度优先选择Tavily或Metaso
                        'engine_name': 'Tavily/Metaso',
                        'max_results': 30,  # 增加到30，获取更多结果
                        'include_domains': None
                    })

                # 🚀 P1优化：移除Google搜索（低质量，avg 1.50），减少不必要的API调用
                # Google搜索结果质量远低于Tavily/Metaso，性价比低
                # if self.google_search_enabled and len(queries_to_use) > 0:
                #     search_tasks.append({...})

                # 任务3: 百度搜索（如果启用且需要中文搜索）
                if strategy.use_chinese_search_engine and self.baidu_search_enabled and len(queries_to_use) > 0:
                    search_tasks.append({
                        'name': '百度搜索',
                        'query': queries_to_use[0],  # 使用第一个查询
                        'func': self.baidu_hunter.search,
                        'engine_name': 'Baidu',
                        'max_results': 30,  # 增加到30
                        'include_domains': None
                    })

                # 🚀 P1优化：本地定向搜索（条件性启用，仅在Tavily/Metaso结果不足时）
                # 策略：先执行主搜索，如果结果数量<30，再启用本地定向搜索作为补充
                # 这样可以避免不必要的API调用，提升性能
                # if selected_domains:
                #     # ... 本地定向搜索逻辑 ...
                # 注意：本地定向搜索已移至主搜索之后，根据结果数量动态决定是否执行

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
                print(f"    [⚙️ 参数] max_results=30")
                try:
                    baidu_results = self.baidu_hunter.search(query, max_results=30)
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
                            google_results = self.google_hunter.search(query, max_results=30, country_code=country_code_upper)
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
                            search_results_a = self.llm_client.search(query, max_results=30, country_code=country_code_upper)
                            print(f"    [✅ 搜索A-Tavily] 找到 {len(search_results_a)} 个结果")
                    else:
                        print(f"    [🔄 降级] 切换到Tavily搜索...")
                        search_results_a = self.llm_client.search(query, max_results=30, country_code=country_code_upper)
                        print(f"    [✅ 搜索A-Tavily] 找到 {len(search_results_a)} 个结果")
            else:
                if strategy.use_chinese_search_engine:
                    print(f"    [🌐 策略] 检测到需要使用中文搜索引擎（如百度、搜狗）")
                    if not self.baidu_search_enabled:
                        print(f"    [⚠️ 注意] 百度搜索未配置，使用其他搜索引擎，可能无法完全覆盖中文内容")
                    else:
                        print(f"    [ℹ️] 百度搜索已配置但未启用（可能策略判断不需要）")
                
                # 对于非中文搜索，优先使用 Tavily（高质量，avg 4.65），Google作为降级选项（低质量，avg 1.50）
                print(f"    [🔍 搜索A-Tavily] 查询: \"{query}\"")
                print(f"    [⚙️ 参数] max_results=30")
                try:
                    # 🔥 从llm_client.search()返回的Dict或SearchResult转换为SearchResult
                    search_dicts = self.llm_client.search(query, max_results=30, country_code=country_code_upper)
                    search_results_a = []
                    for item in search_dicts:
                        # [修复] 2026-01-20: 处理字典和SearchResult对象两种类型
                        if isinstance(item, dict):
                            # 如果是字典，使用.get()方法
                            url = item.get('url', '')
                            # 🔒 P1 SSRF防护: 验证URL安全性
                            if not is_safe_url(url):
                                logger.warning(f"Blocked unsafe URL from search A: {url}")
                                continue  # 跳过不安全的URL

                            search_engine = item.get('search_engine', 'Tavily')
                            search_results_a.append(SearchResult(
                                title=item.get('title', ''),
                                url=url,
                                snippet=item.get('snippet', ''),
                                source=item.get('source', 'Tavily'),
                                search_engine=search_engine
                            ))
                        else:
                            # 如果是SearchResult对象，直接使用属性访问
                            # 🔒 P1 SSRF防护: 验证URL安全性
                            if not is_safe_url(item.url):
                                logger.warning(f"Blocked unsafe URL from search A (SearchResult): {item.url}")
                                continue  # 跳过不安全的URL

                            search_results_a.append(item)
                    print(f"    [✅ 搜索A-Tavily] 找到 {len(search_results_a)} 个结果")
                except Exception as e:
                    print(f"    [❌ 错误] Tavily 搜索失败: {str(e)}")
                    # 降级到 Google 搜索（如果可用）
                    if self.google_search_enabled:
                        print(f"    [🔄 降级] 切换到 Google 搜索...")
                        try:
                            google_results = self.google_hunter.search(query, max_results=30, country_code=country_code_upper)
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
                            search_results_a = []
                    else:
                        print(f"    [❌ 错误] Google 搜索未配置，无法降级")
                        search_results_a = []
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
                    country_language = country_config.language_code if country_config else "en"
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

            # ========== 🔍 记录去重过滤阶段到透明度收集器（P0-1） ==========
            # 收集被过滤的样本（重复URL）
            duplicate_samples = []
            seen_urls_set = set()
            for result in all_results:
                if result.url in seen_urls_set:
                    duplicate_samples.append({
                        "title": result.title[:80],
                        "url": result.url[:100],
                        "reason": "URL重复"
                    })
                    if len(duplicate_samples) >= 3:  # 最多3个样本
                        break
                seen_urls_set.add(result.url)

            self.transparency_collector.record_filtering_stage(
                stage_name="去重",
                input_count=len(all_results),
                output_count=len(search_results),
                filter_reason=f"移除 {duplicate_count} 个重复URL",
                filtered_samples=duplicate_samples
            )
            logger.debug(f"[🔍 透明度] 已记录去重过滤: {len(all_results)} → {len(search_results)}")
            # ========== 去重过滤记录结束 ==========
            
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

            # 🚀 并发获取播放列表信息（优化性能，使用类方法带缓存）
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
                SINGLE_TIMEOUT = 3  # 单个播放列表3秒超时（优化：从8秒降低到3秒，2.6倍提速）

                success_count = 0
                fail_count = 0

                with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_PLAYLIST_WORKERS) as executor:
                    # 提交所有任务（使用类方法带缓存）
                    future_to_result = {
                        executor.submit(self.get_playlist_info_fast, r['url']): r
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
            #
            # [修复] 2026-01-20: 启用视觉评估（默认true），但限制评估数量为TOP 5避免超时

            # 🔒 P1 环境变量验证: 读取环境变量控制是否启用（默认启用）
            ENABLE_VISUAL_EVALUATION = validate_env_bool(
                os.getenv('ENABLE_VISUAL_EVALUATION'),
                'ENABLE_VISUAL_EVALUATION',
                default=True
            )

            # 🔒 P1 环境变量验证: 读取环境变量控制LLM评分数量（默认TOP 10，避免超时）
            LLM_SCORE_TOP_N = validate_env_int(
                os.getenv('LLM_SCORE_TOP_N'),
                'LLM_SCORE_TOP_N',
                default=10,
                min_val=1,
                max_val=50
            )

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

                        # 异步批量截图（增加超时保护 + 避免资源泄漏）
                        async def capture_screenshots_async():
                            """🔒 P1修复：避免关闭全局单例的browser"""
                            try:
                                # 获取截图服务（全局单例，不要关闭）
                                service = await get_screenshot_service()

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
                            # 🔥 关键修复：移除finally块，不要关闭全局单例的browser
                            # ScreenshotService使用全局单例模式，由生命周期管理器负责清理

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

            # ✅ 新逻辑：通过URL匹配评分和结果（2025-01-16）
            # 问题：results_dicts和evaluated_results的顺序可能不一致
            # 解决：通过URL进行一一对应匹配
            logger.info(f"[📊 URL匹配] 开始通过URL匹配评分（{len(results_dicts)}个评分，{len(evaluated_results)}个结果）")

            # 1. 构建URL到评分的映射
            url_to_score = {}
            for scored_dict in results_dicts:
                if 'url' in scored_dict and 'score' in scored_dict:
                    url = scored_dict['url']
                    url_to_score[url] = {
                        'score': scored_dict['score'],
                        'recommendation_reason': scored_dict.get('recommendation_reason', ''),
                        'evaluation_method': scored_dict.get('evaluation_method', 'LLM')
                    }

            # 2. 通过URL匹配，将评分赋值给对应的结果
            matched_count = 0
            for result in evaluated_results:
                result_url = result.url
                if result_url in url_to_score:
                    # 找到匹配的评分
                    score_info = url_to_score[result_url]
                    result.score = score_info['score']
                    result.recommendation_reason = score_info['recommendation_reason']
                    matched_count += 1
                else:
                    # 未找到评分，设置默认值
                    logger.warning(f"[⚠️ 未找到评分] URL: {result_url[:60]}...")
                    result.score = 0.0
                    result.recommendation_reason = '未找到评分'

            logger.info(f"[✅ URL匹配完成] 匹配成功: {matched_count}/{len(evaluated_results)}")

            # 3. 按评分降序排序
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

            # 显示多级缓存统计
            cache_stats = self.multi_cache.get_stats()
            print(f"\n[💾 多级缓存统计]")
            print(f"    [📊 L1内存] 命中: {cache_stats['l1_hits']}次 ({cache_stats['l1_hit_rate']:.1f}%)")
            print(f"    [📊 L2 Redis] 命中: {cache_stats['l2_hits']}次 ({cache_stats['l2_hit_rate']:.1f}%)")
            print(f"    [📊 L3磁盘] 命中: {cache_stats['l3_hits']}次 ({cache_stats['l3_hit_rate']:.1f}%)")
            print(f"    [📊 总计] 查询: {cache_stats['total']}次 | 命中率: {cache_stats['hit_rate']:.1f}%")

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
                # 🔒 P1 环境变量验证: 检查是否启用智能优化（环境变量控制）
                enable_intelligent_optimization = validate_env_bool(
                    os.getenv("ENABLE_INTELLIGENT_OPTIMIZATION"),
                    "ENABLE_INTELLIGENT_OPTIMIZATION",
                    default=True
                )

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
                # 🔒 P1安全修复：不暴露异常细节给用户
                logger.warning(f"智能优化失败: {type(opt_error).__name__}", exc_info=True)
                print(f"    [⚠️ 智能优化失败] 将使用默认排序")
            # ========== 智能优化循环结束 ==========

            # ========== 🔍 记录评分分布和过滤到透明度收集器（P0-1） ==========
            # 记录评分分布
            scores = [r.score for r in evaluated_results if hasattr(r, 'score')]
            self.transparency_collector.record_score_distribution(scores)
            
            # 记录阈值过滤（如果有）
            if MIN_SCORE_THRESHOLD:
                above_threshold = [r for r in evaluated_results if hasattr(r, 'score') and r.score >= MIN_SCORE_THRESHOLD]
                below_threshold = [r for r in evaluated_results if hasattr(r, 'score') and r.score < MIN_SCORE_THRESHOLD]
                
                # 收集被过滤的低分样本
                filtered_low_score_samples = [{
                    "title": r.title[:80] if hasattr(r, 'title') else '',
                    "url": r.url[:100] if hasattr(r, 'url') else '',
                    "score": r.score if hasattr(r, 'score') else 0,
                    "reason": f"评分 {r.score:.1f} < {MIN_SCORE_THRESHOLD}"
                } for r in below_threshold[:5]]  # 最多5个样本
                
                self.transparency_collector.record_filtering_stage(
                    stage_name="评分阈值过滤",
                    input_count=len(evaluated_results),
                    output_count=len(above_threshold),
                    filter_reason=f"评分低于 {MIN_SCORE_THRESHOLD} 分",
                    filtered_samples=filtered_low_score_samples
                )
                logger.debug(f"[🔍 透明度] 已记录评分阈值过滤: {len(evaluated_results)} → {len(above_threshold)}")
            # ========== 评分分布和过滤记录结束 ==========

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

            # ========== 🔍 附加透明度元数据到响应（P0-1） ==========
            transparency_metadata = self.transparency_collector.get_transparency_metadata()
            logger.debug(f"[🔍 透明度] 准备返回透明度元数据: {len(transparency_metadata.get('search_executions', []))} 次搜索, "
                       f"{transparency_metadata.get('total_raw_results', 0)} 个原始结果")
            
            # 可选：打印透明度摘要（调试用）
            # self.transparency_collector.print_summary()
            # ========== 透明度元数据附加结束 ==========

            return SearchResponse(
                success=True,
                query=query,
                results=results_as_dicts,
                total_count=len(evaluated_results),
                playlist_count=playlist_count,
                video_count=video_count,
                message="搜索成功",
                quality_report=quality_report,
                optimization_request=optimization_request,
                transparency=transparency_metadata  # 🔍 新增透明度字段
            )

        except Exception as e:
            # 🔒 P1 安全修复: 不暴露详细的异常信息和堆栈跟踪
            logger.error(f"Search failed for {request.country}/{request.grade}/{request.subject}: {type(e).__name__}")
            print(f"\n[❌ 错误] 搜索失败，请稍后重试")
            print(f"    [💡 提示] 如果问题持续存在，请联系管理员并提供以下信息:")
            print(f"           国家: {request.country}, 年级: {request.grade}, 学科: {request.subject}")

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
            # 🔒 P1 安全修复: 只记录简短的错误信息，不记录堆栈跟踪
            error_msg = str(e)[:200] if str(e) else "No error message"
            logger.error(f"   错误信息: {error_msg}")
            logger.error(f"   耗时: {total_elapsed:.2f}秒")
            logger.error(f"   内存使用: {self._get_memory_usage()}")
            logger.error(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.error("="*80)

# ============================================================================
# 🤖 Agent Native Interface - P1优化
# ============================================================================
"""
Agent-friendly搜索接口，无需HTTP层

这个模块提供了Agent可以直接调用的搜索功能，避免了通过Flask HTTP API的紧耦合。

使用示例:
    from search_engine_v2 import agent_search
    
    # 同步搜索
    results = agent_search(
        country="ID",
        grade="Kelas 1",
        subject="Matematika"
    )
    
    # 带参数的搜索
    results = agent_search(
        country="CN",
        grade="初一",
        subject="数学",
        semester="第一学期",
        language="zh"
    )
"""

import gc
from typing import Optional, Dict, Any, List


def agent_search(
    country: str,
    grade: str,
    subject: str,
    semester: Optional[str] = None,
    language: Optional[str] = None,
    timeout: Optional[int] = 200,
    enable_transparency: bool = False
) -> Dict[str, Any]:
    """
    Agent原生的搜索接口
    
    🔥 关键优势：
    - 无需HTTP层，直接Python调用
    - 自动内存管理
    - 清晰的错误处理
    - 支持透明度日志
    
    Args:
        country: 国家代码 (如: "ID", "CN", "US")
        grade: 年级 (如: "Kelas 1", "初一", "Grade 8")
        subject: 学科 (如: "Matematika", "数学", "Mathematics")
        semester: 学期，可选 (如: "第一学期", "Semester 1")
        language: 语言代码，可选 (如: "zh", "id", "en")
        timeout: 超时时间（秒），默认200秒
        enable_transparency: 是否启用透明度日志，默认False
    
    Returns:
        Dict[str, Any]: 搜索结果字典
        {
            "success": bool,
            "query": str,
            "results": List[Dict],
            "total_count": int,
            "playlist_count": int,
            "video_count": int,
            "message": str,
            "quality_report": Optional[Dict],
            "transparency": Optional[Dict]  # 如果enable_transparency=True
        }
    
    Raises:
        ValueError: 输入参数无效
        TimeoutError: 搜索超时
    
    Example:
        >>> results = agent_search("ID", "Kelas 1", "Matematika")
        >>> if results["success"]:
        ...     for r in results["results"]:
        ...         print(f"{r['title']}: {r['url']}")
    """
    # 输入验证
    if not country or not grade or not subject:
        raise ValueError("country, grade, and subject are required")
    
    # 清理输入（移除前后空格）
    country = country.strip()
    grade = grade.strip()
    subject = subject.strip()
    if semester:
        semester = semester.strip()
    
    logger.info(f"[🤖 Agent接口] 开始搜索: {country}/{grade}/{subject}")
    
    # 创建搜索请求
    search_request = SearchRequest(
        country=country,
        grade=grade,
        subject=subject,
        semester=semester,
        language=language
    )
    
    # 创建搜索引擎实例
    search_engine = None
    
    try:
        # 创建搜索引擎（可选透明度日志）
        if enable_transparency:
            from core.search_transparency_collector import SearchTransparencyCollector
            transparency_collector = SearchTransparencyCollector()
            search_engine = SearchEngineV2(transparency_collector=transparency_collector)
        else:
            search_engine = SearchEngineV2()
        
        # 执行搜索
        logger.info(f"[🤖 Agent接口] 执行搜索...")
        response = search_engine.search(search_request)
        
        # 清理资源
        del search_engine
        gc.collect()
        
        # 转换为字典返回
        result_dict = {
            "success": response.success,
            "query": response.query,
            "results": response.results,
            "total_count": response.total_count,
            "playlist_count": response.playlist_count,
            "video_count": response.video_count,
            "message": response.message,
            "quality_report": response.quality_report,
            "transparency": response.transparency if enable_transparency else None
        }
        
        logger.info(f"[🤖 Agent接口] 搜索完成: {result_dict['total_count']} 个结果")
        return result_dict
        
    except ValueError as e:
        # 输入验证错误
        logger.error(f"[🤖 Agent接口] 输入验证失败: {str(e)}")
        raise
    except Exception as e:
        # 搜索失败
        logger.error(f"[🤖 Agent接口] 搜索失败: {type(e).__name__}: {str(e)[:100]}")
        
        # 确保清理资源
        if search_engine is not None:
            try:
                del search_engine
                gc.collect()
            except:
                pass
        
        # 返回错误结果
        return {
            "success": False,
            "query": f"{country} {grade} {subject}",
            "results": [],
            "total_count": 0,
            "playlist_count": 0,
            "video_count": 0,
            "message": f"搜索失败: {str(e)[:200]}",
            "quality_report": None,
            "transparency": None
        }


class AgentSearchClient:
    """
    Agent搜索客户端（面向对象接口）
    
    提供更高级的功能，如批量搜索、缓存等
    
    Example:
        >>> client = AgentSearchClient()
        >>> results = client.search("ID", "Kelas 1", "Matematika")
        >>> client.cleanup()  # 清理资源
    """
    
    def __init__(self, enable_cache: bool = False):
        """
        初始化Agent搜索客户端
        
        Args:
            enable_cache: 是否启用结果缓存
        """
        self._search_engine = None
        self._enable_cache = enable_cache
        self._cache = {}
        logger.info(f"[🤖 Agent客户端] 初始化完成 (缓存: {enable_cache})")
    
    def search(
        self,
        country: str,
        grade: str,
        subject: str,
        semester: Optional[str] = None,
        language: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        执行搜索（面向对象接口）
        
        Args:
            country: 国家代码
            grade: 年级
            subject: 学科
            semester: 学期，可选
            language: 语言，可选
            use_cache: 是否使用缓存，默认True
        
        Returns:
            搜索结果字典
        """
        # 生成缓存键
        cache_key = f"{country}:{grade}:{subject}:{semester}:{language}"
        
        # 检查缓存
        if self._enable_cache and use_cache and cache_key in self._cache:
            logger.info(f"[🤖 Agent客户端] 缓存命中: {cache_key}")
            return self._cache[cache_key]
        
        # 执行搜索
        result = agent_search(
            country=country,
            grade=grade,
            subject=subject,
            semester=semester,
            language=language,
            enable_transparency=False
        )
        
        # 存入缓存
        if self._enable_cache and result["success"]:
            self._cache[cache_key] = result
            logger.info(f"[🤖 Agent客户端] 结果已缓存: {cache_key}")
        
        return result
    
    def batch_search(
        self,
        queries: List[Dict[str, Any]],
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        批量搜索（并发执行）
        
        Args:
            queries: 查询列表 [{"country": "ID", "grade": "Kelas 1", "subject": "Matematika"}, ...]
            max_concurrent: 最大并发数，默认3
        
        Returns:
            结果列表
        """
        import concurrent.futures
        
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # 提交所有搜索任务
            future_to_query = {
                executor.submit(
                    self.search,
                    q["country"],
                    q["grade"],
                    q.get("subject"),
                    q.get("semester"),
                    q.get("language"),
                    q.get("use_cache", True)
                ): q for q in queries
            }
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    result = future.result(timeout=300)  # 5分钟超时
                    results.append(result)
                except Exception as e:
                    logger.error(f"[🤖 Agent客户端] 批量搜索失败: {query} -> {str(e)[:100]}")
                    results.append({
                        "success": False,
                        "message": f"批量搜索失败: {str(e)[:200]}",
                        "results": [],
                        "total_count": 0
                    })
        
        return results
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("[🤖 Agent客户端] 缓存已清空")
    
    def cleanup(self):
        """清理资源"""
        self.clear_cache()
        if self._search_engine is not None:
            try:
                del self._search_engine
                gc.collect()
            except:
                pass
        logger.info("[🤖 Agent客户端] 资源已清理")
    
    def __enter__(self):
        """上下文管理器支持"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器清理"""
        self.cleanup()


# 便捷函数
def quick_search(country: str, grade: str, subject: str) -> List[Dict[str, Any]]:
    """
    快速搜索（只返回结果列表）
    
    Args:
        country: 国家代码
        grade: 年级
        subject: 学科
    
    Returns:
        结果列表，失败返回空列表
    
    Example:
        >>> results = quick_search("ID", "Kelas 1", "Matematika")
        >>> for r in results:
        ...     print(f"{r['title']}: {r['url']}")
    """
    response = agent_search(country, grade, subject)
    
    if response["success"]:
        return response["results"]
    else:
        logger.warning(f"[快速搜索] 搜索失败: {response['message']}")
        return []


# 导出接口
__all__ = [
    "agent_search",
    "AgentSearchClient", 
    "quick_search"
]
