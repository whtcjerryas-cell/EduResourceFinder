#!/usr/bin/env python3
"""
统一的LLM客户端
支持两套API系统：
1. 公司内部API（优先使用）
2. AI Builders API（备用）
"""

import os
import json
import time
import base64
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
import requests

# 尝试导入OpenAI SDK（用于公司内部API）
try:
    from openai import OpenAI
    HAS_OPENAI_SDK = True
except ImportError:
    HAS_OPENAI_SDK = False

from core.config_loader import get_config
from logger_utils import get_logger
from metaso_search_client import MetasoSearchClient

logger = get_logger('llm_client')

# ========================================
# 重要：启动时清除所有代理环境变量
# 原因：代理会导致公司内部API被WAF拦截
# ========================================
def disable_proxy():
    """
    强制禁用所有代理设置
    确保公司内部API可以正常访问
    """
    proxy_vars = [
        "HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
        "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy"
    ]

    disabled_count = 0
    for var in proxy_vars:
        if var in os.environ:
            del os.environ[var]
            disabled_count += 1

    # 也设置为空，防止代码中读取
    os.environ["HTTP_PROXY"] = ""
    os.environ["HTTPS_PROXY"] = ""
    os.environ["http_proxy"] = ""
    os.environ["https_proxy"] = ""

    if disabled_count > 0:
        logger.info(f"[🔧 代理] 已清除 {disabled_count} 个代理环境变量，确保公司API可访问")

# 在模块加载时立即禁用代理
disable_proxy()


def get_proxy_config() -> Dict[str, Optional[str]]:
    """
    从环境变量读取代理配置

    Returns:
        代理配置字典，格式为 {"http": proxy_url, "https": proxy_url}
        注意：当前已强制禁用代理以避免连接问题
    """
    # 强制禁用代理（避免代理连接问题）
    print(f"[🔧 代理配置] 强制禁用代理，直接连接")
    return {"http": None, "https": None}

    # 原始代码已注释（如果需要启用代理，取消下面的注释）
    # http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    # https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    #
    # if http_proxy or https_proxy:
    #     proxies = {
    #         "http": http_proxy,
    #         "https": https_proxy or http_proxy
    #     }
    #     print(f"[🔧 代理配置] 使用代理: HTTP={http_proxy}, HTTPS={https_proxy or http_proxy}")
    #     return proxies
    # else:
    #     print(f"[🔧 代理配置] 未设置代理，直接连接")
    #     return {"http": None, "https": None}


