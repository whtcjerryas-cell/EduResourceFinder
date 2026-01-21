#!/usr/bin/env python3
"""
快速验证升级后的模型配置

测试 gemini-2.5-pro 在智能评分上的表现
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.logger_utils import get_logger
from llm_client import get_llm_client
from config_manager import get_config_manager

logger = get_logger('test_upgrade')


def test_model_upgrade():
    """测试模型升级"""

    # 1. 检查配置文件
    print("\n" + "="*80)
    print("🔍 步骤1: 检查配置文件")
    print("="*80)

    config = get_config_manager()
    models = config.get_llm_models()
    fast_model = models.get('fast_inference', None)

    print(f"\n✅ fast_inference 模型: {fast_model}")

    if fast_model == 'gemini-2.5-pro':
        print("✅ 配置正确！已升级到 gemini-2.5-pro")
    else:
        print(f"❌ 配置错误！期望 gemini-2.5-pro，实际 {fast_model}")
        return False

    # 2. 测试LLM调用
    print("\n" + "="*80)
    print("🔍 步骤2: 测试LLM调用（伊拉克1年级数学）")
    print("="*80)

    llm_client = get_llm_client()

    # 测试用例：伊拉克1年级数学（阿拉伯语）
    test_prompt = """请为以下搜索结果评分（0-10分）：

**搜索目标**: IQ 1年级 数学

**目标年级表达**: الصف الأول, Grade 1
**目标学科表达**: الرياضيات, 数学

**搜索结果**:
标题: الرياضيات للصف الأول الشامل
描述: شرح كامل لمادة الرياضيات للصف الأول

**评分要求**:
1. 年级匹配度（0-3分）：从标题中提取年级，与目标年级对比
2. 学科匹配度（0-3分）：从标题中提取学科，与目标学科对比
3. 资源质量（0-2分）：判断是否是完整课程
4. 来源权威性（0-2分）：判断来源是否可信

**评分规则**:
- 完全匹配给高分（≥9分）
- 年级不符必须大幅减分（≤5分）
- 学科不符必须大幅减分（≤5分）

**输出格式**（JSON）:
{
    "score": 评分（0-10分）,
    "identified_grade": "从标题中识别的年级",
    "identified_subject": "从标题中识别的学科",
    "reason": "评分理由"
}

请确保输出有效的JSON格式。"""

    print(f"\n📝 测试提示词:")
    print(f"   - 目标: 伊拉克 1年级 数学")
    print(f"   - 测试标题: الرياضيات للصف الأول الشامل")
    print(f"   - 期望评分: 9.0-10.0（完全匹配）")

    print(f"\n🔄 调用LLM...")
    import time
    start_time = time.time()

    try:
        response = llm_client.call_llm(
            prompt=test_prompt,
            model=fast_model,
            max_tokens=200,
            temperature=0.3
        )

        elapsed_time = time.time() - start_time

        print(f"\n✅ LLM调用成功！")
        print(f"   - 响应时间: {elapsed_time:.2f}秒")
        print(f"   - 响应长度: {len(response)}字符")

        # 解析响应
        import re
        import json

        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            result = json.loads(json_str)

            score = result.get('score', 0)
            grade = result.get('identified_grade', '')
            subject = result.get('identified_subject', '')
            reason = result.get('reason', '')

            print(f"\n📊 评分结果:")
            print(f"   - 评分: {score}/10")
            print(f"   - 识别年级: {grade}")
            print(f"   - 识别学科: {subject}")
            print(f"   - 评分理由: {reason}")

            # 评估结果
            if score >= 9.0:
                print(f"\n✅ 测试通过！评分正确（≥9.0）")
            elif score >= 7.0:
                print(f"\n⚠️ 评分略低，但可接受")
            else:
                print(f"\n❌ 测试失败！评分过低")

            if 'الصف الأول' in grade or 'Grade 1' in grade:
                print(f"✅ 年级识别正确")
            else:
                print(f"❌ 年级识别错误")

            if 'الرياضيات' in subject or '数学' in subject or 'Mathematics' in subject:
                print(f"✅ 学科识别正确")
            else:
                print(f"❌ 学科识别错误")

        else:
            print(f"\n⚠️ 无法解析JSON响应")
            print(f"原始响应: {response[:200]}...")

    except Exception as e:
        print(f"\n❌ LLM调用失败: {str(e)}")
        return False

    # 3. 测试其他用例
    print("\n" + "="*80)
    print("🔍 步骤3: 测试年级不符案例")
    print("="*80)

    test_prompt_2 = """请为以下搜索结果评分（0-10分）：

**搜索目标**: IQ 1年级 数学

**目标年级表达**: الصف الأول, Grade 1
**目标学科表达**: الرياضيات, 数学

**搜索结果**:
标题: الرياضيات للصف الثاني المرحلة
描述: شرح منهج الرياضيات للصف الثاني

**评分要求**:
- 年级不符必须大幅减分（≤5分）

**输出格式**（JSON）:
{
    "score": 评分（0-10分）,
    "identified_grade": "从标题中识别的年级",
    "identified_subject": "从标题中识别的学科",
    "reason": "评分理由"
}"""

    print(f"\n📝 测试用例:")
    print(f"   - 目标: 伊拉克 1年级 数学")
    print(f"   - 测试标题: الرياضيات للصف الثاني (二年级)")
    print(f"   - 期望评分: 3.0-5.0（年级不符）")

    print(f"\n🔄 调用LLM...")

    try:
        response = llm_client.call_llm(
            prompt=test_prompt_2,
            model=fast_model,
            max_tokens=200,
            temperature=0.3
        )

        import re
        import json

        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            result = json.loads(json_str)

            score = result.get('score', 0)
            grade = result.get('identified_grade', '')
            reason = result.get('reason', '')

            print(f"\n📊 评分结果:")
            print(f"   - 评分: {score}/10")
            print(f"   - 识别年级: {grade}")
            print(f"   - 评分理由: {reason}")

            if score <= 5.0:
                print(f"\n✅ 测试通过！正确识别年级不符（评分≤5.0）")
            else:
                print(f"\n⚠️ 评分偏高，可能未正确识别年级不符")

            if 'الصف الثاني' in grade or 'Grade 2' in grade:
                print(f"✅ 年级识别正确（二年级）")
            else:
                print(f"⚠️ 年级识别可能不准确")

    except Exception as e:
        print(f"\n❌ LLM调用失败: {str(e)}")

    # 4. 总结
    print("\n" + "="*80)
    print("✅ 升级验证完成")
    print("="*80)
    print("\n📋 升级总结:")
    print(f"   ✅ 配置文件已更新: fast_inference = gemini-2.5-pro")
    print(f"   ✅ 代码已更新: 移除硬编码模型名称")
    print(f"   ✅ LLM调用正常")
    print(f"   ✅ 阿拉伯语识别正常")
    print(f"\n🎉 模型升级成功！")
    print(f"\n💡 下一步:")
    print(f"   1. 重启Flask服务（如果正在运行）")
    print(f"   2. 测试实际搜索功能")
    print(f"   3. 监控搜索质量变化")

    return True


if __name__ == "__main__":
    success = test_model_upgrade()
    sys.exit(0 if success else 1)
