#!/usr/bin/env python3
"""
印尼 K12 视频课程库搜索 Agent
核心策略：通过核心章节找到完整的播放列表 (Playlist)，而不是寻找单个碎片化视频
"""

import os
import json
import csv
import re
import time
from typing import Dict, List, Optional, Any, Set
from pydantic import BaseModel, Field
import requests

# 支持从 .env 文件读取环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # 如果没有 python-dotenv，手动读取 .env 文件
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
# 数据模型定义 (Pydantic)
# ============================================================================

class SearchResult(BaseModel):
    """单个搜索结果"""
    title: str = Field(description="搜索结果标题")
    url: str = Field(description="结果URL")
    snippet: str = Field(description="结果摘要", default="")


class EvaluationResult(BaseModel):
    """LLM评估结果"""
    is_good_batch: bool = Field(description="这一批结果里是否有高质量的列表")
    best_urls: List[str] = Field(description="提取出的合集URL列表", default_factory=list)
    feedback: str = Field(description="评估反馈和建议", default="")


class ChapterInfo(BaseModel):
    """章节信息"""
    grade_level: str = Field(description="年级")
    subject: str = Field(description="学科")
    chapter_title: str = Field(description="章节标题")
    topics_count: int = Field(description="该章节下的知识点数量", default=0)


class PlaylistRecord(BaseModel):
    """最终输出的播放列表记录"""
    grade_level: str = Field(description="年级")
    subject: str = Field(description="学科")
    chapter_title: str = Field(description="章节标题")
    playlist_url: str = Field(description="播放列表URL")
    search_query: str = Field(description="使用的搜索词")
    attempt_number: int = Field(description="第几次尝试成功", default=1)
    reason: str = Field(description="选择理由", default="")


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

# 导入提示词管理器
try:
    from utils.prompt_manager import get_prompt_manager
    HAS_PROMPT_MANAGER = True
except ImportError:
    HAS_PROMPT_MANAGER = False
    print("[⚠️] 警告: 无法导入提示词管理器，将使用原有实现")

