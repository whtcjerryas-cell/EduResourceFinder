#!/usr/bin/env python3
"""
搜索性能测试脚本
对比串行搜索和并行搜索的性能差异
"""

import os
import time
from search_engine_v2 import SearchEngineV2, SearchRequest

def test_performance():
    """性能测试主函数"""

    print("=" * 80)
    print("🔍 搜索性能测试")
    print("=" * 80)

    # 创建搜索引擎实例
    engine = SearchEngineV2()

    # 测试搜索请求
    test_request = SearchRequest(
        country="ID",
        grade="Kelas 5",
        semester="1",
        subject="Matematika"
    )

    print(f"\n📋 测试配置:")
    print(f"  国家: {test_request.country}")
    print(f"  年级: {test_request.grade}")
    print(f"  学期: {test_request.semester}")
    print(f"  学科: {test_request.subject}")
    print(f"  查询: Matematika Kelas 5")

    # 测试1: 并行搜索
    print(f"\n{'='*80}")
    print(f"测试 1: 并行搜索模式")
    print(f"{'='*80}")
    os.environ["ENABLE_PARALLEL_SEARCH"] = "true"

    start_time = time.time()
    response_parallel = engine.search(test_request)
    parallel_time = time.time() - start_time

    print(f"\n⚡ 并行搜索结果:")
    print(f"  成功: {response_parallel.success}")
    print(f"  总耗时: {parallel_time:.2f} 秒")
    print(f"  结果数: {response_parallel.total_count}")
    print(f"  播放列表: {response_parallel.playlist_count}")
    print(f"  视频: {response_parallel.video_count}")

    # 测试2: 串行搜索（回退）
    print(f"\n{'='*80}")
    print(f"测试 2: 串行搜索模式（回退）")
    print(f"{'='*80}")
    os.environ["ENABLE_PARALLEL_SEARCH"] = "false"

    start_time = time.time()
    response_serial = engine.search(test_request)
    serial_time = time.time() - start_time

    print(f"\n🔄 串行搜索结果:")
    print(f"  成功: {response_serial.success}")
    print(f"  总耗时: {serial_time:.2f} 秒")
    print(f"  结果数: {response_serial.total_count}")
    print(f"  播放列表: {response_serial.playlist_count}")
    print(f"  视频: {response_serial.video_count}")

    # 性能对比
    print(f"\n{'='*80}")
    print(f"📊 性能对比")
    print(f"{'='*80}")

    if serial_time > 0:
        speedup = serial_time / parallel_time
        improvement = ((serial_time - parallel_time) / serial_time) * 100

        print(f"\n⚡ 性能提升:")
        print(f"  串行模式耗时: {serial_time:.2f} 秒")
        print(f"  并行模式耗时: {parallel_time:.2f} 秒")
        print(f"  加速比: {speedup:.2f}x")
        print(f"  性能提升: {improvement:.1f}%")

        if speedup > 1.5:
            print(f"  ✅ 性能提升显著！")
        elif speedup > 1.2:
            print(f"  ✅ 性能有所提升")
        else:
            print(f"  ℹ️  性能提升不明显（可能是网络限制）")
    else:
        print(f"\n⚠️ 无法计算性能提升（串行模式耗时为0）")

    # 缓存统计
    print(f"\n{'='*80}")
    print(f"💾 缓存统计")
    print(f"{'='*80}")
    cache_stats = engine.search_cache.get_stats()
    print(f"\n📊 缓存效果:")
    print(f"  总查询次数: {cache_stats['total_queries']}")
    print(f"  缓存命中: {cache_stats['hits']}")
    print(f"  缓存未命中: {cache_stats['misses']}")
    print(f"  命中率: {cache_stats['hit_rate']:.1%}")
    print(f"  缓存文件数: {cache_stats['cache_files_count']}")

    # 结果对比
    print(f"\n{'='*80}")
    print(f"📋 结果对比")
    print(f"{'='*80}")
    print(f"\n🔍 结果质量:")
    print(f"  并行模式结果数: {response_parallel.total_count}")
    print(f"  串行模式结果数: {response_serial.total_count}")
    print(f"  结果数差异: {response_parallel.total_count - response_serial.total_count}")

    if abs(response_parallel.total_count - response_serial.total_count) <= 2:
        print(f"  ✅ 结果数量一致")
    else:
        print(f"  ⚠️  结果数量不一致（可能是搜索引擎的随机性）")

    # 总结
    print(f"\n{'='*80}")
    print(f"✅ 测试完成")
    print(f"{'='*80}")

    if speedup > 1.5:
        print(f"\n🎉 结论: 并行搜索带来了显著的性能提升！")
    elif speedup > 1.2:
        print(f"\n✅ 结论: 并行搜索带来了性能提升。")
    else:
        print(f"\nℹ️  结论: 性能提升不明显，可能需要进一步优化。")

    print(f"\n💡 建议:")
    print(f"  1. 在生产环境中启用并行搜索")
    print(f"  2. 监控缓存命中率，优化TTL设置")
    print(f"  3. 根据实际网络情况调整并发数量")

if __name__ == "__main__":
    try:
        test_performance()
    except KeyboardInterrupt:
        print(f"\n\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
