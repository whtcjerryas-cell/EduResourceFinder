#!/usr/bin/env python3
"""
百度搜索API客户端
支持3种搜索API：
1. 百度搜索
2. 百度智能搜索生成
3. 智能搜索生成高性能版
"""

import os
import json
import time
import requests
from typing import Optional, List, Dict, Any


class BaiduSearchClient:
    """百度搜索API客户端"""
    
    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None):
        """
        初始化百度搜索客户端
        
        Args:
            api_key: API密钥，如果不提供则从环境变量读取
            secret_key: Secret密钥，如果不提供则从环境变量读取
        """
        # 优先使用传入的参数，否则从环境变量读取
        # 优先使用 BAIDU_API_KEY，如果没有则使用 BAIDU_ACCESS_KEY
        baidu_api_key = api_key or os.getenv("BAIDU_API_KEY")
        baidu_access_key = os.getenv("BAIDU_ACCESS_KEY")
        
        # 优先使用 BAIDU_API_KEY（无论格式）
        if baidu_api_key:
            self.api_key = baidu_api_key
            if baidu_api_key.startswith("APIKey-"):
                print(f"    [ℹ️] 使用千帆平台API Key格式（APIKey-xxx）")
            elif baidu_api_key.startswith("bce-v3/"):
                print(f"    [ℹ️] 使用百度云Access Key格式（bce-v3/ALTAK-xxx）")
            else:
                print(f"    [ℹ️] 使用BAIDU_API_KEY")
        elif baidu_access_key:
            self.api_key = baidu_access_key
            print(f"    [ℹ️] 使用BAIDU_ACCESS_KEY")
        else:
            raise ValueError("请设置 BAIDU_API_KEY 或 BAIDU_ACCESS_KEY 环境变量")
        
        self.secret_key = secret_key or os.getenv("BAIDU_SECRET_KEY")
        
        # 百度千帆API基础URL
        # 根据文档：https://cloud.baidu.com/doc/qianfan/s/Omh4su4s0
        # 智能搜索API endpoint: /v2/ai_search/chat/completions
        self.base_url = "https://qianfan.baidubce.com/v2/ai_search"
        
        # 判断API Key格式，选择认证方式
        # 根据文档和测试，千帆平台API可以直接使用API Key作为Bearer token
        # 支持格式：APIKey-xxx 或 bce-v3/ALTAK-xxx
        self.is_qianfan_format = self.api_key.startswith("APIKey-") or self.api_key.startswith("bce-v3/")
        
        if self.is_qianfan_format:
            # APIKey-xxx 或 bce-v3/ALTAK-xxx 格式：根据文档和测试，直接使用作为 Bearer token
            # 文档示例：Authorization: Bearer {api_key}
            print(f"    [✅] 检测到千帆平台API Key格式，将直接使用作为Bearer token")
            self.access_token = None
        else:
            # 其他格式：尝试获取 access_token，如果失败则直接使用API Key
            print(f"    [ℹ️] 检测到其他格式的API Key，尝试获取access_token...")
            self.access_token = self._get_access_token_from_ak_sk()
            if self.access_token is None:
                print(f"    [ℹ️] Token获取失败，将直接使用API Key作为Bearer token")
    
    def _get_access_token_from_ak_sk(self) -> str:
        """
        使用 Access Key 和 Secret Key 获取 access_token
        
        注意：百度千帆平台可能使用不同的token获取方式
        如果标准方式失败，可能需要直接使用Access Key作为Bearer token
        
        Returns:
            access_token字符串，如果获取失败则返回None（将直接使用Access Key）
        """
        # 尝试使用百度智能云的标准token获取方式
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,  # Access Key
            "client_secret": self.secret_key  # Secret Key
        }
        
        try:
            print(f"    [🔍] 使用Access Key和Secret Key获取access_token...")
            print(f"    [🔍] Access Key: {self.api_key[:20]}...")
            print(f"    [🔍] Token获取URL: {url}")
            
            response = requests.post(url, params=params, timeout=10)
            
            print(f"    [📥] Token获取响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                if "access_token" in result:
                    access_token = result["access_token"]
                    expires_in = result.get("expires_in", "未知")
                    print(f"    [✅] 成功获取access_token（有效期: {expires_in}秒）")
                    return access_token
                else:
                    error_msg = result.get("error_description", result.get("error", "未知错误"))
                    print(f"    [❌] Token获取失败: {error_msg}")
                    print(f"    [💡] 提示: 千帆平台可能需要直接使用Access Key作为Bearer token")
                    return None  # 返回None，将直接使用Access Key
            else:
                try:
                    error_data = response.json()
                    print(f"    [❌] Token获取错误响应: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
                except:
                    print(f"    [❌] Token获取错误响应: {response.text[:200]}")
                
                # 如果是401错误，说明可能需要直接使用Access Key
                if response.status_code == 401:
                    print(f"    [💡] 提示: 401错误，千帆平台可能需要直接使用Access Key作为Bearer token")
                    return None  # 返回None，将直接使用Access Key
                
                response.raise_for_status()
        
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            print(f"    [❌] 获取access_token请求失败: {error_msg}")
            print(f"    [💡] 提示: 将尝试直接使用Access Key作为Bearer token")
            return None  # 返回None，将直接使用Access Key
    
    def _get_access_token(self) -> str:
        """
        获取百度API的access_token
        
        注意：百度千帆平台可能使用不同的认证方式
        - 如果API Key格式是 APIKey-xxx，可能需要直接使用API Key
        - 如果API Key格式是传统格式，使用OAuth2获取token
        
        Returns:
            access_token字符串（或API Key本身）
        """
        # 检查API Key格式
        if self.api_key.startswith("APIKey-"):
            # 千帆平台的API Key格式，可能需要直接使用或使用不同的认证方式
            print(f"    [ℹ️] 检测到千帆平台API Key格式，尝试直接使用")
            # 先尝试使用Secret Key获取token
            url = "https://aip.baidubce.com/oauth/2.0/token"
            params = {
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.secret_key
            }
        else:
            # 传统格式，使用OAuth2
            url = "https://aip.baidubce.com/oauth/2.0/token"
            params = {
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.secret_key
            }
        
        try:
            print(f"    [🔍] 尝试获取access_token...")
            print(f"    [🔍] URL: {url}")
            print(f"    [🔍] API Key格式: {'千帆平台' if self.api_key.startswith('APIKey-') else '传统格式'}")
            
            response = requests.post(url, params=params, timeout=10)
            
            print(f"    [📥] Token获取响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                if "access_token" in result:
                    print(f"    [✅] 成功获取百度access_token")
                    return result["access_token"]
                else:
                    # 打印完整响应以便调试
                    print(f"    [❌] Token获取响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    error_msg = result.get("error_description", result.get("error", "未知错误"))
                    raise ValueError(f"获取access_token失败: {error_msg}")
            else:
                # 打印错误响应
                try:
                    error_data = response.json()
                    print(f"    [❌] Token获取错误响应: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
                except:
                    print(f"    [❌] Token获取错误响应: {response.text[:500]}")
                response.raise_for_status()
        
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            print(f"    [❌] 获取access_token请求失败: {error_msg}")
            
            # 如果是401错误且是千帆平台格式，尝试直接使用API Key
            if "401" in error_msg and self.api_key.startswith("APIKey-"):
                print(f"    [💡] 提示: 千帆平台API可能需要不同的认证方式")
                print(f"    [💡] 提示: 请检查文档确认是否需要直接使用API Key作为Bearer token")
                raise ValueError(f"获取access_token失败（千帆平台可能需要不同的认证方式）: {error_msg}")
            
            raise ValueError(f"获取access_token请求失败: {error_msg}")
    
    def search_baidu(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        调用百度搜索API
        
        API文档: https://cloud.baidu.com/doc/qianfan/s/2mh4su4uy
        
        注意：百度搜索API也使用智能搜索的endpoint，但可以通过参数控制只返回搜索结果
        
        Args:
            query: 搜索查询词
            max_results: 最大返回结果数
        
        Returns:
            搜索结果列表
        """
        # 根据文档，百度搜索也使用智能搜索的endpoint
        # 但可以通过search_mode="required"和只返回搜索结果来模拟纯搜索
        endpoint = f"{self.base_url}/chat/completions"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # 根据认证方式设置Authorization header
        if self.is_qianfan_format or self.access_token is None:
            # APIKey-xxx 格式或token获取失败：直接使用API Key/Access Key作为Bearer token
            headers["Authorization"] = f"Bearer {self.api_key}"
            print(f"    [🔍] 使用API Key/Access Key作为Bearer token: {self.api_key[:20]}...")
        else:
            # Access Key + Secret Key 格式且成功获取token：使用access_token
            headers["Authorization"] = f"Bearer {self.access_token}"
            print(f"    [🔍] 使用access_token作为Bearer token")
        
        # 根据文档，请求体格式
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": query
                }
            ],
            "search_source": "baidu_search_v2",
            "resource_type_filter": [
                {
                    "type": "web",
                    "top_k": min(max_results, 20)  # V2版本最多20个
                }
            ],
            "model": "ernie-3.5-8k",
            "search_mode": "required",  # 必须执行搜索
            "stream": False,
            "enable_corner_markers": False,  # 不需要角标
            "enable_deep_search": False,
            "max_completion_tokens": 0  # 不生成总结，只返回搜索结果
        }
        
        try:
            print(f"    [🔍 百度搜索] 准备调用API，查询: \"{query}\"")
            print(f"    [🔍 百度搜索] Endpoint: {endpoint}")
            print(f"    [🔍 百度搜索] Top K: {payload['resource_type_filter'][0]['top_k']}")
            
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=60  # 智能搜索可能需要更长时间生成内容
            )
            
            print(f"    [📥 响应] HTTP状态码: {response.status_code}")
            
            response.raise_for_status()
            result = response.json()
            
            # 检查错误
            if "error" in result or "error_code" in result:
                error_code = result.get("error_code") or result.get("code")
                error_msg = result.get("error_msg") or result.get("message", "未知错误")
                raise ValueError(f"百度搜索API调用失败 [错误码: {error_code}]: {error_msg}")
            
            # 解析结果（根据实际API响应格式调整）
            # 根据文档和实际测试，API返回格式包含：
            # - references: 搜索结果列表
            # - choices: 生成的内容
            results = []
            
            # 优先从references字段提取搜索结果
            if "references" in result and isinstance(result["references"], list):
                items = result["references"]
            elif "search_results" in result:
                items = result["search_results"]
            elif "data" in result:
                data = result["data"]
                if "results" in data:
                    items = data["results"]
                elif isinstance(data, list):
                    items = data
                else:
                    items = []
            else:
                items = []
            
            for item in items[:max_results]:
                results.append({
                    "title": item.get("title", item.get("name", "")),
                    "url": item.get("url", item.get("link", "")),
                    "snippet": item.get("snippet", item.get("description", item.get("content", "")))
                })
            
            print(f"    [✅ 百度搜索] API调用成功，返回 {len(results)} 个结果")
            if results:
                print(f"    [📊 百度搜索] 结果预览:")
                for i, result in enumerate(results[:3], 1):
                    print(f"      [{i}] {result['title'][:50]}... -> {result['url'][:50]}...")
            
            return results
        
        except requests.exceptions.RequestException as e:
            print(f"    [❌ 错误] 百度搜索API请求异常: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"    [❌ 错误] API错误详情: {error_data}")
                except:
                    print(f"    [❌ 错误] API响应: {e.response.text[:200]}")
            raise ValueError(f"百度搜索API请求异常: {str(e)}")
    
    def search_smart(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        调用百度智能搜索生成API
        
        API文档: https://cloud.baidu.com/doc/qianfan/s/Omh4su4s0
        
        Args:
            query: 搜索查询词
            max_results: 最大返回结果数
        
        Returns:
            包含搜索结果和生成内容的字典
        """
        # 根据文档，智能搜索生成API的endpoint
        # URL: /v2/ai_search/chat/completions
        endpoint = f"{self.base_url}/chat/completions"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # 根据认证方式设置Authorization header
        if self.is_qianfan_format or self.access_token is None:
            # APIKey-xxx 格式或token获取失败：直接使用API Key/Access Key作为Bearer token
            headers["Authorization"] = f"Bearer {self.api_key}"
            print(f"    [🔍] 使用API Key/Access Key作为Bearer token: {self.api_key[:20]}...")
        else:
            # Access Key + Secret Key 格式且成功获取token：使用access_token
            headers["Authorization"] = f"Bearer {self.access_token}"
            print(f"    [🔍] 使用access_token作为Bearer token")
        
        # 根据文档，请求体格式
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": query
                }
            ],
            "search_source": "baidu_search_v2",  # 使用V2版本，性能更好
            "resource_type_filter": [
                {
                    "type": "web",
                    "top_k": min(max_results, 20)  # V2版本最多20个
                }
            ],
            "model": "ernie-3.5-8k",  # 默认模型，可以根据需要调整
            "stream": False,
            "enable_corner_markers": True,
            "enable_deep_search": False
        }
        
        try:
            print(f"    [🔍 百度智能搜索] 准备调用API，查询: \"{query}\"")
            print(f"    [🔍 百度智能搜索] Endpoint: {endpoint}")
            print(f"    [🔍 百度智能搜索] Model: {payload['model']}, Top K: {payload['resource_type_filter'][0]['top_k']}")
            
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=60  # 智能搜索可能需要更长时间生成内容
            )
            
            print(f"    [📥 响应] HTTP状态码: {response.status_code}")
            
            response.raise_for_status()
            result = response.json()
            
            # 检查错误（千帆平台可能使用不同的错误格式）
            if "error" in result or "error_code" in result:
                error_code = result.get("error_code") or result.get("code")
                error_msg = result.get("error_msg") or result.get("message", "未知错误")
                raise ValueError(f"百度智能搜索API调用失败 [错误码: {error_code}]: {error_msg}")
            
            print(f"    [✅ 百度智能搜索] API调用成功")
            return result
        
        except requests.exceptions.RequestException as e:
            print(f"    [❌ 错误] 百度智能搜索API请求异常: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"    [❌ 错误] API错误详情: {error_data}")
                except:
                    print(f"    [❌ 错误] API响应: {e.response.text[:200]}")
            raise ValueError(f"百度智能搜索API请求异常: {str(e)}")
    
    def search_high_performance(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        调用智能搜索生成高性能版API
        
        API文档: https://cloud.baidu.com/doc/qianfan/s/Kmiy99ziv
        
        注意：高性能版可能使用相同的endpoint，但可能有不同的参数或模型
        
        Args:
            query: 搜索查询词
            max_results: 最大返回结果数
        
        Returns:
            包含搜索结果和生成内容的字典
        """
        # 高性能版可能使用相同的endpoint，但使用更高性能的模型
        endpoint = f"{self.base_url}/chat/completions"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # 根据认证方式设置Authorization header
        if self.is_qianfan_format or self.access_token is None:
            # APIKey-xxx 格式或token获取失败：直接使用API Key/Access Key作为Bearer token
            headers["Authorization"] = f"Bearer {self.api_key}"
            print(f"    [🔍] 使用API Key/Access Key作为Bearer token: {self.api_key[:20]}...")
        else:
            # Access Key + Secret Key 格式且成功获取token：使用access_token
            headers["Authorization"] = f"Bearer {self.access_token}"
            print(f"    [🔍] 使用access_token作为Bearer token")
        
        # 根据文档，使用高性能模型
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": query
                }
            ],
            "search_source": "baidu_search_v2",
            "resource_type_filter": [
                {
                    "type": "web",
                    "top_k": min(max_results, 20)  # V2版本最多20个
                }
            ],
            "model": "ernie-4.5-turbo-32k",  # 使用高性能模型
            "stream": False,
            "enable_corner_markers": True,
            "enable_deep_search": False
        }
        
        try:
            print(f"    [🔍 智能搜索高性能版] 准备调用API，查询: \"{query}\"")
            print(f"    [🔍 智能搜索高性能版] Endpoint: {endpoint}")
            print(f"    [🔍 智能搜索高性能版] Model: {payload['model']}, Top K: {payload['resource_type_filter'][0]['top_k']}")
            
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=60  # 智能搜索可能需要更长时间生成内容
            )
            
            print(f"    [📥 响应] HTTP状态码: {response.status_code}")
            
            response.raise_for_status()
            result = response.json()
            
            # 检查错误
            if "error" in result or "error_code" in result:
                error_code = result.get("error_code") or result.get("code")
                error_msg = result.get("error_msg") or result.get("message", "未知错误")
                raise ValueError(f"智能搜索高性能版API调用失败 [错误码: {error_code}]: {error_msg}")
            
            print(f"    [✅ 智能搜索高性能版] API调用成功")
            return result
        
        except requests.exceptions.RequestException as e:
            print(f"    [❌ 错误] 智能搜索高性能版API请求异常: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"    [❌ 错误] API错误详情: {error_data}")
                except:
                    print(f"    [❌ 错误] API响应: {e.response.text[:200]}")
            raise ValueError(f"智能搜索高性能版API请求异常: {str(e)}")


class BaiduSearchAPIClient:
    """
    百度搜索API客户端（简化版，用于SearchHunter集成）
    自动选择最适合的API
    """
    
    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None):
        """
        初始化客户端
        
        Args:
            api_key: API密钥
            secret_key: Secret密钥
        """
        self.client = BaiduSearchClient(api_key, secret_key)
        # 通过环境变量选择API类型：baidu, smart, high_performance
        self.api_type = os.getenv("BAIDU_SEARCH_API_TYPE", "baidu")
        print(f"    [📋 配置] 使用百度搜索API类型: {self.api_type}")
    
    def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        执行搜索（根据配置选择API类型）
        
        Args:
            query: 搜索查询词
            max_results: 最大返回结果数
        
        Returns:
            搜索结果列表
        """
        if self.api_type == "smart":
            result = self.client.search_smart(query, max_results)
            # 解析智能搜索的结果
            return self._parse_search_results(result, max_results)
        
        elif self.api_type == "high_performance":
            result = self.client.search_high_performance(query, max_results)
            # 解析高性能版的结果
            return self._parse_search_results(result, max_results)
        
        else:
            # 默认使用百度搜索
            return self.client.search_baidu(query, max_results)
    
    def _parse_search_results(self, result: Dict[str, Any], max_results: int) -> List[Dict[str, Any]]:
        """
        解析搜索结果（智能搜索和高性能版）
        
        Args:
            result: API返回的结果字典
            max_results: 最大结果数
        
        Returns:
            搜索结果列表
        """
        results = []
        
        # 根据文档和实际测试，智能搜索API返回格式包含：
        # - references: 搜索结果列表（主要字段）
        # - choices: 生成的内容
        # - search_results: 搜索结果列表（备用）
        
        if "references" in result and isinstance(result["references"], list):
            items = result["references"]
        elif "search_results" in result:
            items = result["search_results"]
        elif "data" in result:
            data = result["data"]
            if "results" in data:
                items = data["results"]
            elif "items" in data:
                items = data["items"]
            elif isinstance(data, list):
                items = data
            else:
                items = []
        else:
            items = []
        
        for item in items[:max_results]:
            results.append({
                "title": item.get("title", item.get("name", "")),
                "url": item.get("url", item.get("link", "")),
                "snippet": item.get("snippet", item.get("description", item.get("content", "")))
            })
        
        return results

