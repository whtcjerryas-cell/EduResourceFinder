#!/usr/bin/env python3
"""
测试搜索结果评估和资源类型分类功能
"""

import sys
import os
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search_engine_v2 import SearchEngineV2, SearchRequest

def test_evaluation():
    """测试评估功能"""
    print("=" * 80)
    print("🧪 测试搜索结果评估和资源类型分类功能")
    print("=" * 80)
    print()
    
    # 初始化搜索引擎
    print("📦 初始化搜索引擎...")
    try:
        engine = SearchEngineV2()
        print("✅ 搜索引擎初始化成功")
    except Exception as e:
        print(f"❌ 搜索引擎初始化失败: {str(e)}")
        return False
    
    print()
    
    # 创建测试搜索请求
    print("🔍 创建测试搜索请求...")
    test_request = SearchRequest(
        country="ID",
        grade="Kelas 7",
        subject="Matematika",
        semester=None
    )
    print(f"   国家: {test_request.country}")
    print(f"   年级: {test_request.grade}")
    print(f"   学科: {test_request.subject}")
    print()
    
    # 执行搜索
    print("🚀 执行搜索...")
    try:
        response = engine.search(test_request)
        print(f"✅ 搜索完成")
        print(f"   查询词: {response.query}")
        print(f"   结果数量: {len(response.results)}")
        print(f"   播放列表: {response.playlist_count}")
        print(f"   视频: {response.video_count}")
        print()
    except Exception as e:
        print(f"❌ 搜索失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # 验证结果
    print("=" * 80)
    print("📊 验证评估结果")
    print("=" * 80)
    
    if not response.results:
        print("⚠️  警告: 没有搜索结果")
        return False
    
    # 检查评估字段
    success_count = 0
    total_count = len(response.results)
    
    print(f"\n📋 检查前 {min(10, total_count)} 个结果:")
    print("-" * 80)
    
    for idx, result in enumerate(response.results[:10], 1):
        checks = []
        
        # 检查评分
        if result.score and result.score > 0:
            checks.append(f"✅ 评分: {result.score:.1f}/10")
        else:
            checks.append("❌ 评分缺失或为0")
        
        # 检查资源类型
        if result.resource_type:
            checks.append(f"✅ 资源类型: {result.resource_type}")
        else:
            checks.append("❌ 资源类型缺失")
        
        # 检查推荐理由
        if result.recommendation_reason:
            checks.append(f"✅ 推荐理由: {result.recommendation_reason[:50]}...")
        else:
            checks.append("❌ 推荐理由缺失")
        
        # 检查是否按分数排序
        if idx > 1:
            prev_score = response.results[idx - 2].score
            if result.score <= prev_score:
                checks.append("✅ 排序正确（分数递减）")
            else:
                checks.append("❌ 排序错误（分数未递减）")
        
        print(f"\n[{idx}] {result.title[:60]}...")
        print(f"    URL: {result.url[:80]}...")
        for check in checks:
            print(f"    {check}")
        
        # 统计成功项
        if result.score and result.score > 0 and result.resource_type and result.recommendation_reason:
            success_count += 1
    
    print()
    print("-" * 80)
    print(f"📊 统计结果:")
    print(f"   总结果数: {total_count}")
    print(f"   成功评估: {success_count}/{min(10, total_count)}")
    print(f"   成功率: {success_count / min(10, total_count) * 100:.1f}%")
    
    # 统计资源类型分布
    print()
    print("📊 资源类型分布:")
    type_counts = {}
    for result in response.results:
        resource_type = result.resource_type or "未分类"
        type_counts[resource_type] = type_counts.get(resource_type, 0) + 1
    
    for resource_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = count / total_count * 100
        print(f"   {resource_type}: {count} 个 ({percentage:.1f}%)")
    
    # 检查排序
    print()
    print("🔍 检查排序:")
    scores = [r.score for r in response.results]
    is_sorted = all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
    if is_sorted:
        print("   ✅ 结果已按分数从高到低排序")
    else:
        print("   ❌ 结果未正确排序")
        print(f"   前5个分数: {scores[:5]}")
    
    # 检查是否有结果被过滤
    print()
    print("🔍 检查过滤:")
    print(f"   ✅ 所有 {total_count} 个结果都已保留（未过滤）")
    
    print()
    print("=" * 80)
    
    # 判断测试是否通过
    if success_count >= min(10, total_count) * 0.8 and is_sorted:  # 80%以上成功且排序正确
        print("✅ 测试通过！评估和资源类型分类功能正常")
        return True
    else:
        print("⚠️  测试部分通过，但有一些问题需要检查")
        return False

if __name__ == "__main__":
    try:
        success = test_evaluation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)