class InternalAPIClient:
    """公司内部API客户端（使用OpenAI SDK）"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model_type: str = 'internal_api'):
        """
        初始化公司内部API客户端

        Args:
            api_key: API密钥，如果不提供则从环境变量读取
            base_url: API基础URL，如果不提供则从环境变量读取，默认使用hk环境
            model_type: 模型类型，从配置文件中读取（internal_api, vision等），默认为internal_api
        """
        self.api_key = api_key or os.getenv("INTERNAL_API_KEY")
        if not self.api_key:
            raise ValueError("请设置 INTERNAL_API_KEY 环境变量")

        # 支持通过环境变量配置base_url，默认使用hk环境（生产环境）
        # 可选值：hk-intra-paas（生产）或 uat-intra-paas（测试）
        if base_url:
            self.base_url = base_url
        else:
            # 优先从环境变量读取，如果没有则使用hk环境
            env_base_url = os.getenv("INTERNAL_API_BASE_URL")
            if env_base_url:
                self.base_url = env_base_url
            else:
                # 默认使用hk环境（生产环境）
                self.base_url = "https://hk-intra-paas.transsion.com/tranai-proxy/v1"

        # 从配置文件加载模型名称（根据model_type）
        config = get_config()
        models = config.get_llm_models()
        self.model = models.get(model_type, 'gpt-4o')
        self.model_type = model_type  # 记录模型类型

        if HAS_OPENAI_SDK:
            # OpenAI SDK会自动添加Bearer前缀，所以直接传入api_key即可
            # 添加超时设置以避免长时间挂起
            import httpx
            timeout_config = httpx.Timeout(
                connect=10.0,  # 连接超时10秒
                read=60.0,     # 读取超时60秒
                write=30.0,    # 写入超时30秒
                pool=10.0      # 连接池超时10秒
            )
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=timeout_config,
                max_retries=2,   # 最多重试2次
                http_client=httpx.Client(
                    timeout=timeout_config,
                    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
                    proxy=None,  # 明确禁用代理
                    trust_env=False  # 关键：不读取环境变量中的代理设置！
                )
            )
            logger.info(f"✅ 公司内部API客户端初始化成功 (超时: connect=10s, read=60s, 代理: 已强制禁用)")
        else:
            self.client = None
    
    def is_available(self) -> bool:
        """检查API是否可用（需要内网环境）"""
        if not HAS_OPENAI_SDK:
            return False
        if not self.client:
            return False
        # 可以尝试一个简单的健康检查
        # 这里先返回True，实际可用性在调用时判断
        return True
    
    def call_llm(self, prompt: str, system_prompt: Optional[str] = None,
                 max_tokens: Optional[int] = None, temperature: Optional[float] = None,
                 model: Optional[str] = None) -> str:
        """
        调用LLM

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）
            max_tokens: 最大生成token数（可选，默认从配置加载）
            temperature: 温度参数（可选，默认从配置加载）
            model: 模型名称（可选，默认使用gpt-4o）

        Returns:
            模型返回的文本内容

        Raises:
            ValueError: API调用失败
        """
        if not HAS_OPENAI_SDK:
            raise ValueError("OpenAI SDK未安装，无法使用公司内部API")

        if not self.client:
            raise ValueError("公司内部API客户端未初始化")

        # 从配置加载默认参数
        config = get_config()
        if max_tokens is None:
            params = config.get_llm_params('default')
            max_tokens = params.get('max_tokens', 2000)
        if temperature is None:
            params = config.get_llm_params('default')
            temperature = params.get('temperature', 0.3)

        model_name = model or self.model

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            print(f"\n{'='*80}")
            print(f"[🏢 公司内部API] 开始调用 {model_name}")
            print(f"{'='*80}")
            print(f"[📤 输入] Base URL: {self.base_url}")
            print(f"[📤 输入] Model: {model_name}")
            print(f"[📤 输入] Max Tokens: {max_tokens}")
            print(f"[📤 输入] Temperature: {temperature}")
            print(f"[📤 输入] System Prompt 长度: {len(system_prompt) if system_prompt else 0} 字符")
            print(f"[📤 输入] User Prompt 长度: {len(prompt)} 字符")
            if system_prompt:
                print(f"[📤 输入] System Prompt (前500字符):\n{system_prompt[:500]}...")
            print(f"[📤 输入] User Prompt (前500字符):\n{prompt[:500]}...")

            start_time = time.time()

            # 添加额外的超时保护，使用线程池运行
            import concurrent.futures
            import signal

            def call_api_with_timeout():
                return self.client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )

            # 使用线程池执行，设置60秒超时
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(call_api_with_timeout)
                try:
                    completion = future.result(timeout=60)  # 60秒超时
                except concurrent.futures.TimeoutError:
                    print(f"[❌ 错误] API调用超时（60秒），取消请求...")
                    future.cancel()
                    raise TimeoutError("公司内部API调用超时（60秒）")

            elapsed_time = time.time() - start_time

            print(f"\n[📥 响应] 响应时间: {elapsed_time:.2f} 秒")

            if completion.choices and len(completion.choices) > 0:
                content = completion.choices[0].message.content
                if content and content.strip():
                    print(f"[📥 响应] Content 长度: {len(content)} 字符")
                    print(f"[📥 响应] Content (前1000字符):\n{content[:1000]}...")
                    print(f"{'='*80}\n")
                    return content.strip()
                else:
                    raise ValueError("API 响应中 content 为空字符串")
            else:
                raise ValueError("API 响应格式异常，缺少 choices 字段")

        except TimeoutError as e:
            error_msg = str(e)
            print(f"[❌ 错误] 公司内部API调用超时: {error_msg}")
            print(f"[❌ 错误] 建议: 检查网络连接或减小请求体大小")
            # 超时错误不应该立即失败，应该允许降级到备用API
            raise TimeoutError(f"公司内部API调用超时: {error_msg}")

        except Exception as e:
            error_msg = str(e)
            print(f"[❌ 错误] 公司内部API调用失败: {error_msg}")
            print(f"[❌ 错误] 异常类型: {type(e).__name__}")

            # 检查是否是405错误（WAF拦截）
            if '405' in error_msg or 'blocked' in error_msg.lower():
                print(f"[⚠️ 警告] 请求被WAF拦截，可能原因:")
                print(f"  - 请求体过大 ({len(prompt)} 字符)")
                print(f"  - User-Agent或请求头问题")
                print(f"  - 触发了安全规则")
                print(f"[💡 建议] 尝试减小请求体或联系API管理员")

            import traceback
            print(f"[❌ 错误] 异常堆栈:\n{traceback.format_exc()}")
            raise ValueError(f"公司内部API调用失败: {error_msg}")
    
    def _image_to_base64(self, image_path: str) -> str:
        """
        将本地图片文件转换为base64编码的data URI
        
        Args:
            image_path: 图片文件路径
        
        Returns:
            base64编码的data URI字符串
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        
        # 读取图片文件
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # 转换为base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # 根据文件扩展名确定MIME类型
        ext = image_path.suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        mime_type = mime_types.get(ext, 'image/jpeg')
        
        # 返回data URI格式
        return f"data:{mime_type};base64,{image_base64}"
    
    def call_with_vision(self, prompt: str,
                        image_url: Optional[str] = None,
                        image_paths: Optional[List[str]] = None,
                        max_tokens: Optional[int] = None,
                        temperature: Optional[float] = None) -> str:
        """
        调用视觉模型（解析图片）
        按照内部API示例代码实现，支持URL和本地文件

        Args:
            prompt: 文本提示词
            image_url: 图片URL（可选，与image_paths二选一）
            image_paths: 本地图片文件路径列表（可选，与image_url二选一）
            max_tokens: 最大生成token数（可选，默认从配置加载）
            temperature: 温度参数（可选，默认从配置加载）

        Returns:
            模型返回的文本内容

        Raises:
            ValueError: 参数错误或API调用失败
        """
        if not HAS_OPENAI_SDK:
            raise ValueError("OpenAI SDK未安装，无法使用公司内部API")

        if not self.client:
            raise ValueError("公司内部API客户端未初始化")

        # 从配置加载默认参数
        config = get_config()
        if max_tokens is None:
            params = config.get_llm_params('vision')
            max_tokens = params.get('max_tokens', 300)
        if temperature is None:
            params = config.get_llm_params('vision')
            temperature = params.get('temperature', 0.3)

        # 构建content数组
        content = [{"type": "text", "text": prompt}]

        # 处理图片输入
        if image_url:
            # 使用URL（支持HTTP/HTTPS URL或data URI）
            content.append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })
        elif image_paths:
            # 使用本地文件（转换为base64）
            for image_path in image_paths:
                base64_data_uri = self._image_to_base64(image_path)
                content.append({
                    "type": "image_url",
                    "image_url": {"url": base64_data_uri}
                })
        else:
            raise ValueError("必须提供 image_url 或 image_paths 参数")

        messages = [{"role": "user", "content": content}]

        try:
            print(f"\n{'='*80}")
            print(f"[🏢 公司内部API] 开始调用视觉模型 {self.model}")
            print(f"{'='*80}")
            print(f"[📤 输入] Prompt 长度: {len(prompt)} 字符")
            if image_url:
                print(f"[📤 输入] Image URL: {image_url}")
            if image_paths:
                print(f"[📤 输入] 图片数量: {len(image_paths)}")
                for i, path in enumerate(image_paths, 1):
                    print(f"[📤 输入]   图片 {i}: {path}")
            print(f"[📤 输入] Max Tokens: {max_tokens}")
            print(f"[📤 输入] Temperature: {temperature}")

            start_time = time.time()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            elapsed_time = time.time() - start_time

            print(f"\n[📥 响应] 响应时间: {elapsed_time:.2f} 秒")

            if response.choices and len(response.choices) > 0:
                content_text = response.choices[0].message.content
                if content_text and content_text.strip():
                    print(f"[📥 响应] Content 长度: {len(content_text)} 字符")
                    print(f"[📥 响应] Content (前1000字符):\n{content_text[:1000]}...")
                    print(f"{'='*80}\n")
                    return content_text.strip()
                else:
                    raise ValueError("API 响应中 content 为空字符串")
            else:
                raise ValueError("API 响应格式异常，缺少 choices 字段")

        except Exception as e:
            error_msg = str(e)
            print(f"[❌ 错误] 公司内部API视觉调用失败: {error_msg}")
            print(f"[❌ 错误] 异常类型: {type(e).__name__}")
            import traceback
            print(f"[❌ 错误] 异常堆栈:\n{traceback.format_exc()}")
            raise ValueError(f"公司内部API视觉调用失败: {error_msg}")


