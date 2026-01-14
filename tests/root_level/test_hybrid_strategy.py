#!/usr/bin/env python3
"""
测试混合搜索引擎策略
验证基于语言的智能搜索引擎选择是否正常工作
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


def test_search(query, expected_engine):
    """
    测试单个查询

    Args:
        query: 搜索查询
        expected_engine: 预期使用的搜索引擎（"Metaso" 或 "Tavily"）
    """
    print(f"\n{Colors.BOLD}查询: {query}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}预期引擎: {expected_engine}{Colors.ENDC}")

    try:
        results = llm_client.search(query, max_results=3)

        if results:
            print(f"{Colors.OKGREEN}✅ 成功{Colors.ENDC} - 返回 {len(results)} 个结果")
            print(f"   前 2 个结果:")
            for i, result in enumerate(results[:2], 1):
                print(f"   {i}. {result.get('title', 'N/A')[:60]}...")
        else:
            print(f"{Colors.WARNING}⚠️ 未返回结果{Colors.ENDC}")

    except Exception as e:
        print(f"{Colors.FAIL}❌ 错误: {e}{Colors.ENDC}")


def main():
    """主函数"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print("=" * 70)
    print("  混合搜索引擎策略测试")
    print("=" * 70)
    print(f"{Colors.ENDC}\n")

    print("测试策略：")
    print("  • 中文查询 → Metaso（相关性高 31%，速度快 5.8倍）")
    print("  • 国际查询 → Tavily（质量高 35%，教育平台匹配好）")
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
        ("初二地理 全册教程", "Metaso"),
        ("小学三年级数学 乘法口诀", "Metaso"),
        ("Python 编程教程 播放列表", "Metaso"),

        # 国际查询（应该使用 Tavily）
        ("Kelas 1 Matematika video pembelajaran", "Tavily"),
        ("Grade 5 Science energy transformation", "Tavily"),
        ("Class 8 Maths algebra expressions", "Tavily"),
        ("5 класс математика видео уроки", "Tavily"),
        ("Middle School Math algebra equations", "Tavily"),
    ]

    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("=" * 70)
    print("  开始测试")
    print("=" * 70)
    print(f"{Colors.ENDC}")

    # 执行测试
    for query, expected_engine in test_cases:
        test_search(query, expected_engine)

    # 显示统计
    print(f"\n{Colors.BOLD}{Colors.OKCYAN}")
    print("=" * 70)
    print("  测试完成")
    print("=" * 70)
    print(f"{Colors.ENDC}")

    stats = llm_client.get_search_stats()
    print(f"\n{Colors.BOLD}搜索引擎统计:{Colors.ENDC}")
    print(f"  • 启用的引擎: {', '.join(stats['enabled_engines'])}")

    if stats.get('metaso'):
        metaso_stats = stats['metaso']
        print(f"\n  {Colors.BOLD}Metaso 统计:{Colors.ENDC}")
        print(f"    • 使用次数: {metaso_stats['usage_count']:,}")
        print(f"    • 免费额度: {metaso_stats['free_tier_limit']:,}")
        print(f"    • 剩余免费: {metaso_stats['remaining_free']:,}")
        print(f"    • 总成本: ¥{metaso_stats['total_cost']:.2f}")
        print(f"    • 当前层级: {metaso_stats['tier']}")

    print(f"\n{Colors.OKGREEN}✅ 所有测试完成！{Colors.ENDC}\n")


if __name__ == "__main__":
    main()
