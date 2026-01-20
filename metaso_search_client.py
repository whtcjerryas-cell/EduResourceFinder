#!/usr/bin/env python3
"""
Metaso (秘塔AI搜索) 客户端
定价：¥0.03/次（约 $0.004/次）
免费额度：新用户 5,000 次

官方网站：https://metaso.cn
API端点：https://metaso.cn/api/mcp (MCP JSON-RPC 2.0 协议)

支持六种搜索类型：
- webpage: 网页搜索
- document: 文库搜索
- paper: 学术论文搜索
- image: 图片搜索
- video: 视频搜索
- podcast: 播客搜索
"""

import os
import json
import time
import requests
from typing import Optional, List, Dict, Any
from logger_utils import get_logger

logger = get_logger('metaso_client')


class MetasoSearchClient:
    """秘塔AI搜索客户端（MCP JSON-RPC 2.0 协议）"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 Metaso 客户端

        Args:
            api_key: Metaso API Key，如果不提供则从环境变量读取
        """
        self.api_key = api_key or os.getenv("METASO_API_KEY")
        if not self.api_key:
            raise ValueError("METASO_API_KEY not found in environment or arguments")

        # Metaso API 端点（官方 MCP 端点）
        self.base_url = os.getenv("METASO_API_BASE", "https://metaso.cn/api/mcp")

        self.usage_count = 0  # 使用计数器
        self.free_tier_limit = 5000  # 免费额度

        logger.info(f"[✅ Metaso] 客户端初始化成功")
        logger.info(f"[📊 Metaso] 免费额度: {self.free_tier_limit:,} 次")
        logger.info(f"[💰 Metaso] 超出后定价: ¥0.03/次")

    def search(
        self,
        query: str,
        max_results: int = 10,
        search_scope: str = "webpage",  # webpage, document, paper, image, video, podcast
        include_summary: bool = False,
        include_raw_content: bool = False,
        timeout: int = 30,
        include_domains: Optional[List[str]] = None,  # 兼容性参数，通过后过滤实现
        search_mode: Optional[str] = None  # 兼容性参数：simple, deep, research
    ) -> List[Dict[str, Any]]:
        """
        执行搜索（使用 MCP JSON-RPC 2.0 协议）

        Args:
            query: 搜索查询
            max_results: 最大结果数
            search_scope: 搜索类型（webpage/document/paper/image/video/podcast）
            include_summary: 是否包含 AI 摘要
            include_raw_content: 是否包含原始内容
            timeout: 超时时间（秒）
            include_domains: 域名过滤列表（兼容性参数，通过后过滤实现）
            search_mode: 搜索模式（兼容性参数：simple/deep/research）
                         - simple -> 网页搜索
                         - deep -> 网页搜索 + 摘要
                         - research -> 学术搜索

        Returns:
            搜索结果列表，格式：
            [
                {
                    "title": "结果标题",
                    "url": "结果URL",
                    "snippet": "结果摘要",
                    "source": "Metaso搜索",
                    "search_engine": "Metaso"
                },
                ...
            ]
        """
        try:
            # 映射 search_mode 到 Metaso 参数
            if search_mode:
                mode_mapping = {
                    "simple": ("webpage", False),
                    "deep": ("webpage", True),
                    "research": ("paper", True)
                }
                if search_mode in mode_mapping:
                    search_scope, include_summary = mode_mapping[search_mode]
                    logger.info(f"[🔄 模式映射] search_mode='{search_mode}' -> scope='{search_scope}', include_summary={include_summary}")

            logger.info(f"[🔍 Metaso] 开始搜索...")
            logger.info(f"[📝 查询] {query}")
            logger.info(f"[⚙️ 参数] max_results={max_results}, scope={search_scope}")

            # 使用 MCP JSON-RPC 2.0 协议
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # 构造 JSON-RPC 2.0 请求
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "metaso_web_search",
                    "arguments": {
                        "q": query,
                        "size": min(max_results, 20),
                        "scope": search_scope,
                        "includeSummary": include_summary,
                        "includeRawContent": include_raw_content
                    }
                }
            }

            logger.info(f"[📤 请求] JSON-RPC 2.0")
            logger.debug(f"[📄 Payload] {json.dumps(payload, ensure_ascii=False)}")

            # 发送请求
            start_time = time.time()
            with requests.Session() as session:
                session.trust_env = False  # 强制禁用代理
                response = session.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=timeout
                )
            elapsed_time = time.time() - start_time

            logger.info(f"[📥 响应] 状态码: {response.status_code}, 耗时: {elapsed_time:.2f}s")

            # 检查响应状态
            if response.status_code == 401:
                logger.error(f"[❌ 错误] API Key 无效或已过期")
                return []
            elif response.status_code == 429:
                logger.error(f"[❌ 错误] 超出速率限制或配额")
                return []
            elif response.status_code != 200:
                logger.error(f"[❌ 错误] HTTP {response.status_code}: {response.text}")
                return []

            # 解析 JSON-RPC 响应
            data = response.json()

            # 检查是否有错误
            if "error" in data:
                error_info = data["error"]
                logger.error(f"[❌ 错误] JSON-RPC 错误: {error_info}")
                return []

            # 提取结果
            result = data.get("result", {})
            if not result:
                logger.warning(f"[⚠️ 警告] 响应中没有 result 字段")
                return []

            # 解析搜索结果
            # Metaso MCP 响应格式: result.content[0].text 是 JSON 字符串
            content_list = result.get("content", [])
            if not content_list or len(content_list) == 0:
                logger.warning(f"[⚠️ 警告] 响应中没有 content 字段或为空")
                return []

            # 提取 content[0].text（JSON 字符串）
            result_text = content_list[0].get("text", "") if isinstance(content_list[0], dict) else ""
            if not result_text:
                logger.warning(f"[⚠️ 警告] content[0] 中没有 text 字段")
                return []

            # 解析 JSON 字符串
            try:
                result_data = json.loads(result_text)
            except json.JSONDecodeError as e:
                logger.error(f"[❌ 解析] JSON 解析失败: {e}")
                logger.debug(f"[📄 原始文本] {result_text[:500]}")
                return []

            # 提取 webpages 数组
            webpages = result_data.get("webpages", [])
            if not webpages:
                logger.warning(f"[⚠️ 警告] 结果中没有 webpages 字段")
                logger.debug(f"[📄 结果数据] {json.dumps(result_data, ensure_ascii=False)[:500]}")
                return []

            logger.info(f"[📊 原始结果] 找到 {len(webpages)} 个网页")

            # 转换为统一格式
            results = []
            for item in webpages:
                result = {
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),  # Metaso 使用 "link" 字段
                    "snippet": item.get("snippet", ""),
                    "source": "Metaso搜索",
                    "search_engine": "Metaso"
                }
                results.append(result)

            # 域名过滤（如果指定）
            # [修复] 2026-01-20: 重新启用域名过滤，确保搜索结果来自优先域名
            if include_domains:
                original_count = len(results)
                results = [
                    r for r in results
                    if any(domain.lower() in r.get("url", "").lower() for domain in include_domains)
                ]
                logger.info(f"[🔍 过滤] 域名过滤: 从 {original_count} 个结果过滤到 {len(results)} 个")
                logger.info(f"[📋 目标域名] {', '.join(include_domains[:5])}")

                # 如果过滤后没有结果，记录警告但不过滤（回退到全部结果）
                if len(results) == 0:
                    logger.warning(f"[⚠️ 警告] 域名过滤后无结果，使用原始搜索结果（共 {original_count} 个）")
                    results = webpages  # 回退到未过滤的结果
                    for item in results:
                        result = {
                            "title": item.get("title", ""),
                            "url": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                            "source": "Metaso搜索",
                            "search_engine": "Metaso"
                        }
                    results = results[:original_count]

            # 更新使用计数
            self.usage_count += 1

            # 计算成本
            if self.usage_count <= self.free_tier_limit:
                cost = 0.0
                tier = "免费"
            else:
                cost = (self.usage_count - self.free_tier_limit) * 0.03
                tier = "付费"

            logger.info(f"[✅ Metaso] 搜索成功")
            logger.info(f"[📊 统计] 第 {self.usage_count:,} 次调用")
            logger.info(f"[💰 成本] ¥{cost:.2f} ({tier})")
            logger.info(f"[📋 结果] 返回 {len(results)} 个结果")

            return results

        except requests.exceptions.Timeout:
            logger.error(f"[❌ 超时] 请求超时（{timeout}秒）")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"[❌ 网络] 请求失败: {str(e)}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"[❌ 解析] JSON 解析失败: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"[❌ 未知] 搜索失败: {str(e)}")
            return []

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        获取使用统计

        Returns:
            使用统计字典
        """
        if self.usage_count <= self.free_tier_limit:
            remaining = self.free_tier_limit - self.usage_count
            cost = 0.0
        else:
            remaining = 0
            cost = (self.usage_count - self.free_tier_limit) * 0.03

        return {
            "usage_count": self.usage_count,
            "free_tier_limit": self.free_tier_limit,
            "remaining_free": remaining,
            "total_cost": cost,
            "cost_per_search": 0.03,
            "tier": "免费" if self.usage_count <= self.free_tier_limit else "付费"
        }

    def reset_usage_count(self):
        """重置使用计数器（用于测试或新计费周期）"""
        old_count = self.usage_count
        self.usage_count = 0
        logger.info(f"[🔄 Metaso] 使用计数器已重置（原计数: {old_count:,}）")


# 便捷函数
def create_metaso_client() -> Optional[MetasoSearchClient]:
    """
    创建 Metaso 客户端的便捷函数

    Returns:
        MetasoSearchClient 实例，如果初始化失败则返回 None
    """
    try:
        return MetasoSearchClient()
    except Exception as e:
        logger.warning(f"[⚠️ Metaso] 客户端初始化失败: {e}")
        return None


if __name__ == "__main__":
    # 测试代码
    print("=" * 60)
    print("Metaso 搜索客户端测试（MCP JSON-RPC 2.0 协议）")
    print("=" * 60)

    try:
        client = MetasoSearchClient()

        # 测试搜索
        print("\n测试 1: 中文搜索")
        results = client.search("Python 教程", max_results=5)
        print(f"结果: {len(results)} 个")
        for i, result in enumerate(results[:3], 1):
            print(f"{i}. {result['title']}")
            print(f"   {result['url']}")

        print("\n使用统计:")
        stats = client.get_usage_stats()
        print(f"- 使用次数: {stats['usage_count']:,}")
        print(f"- 剩余免费: {stats['remaining_free']:,}")
        print(f"- 总成本: ¥{stats['total_cost']:.2f}")
        print(f"- 当前层级: {stats['tier']}")

    except Exception as e:
        print(f"\n测试失败: {e}")
        print("\n提示：")
        print("1. 请确保已设置 METASO_API_KEY 环境变量")
        print("2. Metaso 使用 MCP JSON-RPC 2.0 协议")
        print("3. API 端点: https://metaso.cn/api/mcp")
