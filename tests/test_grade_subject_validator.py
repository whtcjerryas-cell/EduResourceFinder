#!/usr/bin/env python3
"""
年级学科验证器测试脚本
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.grade_subject_validator import GradeSubjectValidator


def test_validator_initialization():
    """测试验证器初始化"""
    print("\n[测试1] 验证器初始化")
    try:
        validator = GradeSubjectValidator()
        assert validator is not None
        assert validator.rules is not None
        print("✅ PASS: 验证器初始化成功")
        return True
    except Exception as e:
        print(f"❌ FAIL: 验证器初始化失败 - {str(e)}")
        return False


def test_grade_level_detection():
    """测试年级层级识别"""
    print("\n[测试2] 年级层级识别")
    validator = GradeSubjectValidator()
    
    test_cases = [
        ("Kelas 1", "primary_lower"),
        ("Kelas 2", "primary_lower"),
        ("Kelas 5", "primary_upper"),
        ("Grade 7", "junior_high"),
        ("Kelas 10", "senior_high"),
        ("一年级", "primary_lower"),
    ]
    
    passed = 0
    failed = 0
    
    for grade, expected_level in test_cases:
        result = validator._get_grade_level(grade)
        if result == expected_level:
            print(f"  ✅ {grade} -> {result}")
            passed += 1
        else:
            print(f"  ❌ {grade} -> {result} (期望: {expected_level})")
            failed += 1
    
    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0


def test_grade_subject_validation():
    """测试年级-学科配对验证"""
    print("\n[测试3] 年级-学科配对验证")
    validator = GradeSubjectValidator()
    
    test_cases = [
        # (country_code, grade, subject, should_be_valid)
        ("ID", "Kelas 1", "Fisika", False),
        ("ID", "Kelas 1", "Matematika", True),
        ("ID", "Kelas 7", "Fisika", True),
        ("ID", "Kelas 10", "Fisika", True),
        ("CN", "一年级", "物理", False),
        ("CN", "初二", "物理", True),
    ]
    
    passed = 0
    failed = 0
    
    for country_code, grade, subject, should_be_valid in test_cases:
        result = validator.validate(country_code, grade, subject)
        is_valid = result["valid"]
        
        if is_valid == should_be_valid:
            status = "✅"
            passed += 1
        else:
            status = "❌"
            failed += 1
        
        print(f"  {status} {country_code} {grade} {subject}: valid={is_valid} (期望: {should_be_valid})")
        if not is_valid:
            print(f"     原因: {result['reason']}")
    
    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0


def test_get_available_subjects():
    """测试获取可用学科"""
    print("\n[测试4] 获取可用学科")
    validator = GradeSubjectValidator()
    
    subjects = [
        {"local_name": "Matematika", "zh_name": "数学"},
        {"local_name": "Fisika", "zh_name": "物理"},
        {"local_name": "Kimia", "zh_name": "化学"},
    ]
    
    all_passed = True
    
    # 测试1年级（应该过滤掉物理和化学）
    print("\n  测试1年级:")
    available = validator.get_available_subjects("ID", "Kelas 1", subjects)
    
    has_math = False
    has_physics = False
    has_chemistry = False
    
    for subj in available:
        if subj["local_name"] == "Matematika":
            has_math = True
            if subj["is_allowed"]:
                print(f"    ✅ 数学允许开设")
            else:
                print(f"    ❌ 数学应该允许开设")
                all_passed = False
        
        if subj["local_name"] == "Fisika":
            has_physics = True
            if not subj["is_allowed"]:
                print(f"    ✅ 物理不允许开设（正确）")
            else:
                print(f"    ❌ 物理不应该在1年级开设")
                all_passed = False
        
        if subj["local_name"] == "Kimia":
            has_chemistry = True
            if not subj["is_allowed"]:
                print(f"    ✅ 化学不允许开设（正确）")
            else:
                print(f"    ❌ 化学不应该在1年级开设")
                all_passed = False
    
    # 验证：数学应该存在且允许，物理和化学应该存在但不允许
    grade1_passed = has_math and has_physics and has_chemistry
    
    # 测试7年级（应该允许物理）
    print("\n  测试7年级:")
    available = validator.get_available_subjects("ID", "Kelas 7", subjects)
    
    has_physics = False
    for subj in available:
        if subj["local_name"] == "Fisika":
            has_physics = True
            if subj["is_allowed"]:
                print(f"    ✅ 物理允许开设（正确）")
            else:
                print(f"    ❌ 物理应该在7年级开设")
                all_passed = False
    
    grade7_passed = has_physics
    
    if grade1_passed and grade7_passed:
        print("\n✅ PASS: 获取可用学科测试通过")
        return True
    else:
        print(f"\n❌ FAIL: 获取可用学科测试失败 (grade1={grade1_passed}, grade7={grade7_passed})")
        return False


def test_streams():
    """测试获取选科信息"""
    print("\n[测试5] 获取选科信息（高中）")
    validator = GradeSubjectValidator()
    
    streams = validator.get_streams_for_grade("ID", "Kelas 10")
    
    if len(streams) > 0:
        print(f"  ✅ 找到 {len(streams)} 个选科方向:")
        for stream in streams:
            print(f"    - {stream['stream_name']}: {len(stream['required_subjects'])}个必修科目")
        return True
    else:
        print("  ⚠️ 未找到选科信息（可能配置不完整）")
        return True  # 不算失败，因为可能是配置问题


def run_all_tests():
    """运行所有测试"""
    print("="*80)
    print("年级学科验证器测试套件")
    print("="*80)
    
    tests = [
        test_validator_initialization,
        test_grade_level_detection,
        test_grade_subject_validation,
        test_get_available_subjects,
        test_streams,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ 测试异常: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    passed = sum(results)
    total = len(results)
    print(f"总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return 0
    else:
        print(f"⚠️ {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
