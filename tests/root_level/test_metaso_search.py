#!/usr/bin/env python3
"""
Metaso 搜索测试脚本
测试 Metaso 客户端的基本功能和集成
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ 已加载 .env 文件: {env_file}")
    else:
        print(f"⚠️ .env 文件不存在: {env_file}")
except ImportError:
    print("⚠️ python-dotenv 未安装，尝试手动加载 .env 文件...")
    env_file = project_root / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print(f"✅ 已手动加载 .env 文件")

from metaso_search_client import MetasoSearchClient
from llm_client import UnifiedLLMClient
from utils.logger_utils import get_logger

logger = get_logger('test_metaso')

# ANSI 颜色代码
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_test_header(title):
    """打印测试标题"""
    print("\n" + "=" * 70)
    print(f"{Colors.HEADER}{Colors.BOLD}{title}{Colors.ENDC}")
    print("=" * 70)


def print_test_result(test_name, success, message=""):
    """打印测试结果"""
    if success:
        print(f"{Colors.OKGREEN}✅ PASS{Colors.ENDC} {test_name}")
        if message:
            print(f"   {message}")
    else:
        print(f"{Colors.FAIL}❌ FAIL{Colors.ENDC} {test_name}")
        if message:
            print(f"   {Colors.FAIL}{message}{Colors.ENDC}")


def test_metaso_client_initialization():
    """测试 1: Metaso 客户端初始化"""
    print_test_header("测试 1: Metaso 客户端初始化")

    try:
        client = MetasoSearchClient()
        print_test_result("客户端初始化", True, f"API Key: {client.api_key[:20]}...")
        print_test_result("免费额度设置", True, f"{client.free_tier_limit:,} 次")
        print_test_result("使用计数器", True, f"初始值: {client.usage_count}")
        return client
    except Exception as e:
        print_test_result("客户端初始化", False, str(e))
        return None


def test_chinese_search(client):
    """测试 2: 中文搜索（测试免费额度）"""
    print_test_header("测试 2: 中文搜索")

    if not client:
        print_test_result("跳过测试", False, "客户端未初始化")
        return

    try:
        query = "Python 教程 播放列表"
        print(f"查询: {query}")

        results = client.search(query, max_results=5)

        if results:
            print_test_result("中文搜索", True, f"返回 {len(results)} 个结果")
            print("\n前 3 个结果:")
            for i, result in enumerate(results[:3], 1):
                print(f"  {i}. {result.get('title', 'N/A')}")
                print(f"     URL: {result.get('url', 'N/A')}")
                print(f"     摘要: {result.get('snippet', 'N/A')[:80]}...")
        else:
            print_test_result("中文搜索", False, "未返回结果")

        # 显示使用统计
        stats = client.get_usage_stats()
        print(f"\n使用统计:")
        print(f"  - 使用次数: {stats['usage_count']:,}")
        print(f"  - 剩余免费: {stats['remaining_free']:,}")
        print(f"  - 总成本: ¥{stats['total_cost']:.2f}")
        print(f"  - 当前层级: {stats['tier']}")

    except Exception as e:
        print_test_result("中文搜索", False, str(e))


def test_indonesian_search(client):
    """测试 3: 印尼语搜索（测试国际内容质量）"""
    print_test_header("测试 3: 印尼语搜索")

    if not client:
        print_test_result("跳过测试", False, "客户端未初始化")
        return

    try:
        query = "Kelas 1 Matematika video pembelajaran"
        print(f"查询: {query}")

        results = client.search(query, max_results=5)

        if results:
            print_test_result("印尼语搜索", True, f"返回 {len(results)} 个结果")
            print("\n前 3 个结果:")
            for i, result in enumerate(results[:3], 1):
                print(f"  {i}. {result.get('title', 'N/A')}")
                print(f"     URL: {result.get('url', 'N/A')}")
        else:
            print_test_result("印尼语搜索", False, "未返回结果")

    except Exception as e:
        print_test_result("印尼语搜索", False, str(e))


def test_english_search(client):
    """测试 4: 英语搜索（测试国际内容质量）"""
    print_test_header("测试 4: 英语搜索")

    if not client:
        print_test_result("跳过测试", False, "客户端未初始化")
        return

    try:
        query = "Grade 5 Science video lessons playlist"
        print(f"查询: {query}")

        results = client.search(query, max_results=5)

        if results:
            print_test_result("英语搜索", True, f"返回 {len(results)} 个结果")
            print("\n前 3 个结果:")
            for i, result in enumerate(results[:3], 1):
                print(f"  {i}. {result.get('title', 'N/A')}")
                print(f"     URL: {result.get('url', 'N/A')}")
        else:
            print_test_result("英语搜索", False, "未返回结果")

    except Exception as e:
        print_test_result("英语搜索", False, str(e))


def test_llm_client_integration():
    """测试 5: LLM 客户端集成"""
    print_test_header("测试 5: LLM 客户端集成")

    try:
        llm_client = UnifiedLLMClient()
        print_test_result("LLM 客户端初始化", True)

        # 检查 Metaso 客户端是否已集成
        if hasattr(llm_client, 'metaso_client') and llm_client.metaso_client:
            print_test_result("Metaso 客户端集成", True)
        else:
            print_test_result("Metaso 客户端集成", False, "Metaso 客户端未初始化")
            return

        # 测试搜索方法
        print("\n测试中文内容检测:")
        test_queries = [
            ("Python 教程", True),
            ("Python tutorial", False),
            ("Kelas 1 Matematika", False),
            ("初二 地理", True),
            ("Grade 5 Science", False)
        ]

        for query, expected in test_queries:
            is_chinese = llm_client._is_chinese_content(query)
            status = "✅" if is_chinese == expected else "❌"
            print(f"  {status} '{query}' -> 中文={is_chinese} (预期: {expected})")

        # 获取搜索统计
        stats = llm_client.get_search_stats()
        print(f"\n启用的搜索引擎: {', '.join(stats['enabled_engines'])}")

        if stats['metaso']:
            print(f"Metaso 统计:")
            print(f"  - 使用次数: {stats['metaso']['usage_count']:,}")
            print(f"  - 剩余免费: {stats['metaso']['remaining_free']:,}")

    except Exception as e:
        print_test_result("LLM 客户端集成", False, str(e))


def test_domain_filtering(client):
    """测试 6: 域名过滤"""
    print_test_header("测试 6: 域名过滤")

    if not client:
        print_test_result("跳过测试", False, "客户端未初始化")
        return

    try:
        query = "Python 教程"
        domains = ["youtube.com", "bilibili.com"]
        print(f"查询: {query}")
        print(f"域名过滤: {', '.join(domains)}")

        results = client.search(query, max_results=5, include_domains=domains)

        if results:
            print_test_result("域名过滤", True, f"返回 {len(results)} 个结果")
            print("\n结果:")
            for i, result in enumerate(results[:3], 1):
                print(f"  {i}. {result.get('title', 'N/A')}")
                url = result.get('url', 'N/A')
                print(f"     URL: {url}")
                # 检查是否包含指定域名
                matched = any(domain in url for domain in domains)
                status = "✅" if matched else "❌"
                print(f"     {status} 域名匹配: {matched}")
        else:
            print_test_result("域名过滤", False, "未返回结果")

    except Exception as e:
        print_test_result("域名过滤", False, str(e))


def test_search_modes(client):
    """测试 7: 搜索模式"""
    print_test_header("测试 7: 搜索模式")

    if not client:
        print_test_result("跳过测试", False, "客户端未初始化")
        return

    modes = ["simple", "deep", "research"]
    query = "机器学习教程"

    for mode in modes:
        try:
            print(f"\n模式: {mode}")
            results = client.search(query, max_results=3, search_mode=mode)

            if results:
                print_test_result(f"模式 '{mode}'", True, f"返回 {len(results)} 个结果")
            else:
                print_test_result(f"模式 '{mode}'", False, "未返回结果")

        except Exception as e:
            print_test_result(f"模式 '{mode}'", False, str(e))


def main():
    """主函数"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("=" * 70)
    print("  Metaso 搜索集成测试")
    print("=" * 70)
    print(f"{Colors.ENDC}")

    # 检查环境变量
    if not os.getenv("METASO_API_KEY"):
        print(f"{Colors.WARNING}警告: METASO_API_KEY 环境变量未设置{Colors.ENDC}")
        print("请确保已在 .env 文件中设置 METASO_API_KEY")
        sys.exit(1)

    # 运行测试
    client = test_metaso_client_initialization()

    if client:
        test_chinese_search(client)
        test_indonesian_search(client)
        test_english_search(client)
        test_domain_filtering(client)
        test_search_modes(client)

    test_llm_client_integration()

    # 最终统计
    print_test_header("测试总结")
    if client:
        stats = client.get_usage_stats()
        if stats and 'metaso' in stats and stats['metaso']:
            print(f"Metaso 使用统计:")
            print(f"  - 总使用次数: {stats['metaso']['usage_count']:,}")
            print(f"  - 剩余免费额度: {stats['metaso']['remaining_free']:,}")
            print(f"  - 累计成本: ¥{stats['metaso']['total_cost']:.2f}")
            print(f"  - 当前层级: {stats['metaso']['tier']}")
        else:
            print("Metaso 未使用或无统计数据")

    print(f"\n{Colors.OKGREEN}测试完成！{Colors.ENDC}\n")


if __name__ == "__main__":
    main()
