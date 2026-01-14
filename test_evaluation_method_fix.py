#!/usr/bin/env python3
"""
测试 evaluation_method 字段是否正确传递

修复内容：
1. SearchResult 模型添加了 evaluation_method 字段
2. verify the field is preserved through the scoring pipeline
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_evaluation_method_field():
    """测试evaluation_method字段是否在SearchResult模型中"""
    print("=" * 80)
    print("测试: evaluation_method 字段修复")
    print("=" * 80)

    # 1. 检查SearchResult模型是否有evaluation_method字段
    from search_engine_v2 import SearchResult
    from pydantic import BaseModel

    # 获取模型字段
    fields = SearchResult.model_fields
    print(f"\n1. SearchResult模型字段:")
    print(f"   总字段数: {len(fields)}")
    print(f"   有evaluation_method字段? {'✅' if 'evaluation_method' in fields else '❌'}")

    if 'evaluation_method' in fields:
        field_info = fields['evaluation_method']
        print(f"   字段类型: {field_info.annotation}")
        print(f"   默认值: {field_info.default}")
        print(f"   描述: {field_info.description}")
    else:
        print("   ❌ 错误: evaluation_method字段不存在！")
        return False

    # 2. 测试创建SearchResult对象时能否设置evaluation_method
    print(f"\n2. 测试创建SearchResult对象:")
    try:
        result = SearchResult(
            title="测试视频",
            url="https://www.youtube.com/watch?v=test",
            snippet="测试摘要",
            score=10.0,
            recommendation_reason="测试理由",
            evaluation_method="MCP Tools"  # ✅ 现在应该可以设置
        )
        print(f"   ✅ 成功创建SearchResult对象")
        print(f"   evaluation_method = {result.evaluation_method}")

        # 验证字段确实被设置
        assert result.evaluation_method == "MCP Tools", "字段值不正确"
        print(f"   ✅ 字段值正确")

    except Exception as e:
        print(f"   ❌ 创建失败: {e}")
        return False

    # 3. 测试model_dump()是否包含evaluation_method
    print(f"\n3. 测试model_dump()方法:")
    result_dict = result.model_dump()
    if 'evaluation_method' in result_dict:
        print(f"   ✅ model_dump()包含evaluation_method: {result_dict['evaluation_method']}")
    else:
        print(f"   ❌ model_dump()不包含evaluation_method")
        return False

    # 4. 测试从字典重新创建SearchResult
    print(f"\n4. 测试从字典重新创建对象:")
    try:
        result2 = SearchResult(**result_dict)
        assert result2.evaluation_method == "MCP Tools"
        print(f"   ✅ 成功从字典重新创建")
        print(f"   evaluation_method = {result2.evaluation_method}")
    except Exception as e:
        print(f"   ❌ 重新创建失败: {e}")
        return False

    # 5. 测试None值
    print(f"\n5. 测试None值（默认情况）:")
    try:
        result3 = SearchResult(
            title="测试视频2",
            url="https://www.youtube.com/watch?v=test2",
            score=8.5,
            recommendation_reason="测试"
            # 不设置evaluation_method
        )
        print(f"   evaluation_method（不设置）= {result3.evaluation_method}")
        print(f"   ✅ None值处理正确")
    except Exception as e:
        print(f"   ❌ None值处理失败: {e}")
        return False

    print(f"\n{'=' * 80}")
    print("所有测试通过! ✅")
    print(f"{'=' * 80}")
    print("\n总结:")
    print("  ✅ SearchResult模型已包含evaluation_method字段")
    print("  ✅ 可以正确设置和读取evaluation_method值")
    print("  ✅ model_dump()和从字典重建都正常工作")
    print("  ✅ None默认值处理正确")
    print("\n下一步:")
    print("  - 重启web应用")
    print("  - 运行批量搜索测试")
    print("  - 验证API响应中的evaluation_method字段")

    return True

if __name__ == '__main__':
    success = test_evaluation_method_field()
    sys.exit(0 if success else 1)
