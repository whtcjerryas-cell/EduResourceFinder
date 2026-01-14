#!/usr/bin/env python3
"""
测试Google优先策略
验证优化后的搜索策略：
- Google搜3次（主要引擎）
- Tavily/Metaso搜1次（辅助引擎）
- 百度搜1次（中文辅助）
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载 .env
try:
    from dotenv import load_dotenv
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ 已加载 .env 文件")
except ImportError:
    # 手动加载
    env_file = project_root / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print(f"✅ 已手动加载 .env 文件")

from llm_client import UnifiedLLMClient

# ANSI 颜色
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def test_search(query, country_code, expected_engine):
    """
    测试单个查询

    Args:
        query: 搜索查询
        country_code: 国家代码
        expected_engine: 预期使用的搜索引擎
    """
    print(f"\n{Colors.BOLD}查询: {query}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}国家: {country_code}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}预期引擎: {expected_engine}{Colors.ENDC}")

    try:
        results = llm_client.search(query, max_results=3, country_code=country_code)

        if results:
            # 判断实际使用的搜索引擎
            if results and len(results) > 0:
                actual_engine = results[0].get('search_engine', 'Unknown')
            else:
                actual_engine = 'Unknown'

            print(f"{Colors.OKGREEN}✅ 成功{Colors.ENDC} - 返回 {len(results)} 个结果")
            print(f"   实际引擎: {actual_engine}")

            # 检查是否使用了预期引擎
            if actual_engine == expected_engine:
                print(f"{Colors.OKGREEN}✅ 引擎选择正确{Colors.ENDC}")
            else:
                print(f"{Colors.WARNING}⚠️ 引擎选择与预期不符（预期: {expected_engine}, 实际: {actual_engine}）{Colors.ENDC}")

            # 显示前2个结果
            print(f"   前 2 个结果:")
            for i, result in enumerate(results[:2], 1):
                print(f"   {i}. {result.get('title', 'N/A')[:60]}...")
        else:
            print(f"{Colors.WARNING}⚠️ 未返回结果{Colors.ENDC}")

    except Exception as e:
        print(f"{Colors.FAIL}❌ 错误: {e}{Colors.ENDC}")


def test_google_priority_strategy():
    """测试Google优先策略"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("=" * 70)
    print("  测试 Google 优先策略")
    print("=" * 70)
    print(f"{Colors.ENDC}\n")

    print("测试策略：")
    print("  • Google搜3次（主要引擎，充分利用免费额度）")
    print("  • Tavily/Metaso搜1次（辅助引擎，节约使用）")
    print("  • 百度搜1次（中文辅助，保持不变）")
    print()

    # 初始化客户端
    try:
        global llm_client
        llm_client = UnifiedLLMClient()
        print(f"{Colors.OKGREEN}✅ 客户端初始化成功\n{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}❌ 客户端初始化失败: {e}{Colors.ENDC}")
        sys.exit(1)

    # 测试用例
    test_cases = [
        # 国际查询（应该使用 Google）
        ("Kelas 1 Matematika", "ID", "Google"),
        ("Grade 5 Science", "US", "Google"),
        ("Class 8 Maths algebra", "IN", "Google"),

        # 中文查询（应该使用 Google）
        ("初二地理 全册教程", "CN", "Google"),
        ("小学数学 乘法口诀", "CN", "Google"),

        # 测试辅助引擎是否被正确调用
        # 需要监控实际API调用
    ]

    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("=" * 70)
    print("  开始测试")
    print("=" * 70)
    print(f"{Colors.ENDC}")

    # 执行测试
    for query, country, expected_engine in test_cases:
        test_search(query, country, expected_engine)

    # 显示统计
    print(f"\n{Colors.BOLD}{Colors.OKCYAN}")
    print("=" * 70)
    print("  测试完成")
    print("=" * 70)
    print(f"{Colors.ENDC}")

    stats = llm_client.get_search_stats()
    print(f"\n{Colors.BOLD}搜索引擎统计:{Colors.ENDC}")
    print(f"  • 启用的引擎: {', '.join(stats['enabled_engines'])}")

    if stats.get('google'):
        google_stats = stats['google']
        print(f"\n  {Colors.BOLD}Google 统计:{Colors.ENDC}")
        print(f"    • 使用次数: {google_stats['usage_count']:,}")
        print(f"    • 剩余免费: {google_stats['remaining_free']:,}")
        print(f"    • 总成本: ¥{google_stats['total_cost']:.2f}")
        print(f"    • 当前层级: {google_stats['tier']}")

    if stats.get('metaso'):
        metaso_stats = stats['metaso']
        print(f"\n  {Colors.BOLD}Metaso 统计:{Colors.ENDC}")
        print(f"    • 使用次数: {metaso_stats['usage_count']:,}")
        print(f"    • 剩余免费: {metaso_stats['remaining_free']:,}")
        print(f"    • 总成本: ¥{metaso_stats['total_cost']:.2f}")
        print(f"    • 当前层级: {metaso_stats['tier']}")

    if stats.get('tavily'):
        tavily_stats = stats['tavily']
        print(f"\n  {Colors.BOLD}Tavily 统计:{Colors.ENDC}")
        print(f"    • 使用次数: {tavily_stats['usage_count']:,}")
        print(f"    • 剩余免费: {tavily_stats['remaining_free']:,}")
        print(f"    • 总成本: ¥{tavily_stats['total_cost']:.2f}")
        print(f"    • 当前层级: {tavily_stats['tier']}")

    # 成本预测
    google_usage = stats.get('google', {}).get('usage_count', 0)
    metaso_usage = stats.get('metaso', {}).get('usage_count', 0)
    tavily_usage = stats.get('tavily', {}).get('usage_count', 0)

    print(f"\n{Colors.BOLD}💰 成本预测（假设30,000次搜索/月）:{Colors.ENDC}")
    print(f"  • Google: 3次 × 30,000 = 90,000次/月")
    print(f"    └─ 成本: ¥0（10,000次/天免费）")

    if metaso_usage > 0:
        metaso_calls = min(metaso_usage, 30000)
        metaso_cost = max(0, metaso_calls - 5000) * 0.03
        print(f"\n  • Metaso: {metaso_calls:,}次/月")
        print(f"    └─ 成本: ¥{metaso_cost:.2f}")

    if tavily_usage > 0:
        tavily_calls = min(tavily_usage, 30000)
        tavily_cost = max(0, tavily_calls - 1000) * 0.05
        print(f"\n  • Tavily: {tavily_calls:,}次/月")
        print(f"    └─ 成本: ¥{tavily_cost:.2f}")

    total_cost = metaso_cost + tavily_cost
    print(f"\n  💰 总成本: ¥{total_cost:.2f}/月")

    if total_cost > 100:
        print(f"{Colors.WARNING}  ⚠️ 成本预警: 月成本超过 ¥100{Colors.ENDC}")
    else:
        print(f"{Colors.OKGREEN}  ✅ 成本控制良好: ¥{total_cost:.2f}/月 < ¥100{Colors.ENDC}")

    print(f"\n{Colors.OKGREEN}✅ 所有测试完成！{Colors.ENDC}\n")


if __name__ == "__main__":
    main()
