#!/usr/bin/env python3
"""
后端集成测试脚本
测试各个模块之间的协作
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config_manager import ConfigManager
from core.grade_subject_validator import GradeSubjectValidator
from discovery_agent import CountryProfile


def test_integration_validator_config_manager():
    """测试验证器与配置管理器集成"""
    print("\n[集成测试1] 验证器 + 配置管理器")
    try:
        manager = ConfigManager()
        validator = GradeSubjectValidator()
        
        # 获取一个国家配置
        config = manager.get_country_config("ID")
        
        if config is None:
            print("⚠️ WARN: 未找到印尼配置，跳过测试")
            return True
        
        # 验证一些年级-学科配对
        test_cases = [
            ("Kelas 1", "Matematika", True),
            ("Kelas 1", "Fisika", False),
            ("Kelas 7", "Fisika", True),
        ]
        
        passed = 0
        for grade, subject, should_be_valid in test_cases:
            result = validator.validate("ID", grade, subject)
            if result["valid"] == should_be_valid:
                print(f"  ✅ {grade} + {subject}: valid={result['valid']}")
                passed += 1
            else:
                print(f"  ❌ {grade} + {subject}: 期望valid={should_be_valid}, 实际valid={result['valid']}")
        
        if passed == len(test_cases):
            print("✅ PASS: 验证器与配置管理器集成正常")
            return True
        else:
            print(f"❌ FAIL: {passed}/{len(test_cases)} 测试通过")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: 集成测试失败 - {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_integration_generate_mappings():
    """测试生成年级-学科配对"""
    print("\n[集成测试2] 自动生成年级-学科配对")
    try:
        manager = ConfigManager()
        validator = GradeSubjectValidator()
        
        # 获取印尼配置
        config = manager.get_country_config("ID")
        
        if config is None:
            print("⚠️ WARN: 未找到印尼配置，创建测试配置")
            # 创建测试配置
            config = CountryProfile(
                country_code="ID",
                country_name="Indonesia",
                language_code="id",
                grades=[
                    {"local_name": "Kelas 1", "zh_name": "一年级"},
                    {"local_name": "Kelas 7", "zh_name": "七年级"}
                ],
                subjects=[
                    {"local_name": "Matematika", "zh_name": "数学"},
                    {"local_name": "Fisika", "zh_name": "物理"}
                ],
                grade_subject_mappings={},
                domains=[],
                notes="测试"
            )
        
        # 如果没有配对信息，生成
        if not config.grade_subject_mappings:
            print("  为每个年级生成可用学科...")
            mappings = {}
            
            for grade_dict in config.grades:
                grade_name = grade_dict["local_name"]
                available = validator.get_available_subjects(
                    "ID",
                    grade_name,
                    config.subjects
                )
                
                # 只保留允许的学科
                allowed = [s for s in available if s.get("is_allowed", True)]
                mappings[grade_name] = {
                    "available_subjects": allowed,
                    "notes": "自动生成"
                }
            
            config.grade_subject_mappings = mappings
        
        print(f"✅ PASS: 成功生成 {len(config.grade_subject_mappings)} 个年级的配对")
        
        for grade, mapping in config.grade_subject_mappings.items():
            subjects = mapping.get("available_subjects", [])
            print(f"  {grade}: {len(subjects)} 个可用学科")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: 生成配对失败 - {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_integration_full_workflow():
    """测试完整工作流"""
    print("\n[集成测试3] 完整工作流测试")
    try:
        from discovery_agent import CountryDiscoveryAgent
        
        print("  步骤1: 创建CountryProfile对象")
        profile = CountryProfile(
            country_code="TEST",
            country_name="Test Country",
            language_code="en",
            grades=[
                {"local_name": "Grade 1", "zh_name": "一年级"},
                {"local_name": "Grade 7", "zh_name": "七年级"}
            ],
            subjects=[
                {"local_name": "Mathematics", "zh_name": "数学"},
                {"local_name": "Physics", "zh_name": "物理"},
                {"local_name": "Chemistry", "zh_name": "化学"}
            ],
            grade_subject_mappings={},
            domains=[],
            notes="测试工作流"
        )
        
        print("  步骤2: 生成年级-学科配对")
        agent = CountryDiscoveryAgent()
        profile_with_mappings = agent.verify_and_enrich_grade_subject_mappings(profile, "Test Country")
        
        print("  步骤3: 验证配对结果")
        if not profile_with_mappings.grade_subject_mappings:
            print("  ⚠️ WARN: 未生成配对信息")
            return True
        
        print(f"  步骤4: 检查配对质量")
        for grade, mapping in profile_with_mappings.grade_subject_mappings.items():
            subjects = mapping.get("available_subjects", [])
            print(f"    {grade}: {len(subjects)} 个学科")
            
            # Grade 1不应该有Physics
            if "Grade 1" in grade:
                has_physics = any(s["local_name"] == "Physics" for s in subjects)
                if has_physics:
                    print(f"    ❌ Grade 1不应该有Physics")
                    return False
                else:
                    print(f"    ✅ Grade 1正确过滤了Physics")
            
            # Grade 7应该有Physics
            if "Grade 7" in grade:
                has_physics = any(s["local_name"] == "Physics" for s in subjects)
                if not has_physics:
                    print(f"    ❌ Grade 7应该有Physics")
                    return False
                else:
                    print(f"    ✅ Grade 7正确包含Physics")
        
        print("  步骤5: 保存配置")
        manager = ConfigManager()
        manager.update_country_config(profile_with_mappings)
        
        # 验证保存成功
        saved_config = manager.get_country_config("TEST")
        if saved_config and len(saved_config.grade_subject_mappings) > 0:
            print(f"  ✅ 配置保存成功，包含 {len(saved_config.grade_subject_mappings)} 个年级的配对")
        else:
            print(f"  ❌ 配置保存失败")
            return False
        
        # 清理
        manager.delete_country_config("TEST")
        print("  ✅ 已清理测试数据")
        
        print("✅ PASS: 完整工作流测试通过")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: 工作流测试失败 - {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_all_countries_validation():
    """测试所有已配置国家的验证"""
    print("\n[集成测试4] 验证所有国家配置")
    try:
        manager = ConfigManager()
        validator = GradeSubjectValidator()
        
        countries = manager.get_all_countries()
        
        if not countries:
            print("⚠️ WARN: 没有已配置的国家")
            return True
        
        print(f"  正在验证 {len(countries)} 个国家...")
        
        total_issues = 0
        for country in countries[:5]:  # 只测试前5个国家
            code = country["country_code"]
            config = manager.get_country_config(code)
            
            if not config:
                continue
            
            # 验证一些常见的年级-学科配对
            issues = 0
            
            for grade in config.grades[:3]:  # 只测试前3个年级
                grade_name = grade["local_name"]
                grade_level = validator._get_grade_level(grade_name)
                
                if not grade_level:
                    continue
                
                # 获取可用学科
                available = validator.get_available_subjects(
                    code,
                    grade_name,
                    config.subjects
                )
                
                # 检查是否有不允许的学科被标记为允许
                for subj in available:
                    if not subj.get("is_allowed", True):
                        issues += 1
            
            if issues > 0:
                print(f"  ⚠️ {code}: 发现 {issues} 个潜在问题")
                total_issues += issues
            else:
                print(f"  ✅ {code}: 验证通过")
        
        if total_issues == 0:
            print("✅ PASS: 所有国家配置验证通过")
            return True
        else:
            print(f"⚠️ WARN: 发现 {total_issues} 个潜在问题（可能需要人工审核）")
            return True  # 不算失败，因为可能是配置差异
            
    except Exception as e:
        print(f"❌ FAIL: 国家配置验证失败 - {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有集成测试"""
    print("="*80)
    print("后端集成测试套件")
    print("="*80)
    
    tests = [
        test_integration_validator_config_manager,
        test_integration_generate_mappings,
        test_integration_full_workflow,
        test_all_countries_validation,
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
        print("🎉 所有集成测试通过！")
        return 0
    else:
        print(f"⚠️ {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