class AIBuildersAPIClient:
    """AI Builders API客户端（备用）"""
    
    def __init__(self, api_token: Optional[str] = None):
        """
        初始化AI Builders API客户端
        
        Args:
            api_token: API令牌，如果不提供则从环境变量读取
        """
        self.api_token = api_token or os.getenv("AI_BUILDER_TOKEN")
        if not self.api_token:
            raise ValueError("请设置 AI_BUILDER_TOKEN 环境变量")
        
        self.base_url = "https://space.ai-builders.com/backend"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    def call_llm(self, prompt: str, system_prompt: Optional[str] = None,
                 max_tokens: Optional[int] = None, temperature: Optional[float] = None,
                 model: str = "deepseek") -> str:
        """
        调用LLM

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）
            max_tokens: 最大生成token数（可选，默认从配置加载）
            temperature: 温度参数（可选，默认从配置加载）
            model: 模型名称（deepseek 或 gemini-2.5-pro）

        Returns:
            模型返回的文本内容
        """
        # 从配置加载默认参数
        config = get_config()
        if max_tokens is None:
            params = config.get_llm_params('default')
            max_tokens = params.get('max_tokens', 2000)
        if temperature is None:
            params = config.get_llm_params('default')
            temperature = params.get('temperature', 0.3)

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
        }

        print(f"\n{'='*80}")
        print(f"[🌐 AI Builders API] 开始调用 {model}")
        print(f"{'='*80}")
        print(f"[📤 输入] Endpoint: {endpoint}")
        print(f"[📤 输入] Model: {model}")
        print(f"[📤 输入] Max Tokens: {max_tokens}")
        print(f"[📤 输入] Temperature: {temperature}")
        print(f"[📤 输入] System Prompt 长度: {len(system_prompt) if system_prompt else 0} 字符")
        print(f"[📤 输入] User Prompt 长度: {len(prompt)} 字符")
        if system_prompt:
            print(f"[📤 输入] System Prompt (前500字符):\n{system_prompt[:500]}...")
        print(f"[📤 输入] User Prompt (前500字符):\n{prompt[:500]}...")

        try:
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

            print(f"\n[📥 响应] HTTP 状态码: {response.status_code}")
            print(f"[📥 响应] 响应时间: {elapsed_time:.2f} 秒")

            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    choice = result["choices"][0]
                    message = choice.get("message", {})
                    content = message.get("content", "")

                    if content and content.strip():
                        print(f"[📥 响应] Content 长度: {len(content)} 字符")
                        print(f"[📥 响应] Content (前1000字符):\n{content[:1000]}...")
                        print(f"{'='*80}\n")
                        return content.strip()
                    else:
                        # 如果 deepseek 失败，尝试 gemini
                        if model == "deepseek":
                            print(f"    [⚠️ 警告] DeepSeek 返回空内容，尝试 Gemini...")
                            return self.call_llm(prompt, system_prompt, max_tokens, temperature, "gemini-2.5-pro")
                        raise ValueError("API 响应中 content 为空字符串")
                else:
                    raise ValueError("API 响应格式异常，缺少 choices 字段")
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
    
    def call_gemini(self, prompt: str, system_prompt: Optional[str] = None,
                    max_tokens: int = 8000, temperature: float = 0.3) -> str:
        """
        调用Gemini模型
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）
            max_tokens: 最大生成token数
            temperature: 温度参数
        
        Returns:
            模型返回的文本内容
        """
        return self.call_llm(prompt, system_prompt, max_tokens, temperature, "gemini-2.5-pro")


