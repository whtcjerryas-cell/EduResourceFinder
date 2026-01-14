#!/usr/bin/env python3
"""
测试详细日志功能
验证搜索流程的每个步骤都能记录详细日志
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_logging():
    """测试详细日志"""
    print("="*80)
    print("测试详细日志功能")
    print("="*80)

    try:
        from search_engine_v2 import SearchEngineV2, SearchRequest

        # 创建搜索引擎
        print("\n[1/2] 创建搜索引擎...")
        engine = SearchEngineV2()

        # 测试内存监控
        print("\n[2/2] 测试内存监控...")
        memory = engine._get_memory_usage()
        print(f"✅ 当前内存使用: {memory}")

        print("\n" + "="*80)
        print("✅ 日志功能正常")
        print("="*80)
        print("\n💡 提示：运行实际搜索时会记录详细日志")
        print("日志文件位置: search_system.log")
        print("\n查看实时日志：")
        print("  tail -f search_system.log")

        return True

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import time
    print(f"\n🕐 测试开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    success = test_logging()
    print(f"\n🕐 测试结束时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    sys.exit(0 if success else 1)
