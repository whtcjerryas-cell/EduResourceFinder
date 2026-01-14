#!/usr/bin/env python3
"""
测试搜索功能的安全性
验证视觉评估不会导致崩溃
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_search_without_crash():
    """测试搜索功能不会崩溃"""
    try:
        print("=" * 60)
        print("测试搜索功能（防止崩溃）")
        print("=" * 60)

        # 1. 测试模块导入
        print("\n[1/4] 测试模块导入...")
        from search_engine_v2 import SearchEngineV2, SearchRequest
        print("✅ search_engine_v2 导入成功")

        # 2. 测试搜索引擎初始化
        print("\n[2/4] 测试搜索引擎初始化...")
        engine = SearchEngineV2()
        print("✅ 搜索引擎初始化成功")

        # 3. 创建小规模测试请求（只搜索少量结果，避免耗时太长）
        print("\n[3/4] 创建测试搜索请求...")
        request = SearchRequest(
            country="IQ",  # 伊拉克
            grade="الصف الأول",  # 1年级
            subject="الرياضيات"  # 数学
        )
        print(f"✅ 搜索请求创建成功: {request.country} - {request.grade} - {request.subject}")

        # 4. 执行搜索（这是关键测试）
        print("\n[4/4] 执行搜索（这可能需要30-60秒）...")
        print("   提示: 如果超过2分钟没响应，请按Ctrl+C中断")

        import time
        start_time = time.time()

        response = engine.search(request)

        elapsed_time = time.time() - start_time

        print(f"\n✅ 搜索完成！")
        print(f"   耗时: {elapsed_time:.1f}秒")
        print(f"   总结果数: {response.total_count}")
        print(f"   播放列表数: {response.playlist_count}")
        print(f"   视频数: {response.video_count}")

        # 检查评估方法
        if response.results:
            print(f"\n   前5个结果的评估方法:")
            for i, result in enumerate(response.results[:5], 1):
                method = getattr(result, 'evaluation_method', 'Unknown')
                score = getattr(result, 'score', 0)
                title = result.title[:40] if result.title else 'N/A'
                print(f"      {i}. [{method}] {score:.1f}/10 - {title}...")

        print("\n" + "=" * 60)
        print("✅ 测试通过！搜索功能正常运行，没有崩溃")
        print("=" * 60)
        return True

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断测试")
        return False
    except Exception as e:
        print(f"\n\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_search_without_crash()
    sys.exit(0 if success else 1)