class UnifiedLLMClient:
    """
    统一的LLM客户端
    优先使用公司内部API，失败时fallback到AI Builders API
    """
    
    def __init__(self, internal_api_key: Optional[str] = None,
                 ai_builder_token: Optional[str] = None,
                 internal_base_url: Optional[str] = None):
        """
        初始化统一LLM客户端
        
        Args:
            internal_api_key: 公司内部API密钥（可选）
            ai_builder_token: AI Builders API令牌（可选）
            internal_base_url: 公司内部API基础URL（可选，默认使用hk环境）
        """
        self.internal_client = None
        self.ai_builders_client = None
        
        # 尝试初始化公司内部API客户端
        try:
            self.internal_client = InternalAPIClient(
                api_key=internal_api_key,
                base_url=internal_base_url
            )
            if self.internal_client.is_available():
                print(f"[✅] 公司内部API客户端初始化成功 (Base URL: {self.internal_client.base_url})")
            else:
                print("[⚠️] 公司内部API客户端初始化失败（可能不在内网环境）")
                self.internal_client = None
        except Exception as e:
            print(f"[⚠️] 公司内部API客户端初始化失败: {str(e)}")
            self.internal_client = None
        
        # 初始化AI Builders API客户端（备用）
        try:
            self.ai_builders_client = AIBuildersAPIClient(ai_builder_token)
            print("[✅] AI Builders API客户端初始化成功")
        except Exception as e:
            print(f"[⚠️] AI Builders API客户端初始化失败: {str(e)}")
            # 如果两个客户端都失败，抛出异常
            if not self.internal_client:
                raise ValueError("无法初始化任何API客户端，请检查环境变量配置")

        # 初始化Metaso搜索客户端（主要搜索引擎）
        try:
            self.metaso_client = MetasoSearchClient()
            print("[✅] Metaso搜索客户端初始化成功")
            print(f"[💰 Metaso] 免费额度: 5,000 次，超出后 ¥0.03/次")
        except Exception as e:
            print(f"[⚠️] Metaso搜索客户端初始化失败: {str(e)}")
            print(f"[ℹ️] 将使用 AI Builders Tavily 作为主要搜索引擎")
            self.metaso_client = None

        # 初始化Google搜索客户端（免费额度优先）
        try:
            from search_strategist import SearchHunter
            google_api_key = os.getenv("GOOGLE_API_KEY")
            google_cx = os.getenv("GOOGLE_CX")
            if google_api_key and google_cx:
                self.google_hunter = SearchHunter(search_engine="google", llm_client=None)
                self.google_usage = 0  # 使用计数器（每天重置）
                print("[✅] Google搜索客户端初始化成功")
                print(f"[💰 Google] 免费额度: 10,000 次/天，完全免费")
            else:
                self.google_hunter = None
                self.google_usage = 0
                print("[⚠️] Google搜索客户端未配置（缺少 GOOGLE_API_KEY 或 GOOGLE_CX）")
        except Exception as e:
            self.google_hunter = None
            self.google_usage = 0
            print(f"[⚠️] Google搜索客户端初始化失败: {str(e)}")

        # 初始化Baidu搜索客户端（中文备用）
        try:
            from baidu_search_client import BaiduSearchClient
            baidu_api_key = os.getenv("BAIDU_API_KEY")
            baidu_secret_key = os.getenv("BAIDU_SECRET_KEY")
            if baidu_api_key and baidu_secret_key:
                self.baidu_hunter = BaiduSearchClient()
                self.baidu_usage = 0  # 使用计数器（每天重置）
                print("[✅] Baidu搜索客户端初始化成功")
                print(f"[💰 Baidu] 免费额度: 100 次/天，完全免费")
            else:
                self.baidu_hunter = None
                self.baidu_usage = 0
                print("[⚠️] Baidu搜索客户端未配置（缺少 BAIDU_API_KEY 或 BAIDU_SECRET_KEY）")
        except Exception as e:
            self.baidu_hunter = None
            self.baidu_usage = 0
            print(f"[⚠️] Baidu搜索客户端初始化失败: {str(e)}")

        # 初始化 Tavily 使用计数器（每月重置）
        self.tavily_usage = 0

    def call_llm(self, prompt: str, system_prompt: Optional[str] = None,
                 max_tokens: int = 2000, temperature: float = 0.3,
                 model: str = "deepseek") -> str:
        """
        调用LLM（带fallback机制）
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）
            max_tokens: 最大生成token数
            temperature: 温度参数
            model: 模型名称（对于公司内部API，会使用gpt-4o；对于AI Builders，使用传入的model）
        
        Returns:
            模型返回的文本内容
        
        Raises:
            ValueError: 所有API调用都失败
        """
        # 优先使用公司内部API
        if self.internal_client:
            try:
                print(f"[🔄] 尝试使用公司内部API...")
                return self.internal_client.call_llm(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    model=None  # 公司内部API使用gpt-4o
                )
            except Exception as e:
                print(f"[⚠️] 公司内部API调用失败: {str(e)}")
                print(f"[🔄] 切换到AI Builders API...")
                # Fallback到AI Builders API
                if self.ai_builders_client:
                    return self.ai_builders_client.call_llm(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        model=model
                    )
                else:
                    raise ValueError("公司内部API失败，且AI Builders API不可用")
        else:
            # 如果没有公司内部API，直接使用AI Builders API
            if self.ai_builders_client:
                print(f"[🔄] 使用AI Builders API（公司内部API不可用）...")
                return self.ai_builders_client.call_llm(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    model=model
                )
            else:
                raise ValueError("没有可用的API客户端")
    
    def call_gemini(self, prompt: str, system_prompt: Optional[str] = None,
                    max_tokens: int = 8000, temperature: float = 0.3) -> str:
        """
        调用Gemini模型（带fallback机制）
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）
            max_tokens: 最大生成token数
            temperature: 温度参数
        
        Returns:
            模型返回的文本内容
        """
        # 优先使用公司内部API（使用gpt-4o）
        if self.internal_client:
            try:
                print(f"[🔄] 尝试使用公司内部API（Gemini任务）...")
                return self.internal_client.call_llm(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    model=None
                )
            except Exception as e:
                print(f"[⚠️] 公司内部API调用失败: {str(e)}")
                print(f"[🔄] 切换到AI Builders API（Gemini）...")
                if self.ai_builders_client:
                    return self.ai_builders_client.call_gemini(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                else:
                    raise ValueError("公司内部API失败，且AI Builders API不可用")
        else:
            if self.ai_builders_client:
                print(f"[🔄] 使用AI Builders API（Gemini，公司内部API不可用）...")
                return self.ai_builders_client.call_gemini(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            else:
                raise ValueError("没有可用的API客户端")
    
    def call_with_vision(self, prompt: str,
                         image_url: Optional[str] = None,
                         image_paths: Optional[List[str]] = None,
                         max_tokens: int = 300, 
                         temperature: float = 0.3) -> str:
        """
        调用视觉模型（解析图片）
        按照内部API示例代码实现，支持URL和本地文件
        
        Args:
            prompt: 文本提示词
            image_url: 图片URL（可选，与image_paths二选一）
            image_paths: 本地图片文件路径列表（可选，与image_url二选一）
            max_tokens: 最大生成token数
            temperature: 温度参数
        
        Returns:
            模型返回的文本内容
        
        Raises:
            ValueError: 参数错误或所有API调用都失败
        """
        # 优先使用公司内部API（支持视觉）
        if self.internal_client:
            try:
                print(f"[🔄] 尝试使用公司内部API（视觉任务）...")
                return self.internal_client.call_with_vision(
                    prompt=prompt,
                    image_url=image_url,
                    image_paths=image_paths,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            except Exception as e:
                print(f"[⚠️] 公司内部API视觉调用失败: {str(e)}")
                # AI Builders API不支持视觉，抛出异常
                raise ValueError(f"公司内部API视觉调用失败，且AI Builders API不支持视觉: {str(e)}")
        else:
            raise ValueError("公司内部API不可用，无法使用视觉功能")
    
    def search(self, query: str, max_results: int = 20,
               include_domains: Optional[List[str]] = None,
               country_code: str = "CN") -> List[Dict[str, Any]]:
        """
        搜索功能（Google优先策略）

        优化后的搜索引擎选择策略：
        - Google优先（10,000次/天免费，主要引擎）
        - Metaso辅助（5,000次免费，中文优化）
        - Tavily辅助（1,000次/月免费，国际质量）
        - Baidu辅助（100次/天免费，中文备用）

        调用次数策略：
        - Google: 3次（所有查询）
        - Tavily/Metaso: 1次（仅第一个查询）
        - Baidu: 1次（仅中文，仅第一个查询）

        Args:
            query: 搜索查询
            max_results: 最大结果数
            include_domains: 可选的域名列表
            country_code: 国家代码（用于区域优化）

        Returns:
            搜索结果列表
        """
        # 步骤 1: 检测查询语言
        is_chinese = self._is_chinese_content(query)

        # 步骤 2: 计算剩余免费额度
        google_remaining = 10000 - self.google_usage if self.google_hunter else 0
        metaso_remaining = 5000 - self.metaso_client.usage_count if self.metaso_client else 0
        tavily_remaining = 1000 - self.tavily_usage
        baidu_remaining = 100 - self.baidu_usage if self.baidu_hunter else 0

        # 步骤 3: 根据语言和国家选择搜索引擎（Google优先策略）
        if is_chinese:
            # 中文查询优先级: Google > Metaso > Baidu > Tavily ✅ Google优先
            if google_remaining > 0:
                return self._search_with_google(query, max_results,
                                              reason=f"中文内容（Google优先，剩余免费: {google_remaining:,}）")
            elif metaso_remaining > 0:
                return self._search_with_metaso(query, max_results, include_domains,
                                              reason=f"中文内容（剩余免费: {metaso_remaining:,}）")
            elif baidu_remaining > 0:
                return self._search_with_baidu(query, max_results,
                                          reason=f"中文内容（剩余免费: {baidu_remaining:,}）")
            else:
                return self._search_with_tavily(query, max_results, include_domains,
                                               reason="中文内容（其他引擎额度用尽）")
        else:
            # 国际查询优先级: Google > Tavily > Metaso ✅ Google优先
            if google_remaining > 0:
                return self._search_with_google(query, max_results,
                                               reason=f"国际内容（Google优先，剩余免费: {google_remaining:,}）")
            elif tavily_remaining > 0:
                return self._search_with_tavily(query, max_results, include_domains,
                                               reason=f"国际内容（剩余免费: {tavily_remaining:,}）")
            elif metaso_remaining > 0:
                return self._search_with_metaso(query, max_results, include_domains,
                                               reason=f"国际内容（剩余免费: {metaso_remaining:,}）")
            else:
                raise ValueError("所有搜索引擎免费额度已用尽")

    def _search_with_metaso(
        self,
        query: str,
        max_results: int,
        include_domains: Optional[List[str]],
        reason: str = ""
    ) -> List[Dict[str, Any]]:
        """
        使用 Metaso 搜索

        Args:
            query: 搜索查询
            max_results: 最大结果数
            include_domains: 可选的域名列表
            reason: 选择 Metaso 的原因

        Returns:
            搜索结果列表
        """
        if not self.metaso_client:
            print(f"[⚠️ Metaso] 客户端未初始化，降级到 Tavily")
            return self._search_with_tavily(query, max_results, include_domains, reason="Metaso不可用")

        # 显示选择原因
        if self.metaso_client.usage_count < 5000:
            remaining = 5000 - self.metaso_client.usage_count
            print(f"[🔍 搜索] 使用 Metaso（{reason}，免费额度剩余: {remaining:,} 次）")
        else:
            print(f"[🔍 搜索] 使用 Metaso（{reason}，付费模式 ¥0.03/次）")

        try:
            results = self.metaso_client.search(
                query=query,
                max_results=min(max_results, 20),
                include_domains=include_domains
            )
            if results:
                # 🔥 为每个结果添加search_engine字段
                for item in results:
                    item["search_engine"] = "Metaso"
                print(f"[✅ Metaso] 搜索成功，返回 {len(results)} 个结果")
                return results
            else:
                print(f"[⚠️ Metaso] 未返回结果，尝试 Tavily")
        except Exception as e:
            print(f"[⚠️ Metaso] 搜索失败: {str(e)}，尝试 Tavily")

        # 降级到 Tavily
        print(f"[🔄 降级] 切换到 Tavily")
        return self._search_with_tavily(query, max_results, include_domains, reason="Metaso失败")

    def _search_with_tavily(
        self,
        query: str,
        max_results: int,
        include_domains: Optional[List[str]],
        reason: str = ""
    ) -> List[Dict[str, Any]]:
        """
        使用 Tavily 搜索（AI Builders API）

        Args:
            query: 搜索查询
            max_results: 最大结果数
            include_domains: 可选的域名列表
            reason: 选择 Tavily 的原因

        Returns:
            搜索结果列表
        """
        if not self.ai_builders_client:
            raise ValueError("AI Builders API不可用，无法使用 Tavily 搜索")

        # 更新使用计数器
        self.tavily_usage += 1

        # 显示选择原因
        if reason:
            print(f"[🔍 搜索] 使用 Tavily（{reason}）")
        else:
            print(f"[🔍 搜索] 使用 Tavily（AI Builders）")

        endpoint = f"{self.ai_builders_client.base_url}/v1/search/"

        payload = {
            "keywords": [query],
            "max_results": min(max_results, 20)
        }

        # 处理域名限制
        if include_domains and len(include_domains) > 0:
            selected_domains = include_domains[:5]
            domain_site_clause = " OR ".join([f"site:{domain}" for domain in selected_domains])
            enhanced_query = f"{query} ({domain_site_clause})"
            payload["keywords"] = [enhanced_query]

        try:
            response = requests.post(
                endpoint,
                headers=self.ai_builders_client.headers,
                json=payload,
                timeout=30,
                proxies=get_proxy_config()
            )

            if response.status_code == 200:
                result = response.json()
                if "queries" in result and len(result["queries"]) > 0:
                    query_result = result["queries"][0]
                    if "response" in query_result and "results" in query_result["response"]:
                        # 🔥 为每个结果添加search_engine字段
                        results = query_result["response"]["results"]
                        for item in results:
                            item["search_engine"] = "Tavily"
                        print(f"[✅ Tavily] 搜索成功，返回 {len(results)} 个结果")
                        return results

            raise ValueError(f"Tavily搜索API调用失败，状态码: {response.status_code}")

        except Exception as e:
            raise ValueError(f"Tavily搜索API请求异常: {str(e)}")

    def _search_with_google(
        self,
        query: str,
        max_results: int,
        reason: str = ""
    ) -> List[Dict[str, Any]]:
        """
        使用 Google 搜索（免费额度优先）

        Args:
            query: 搜索查询
            max_results: 最大结果数
            reason: 选择 Google 的原因

        Returns:
            搜索结果列表
        """
        if not self.google_hunter:
            raise ValueError("Google搜索客户端不可用")

        # 更新使用计数器
        self.google_usage += 1

        # 显示选择原因
        print(f"[🔍 搜索] 使用 Google（{reason}）")

        try:
            results = self.google_hunter.search(query, max_results=max_results)

            # 转换为统一格式
            formatted_results = []
            for item in results:
                formatted_results.append({
                    "title": item.title,
                    "url": item.url,
                    "snippet": item.snippet,
                    "source": "Google搜索",
                    "search_engine": "Google"
                })

            print(f"[✅ Google] 搜索成功，返回 {len(formatted_results)} 个结果")
            return formatted_results

        except Exception as e:
            print(f"[⚠️ Google] 搜索失败: {str(e)}")
            return []

    def _search_with_baidu(
        self,
        query: str,
        max_results: int,
        reason: str = ""
    ) -> List[Dict[str, Any]]:
        """
        使用 Baidu 搜索（中文备用）

        Args:
            query: 搜索查询
            max_results: 最大结果数
            reason: 选择 Baidu 的原因

        Returns:
            搜索结果列表
        """
        if not self.baidu_hunter:
            raise ValueError("Baidu搜索客户端不可用")

        # 更新使用计数器
        self.baidu_usage += 1

        # 显示选择原因
        print(f"[🔍 搜索] 使用 Baidu（{reason}）")

        try:
            results = self.baidu_hunter.search(query, max_results=max_results)

            # 转换为统一格式
            formatted_results = []
            for item in results:
                formatted_results.append({
                    "title": item.title,
                    "url": item.url,
                    "snippet": item.snippet,
                    "source": "Baidu搜索",
                    "search_engine": "Baidu"
                })

            print(f"[✅ Baidu] 搜索成功，返回 {len(formatted_results)} 个结果")
            return formatted_results

        except Exception as e:
            print(f"[⚠️ Baidu] 搜索失败: {str(e)}")
            return []

    def _is_chinese_content(self, query: str) -> bool:
        """
        检测查询是否为中文内容

        Args:
            query: 搜索查询

        Returns:
            True 如果中文内容占比超过 30%
        """
        chinese_chars = sum(1 for c in query if '\u4e00' <= c <= '\u9fff')
        return chinese_chars > len(query) * 0.3 if len(query) > 0 else False

    def get_search_stats(self) -> Dict[str, Any]:
        """
        获取搜索引擎使用统计（包含所有引擎）

        Returns:
            统计信息字典
        """
        stats = {
            "metaso": None,
            "tavily": None,
            "google": None,
            "baidu": None,
            "enabled_engines": []
        }

        # Metaso 统计
        if self.metaso_client:
            stats["metaso"] = {
                "usage_count": self.metaso_client.usage_count,
                "free_tier_limit": 5000,
                "remaining_free": 5000 - self.metaso_client.usage_count,
                "total_cost": max(0, self.metaso_client.usage_count - 5000) * 0.03,
                "tier": "免费" if self.metaso_client.usage_count < 5000 else "付费"
            }
            stats["enabled_engines"].append("Metaso")

        # Tavily 统计
        if self.ai_builders_client:
            stats["tavily"] = {
                "usage_count": self.tavily_usage,
                "free_tier_limit": 1000,
                "remaining_free": 1000 - self.tavily_usage,
                "total_cost": max(0, self.tavily_usage - 1000) * 0.05,
                "tier": "免费" if self.tavily_usage < 1000 else "付费"
            }
            stats["enabled_engines"].append("Tavily (AI Builders)")

        # Google 统计
        if self.google_hunter:
            stats["google"] = {
                "usage_count": self.google_usage,
                "free_tier_limit": 10000,
                "remaining_free": 10000 - self.google_usage,
                "total_cost": 0,
                "tier": "免费"
            }
            stats["enabled_engines"].append("Google")

        # Baidu 统计
        if self.baidu_hunter:
            stats["baidu"] = {
                "usage_count": self.baidu_usage,
                "free_tier_limit": 100,
                "remaining_free": 100 - self.baidu_usage,
                "total_cost": 0,
                "tier": "免费"
            }
            stats["enabled_engines"].append("Baidu")

        return stats

    def check_cost_alert(self) -> Dict[str, Any]:
        """
        检查成本预警（监控免费额度使用情况）

        Returns:
            预警信息字典，包含：
            - alerts: 预警列表
            - stats: 当前统计数据
            - total_cost: 总成本
        """
        stats = self.get_search_stats()
        alerts = []

        # Metaso 预警（80% 免费额度用完）
        if stats.get('metaso') and stats['metaso']['usage_count'] > 4000:
            remaining = stats['metaso']['remaining_free']
            alerts.append({
                "level": "WARNING",
                "engine": "Metaso",
                "message": f"Metaso 免费额度即将用尽: {stats['metaso']['usage_count']:,}/5,000（剩余: {remaining:,}）",
                "usage": stats['metaso']['usage_count'],
                "remaining": remaining,
                "cost": stats['metaso']['total_cost']
            })

        # Tavily 预警（80% 免费额度用完）
        if stats.get('tavily') and stats['tavily']['usage_count'] > 800:
            remaining = stats['tavily']['remaining_free']
            alerts.append({
                "level": "WARNING",
                "engine": "Tavily",
                "message": f"Tavily 免费额度即将用尽: {stats['tavily']['usage_count']:,}/1,000（剩余: {remaining:,}）",
                "usage": stats['tavily']['usage_count'],
                "remaining": remaining,
                "cost": stats['tavily']['total_cost']
            })

        # Google 预警（80% 当天额度用完）
        if stats.get('google') and stats['google']['usage_count'] > 8000:
            remaining = stats['google']['remaining_free']
            alerts.append({
                "level": "INFO",
                "engine": "Google",
                "message": f"Google 当天额度即将用尽: {stats['google']['usage_count']:,}/10,000（剩余: {remaining:,}）",
                "usage": stats['google']['usage_count'],
                "remaining": remaining,
                "cost": 0
            })

        # Baidu 预警（80% 当天额度用完）
        if stats.get('baidu') and stats['baidu']['usage_count'] > 80:
            remaining = stats['baidu']['remaining_free']
            alerts.append({
                "level": "INFO",
                "engine": "Baidu",
                "message": f"Baidu 当天额度即将用尽: {stats['baidu']['usage_count']:,}/100（剩余: {remaining:,}）",
                "usage": stats['baidu']['usage_count'],
                "remaining": remaining,
                "cost": 0
            })

        # 计算总成本
        metaso_cost = stats['metaso']['total_cost'] if stats.get('metaso') else 0
        tavily_cost = stats['tavily']['total_cost'] if stats.get('tavily') else 0
        total_cost = metaso_cost + tavily_cost

        # 月度成本预警（>¥100）
        if total_cost > 100:
            alerts.append({
                "level": "CRITICAL",
                "engine": "Total",
                "message": f"⚠️ 月度成本预警: ¥{total_cost:.2f}（Metaso: ¥{metaso_cost:.2f}, Tavily: ¥{tavily_cost:.2f}）",
                "usage": 0,
                "remaining": 0,
                "cost": total_cost
            })

        # 打印预警
        if alerts:
            print(f"\n{'='*70}")
            print(f"[📊 成本监控] 搜索引擎使用情况")
            print(f"{'='*70}")

            for alert in alerts:
                level_icon = {
                    "CRITICAL": "🚨",
                    "WARNING": "⚠️",
                    "INFO": "ℹ️"
                }.get(alert['level'], "•")

                print(f"{level_icon} {alert['message']}")

            print(f"\n💰 总成本: ¥{total_cost:.2f}")
            print(f"{'='*70}\n")

        return {
            "alerts": alerts,
            "stats": stats,
            "total_cost": total_cost
        }

    def print_search_summary(self):
        """打印搜索使用摘要（便于监控）"""
        stats = self.get_search_stats()

        print(f"\n{'='*70}")
        print(f"[📊 搜索引擎统计摘要]")
        print(f"{'='*70}")

        if stats.get('metaso'):
            metaso = stats['metaso']
            print(f"\n  🔍 Metaso:")
            print(f"     • 使用次数: {metaso['usage_count']:,}/5,000")
            print(f"     • 剩余免费: {metaso['remaining_free']:,}")
            print(f"     • 当前成本: ¥{metaso['total_cost']:.2f}")
            print(f"     • 当前层级: {metaso['tier']}")

        if stats.get('tavily'):
            tavily = stats['tavily']
            print(f"\n  🔍 Tavily:")
            print(f"     • 使用次数: {tavily['usage_count']:,}/1,000")
            print(f"     • 剩余免费: {tavily['remaining_free']:,}")
            print(f"     • 当前成本: ¥{tavily['total_cost']:.2f}")
            print(f"     • 当前层级: {tavily['tier']}")

        if stats.get('google'):
            google = stats['google']
            print(f"\n  🔍 Google:")
            print(f"     • 使用次数: {google['usage_count']:,}/10,000")
            print(f"     • 剩余免费: {google['remaining_free']:,}")
            print(f"     • 当前成本: ¥{google['total_cost']:.2f}（免费）")

        if stats.get('baidu'):
            baidu = stats['baidu']
            print(f"\n  🔍 Baidu:")
            print(f"     • 使用次数: {baidu['usage_count']:,}/100")
            print(f"     • 剩余免费: {baidu['remaining_free']:,}")
            print(f"     • 当前成本: ¥{baidu['total_cost']:.2f}（免费）")

        # 总成本
        total_cost = sum(s['total_cost'] for s in [stats.get('metaso'), stats.get('tavily'), stats.get('google'), stats.get('baidu')] if s)
        print(f"\n  💰 总成本: ¥{total_cost:.2f}")
        print(f"{'='*70}\n")


# ============================================================================
# 全局客户端实例和工厂函数
# ============================================================================

_llm_client_instance = None


def get_llm_client() -> UnifiedLLMClient:
    """
    获取全局LLM客户端实例（单例模式）

    Returns:
        UnifiedLLMClient实例
    """
    global _llm_client_instance
    if _llm_client_instance is None:
        _llm_client_instance = UnifiedLLMClient()
    return _llm_client_instance

