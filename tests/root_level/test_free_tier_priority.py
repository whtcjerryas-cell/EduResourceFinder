#!/usr/bin/env python3
"""
测试免费额度优先策略
验证搜索引擎选择是否正确：
- 中文查询 → Metaso > Baidu > Google > Tavily
- 印尼/俄罗斯查询 → Google > Tavily > Metaso
- 美国/印度/菲律宾查询 → Tavily > Google > Metaso
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
            print(f"   前 2 个结果:")
            for i, result in enumerate(results[:2], 1):
                print(f"   {i}. {result.get('title', 'N/A')[:60]}...")

            # 检查是否使用了预期引擎
            if actual_engine == expected_engine:
                print(f"{Colors.OKGREEN}✅ 引擎选择正确{Colors.ENDC}")
            else:
                print(f"{Colors.WARNING}⚠️ 引擎选择与预期不符（预期: {expected_engine}, 实际: {actual_engine}）{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}⚠️ 未返回结果{Colors.ENDC}")

    except Exception as e:
        print(f"{Colors.FAIL}❌ 错误: {e}{Colors.ENDC}")


def test_free_tier_priority():
    """测试免费额度优先策略"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("=" * 70)
    print("  测试 1: 免费额度优先策略")
    print("=" * 70)
    print(f"{Colors.ENDC}\n")

    print("测试策略：")
    print("  • 中文查询 → Metaso（免费额度 5,000 次）")
    print("  • 印尼/俄罗斯 → Google（免费额度 10,000 次/天）")
    print("  • 美国/印度/菲律宾 → Tavily（免费额度 1,000 次/月）")
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
        # 中文查询（应该使用 Metaso）
        ("初二地理 全册教程", "CN", "Metaso"),
        ("小学数学 乘法口诀", "CN", "Metaso"),
        ("Python 编程教程 播放列表", "CN", "Metaso"),

        # 印尼查询（应该使用 Google）
        ("Kelas 1 Matematika", "ID", "Google"),
        ("IPA Kelas 5 video pembelajaran", "ID", "Google"),

        # 俄罗斯查询（应该使用 Google）
        ("5 класс математика", "RU", "Google"),
        ("видео уроки по физике", "RU", "Google"),

        # 美国查询（应该使用 Tavily）
        ("5th grade Math", "US", "Tavily"),
        ("6th grade Science", "US", "Tavily"),

        # 印度查询（应该使用 Tavily）
        ("Grade 5 Science", "IN", "Tavily"),
        ("Class 8 Maths algebra", "IN", "Tavily"),

        # 菲律宾查询（应该使用 Tavily）
        ("Grade 10 Math", "PH", "Tavily"),
    ]

    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("=" * 70)
    print("  开始测试")
    print("=" * 70)
    print(f"{Colors.ENDC}")

    # 执行测试
    for query, country, expected_engine in test_cases:
        test_search(query, country, expected_engine)


def test_cost_monitoring():
    """测试成本监控和预警"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("=" * 70)
    print("  测试 2: 成本监控和预警")
    print("=" * 70)
    print(f"{Colors.ENDC}\n")

    # 检查成本预警
    print("检查成本预警...")
    alert_result = llm_client.check_cost_alert()

    print(f"\n预警数量: {len(alert_result['alerts'])}")
    for i, alert in enumerate(alert_result['alerts'], 1):
        level_color = {
            "CRITICAL": Colors.FAIL,
            "WARNING": Colors.WARNING,
            "INFO": Colors.OKBLUE
        }.get(alert['level'], Colors.ENDC)

        print(f"{i}. [{alert['level']}] {alert['message']}")

    # 打印搜索统计摘要
    print(f"\n打印搜索统计摘要...")
    llm_client.print_search_summary()


def test_cost_simulation():
    """测试成本模拟（模拟 100 次搜索）"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("=" * 70)
    print("  测试 3: 成本模拟（100 次搜索）")
    print("=" * 70)
    print(f"{Colors.ENDC}\n")

    # 记录初始状态
    initial_stats = llm_client.get_search_stats()

    # 模拟 100 次搜索
    queries = [
        ("初二地理", "CN"),
        ("Kelas 1 Matematika", "ID"),
        ("Grade 5 Science", "US"),
        ("5 класс математика", "RU"),
    ] * 25  # 100 次搜索

    print(f"模拟 {len(queries)} 次搜索...")
    for i, (query, country) in enumerate(queries, 1):
        try:
            llm_client.search(query, max_results=1, country_code=country)
            if i % 10 == 0:
                print(f"  进度: {i}/{len(queries)}")
        except Exception as e:
            print(f"  搜索 {i} 失败: {e}")

    # 显示成本
    final_stats = llm_client.get_search_stats()

    print(f"\n{Colors.BOLD}{Colors.OKGREEN}")
    print("=" * 70)
    print("  成本模拟结果")
    print("=" * 70)
    print(f"{Colors.ENDC}")

    if final_stats.get('metaso'):
        metaso = final_stats['metaso']
        print(f"\n  🔍 Metaso: {metaso['usage_count']} 次 = ¥{metaso['total_cost']:.2f}")

    if final_stats.get('tavily'):
        tavily = final_stats['tavily']
        print(f"  🔍 Tavily: {tavily['usage_count']} 次 = ¥{tavily['total_cost']:.2f}")

    if final_stats.get('google'):
        google = final_stats['google']
        print(f"  🔍 Google: {google['usage_count']} 次 = ¥{google['total_cost']:.2f}（免费）")

    if final_stats.get('baidu'):
        baidu = final_stats['baidu']
        print(f"  🔍 Baidu: {baidu['usage_count']} 次 = ¥{baidu['total_cost']:.2f}（免费）")

    # 总成本
    total_cost = sum(s['total_cost'] for s in [
        final_stats.get('metaso'),
        final_stats.get('tavily'),
        final_stats.get('google'),
        final_stats.get('baidu')
    ] if s)

    print(f"\n  💰 总成本: ¥{total_cost:.2f}")
    print(f"  ✅ 预期: ¥0（全部在免费额度内）")


def main():
    """主函数"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print("=" * 70)
    print("  免费额度优先策略测试")
    print("=" * 70)
    print(f"{Colors.ENDC}\n")

    print("测试目标：")
    print("  1. 验证免费额度优先策略是否正确工作")
    print("  2. 验证区域优化是否正确")
    print("  3. 验证成本监控和预警功能")
    print("  4. 模拟成本计算")
    print()

    # 初始化客户端
    try:
        global llm_client
        llm_client = UnifiedLLMClient()
        print(f"{Colors.OKGREEN}✅ 客户端初始化成功\n{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}❌ 客户端初始化失败: {e}{Colors.ENDC}")
        sys.exit(1)

    # 测试 1: 免费额度优先策略
    test_free_tier_priority()

    # 测试 2: 成本监控
    test_cost_monitoring()

    # 测试 3: 成本模拟
    test_cost_simulation()

    # 最终总结
    print(f"\n{Colors.BOLD}{Colors.OKCYAN}")
    print("=" * 70)
    print("  测试完成")
    print("=" * 70)
    print(f"{Colors.ENDC}")

    # 最终统计
    llm_client.print_search_summary()

    print(f"{Colors.OKGREEN}✅ 所有测试完成！{Colors.ENDC}\n")


if __name__ == "__main__":
    main()
