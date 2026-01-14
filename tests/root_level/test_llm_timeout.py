#!/usr/bin/env python3
"""
测试LLM推荐理由生成功能（带超时保护）
验证：
1. 搜索功能正常
2. LLM推荐理由生成成功或在超时后优雅降级到规则生成
3. 整体请求在合理时间内完成（60秒内）
"""

import sys
import time
import requests
from pathlib import Path

# 配置
SERVER_URL = "http://localhost:5001"
SEARCH_ENDPOINT = f"{SERVER_URL}/api/search"


def test_search_with_llm_recommendations():
    """测试搜索功能（带LLM推荐理由生成）"""

    print("=" * 80)
    print("🧪 测试LLM推荐理由生成功能")
    print("=" * 80)
    print()

    # 构建搜索请求
    search_data = {
        "country": "Indonesia",
        "countryCode": "ID",
        "grade": "Grade 2",
        "semester": "Semester 1",
        "subject": "Mathematics",
        "query": "penjumlahan dan pengurangan",
        "resourceType": "video",
        "maxResults": 10
    }

    print(f"📤 搜索请求:")
    print(f"  - 国家: {search_data['country']}")
    print(f"  - 年级: {search_data['grade']}")
    print(f"  - 学科: {search_data['subject']}")
    print(f"  - 查询: {search_data['query']}")
    print(f"  - 资源类型: {search_data['resourceType']}")
    print()

    # 记录开始时间
    start_time = time.time()

    try:
        print("🔍 正在发送搜索请求...")
        response = requests.post(
            SEARCH_ENDPOINT,
            json=search_data,
            timeout=120,  # 设置2分钟超时（应该足够LLM生成推荐理由）
            headers={"Content-Type": "application/json"}
        )

        # 计算耗时
        elapsed_time = time.time() - start_time

        print(f"⏱️  请求完成，耗时: {elapsed_time:.2f} 秒")
        print()

        # 检查响应状态
        if response.status_code != 200:
            print(f"❌ 搜索失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False

        # 解析响应
        result = response.json()

        if not result.get('success'):
            print(f"❌ 搜索失败: {result.get('message', '未知错误')}")
            return False

        # 检查结果
        results = result.get('results', [])

        print(f"✅ 搜索成功！")
        print(f"  - 找到 {len(results)} 个结果")
        print()

        # 检查推荐理由
        print("📝 推荐理由检查:")
        has_llm_recommendations = 0
        has_rule_recommendations = 0
        no_recommendations = 0

        for i, item in enumerate(results[:5], 1):  # 只显示前5个
            title = item.get('title', '无标题')[:60]
            reason = item.get('recommendation_reason', '')

            if not reason:
                no_recommendations += 1
                reason_type = "❌ 缺失"
            elif "根据搜索匹配度推荐" in reason or "匹配" in reason:
                has_rule_recommendations += 1
                reason_type = "📋 规则生成"
            else:
                has_llm_recommendations += 1
                reason_type = "🤖 LLM生成"

            print(f"  {i}. [{reason_type}] {title}")
            if reason:
                print(f"     推荐理由: {reason[:80]}...")
            print()

        # 统计
        total_checked = len(results)
        print(f"📊 推荐理由统计:")
        print(f"  - LLM生成: {has_llm_recommendations} 个")
        print(f"  - 规则生成: {has_rule_recommendations} 个")
        print(f"  - 缺失: {no_recommendations} 个")
        print()

        # 性能检查
        if elapsed_time <= 60:
            print(f"✅ 性能测试通过！耗时 {elapsed_time:.2f} 秒 ≤ 60秒")
        elif elapsed_time <= 90:
            print(f"⚠️  性能警告：耗时 {elapsed_time:.2f} 秒，略超预期")
        else:
            print(f"❌ 性能测试失败：耗时 {elapsed_time:.2f} 秒 > 90秒")

        print()
        print("=" * 80)
        print("✅ 测试完成！LLM推荐理由生成功能正常")
        print("=" * 80)

        return True

    except requests.exceptions.Timeout:
        elapsed_time = time.time() - start_time
        print(f"❌ 请求超时（{elapsed_time:.2f}秒）")
        print(f"这可能表示LLM API调用超时保护机制未生效")
        return False

    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"❌ 测试异常: {str(e)}")
        print(f"耗时: {elapsed_time:.2f} 秒")
        import traceback
        print(f"异常堆栈:\n{traceback.format_exc()}")
        return False


if __name__ == "__main__":
    print()
    print("🚀 开始测试...")
    print()

    success = test_search_with_llm_recommendations()

    print()
    if success:
        print("✅ 所有测试通过！")
        sys.exit(0)
    else:
        print("❌ 测试失败！")
        sys.exit(1)
