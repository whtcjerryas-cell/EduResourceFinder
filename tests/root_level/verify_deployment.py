#!/usr/bin/env python3
"""
部署验证脚本
确认新代码已经加载到运行环境
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def verify_arabic_normalizer():
    """验证阿拉伯语标准化模块"""
    print("\n" + "="*80)
    print("✅ 验证1: 阿拉伯语标准化模块")
    print("="*80)

    try:
        from core.arabic_normalizer import ArabicNormalizer
        print("✅ ArabicNormalizer 导入成功")

        # 测试基本功能
        grade_info = ArabicNormalizer.extract_grade("شرح رياضيات صف سادس")
        print(f"✅ 提取年级: {grade_info['grade']}（六年级）")

        if grade_info['grade'] == '六年级':
            print("✅ 功能正常")
            return True
        else:
            print("❌ 功能异常")
            return False
    except Exception as e:
        print(f"❌ 导入失败: {str(e)}")
        return False


def verify_rule_validation():
    """验证规则验证功能"""
    print("\n" + "="*80)
    print("✅ 验证2: 规则验证功能")
    print("="*80)

    try:
        from core.result_scorer import IntelligentResultScorer
        print("✅ IntelligentResultScorer 导入成功")

        # 检查是否有_validate_with_rules方法
        if hasattr(IntelligentResultScorer, '_validate_with_rules'):
            print("✅ _validate_with_rules 方法存在")

            # 创建实例并测试
            scorer = IntelligentResultScorer()
            result = {"title": "شرح رياضيات صف سادس"}
            metadata = {"grade": "一年级", "subject": "数学"}

            validation = scorer._validate_with_rules(result, metadata)

            if validation and validation.get('score') == 3.0:
                print(f"✅ 规则验证生效: 六年级给低分 {validation['score']}")
                return True
            else:
                print(f"⚠️ 规则验证未按预期工作")
                return False
        else:
            print("❌ _validate_with_rules 方法不存在")
            return False
    except Exception as e:
        print(f"❌ 验证失败: {str(e)}")
        return False


def verify_prompt_optimization():
    """验证Prompt优化"""
    print("\n" + "="*80)
    print("✅ 验证3: Prompt优化")
    print("="*80)

    try:
        # 读取result_scorer.py文件
        with open('core/result_scorer.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查关键字符串
        checks = [
            ("年级匹配度（0-3分）【最关键】", "年级匹配强调"),
            ("الصف الأول = الاول = صف اول = 一年级", "阿拉伯语示例"),
            ("六年级被识别为一年级 → 错误！应该给≤3分", "常见错误警告"),
        ]

        all_passed = True
        for check_str, description in checks:
            if check_str in content:
                print(f"✅ {description}: 已添加")
            else:
                print(f"❌ {description}: 未找到")
                all_passed = False

        return all_passed
    except Exception as e:
        print(f"❌ 验证失败: {str(e)}")
        return False


def main():
    """主验证函数"""
    print("\n" + "="*80)
    print("🔍 部署验证")
    print("="*80)

    results = []
    results.append(("阿拉伯语标准化模块", verify_arabic_normalizer()))
    results.append(("规则验证功能", verify_rule_validation()))
    results.append(("Prompt优化", verify_prompt_optimization()))

    # 汇总结果
    print("\n" + "="*80)
    print("📊 验证结果汇总")
    print("="*80)

    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")

    all_passed = all(passed for _, passed in results)

    print("\n" + "="*80)
    if all_passed:
        print("🎉 所有验证通过！新代码已成功部署。")
        print("\n✅ 可以开始测试搜索功能了")
        print("\n建议测试用例:")
        print("  1. 伊拉克 一年级 数学")
        print("  2. 伊拉克 三年级 科学")
        print("  3. 中国 五年级 数学")
    else:
        print("⚠️ 部分验证失败，请检查部署。")
    print("="*80)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