class AIBuildersClient:
    """
    AI Builders API 客户端（兼容性包装器）
    内部使用统一LLM客户端，支持公司内部API和AI Builders API的fallback机制
    """
    
    def __init__(self, api_token: Optional[str] = None):
        """
        初始化客户端
        
        Args:
            api_token: AI Builders API 令牌，如果不提供则从环境变量读取
        """
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
                    raise ValueError("请设置 AI_BUILDER_TOKEN 环境变量或传入 api_token 参数")
        else:
            self.use_unified_client = False
            if not self.api_token:
                raise ValueError("请设置 AI_BUILDER_TOKEN 环境变量或传入 api_token 参数")
        
        # 保留原有属性以保持兼容性
        self.base_url = "https://space.ai-builders.com/backend"
        self.headers = {
            "Authorization": f"Bearer {self.api_token or ''}",
            "Content-Type": "application/json"
        }
    
    def call_gemini(self, prompt: str, system_prompt: Optional[str] = None, 
                    max_tokens: int = 8000, temperature: float = 0.3,
                    model: str = "gemini-2.5-pro") -> str:
        """
        调用 gemini-2.5-pro 模型
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）
            max_tokens: 最大生成 token 数
            temperature: 温度参数
        
        Returns:
            模型返回的文本内容
        """
        # 如果使用统一客户端，直接调用
        if self.use_unified_client:
            return self.unified_client.call_gemini(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
        
        # 否则使用原有实现
        endpoint = f"{self.base_url}/v1/chat/completions"
        
        messages = []
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        payload = {
            "model": model,  # 使用传入的模型参数
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
            # 不设置 tool_choice 和 tools，让 API 使用默认行为
        }
        
        # 尝试添加安全设置，允许所有内容（如果 API 支持）
        # 注意：这取决于 API 提供者的实现
        # 如果 API 不支持此参数，会被忽略
        try:
            # 某些 Gemini API 实现可能支持 safety_settings
            # 但 AI Builders API 可能不支持，所以先注释掉
            # payload["safety_settings"] = [
            #     {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            #     {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            #     {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            #     {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            # ]
            pass
        except:
            pass
        
        try:
            proxies = {
                "http": None,
                "https": None
            }
            # 根据 OpenAPI 文档，添加 debug=true 参数以获取 orchestrator 执行跟踪
            # 这可以帮助我们诊断为什么返回空内容
            params = {"debug": True}
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                params=params,  # 添加 debug 参数
                timeout=300,
                proxies=proxies
            )
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    message = result["choices"][0].get("message", {})
                    content = message.get("content")
                    
                    # 检查是否有 tool_calls（工具调用）
                    if message.get("tool_calls"):
                        # 如果有工具调用，说明模型想要调用工具而不是直接返回内容
                        tool_calls = message.get("tool_calls", [])
                        print(f"    [⚠️ 警告] LLM 返回了工具调用而不是内容，工具调用数量: {len(tool_calls)}")
                        # 对于评估任务，我们不希望使用工具调用，应该返回错误
                        raise ValueError("LLM 返回了工具调用而不是评估结果，请检查提示词")
                    
                    if content is None:
                        raise ValueError("API 响应中 content 字段为 None")
                    
                    if not content.strip():
                        # 调试：打印完整响应（仅用于调试）
                        print(f"    [🔍 调试] content 为空字符串")
                        print(f"    [🔍 调试] finish_reason: {result['choices'][0].get('finish_reason', 'N/A')}")
                        
                        # 检查是否有 safety_ratings 或其他阻止信息
                        choice = result['choices'][0]
                        message = choice.get('message', {})
                        
                        # 检查各种可能的字段
                        if 'safety_ratings' in choice:
                            print(f"    [🔍 调试] safety_ratings: {choice.get('safety_ratings')}")
                        if 'finish_details' in choice:
                            print(f"    [🔍 调试] finish_details: {choice.get('finish_details')}")
                        if 'safety_ratings' in message:
                            print(f"    [🔍 调试] message.safety_ratings: {message.get('safety_ratings')}")
                        
                        # 检查响应中的其他字段
                        if 'prompt_feedback' in result:
                            print(f"    [🔍 调试] prompt_feedback: {result.get('prompt_feedback')}")
                        
                        # 检查 orchestrator_trace（根据 OpenAPI 文档，debug=true 时会包含此字段）
                        if 'orchestrator_trace' in result and result.get('orchestrator_trace'):
                            trace = result.get('orchestrator_trace')
                            print(f"    [🔍 调试] orchestrator_trace 存在，长度: {len(str(trace))}")
                            
                            # 检查是否有 forced_tool 配置
                            rounds = trace.get('rounds', [])
                            for round_info in rounds:
                                if round_info.get('forced_tool'):
                                    forced_tool = round_info.get('forced_tool')
                                    print(f"    [⚠️ 警告] 检测到 forced_tool: {forced_tool}")
                                    print(f"    [💡 建议] 模型 {model} 被配置为强制使用工具 '{forced_tool}'")
                                    print(f"    [💡 建议] 请改用 'deepseek' 模型进行纯文本生成任务")
                            
                            print(f"    [🔍 调试] orchestrator_trace 内容: {json.dumps(trace, ensure_ascii=False, indent=2)[:1000]}...")
                        else:
                            print(f"    [🔍 调试] orchestrator_trace: 不存在或为空")
                        
                        # 打印 token 使用情况
                        usage = result.get('usage', {})
                        print(f"    [🔍 调试] prompt_tokens: {usage.get('prompt_tokens', 0)}")
                        print(f"    [🔍 调试] completion_tokens: {usage.get('completion_tokens', 0)}")
                        print(f"    [🔍 调试] total_tokens: {usage.get('total_tokens', 0)}")
                        
                        # 打印完整的原始 JSON 响应以便调试（仅在详细模式下）
                        print(f"    [🔍 调试] 原始 API 响应 JSON: {json.dumps(result, ensure_ascii=False, indent=2)}")
                        
                        # 提供诊断建议
                        print(f"    [💡 建议] LLM 返回空内容可能的原因：")
                        print(f"        1. API 提供者的 Safety Settings 配置过于严格")
                        print(f"        2. API 端点配置问题")
                        print(f"        3. 模型版本或配置问题")
                        print(f"        建议：联系 API 提供者（AI Builders）检查配置")
                        
                        raise ValueError("API 响应中 content 为空字符串")
                    
                    return content
                else:
                    raise ValueError(f"API 响应格式异常: {json.dumps(result, ensure_ascii=False)}")
            else:
                raise ValueError(f"API 调用失败，状态码: {response.status_code}, 响应: {response.text[:500]}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"API 请求异常: {str(e)}")
    
    def call_llm(self, prompt: str, system_prompt: Optional[str] = None,
                 max_tokens: int = 8000, temperature: float = 0.3,  # [修复] 2026-01-20: 从2000增加到8000
                 model: str = "deepseek") -> str:
        """
        调用 LLM（支持 DeepSeek 和 Gemini）
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）
            max_tokens: 最大生成 token 数
            temperature: 温度参数
            model: 模型名称（deepseek 或 gemini-2.5-pro）
        
        Returns:
            模型返回的文本内容
        """
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
        # 对于 deepseek，使用 call_gemini 方法（因为 API 接口相同）
        # 但设置 model="deepseek" 和 tool_choice="none"
        if model == "deepseek":
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
            
            try:
                from llm_client import get_proxy_config
                response = requests.post(
                    endpoint,
                    headers=self.headers,
                    json=payload,
                    params={"debug": "true"},
                    timeout=300,
                    proxies=None  # [修复] 2026-01-20: AI Builders 是内网 API，不需要代理
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        content = result["choices"][0].get("message", {}).get("content", "")
                        if content and content.strip():
                            return content.strip()
                        else:
                            # 如果 deepseek 失败，尝试 gemini
                            if model == "deepseek":
                                print(f"    [⚠️ 警告] DeepSeek 返回空内容，尝试 Gemini...")
                                return self.call_gemini(prompt, system_prompt, max_tokens, temperature, "gemini-2.5-pro")
                            raise ValueError("API 响应中 content 为空字符串")
                    else:
                        raise ValueError(f"API 响应格式异常")
                else:
                    raise ValueError(f"API 调用失败，状态码: {response.status_code}")
            except requests.exceptions.RequestException as e:
                raise ValueError(f"API 请求异常: {str(e)}")
        else:
            # 对于其他模型，使用 call_gemini
            return self.call_gemini(prompt, system_prompt, max_tokens, temperature, model)
    
    def search(self, query: str, max_results: int = 10, region: str = "id",
               search_depth: str = "advanced",
               include_domains: Optional[List[str]] = None,
               country_code: Optional[str] = None) -> List[SearchResult]:
        """
        使用 AI Builders Tavily 搜索 API 执行搜索
        [修复] 2026-01-20: 添加 country_code 参数支持

        Args:
            query: 搜索查询词
            max_results: 最大返回结果数（1-20，默认10）
            region: 搜索区域（默认：id，印尼）- 注意：Tavily API 可能不支持此参数
            search_depth: 搜索深度（"basic" 或 "advanced"，默认 "advanced"）
            include_domains: 限定搜索的域名列表（可选）
            country_code: 国家代码（可选，如果提供则使用 country_code）

        Returns:
            搜索结果列表
        """
        # 如果使用统一客户端，尝试使用其search方法
        if self.use_unified_client:
            try:
                # [修复] 2026-01-20: 传递 country_code 参数
                search_results = self.unified_client.search(
                    query=query,
                    max_results=max_results,
                    include_domains=include_domains,
                    country_code=country_code or region  # 如果提供了 country_code，使用它；否则使用 region
                )
                # 转换为SearchResult对象
                results = []
                for item in search_results:
                    results.append(SearchResult(
                        title=item.get('title', ''),
                        url=item.get('url', ''),
                        snippet=item.get('content', item.get('snippet', item.get('description', '')))
                    ))
                return results
            except Exception as e:
                print(f"[⚠️] 统一客户端搜索失败: {str(e)}，回退到原有实现")
                # 回退到原有实现
        
        # 原有实现
        # Tavily 搜索端点
        endpoint = f"{self.base_url}/v1/search/"
        
        # 构建请求体（根据 OpenAPI 规范）
        payload = {
            "keywords": [query],  # Tavily API 接受关键词数组
            "max_results": min(max_results, 20)  # 限制在 1-20 之间
        }
        
        # 注意：根据 OpenAPI 文档，include_domains 和 search_depth 可能不在标准请求体中
        # 这些参数可能需要通过 Tavily API 的原始参数传递
        # 如果后端支持，可以尝试添加这些参数
        # 但根据 OpenAPI 规范，SearchRequest 只包含 keywords 和 max_results
        
        try:
            proxies = {
                "http": None,
                "https": None
            }
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=30,
                proxies=proxies
            )
            
            if response.status_code == 200:
                result = response.json()
                results = []
                
                # 解析 Tavily 响应格式
                # 响应格式：{"queries": [{"keyword": "...", "response": {...}}], ...}
                if isinstance(result, dict) and "queries" in result:
                    queries = result.get("queries", [])
                    if queries:
                        # 获取第一个查询的结果（因为我们只传了一个关键词）
                        query_result = queries[0]
                        tavily_response = query_result.get("response", {})
                        
                        # Tavily 响应通常包含 "results" 数组
                        tavily_results = tavily_response.get("results", [])
                        
                        for item in tavily_results[:max_results]:
                            # Tavily 结果格式：title, url, content, score 等
                            results.append(SearchResult(
                                title=item.get('title', ''),
                                url=item.get('url', ''),
                                snippet=item.get('content', item.get('snippet', item.get('description', '')))
                            ))
                
                if results:
                    return results
                else:
                    raise ValueError(f"Tavily 搜索返回空结果")
            else:
                error_text = response.text[:500] if hasattr(response, 'text') else str(response.status_code)
                raise ValueError(f"Tavily 搜索 API 调用失败，状态码: {response.status_code}, 响应: {error_text}")
                
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Tavily 搜索 API 请求异常: {str(e)}")
    
    def _search_via_llm_tools(self, query: str, max_results: int, region: str) -> List[SearchResult]:
        """
        通过 LLM 工具调用方式执行搜索（备选方案）

        Args:
            query: 搜索查询词
            max_results: 最大返回结果数
            region: 搜索区域

        Returns:
            搜索结果列表
        """
        # ✨ 使用提示词管理器构建搜索助手提示词（替代硬编码）
        if HAS_PROMPT_MANAGER:
            prompt_mgr = get_prompt_manager()
            system_prompt, user_prompt = prompt_mgr.get_llm_search_assistant_prompts(
                query=query,
                max_results=max_results,
                region=region
            )
        else:
            # 降级方案：使用原有实现
            system_prompt = """你是一个搜索助手。当用户请求搜索时，请使用可用的搜索工具来获取结果。
如果搜索工具返回了结果，请以 JSON 格式返回搜索结果数组。"""

            user_prompt = f"""请搜索以下查询词，返回前 {max_results} 个结果：
查询词: {query}
地区: {region}

请以 JSON 数组格式返回结果，每个结果包含 title, url, snippet 字段。"""
        
        # 尝试调用 LLM，看是否支持工具调用
        try:
            response_text = self.call_gemini(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=8000,  # [修复] 2026-01-20: 从4000增加到8000
                temperature=0.1
            )
            
            # 尝试从响应中提取 JSON
            json_text = self._extract_json_from_response(response_text)
            results_data = json.loads(json_text)
            
            results = []
            if isinstance(results_data, list):
                for item in results_data[:max_results]:
                    results.append(SearchResult(
                        title=item.get('title', ''),
                        url=item.get('url', ''),
                        snippet=item.get('snippet', '')
                    ))
            
            return results
            
        except Exception as e:
            raise ValueError(f"通过 LLM 工具调用搜索失败: {str(e)}")
    
    def _extract_json_from_response(self, response_text: str) -> str:
        """从响应文本中提取 JSON 部分"""
        # 尝试查找代码块中的 JSON
        json_pattern = r'```(?:json)?\s*(\[.*?\])\s*```'
        match = re.search(json_pattern, response_text, re.DOTALL)
        if match:
            return match.group(1)
        
        # 尝试找到 JSON 数组的开始和结束
        start_idx = response_text.find('[')
        end_idx = response_text.rfind(']')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return response_text[start_idx:end_idx+1]
        
        raise ValueError("无法从响应中提取 JSON")


# ============================================================================
# 搜索工具 (Hunter)
# ============================================================================

class SearchHunter:
    """搜索执行器 - 负责执行实际搜索"""
    
    def __init__(self, search_engine: str = "ai-builders", llm_client: Optional[AIBuildersClient] = None):
        """
        初始化搜索器
        
        Args:
            search_engine: 搜索引擎类型 ("ai-builders", "duckduckgo", "serpapi", "google" 或 "baidu")
            llm_client: AI Builders 客户端（当使用 ai-builders 时必需）
        """
        self.search_engine = search_engine
        self.llm_client = llm_client
        
        # 检查Google搜索配置
        if search_engine == "google":
            self.google_api_key = os.getenv("GOOGLE_API_KEY")
            self.google_cx = os.getenv("GOOGLE_CX")
            if not self.google_api_key:
                print(f"    [⚠️ 警告] GOOGLE_API_KEY 未设置，Google搜索将不可用")
            if not self.google_cx:
                print(f"    [⚠️ 警告] GOOGLE_CX 未设置，请在.env文件中配置")
        
        # 检查百度搜索配置
        if search_engine == "baidu":
            self.baidu_api_key = os.getenv("BAIDU_API_KEY")
            self.baidu_secret_key = os.getenv("BAIDU_SECRET_KEY")
            if not self.baidu_api_key:
                print(f"    [⚠️ 警告] BAIDU_API_KEY 未设置，百度搜索将不可用")
            if not self.baidu_secret_key:
                print(f"    [⚠️ 警告] BAIDU_SECRET_KEY 未设置，请在.env文件中配置")
    
    def search(self, query: str, max_results: int = 10, country_code: str = None) -> List[SearchResult]:
        """
        执行搜索

        Args:
            query: 搜索查询词
            max_results: 最大返回结果数
            country_code: 国家代码（ISO 3166-1 alpha-2），用于本地化搜索结果

        Returns:
            搜索结果列表
        """
        print(f"    [🔍 搜索] 执行搜索: \"{query}\"" + (f" [国家: {country_code}]" if country_code else ""))

        try:
            if self.search_engine == "ai-builders":
                return self._search_ai_builders(query, max_results, country_code)
            elif self.search_engine == "duckduckgo":
                return self._search_duckduckgo(query, max_results)
            elif self.search_engine == "serpapi":
                return self._search_serpapi(query, max_results)
            elif self.search_engine == "google":
                return self._search_google(query, max_results, country_code)
            elif self.search_engine == "baidu":
                return self._search_baidu(query, max_results)
            else:
                raise ValueError(f"不支持的搜索引擎: {self.search_engine}")
        except Exception as e:
            print(f"    [❌ 错误] 搜索失败: {str(e)}")
            # 如果 ai-builders 失败，尝试降级到 duckduckgo
            if self.search_engine == "ai-builders":
                print(f"    [🔄 降级] AI Builders 搜索失败，尝试使用 DuckDuckGo...")
                try:
                    return self._search_duckduckgo(query, max_results)
                except Exception as e2:
                    print(f"    [❌ 错误] DuckDuckGo 搜索也失败: {str(e2)}")
                    return []
            return []
    
    def _search_duckduckgo(self, query: str, max_results: int) -> List[SearchResult]:
        """
        使用 DuckDuckGo 搜索（使用 duckduckgo-search 库）
        
        Args:
            query: 搜索查询词
            max_results: 最大返回结果数
        
        Returns:
            搜索结果列表
        """
        try:
            from duckduckgo_search import DDGS
            
            results = []
            with DDGS() as ddgs:
                # 搜索，获取前 max_results 个结果
                search_results = ddgs.text(
                    query,
                    max_results=max_results,
                    region='id',  # 印尼地区
                    safesearch='moderate'
                )
                
                for result in search_results:
                    results.append(SearchResult(
                        title=result.get('title', ''),
                        url=result.get('href', ''),
                        snippet=result.get('body', '')
                    ))
            
            print(f"    [✅ 搜索] 找到 {len(results)} 个结果")
            return results
            
        except ImportError:
            print(f"    [⚠️ 警告] duckduckgo-search 库未安装，使用模拟搜索")
            return self._mock_search(query, max_results)
        except Exception as e:
            print(f"    [❌ 错误] DuckDuckGo 搜索异常: {str(e)}")
            return self._mock_search(query, max_results)
    
    def _search_ai_builders(self, query: str, max_results: int, country_code: str = None) -> List[SearchResult]:
        """
        使用 AI Builders Tavily 搜索 API（增强日志版本）

        Args:
            query: 搜索查询词
            max_results: 最大返回结果数
            country_code: 国家代码（ISO 3166-1 alpha-2）

        Returns:
            搜索结果列表
        """
        if not self.llm_client:
            raise ValueError("使用 ai-builders 搜索需要提供 llm_client")

        try:
            print(f"    [🔍 Tavily] 准备调用 API，查询: \"{query}\"")
            print(f"    [🔍 Tavily] 请求参数: max_results={max_results}, country_code={country_code or 'ID'}")

            results = self.llm_client.search(
                query=query,
                max_results=max_results,
                country_code=country_code or "ID"
                # 注意：search_depth 和 include_domains 参数已移除，因为 API 不支持
            )
            
            print(f"    [✅ Tavily] API 调用成功，返回 {len(results)} 个结果")
            if results:
                print(f"    [📊 Tavily] 结果预览:")
                for i, result in enumerate(results[:3], 1):
                    print(f"      [{i}] {result.title[:50]}... -> {result.url[:50]}...")
            
            return results
        except Exception as e:
            print(f"    [❌ 错误] Tavily 搜索异常: {str(e)}")
            import traceback
            print(f"    [🔍 调试] 异常详情: {traceback.format_exc()[:300]}")
            raise
    
    def _search_serpapi(self, query: str, max_results: int) -> List[SearchResult]:
        """
        使用 SerpAPI 搜索
        
        Args:
            query: 搜索查询词
            max_results: 最大返回结果数
        
        Returns:
            搜索结果列表
        """
        api_key = os.getenv("SERPAPI_KEY")
        if not api_key:
            print(f"    [⚠️ 警告] SERPAPI_KEY 未设置，使用模拟搜索")
            return self._mock_search(query, max_results)
        
        try:
            params = {
                "q": query,
                "api_key": api_key,
                "engine": "google",
                "gl": "id",  # 印尼地区
                "num": max_results
            }
            
            response = requests.get("https://serpapi.com/search", params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if "organic_results" in data:
                for item in data["organic_results"][:max_results]:
                    results.append(SearchResult(
                        title=item.get('title', ''),
                        url=item.get('link', ''),
                        snippet=item.get('snippet', '')
                    ))
            
            print(f"    [✅ 搜索] 找到 {len(results)} 个结果")
            return results
            
        except Exception as e:
            print(f"    [❌ 错误] SerpAPI 搜索异常: {str(e)}")
            return self._mock_search(query, max_results)
    
    def _search_google(self, query: str, max_results: int, country_code: str = None) -> List[SearchResult]:
        """
        使用 Google Custom Search API 搜索

        Args:
            query: 搜索查询词
            max_results: 最大返回结果数（Google API限制每次最多10个结果）
            country_code: 国家代码（ISO 3166-1 alpha-2），用于本地化搜索结果

        Returns:
            搜索结果列表
        """
        # ✨ 修复：国家代码到 Google 参数的映射（支持多语言/多地区搜索）
        # 参考: https://developers.google.com/custom-search/v1/parameter_guide
        country_google_params = {
            # 亚洲
            "ID": {"gl": "ID", "hl": "id", "lr": "lang_id"},  # 印度尼西亚
            "PH": {"gl": "PH", "hl": "fil", "lr": "lang_tl"},  # 菲律宾
            "JP": {"gl": "JP", "hl": "ja", "lr": "lang_ja"},  # 日本
            "CN": {"gl": "CN", "hl": "zh-CN", "lr": "lang_zh-CN"},  # 中国
            "MY": {"gl": "MY", "hl": "ms", "lr": "lang_ms"},  # 马来西亚
            "SG": {"gl": "SG", "hl": "en", "lr": "lang_en"},  # 新加坡
            "IN": {"gl": "IN", "hl": "hi", "lr": "lang_hi"},  # 印度
            "TH": {"gl": "TH", "hl": "th", "lr": "lang_th"},  # 泰国
            "VN": {"gl": "VN", "hl": "vi", "lr": "lang_vi"},  # 越南
            "KR": {"gl": "KR", "hl": "ko", "lr": "lang_ko"},  # 韩国
            "TW": {"gl": "TW", "hl": "zh-TW", "lr": "lang_zh-TW"},  # 台湾
            # 中东
            "IQ": {"gl": "IQ", "hl": "ar", "lr": "lang_ar"},  # 伊拉克
            "SA": {"gl": "SA", "hl": "ar", "lr": "lang_ar"},  # 沙特阿拉伯
            "AE": {"gl": "AE", "hl": "ar", "lr": "lang_ar"},  # 阿联酋
            "EG": {"gl": "EG", "hl": "ar", "lr": "lang_ar"},  # 埃及
            "IR": {"gl": "IR", "hl": "fa", "lr": "lang_fa"},  # 伊朗
            "SY": {"gl": "SY", "hl": "ar", "lr": "lang_ar"},  # 叙利亚
            "JO": {"gl": "JO", "hl": "ar", "lr": "lang_ar"},  # 约旦
            "LB": {"gl": "LB", "hl": "ar", "lr": "lang_ar"},  # 黎巴嫩
            "IL": {"gl": "IL", "hl": "he", "lr": "lang_he"},  # 以色列
            "KW": {"gl": "KW", "hl": "ar", "lr": "lang_ar"},  # 科威特
            "QA": {"gl": "QA", "hl": "ar", "lr": "lang_ar"},  # 卡塔尔
            "BH": {"gl": "BH", "hl": "ar", "lr": "lang_ar"},  # 巴林
            "OM": {"gl": "OM", "hl": "ar", "lr": "lang_ar"},  # 阿曼
            "YE": {"gl": "YE", "hl": "ar", "lr": "lang_ar"},  # 也门
            # 欧美
            "US": {"gl": "US", "hl": "en", "lr": "lang_en"},  # 美国
            "GB": {"gl": "GB", "hl": "en", "lr": "lang_en"},  # 英国
            "CA": {"gl": "CA", "hl": "en", "lr": "lang_en"},  # 加拿大
            "AU": {"gl": "AU", "hl": "en", "lr": "lang_en"},  # 澳大利亚
            "NZ": {"gl": "NZ", "hl": "en", "lr": "lang_en"},  # 新西兰
            "DE": {"gl": "DE", "hl": "de", "lr": "lang_de"},  # 德国
            "FR": {"gl": "FR", "hl": "fr", "lr": "lang_fr"},  # 法国
            "IT": {"gl": "IT", "hl": "it", "lr": "lang_it"},  # 意大利
            "ES": {"gl": "ES", "hl": "es", "lr": "lang_es"},  # 西班牙
            "RU": {"gl": "RU", "hl": "ru", "lr": "lang_ru"},  # 俄罗斯
            "TR": {"gl": "TR", "hl": "tr", "lr": "lang_tr"},  # 土耳其
            # 拉美
            "BR": {"gl": "BR", "hl": "pt-BR", "lr": "lang_pt-BR"},  # 巴西
            "MX": {"gl": "MX", "hl": "es", "lr": "lang_es"},  # 墨西哥
            "AR": {"gl": "AR", "hl": "es", "lr": "lang_es"},  # 阿根廷
            "CL": {"gl": "CL", "hl": "es", "lr": "lang_es"},  # 智利
            "CO": {"gl": "CO", "hl": "es", "lr": "lang_es"},  # 哥伦比亚
            "PE": {"gl": "PE", "hl": "es", "lr": "lang_es"},  # 秘鲁
            # 非洲
            "ZA": {"gl": "ZA", "hl": "en", "lr": "lang_en"},  # 南非
            "NG": {"gl": "NG", "hl": "en", "lr": "lang_en"},  # 尼日利亚
            "KE": {"gl": "KE", "hl": "en", "lr": "lang_en"},  # 肯尼亚
            "GH": {"gl": "GH", "hl": "en", "lr": "lang_en"},  # 加纳
            "ET": {"gl": "ET", "hl": "am", "lr": "lang_am"},  # 埃塞俄比亚
            "MA": {"gl": "MA", "hl": "ar", "lr": "lang_ar"},  # 摩洛哥
            "DZ": {"gl": "DZ", "hl": "ar", "lr": "lang_ar"},  # 阿尔及利亚
            "TN": {"gl": "TN", "hl": "ar", "lr": "lang_ar"},  # 突尼斯
            "LY": {"gl": "LY", "hl": "ar", "lr": "lang_ar"},  # 利比亚
            "SD": {"gl": "SD", "hl": "ar", "lr": "lang_ar"},  # 苏丹
        }

        # 根据国家代码获取 Google 参数，如果未找到则使用默认值（英语）
        # ✨ 增强：支持国家名称（如 "Iraq"）和 ISO 代码（如 "IQ"）
        country_key = country_code.upper() if country_code else None
        if country_key and country_key in country_google_params:
            google_params = country_google_params[country_key]
            print(f"    [✅ 本地化] 使用国家代码 {country_key}: gl={google_params['gl']}, hl={google_params['hl']}, lr={google_params['lr']}")
        elif country_key:
            # 尝试从国家名称查找 ISO 代码
            # 创建国家名称到 ISO 代码的反向映射
            name_to_code = {
                "IRAQ": "IQ", "IRAQ": "IQ",
                "INDONESIA": "ID", "INDONESIA": "ID",
                "SAUDI ARABIA": "SA", "SAUDI ARABIA": "SA",
                "UNITED ARAB EMIRATES": "AE", "UAE": "AE",
                "EGYPT": "EG",
                "IRAN": "IR",
                "SYRIA": "SY",
                "JORDAN": "JO",
                "LEBANON": "LB",
                "ISRAEL": "IL",
                "KUWAIT": "KW",
                "QATAR": "QA",
                "BAHRAIN": "BH",
                "OMAN": "OM",
                "YEMEN": "YE",
                "PHILIPPINES": "PH",
                "JAPAN": "JP",
                "CHINA": "CN",
                "MALAYSIA": "MY",
                "SINGAPORE": "SG",
                "INDIA": "IN",
                "THAILAND": "TH",
                "VIETNAM": "VN",
                "SOUTH KOREA": "KR", "KOREA": "KR",
                "TAIWAN": "TW",
                "UNITED STATES": "US", "USA": "US",
                "UNITED KINGDOM": "GB", "UK": "GB",
                "CANADA": "CA",
                "AUSTRALIA": "AU",
                "NEW ZEALAND": "NZ",
                "GERMANY": "DE",
                "FRANCE": "FR",
                "ITALY": "IT",
                "SPAIN": "ES",
                "RUSSIA": "RU",
                "TURKEY": "TR",
                "BRAZIL": "BR",
                "MEXICO": "MX",
                "ARGENTINA": "AR",
                "CHILE": "CL",
                "COLOMBIA": "CO",
                "PERU": "PE",
                "SOUTH AFRICA": "ZA",
                "NIGERIA": "NG",
                "KENYA": "KE",
                "GHANA": "GH",
                "ETHIOPIA": "ET",
                "MOROCCO": "MA",
                "ALGERIA": "DZ",
                "TUNISIA": "TN",
                "LIBYA": "LY",
                "SUDAN": "SD",
            }
            iso_code = name_to_code.get(country_key)
            if iso_code and iso_code in country_google_params:
                google_params = country_google_params[iso_code]
                print(f"    [✅ 本地化] 从国家名称 {country_key} 映射到 ISO 代码 {iso_code}: gl={google_params['gl']}, hl={google_params['hl']}, lr={google_params['lr']}")
            else:
                # 默认使用英语
                google_params = {"gl": "US", "hl": "en", "lr": "lang_en"}
                print(f"    [⚠️ 警告] 未找到国家 {country_key} 的映射，使用默认值（美国/英语）")
        else:
            # 默认使用英语
            google_params = {"gl": "US", "hl": "en", "lr": "lang_en"}
            print(f"    [ℹ️ 信息] 未提供国家代码，使用默认值（美国/英语）")

        api_key = getattr(self, 'google_api_key', None) or os.getenv("GOOGLE_API_KEY")
        cx = getattr(self, 'google_cx', None) or os.getenv("GOOGLE_CX")
        
        if not api_key:
            print(f"    [⚠️ 警告] GOOGLE_API_KEY 未设置，使用模拟搜索")
            return self._mock_search(query, max_results)
        
        if not cx:
            print(f"    [❌ 错误] GOOGLE_CX 未设置，请在.env文件中配置GOOGLE_CX")
            raise ValueError("GOOGLE_CX环境变量未设置，请配置搜索引擎ID")
        
        try:
            # Google Custom Search API端点
            endpoint = "https://customsearch.googleapis.com/customsearch/v1"
            
            # Google API限制每次最多返回10个结果
            # 如果需要更多结果，需要分页请求
            num_results = min(max_results, 10)
            
            params = {
                "key": api_key,
                "cx": cx,
                "q": query,
                "num": num_results,
                # ✨ 修复：使用动态国家参数（支持多语言/多地区搜索）
                "gl": google_params["gl"],  # 地理位置（影响排序和本地化）
                "hl": google_params["hl"],  # 界面语言
                "lr": google_params["lr"]   # 结果语言限制
            }

            print(f"    [🔍 Google] 准备调用 API，查询: \"{query}\"")
            print(f"    [🔍 Google] 请求参数: num={num_results}, cx={cx}, gl={google_params['gl']}, hl={google_params['hl']}, lr={google_params['lr']}")
            
            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if "items" in data:
                for item in data["items"][:max_results]:
                    results.append(SearchResult(
                        title=item.get('title', ''),
                        url=item.get('link', ''),
                        snippet=item.get('snippet', item.get('htmlSnippet', ''))
                    ))
            
            print(f"    [✅ Google] API 调用成功，返回 {len(results)} 个结果")
            if results:
                print(f"    [📊 Google] 结果预览:")
                for i, result in enumerate(results[:3], 1):
                    print(f"      [{i}] {result.title[:50]}... -> {result.url[:50]}...")
            
            return results
            
        except requests.exceptions.RequestException as e:
            print(f"    [❌ 错误] Google 搜索 API 请求异常: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"    [❌ 错误] API 错误详情: {error_data}")
                except:
                    print(f"    [❌ 错误] API 响应: {e.response.text[:200]}")
            return self._mock_search(query, max_results)
        except Exception as e:
            print(f"    [❌ 错误] Google 搜索异常: {str(e)}")
            import traceback
            print(f"    [🔍 调试] 异常详情: {traceback.format_exc()[:300]}")
            return self._mock_search(query, max_results)
    
    def _search_baidu(self, query: str, max_results: int) -> List[SearchResult]:
        """
        使用百度搜索API搜索
        
        Args:
            query: 搜索查询词
            max_results: 最大返回结果数
        
        Returns:
            搜索结果列表
        """
        api_key = getattr(self, 'baidu_api_key', None) or os.getenv("BAIDU_API_KEY")
        secret_key = getattr(self, 'baidu_secret_key', None) or os.getenv("BAIDU_SECRET_KEY")
        
        if not api_key or not secret_key:
            print(f"    [⚠️ 警告] 百度搜索API密钥未设置，使用模拟搜索")
            return self._mock_search(query, max_results)
        
        try:
            # 导入百度搜索客户端
            from baidu_search_client import BaiduSearchAPIClient
            
            client = BaiduSearchAPIClient(api_key=api_key, secret_key=secret_key)
            search_results = client.search(query, max_results=max_results)
            
            # 转换为SearchResult对象
            results = []
            for item in search_results:
                results.append(SearchResult(
                    title=item.get('title', ''),
                    url=item.get('url', ''),
                    snippet=item.get('snippet', '')
                ))
            
            print(f"    [✅ 搜索] 找到 {len(results)} 个结果")
            return results
        
        except ImportError:
            print(f"    [⚠️ 警告] baidu_search_client 模块未找到，使用模拟搜索")
            return self._mock_search(query, max_results)
        except Exception as e:
            print(f"    [❌ 错误] 百度搜索异常: {str(e)}")
            import traceback
            print(f"    [🔍 调试] 异常详情: {traceback.format_exc()[:300]}")
            return self._mock_search(query, max_results)
    
    def _mock_search(self, query: str, max_results: int) -> List[SearchResult]:
        """
        模拟搜索（用于测试或当真实搜索不可用时）
        
        Args:
            query: 搜索查询词
            max_results: 最大返回结果数
        
        Returns:
            模拟搜索结果列表
        """
        print(f"    [🧪 模拟] 生成 {max_results} 个模拟搜索结果")
        # 返回空列表，实际使用时应该返回模拟数据
        return []


# ============================================================================
# 结果评估器 (Inspector - LLM)
# ============================================================================

class ResultInspector:
    """结果评估器 - 使用 LLM 评估搜索结果质量，带规则兜底机制"""
    
    def __init__(self, llm_client: AIBuildersClient):
        """
        初始化评估器

        Args:
            llm_client: LLM 客户端实例
        """
        self.llm_client = llm_client
        # ✨ 初始化提示词管理器
        self.prompt_mgr = get_prompt_manager() if HAS_PROMPT_MANAGER else None
    
    def evaluate_results(self, search_results: List[SearchResult], 
                        chapter_info: ChapterInfo) -> EvaluationResult:
        """
        评估搜索结果，判断是否有高质量的播放列表
        采用三步策略：规则筛选 -> LLM 筛选（可选）-> 合并结果
        
        Args:
            search_results: 搜索结果列表
            chapter_info: 章节信息
        
        Returns:
            评估结果
        """
        print(f"    [🕵️ 评估] 正在评估 {len(search_results)} 个搜索结果...")
        
        # ========================================================================
        # Step 1: 规则筛选（硬规则检查）- 核心兜底机制
        # ========================================================================
        print(f"    [📋 Step 1] 执行规则匹配（硬规则检查）...")
        rule_matched_urls = self._heuristic_match(search_results, chapter_info)
        
        if rule_matched_urls:
            print(f"    [✅ 规则匹配] 通过硬规则找到 {len(rule_matched_urls)} 个高质量资源")
            for i, url in enumerate(rule_matched_urls, 1):
                url_type = self._classify_url_type(url)
                print(f"    [✅ 规则资源 {i}] {url_type}: {url[:70]}...")
        
        # ========================================================================
        # Step 2: LLM 筛选（可选）- 对剩余模糊结果进行判断
        # ========================================================================
        llm_matched_urls = []
        llm_feedback = ""
        
        # 如果规则匹配已经找到足够好的结果，可以跳过 LLM（但为了更全面，我们还是尝试 LLM）
        # 如果规则匹配为空，则必须使用 LLM
        try:
            print(f"    [🤖 Step 2] 尝试使用 LLM 评估剩余结果...")
            
            # 简化提示词，减少长度，避免触发安全限制
            # 只评估前5个结果，减少 token 数量
            limited_results = search_results[:5]
            results_text = self._format_results_for_llm(limited_results)

            # ✨ 使用提示词管理器构建评估提示词（替代硬编码）
            if self.prompt_mgr:
                user_prompt = self.prompt_mgr.get_search_evaluation_user_prompt(
                    grade=chapter_info.grade_level,
                    subject=chapter_info.subject,
                    chapter=chapter_info.chapter_title,
                    results_text=results_text
                )
            else:
                # 降级方案：使用原有实现
                user_prompt = f"""请直接返回JSON格式，不要使用任何工具或搜索功能。

从以下搜索结果中选择适合小学1-2年级数学教学的视频资源。

年级：{chapter_info.grade_level}
学科：{chapter_info.subject}
章节：{chapter_info.chapter_title}

搜索结果：
{results_text}

请直接返回以下JSON格式，不要调用任何工具：
{{
    "is_good_batch": true,
    "best_indices": [1, 2],
    "feedback": "找到资源"
}}"""
            
            # 尝试多个模型，如果 Gemini 失败则降级到 deepseek
            models_to_try = ["gemini-2.5-pro", "deepseek"]
            max_retries = 2
            response_text = None
            
            for model_name in models_to_try:
                if response_text:
                    break  # 如果已经成功获取响应，跳出循环
                    
                for retry in range(max_retries):
                    try:
                        print(f"    [🔍 尝试] 使用模型: {model_name} (尝试 {retry + 1}/{max_retries})")
                        # 尝试不使用 system_prompt，直接合并到 user_prompt，避免可能的格式问题
                        response_text = self.llm_client.call_gemini(
                            prompt=user_prompt,
                            system_prompt=None,  # 不使用 system_prompt，避免可能的格式问题
                            max_tokens=8000,  # [修复] 2026-01-20: 从500增加到8000
                            temperature=0.0,  # 使用最低温度，使输出更确定
                            model=model_name  # 使用指定的模型
                        )
                        
                        # 检查响应是否为空
                        if response_text and response_text.strip():
                            print(f"    [✅ 成功] 模型 {model_name} 返回了内容")
                            break  # 成功获取响应，跳出重试循环
                        else:
                            if retry < max_retries - 1:
                                print(f"    [⚠️ 警告] 模型 {model_name} 返回空响应，重试 {retry + 1}/{max_retries}...")
                                time.sleep(1)
                                continue
                            else:
                                print(f"    [⚠️ 警告] 模型 {model_name} 返回空响应（已重试 {max_retries} 次），尝试下一个模型...")
                                response_text = None
                                break  # 尝试下一个模型
                    except Exception as e:
                        if retry < max_retries - 1:
                            print(f"    [⚠️ 警告] 模型 {model_name} 调用失败: {str(e)}，重试 {retry + 1}/{max_retries}...")
                            time.sleep(1)
                            continue
                        else:
                            print(f"    [⚠️ 警告] 模型 {model_name} 调用失败（已重试 {max_retries} 次）: {str(e)}，尝试下一个模型...")
                            response_text = None
                            break  # 尝试下一个模型
            
            # 如果所有模型都失败，设置 response_text 为 None
            if not response_text or not response_text.strip():
                response_text = None
                print(f"    [⚠️ 警告] 所有模型都失败，转为使用规则过滤")
            
            # 如果 LLM 调用成功，解析结果
            if response_text:
                try:
                    # 提取 JSON
                    try:
                        json_text = self._extract_json_from_response(response_text)
                        # 解析 JSON
                        eval_data = json.loads(json_text)
                    except (ValueError, json.JSONDecodeError) as e:
                        print(f"    [⚠️ 警告] JSON 解析失败，尝试修复: {str(e)}")
                        print(f"    [🔍 调试] 响应内容预览: {response_text[:300]}")
                        # 尝试修复常见的 JSON 问题
                        json_text = response_text.strip()
                        # 移除可能的 markdown 代码块标记
                        json_text = re.sub(r'```(?:json)?\s*', '', json_text)
                        json_text = re.sub(r'```\s*$', '', json_text)
                        # 尝试找到 JSON 对象
                        start_idx = json_text.find('{')
                        end_idx = json_text.rfind('}')
                        if start_idx != -1 and end_idx != -1:
                            json_text = json_text[start_idx:end_idx+1]
                            try:
                                eval_data = json.loads(json_text)
                            except Exception as parse_error:
                                print(f"    [⚠️ 警告] JSON 解析最终失败，转为使用规则过滤: {str(parse_error)}")
                                eval_data = None
                        else:
                            print(f"    [⚠️ 警告] 无法找到 JSON 对象，转为使用规则过滤")
                            eval_data = None
                    
                    if eval_data:
                        # 从索引中提取真实的 URL
                        best_indices = eval_data.get("best_indices", [])
                        
                        # 如果 LLM 返回了 best_urls（向后兼容），也尝试使用
                        if not best_indices and "best_urls" in eval_data:
                            llm_matched_urls = eval_data.get("best_urls", [])
                        else:
                            # 从索引中提取 URL（索引从1开始，相对于 limited_results）
                            # 需要映射回原始的 search_results
                            for idx in best_indices:
                                if isinstance(idx, int) and 1 <= idx <= len(limited_results):
                                    # limited_results 中的索引（1-based）
                                    limited_result = limited_results[idx - 1]  # 转换为0-based索引
                                    # 找到在原始 search_results 中的位置
                                    for orig_idx, orig_result in enumerate(search_results):
                                        if orig_result.url == limited_result.url:
                                            if orig_result.url and orig_result.url.strip():
                                                llm_matched_urls.append(orig_result.url.strip())
                                            break
                        
                        llm_feedback = eval_data.get("feedback", "")
                        print(f"    [✅ LLM 评估] 找到 {len(llm_matched_urls)} 个高质量资源")
                        print(f"    [✅ LLM 反馈] {llm_feedback[:200]}...")
                    else:
                        print(f"    [⚠️ 警告] LLM 返回的数据无法解析，转为使用规则过滤")
                except Exception as e:
                    print(f"    [⚠️ 警告] LLM 评估过程异常，转为使用规则过滤: {str(e)}")
            else:
                print(f"    [⚠️ 警告] LLM 调用失败，转为使用规则过滤")
        
        except Exception as e:
            # LLM 调用完全失败，记录错误但不崩溃
            print(f"    [⚠️ 警告] LLM 评估失败，转为使用规则过滤: {str(e)}")
        
        # ========================================================================
        # Step 3: 合并结果
        # ========================================================================
        print(f"    [🔄 Step 3] 合并规则匹配和 LLM 评估结果...")
        
        # 合并 URL（去重）
        all_matched_urls = list(set(rule_matched_urls + llm_matched_urls))
        
        # 分类 URL
        valid_urls = []
        video_urls = []
        
        for url in all_matched_urls:
            if "youtube.com/watch" in url and "list=" not in url:
                video_urls.append(url)
            else:
                valid_urls.append(url)
        
        # 将单集视频也添加到有效 URL 列表中（放宽标准）
        valid_urls.extend(video_urls)
        
        # 构建最终评估结果
        is_good_batch = len(valid_urls) > 0
        
        # 生成反馈信息
        feedback_parts = []
        if rule_matched_urls:
            feedback_parts.append(f"规则匹配找到 {len(rule_matched_urls)} 个资源")
        if llm_matched_urls:
            feedback_parts.append(f"LLM 评估找到 {len(llm_matched_urls)} 个资源")
        if llm_feedback:
            feedback_parts.append(llm_feedback)
        
        feedback = " | ".join(feedback_parts) if feedback_parts else "使用规则匹配和 LLM 评估"
        
        evaluation = EvaluationResult(
            is_good_batch=is_good_batch,
            best_urls=valid_urls,
            feedback=feedback
        )
        
        # 详细日志输出
        if evaluation.is_good_batch:
            print(f"    [✅ 最终评估] 发现 {len(evaluation.best_urls)} 个高质量资源")
            print(f"    [✅ 评估详情] 规则匹配: {len(rule_matched_urls)} 个")
            print(f"    [✅ 评估详情] LLM 评估: {len(llm_matched_urls)} 个")
            print(f"    [✅ 评估详情] 播放列表/频道: {len(valid_urls) - len(video_urls)} 个")
            print(f"    [✅ 评估详情] 单集视频（系列）: {len(video_urls)} 个")
            for i, url in enumerate(evaluation.best_urls, 1):
                url_type = "视频（系列）" if url in video_urls else "播放列表/频道"
                source = "规则" if url in rule_matched_urls else "LLM"
                print(f"    [✅ 资源 {i}] [{source}] {url_type}: {url[:70]}...")
        else:
            print(f"    [⚠️ 最终评估] 未发现高质量列表")
        
        return evaluation
    
    def _heuristic_match(self, search_results: List[SearchResult], 
                        chapter_info: ChapterInfo) -> List[str]:
        """
        规则匹配（硬规则检查）- 核心兜底机制
        在调用 LLM 之前或 LLM 失败后，使用硬规则筛选高质量资源
        
        Args:
            search_results: 搜索结果列表
            chapter_info: 章节信息
        
        Returns:
            匹配的 URL 列表
        """
        matched_urls = []
        
        for result in search_results:
            url = result.url.lower() if result.url else ""
            title = result.title.lower() if result.title else ""
            snippet = result.snippet.lower() if result.snippet else ""
            
            # 规则 1: YouTube 播放列表（100% 确定）
            if ("youtube.com/playlist" in url or 
                ("youtube.com/watch" in url and "list=" in url)):
                matched_urls.append(result.url)
                continue
            
            # 规则 2: YouTube 频道页面
            if any(pattern in url for pattern in ["youtube.com/c/", "youtube.com/channel/", "youtube.com/@"]):
                # 检查是否是教育相关内容
                if any(keyword in title or keyword in snippet for keyword in 
                       ["matematika", "belajar", "pembelajaran", "kelas", "education", "tutorial"]):
                    matched_urls.append(result.url)
                    continue
            
            # 规则 3: EdTech 网站（印尼主要教育平台）
            edtech_domains = ["ruangguru.com", "zenius.net", "quipper.com", 
                             "pahamify.com", "kelaspintar.id"]
            if any(domain in url for domain in edtech_domains):
                # 检查路径是否看起来像课程页（包含课程相关关键词）
                course_keywords = ["course", "kelas", "materi", "pembelajaran", 
                                  "video", "tutorial", "belajar"]
                if any(keyword in url or keyword in title or keyword in snippet 
                       for keyword in course_keywords):
                    matched_urls.append(result.url)
                    continue
            
            # 规则 4: YouTube 单集视频（但标题显示是系列的一部分）
            if "youtube.com/watch" in url:
                series_keywords = ["part 1", "part 2", "bagian 1", "bagian 2",
                                  "episode", "seri", "series", "full", "lengkap",
                                  "complete", "playlist", "kumpulan"]
                if any(keyword in title or keyword in snippet for keyword in series_keywords):
                    matched_urls.append(result.url)
                    continue
            
            # 规则 5: 标题包含章节关键词的单集视频
            if "youtube.com/watch" in url:
                chapter_keywords = chapter_info.chapter_title.lower().split()
                # 检查标题或摘要中是否包含章节关键词
                if any(keyword in title or keyword in snippet for keyword in chapter_keywords if len(keyword) > 3):
                    # 同时检查是否与数学相关
                    if "matematika" in title or "matematika" in snippet:
                        matched_urls.append(result.url)
                        continue
        
        return matched_urls
    
    def _classify_url_type(self, url: str) -> str:
        """
        分类 URL 类型
        
        Args:
            url: URL 字符串
        
        Returns:
            URL 类型描述
        """
        url_lower = url.lower()
        if "youtube.com/playlist" in url_lower or ("youtube.com/watch" in url_lower and "list=" in url_lower):
            return "播放列表"
        elif any(pattern in url_lower for pattern in ["youtube.com/c/", "youtube.com/channel/", "youtube.com/@"]):
            return "频道页面"
        elif "youtube.com/watch" in url_lower:
            return "单集视频（系列）"
        elif any(domain in url_lower for domain in ["ruangguru.com", "zenius.net", "quipper.com", 
                                                    "pahamify.com", "kelaspintar.id"]):
            return "EdTech 平台"
        else:
            return "其他资源"
    
    def _format_results_for_llm(self, results: List[SearchResult]) -> str:
        """
        格式化搜索结果供 LLM 评估
        
        Args:
            results: 搜索结果列表
        
        Returns:
            格式化后的文本
        """
        formatted = []
        for i, result in enumerate(results, 1):
            # Tavily 返回的 content 字段通常包含更详细的内容，优先使用
            snippet = result.snippet
            # 如果 snippet 为空或很短，尝试使用更长的内容（Tavily 的 content 字段可能更长）
            if not snippet or len(snippet) < 50:
                snippet = result.snippet  # 保持原样，因为 SearchResult 已经处理了
            
            # 显示更多内容（Tavily 的 content 字段通常包含更详细的信息）
            snippet_preview = snippet[:300] if snippet else "（无摘要）"
            formatted.append(f"""
结果 {i}:
标题: {result.title}
URL: {result.url}
内容: {snippet_preview}...
""")
        return "\n".join(formatted)
    
    def _extract_json_from_response(self, response_text: str) -> str:
        """从响应文本中提取 JSON 部分"""
        # 尝试查找代码块中的 JSON
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, response_text, re.DOTALL)
        if match:
            return match.group(1)
        
        # 尝试找到 JSON 对象的开始和结束
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return response_text[start_idx:end_idx+1]
        
        return response_text


# ============================================================================
# 🔥 QueryGenerator 已被移除（2025-01-10）
# 原因：功能与 IntelligentQueryGenerator 重复
# - IntelligentQueryGenerator 使用更新的模型（gemini-2.5-flash）
# - IntelligentQueryGenerator 支持更好的多语言识别
# - 搜索流程已有 3 层降级：IntelligentQueryGenerator → 搜索策略 → 规则生成
# - QueryGenerator 作为第 4 层降级没有必要，增加系统复杂度
#
# 替代方案：
# 1. IntelligentQueryGenerator (core/intelligent_query_generator.py)
#    - 使用 LLM 智能生成多语言搜索词
#    - 支持多国语言和术语识别
# 2. SearchStrategist._generate_fallback_query() (本文件)
#    - 使用规则生成降级搜索词
# 3. SearchEngineV2._generate_fallback_query() (search_engine_v2.py)
#    - 最终降级：简单拼接搜索词
# ============================================================================

# ============================================================================
# 主搜索策略器 (Search Strategist)
# ============================================================================

class SearchStrategist:
    """搜索策略器 - 核心 Agent 逻辑"""
    
    def __init__(self, llm_client: AIBuildersClient, search_engine: str = "ai-builders"):
        """
        初始化搜索策略器

        Args:
            llm_client: LLM 客户端
            search_engine: 搜索引擎类型 ("ai-builders", "duckduckgo" 或 "serpapi")
        """
        self.hunter = SearchHunter(search_engine, llm_client=llm_client)
        self.inspector = ResultInspector(llm_client)
        self.unique_playlists: Set[str] = set()  # 全局去重集合
        self.all_records: List[PlaylistRecord] = []  # 所有找到的记录

    def _generate_fallback_query(self, chapter_info: 'ChapterInfo', attempt: int) -> str:
        """
        生成降级搜索词（规则生成，替代 QueryGenerator）

        Args:
            chapter_info: 章节信息
            attempt: 尝试次数（1-5）

        Returns:
            搜索查询词
        """
        import re

        # 提取年级关键词
        grade_text = chapter_info.grade_level
        if "Kelas 1-2" in grade_text or "Fase A" in grade_text:
            grade_keyword = "kelas 1"
        elif "Kelas" in grade_text:
            match = re.search(r'Kelas\s+(\d+)', grade_text)
            if match:
                grade_keyword = f"kelas {match.group(1)}"
            else:
                grade_keyword = "kelas 1"
        else:
            grade_keyword = "kelas 1"

        # 简化章节名称
        chapter = chapter_info.chapter_title.lower()

        # 判断学期（简单启发式）
        semester2_keywords = ["geometri", "statistik", "peluang", "data", "pengukuran", "bangun"]
        semester = "semester 2" if any(kw in chapter for kw in semester2_keywords) else "semester 1"

        # 根据尝试次数生成不同的搜索词
        if attempt == 1:
            # 尝试 1: 精准列表 - 限定 YouTube，包含章节名
            query = f"site:youtube.com playlist matematika {grade_keyword} {chapter}"
        elif attempt == 2:
            # 尝试 2: 学期/全套合集
            query = f"site:youtube.com playlist matematika {grade_keyword} full course {semester}"
        elif attempt == 3:
            # 尝试 3: 寻找频道
            query = f"rekomendasi channel youtube belajar matematika {grade_keyword} terbaik"
        elif attempt == 4:
            # 尝试 4: 更宽泛的 YouTube 搜索
            query = f"playlist lengkap matematika {grade_keyword} {semester}"
        else:
            # 尝试 5: 教育平台搜索
            query = f"ruangguru zenius pahamify matematika {grade_keyword} {chapter}"

        return query

    def search_for_playlists(self, syllabus_data: Dict[str, Any]) -> List[PlaylistRecord]:
        """
        主函数：为教学大纲数据搜索播放列表
        
        Args:
            syllabus_data: 知识点 JSON 数据
        
        Returns:
            找到的播放列表记录列表
        """
        print("\n" + "="*80)
        print("🚀 开始搜索播放列表")
        print("="*80 + "\n")
        
        # 提取知识点数据
        knowledge_points = syllabus_data.get("knowledge_points", [])
        
        if not knowledge_points:
            print("❌ 错误: 未找到知识点数据")
            return []
        
        # 按章节分组
        chapters = self._group_by_chapter(knowledge_points)
        
        print(f"📚 发现 {len(chapters)} 个章节需要搜索\n")
        
        # 遍历每个章节
        for idx, (chapter_key, chapter_info) in enumerate(chapters.items(), 1):
            print(f"\n{'─'*80}")
            print(f"📖 [{idx}/{len(chapters)}] 处理章节: {chapter_info.chapter_title}")
            print(f"{'─'*80}")
            
            # 为每个章节执行智能搜索循环
            self._search_chapter(chapter_info)
            
            # 添加延迟，避免请求过快
            time.sleep(1)
        
        print(f"\n{'='*80}")
        print(f"✅ 搜索完成！共找到 {len(self.all_records)} 个播放列表")
        print(f"{'='*80}\n")
        
        return self.all_records
    
    def _group_by_chapter(self, knowledge_points: List[Dict[str, Any]]) -> Dict[str, ChapterInfo]:
        """
        按章节分组知识点
        
        Args:
            knowledge_points: 知识点列表
        
        Returns:
            章节字典，key 为章节唯一标识，value 为章节信息
        """
        chapters = {}
        
        for point in knowledge_points:
            # 构建章节唯一标识
            chapter_key = f"{point.get('grade_level', '')}_{point.get('subject', '')}_{point.get('chapter_title', '')}"
            
            if chapter_key not in chapters:
                chapters[chapter_key] = ChapterInfo(
                    grade_level=point.get('grade_level', ''),
                    subject=point.get('subject', ''),
                    chapter_title=point.get('chapter_title', ''),
                    topics_count=0
                )
            
            chapters[chapter_key].topics_count += 1
        
        return chapters
    
    def _search_chapter(self, chapter_info: ChapterInfo, max_attempts: int = 5):
        """
        为单个章节执行智能搜索循环（增强日志版本）
        
        Args:
            chapter_info: 章节信息
            max_attempts: 最大尝试次数
        """
        print(f"\n[🔍 策略] 正为章节 \"{chapter_info.chapter_title}\" 生成搜索词...")
        print(f"[🔍 策略详情] 年级: {chapter_info.grade_level}, 学科: {chapter_info.subject}")
        
        # 获取所有章节列表（用于判断学期）
        all_chapter_titles = list(set([r.chapter_title for r in self.all_records] + [chapter_info.chapter_title]))
        
        # 智能搜索循环
        for attempt in range(1, max_attempts + 1):
            print(f"\n{'='*60}")
            print(f"[🔄 循环 {attempt}/{max_attempts}] 开始新的搜索尝试")
            print(f"{'='*60}")
            
            # 生成查询（根据尝试次数调整策略）
            query = self._generate_fallback_query(chapter_info, attempt)
            print(f"[📝 最终查询] \"{query}\"")
            
            # 步骤 A: 执行搜索
            print(f"\n[🔍 搜索执行] 调用 Tavily 搜索 API...")
            search_results = self.hunter.search(query, max_results=10)
            
            if not search_results:
                print(f"[⚠️ 警告] Tavily 未返回搜索结果")
                print(f"[🔄 循环] 尝试次数 {attempt}/{max_attempts} 失败，继续下一次尝试...")
                continue
            
            # 打印 Tavily 返回的原始结果
            print(f"\n[📊 Tavily 返回结果] 共 {len(search_results)} 个结果:")
            for i, result in enumerate(search_results[:5], 1):  # 只显示前5个
                print(f"  [{i}] {result.title[:60]}...")
                print(f"      URL: {result.url[:70]}...")
                print(f"      摘要: {result.snippet[:80]}..." if result.snippet else "      摘要: （无）")
            
            # 步骤 B: 评估结果
            print(f"\n[🕵️ LLM 评估] 开始评估搜索结果...")
            evaluation = self.inspector.evaluate_results(search_results, chapter_info)
            
            # 步骤 C: 决策与修正
            if evaluation.is_good_batch and evaluation.best_urls:
                # 找到高质量列表，保存并跳出循环
                print(f"\n[✅ 评估成功] 找到 {len(evaluation.best_urls)} 个高质量资源")
                for url in evaluation.best_urls:
                    if url not in self.unique_playlists:
                        self.unique_playlists.add(url)
                        # 生成理由
                        reason = f"匹配章节: {chapter_info.chapter_title}"
                        if evaluation.feedback:
                            reason += f" | {evaluation.feedback[:100]}"
                        
                        # 检查是否是单集视频
                        url_type = "Video Source" if "youtube.com/watch" in url and "list=" not in url else "Playlist/Channel"
                        reason += f" | 类型: {url_type}"
                        
                        record = PlaylistRecord(
                            grade_level=chapter_info.grade_level,
                            subject=chapter_info.subject,
                            chapter_title=chapter_info.chapter_title,
                            playlist_url=url,
                            search_query=query,
                            attempt_number=attempt,
                            reason=reason
                        )
                        self.all_records.append(record)
                        print(f"[✅ 成功] 锁定资源 ({url_type}): {url}")
                
                print(f"[✅ 循环完成] 在第 {attempt} 次尝试中成功找到资源，退出循环")
                return
            
            else:
                # 未找到高质量列表
                print(f"\n[⚠️ 评估结果] 未找到高质量资源")
                print(f"[⚠️ 反馈] {evaluation.feedback[:200]}...")
                if attempt < max_attempts:
                    print(f"[🔄 循环] 尝试次数 {attempt}/{max_attempts} 未成功，继续下一次尝试...")
                else:
                    print(f"[❌ 循环] 已达到最大尝试次数 {max_attempts}，退出循环")
        
        # 如果所有尝试都失败，尝试使用 LLM 生成已知教育平台的直接链接
        # 检查当前章节是否已经找到资源
        current_chapter_found = any(
            record.chapter_title == chapter_info.chapter_title 
            for record in self.all_records
        )
        
        if not current_chapter_found:
            print(f"[🔄 补充策略] 尝试使用 LLM 生成已知教育平台的直接链接...")
            self._try_llm_generated_links(chapter_info)
        
        # 再次检查是否找到资源
        final_check = any(
            record.chapter_title == chapter_info.chapter_title 
            for record in self.all_records
        )
        
        if not final_check:
            print(f"[⚠️ 完成] 章节 \"{chapter_info.chapter_title}\" 未找到合适的播放列表")
    
    def _try_llm_generated_links(self, chapter_info: ChapterInfo):
        """使用 LLM 生成已知印尼教育平台的直接链接"""
        try:
            # ✨ 使用提示词管理器构建平台链接生成提示词（替代硬编码）
            if self.prompt_mgr:
                prompt = self.prompt_mgr.get_platform_links_user_prompt(
                    grade=chapter_info.grade_level,
                    subject=chapter_info.subject,
                    chapter=chapter_info.chapter_title
                )
            else:
                # 降级方案：使用原有实现
                prompt = f"""请为以下章节提供印尼主要教育平台（Ruangguru, Quipper, Zenius, Pahamify, Kelas Pintar）的直接链接。

年级：{chapter_info.grade_level}（小学1-2年级）
学科：{chapter_info.subject}
章节：{chapter_info.chapter_title}

请提供这些平台的课程页面或播放列表链接。如果不知道确切链接，请提供平台主页和搜索建议。

请以 JSON 格式返回：
{{
    "links": [
        {{"platform": "平台名称", "url": "链接", "description": "描述"}},
        ...
    ]
}}

只返回 JSON，不要其他文字。"""
            
            response = self.inspector.llm_client.call_gemini(
                prompt,
                max_tokens=8000,  # [修复] 2026-01-20: 从1000增加到8000
                temperature=0.3
            )
            
            # 提取 JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                links = data.get("links", [])
                
                for link_info in links[:3]:  # 最多3个
                    url = link_info.get("url", "")
                    if url and url.startswith("http"):
                        if url not in self.unique_playlists:
                            self.unique_playlists.add(url)
                            reason = f"LLM生成 | {link_info.get('platform', '')}: {link_info.get('description', '')}"
                            record = PlaylistRecord(
                                grade_level=chapter_info.grade_level,
                                subject=chapter_info.subject,
                                chapter_title=chapter_info.chapter_title,
                                playlist_url=url,
                                search_query=f"LLM生成-{link_info.get('platform', '')}",
                                attempt_number=999,
                                reason=reason
                            )
                            self.all_records.append(record)
                            print(f"[✅ 补充] LLM生成链接: {url}")
        except Exception as e:
            print(f"[⚠️ 警告] LLM生成链接失败: {str(e)}")


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数"""
    import sys
    
    # 确定输入文件
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        # 默认使用 1-2 年级的文件
        input_file = "/Users/shmiwanghao8/Desktop/education/Indonesia/Knowledge Point/5. Final Panduan Mata Pelajaran Matematika_12_09_2025_Revisi 3_30-58_knowledge_points.json"
    
    if not os.path.exists(input_file):
        print(f"❌ 错误: 文件不存在: {input_file}")
        return
    
    # 读取知识点数据
    print(f"📖 读取知识点文件: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        syllabus_data = json.load(f)
    
    # 初始化客户端和策略器
    try:
        llm_client = AIBuildersClient()
        # 使用 ai-builders 搜索 API（免费且更智能）
        strategist = SearchStrategist(llm_client, search_engine="ai-builders")
        
        # 执行搜索
        playlist_records = strategist.search_for_playlists(syllabus_data)
        
        # 保存结果到 CSV
        output_file = input_file.replace("_knowledge_points.json", "_playlists.csv")
        print(f"\n💾 保存结果到: {output_file}")
        
        if playlist_records:
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'grade_level', 'subject', 'chapter_title', 
                    'playlist_url', 'search_query', 'attempt_number', 'reason'
                ])
                writer.writeheader()
                for record in playlist_records:
                    writer.writerow(record.model_dump())
            
            print(f"✅ 成功保存 {len(playlist_records)} 条记录")
        else:
            print("⚠️ 未找到任何播放列表")
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

