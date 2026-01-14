#!/usr/bin/env python3
"""
配置管理器测试脚本
"""

import sys
import os
import json

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config_manager import ConfigManager
from discovery_agent import CountryProfile


def test_config_manager_initialization():
    """测试配置管理器初始化"""
    print("\n[测试1] 配置管理器初始化")
    try:
        manager = ConfigManager()
        assert manager is not None
        assert manager.config_file is not None
        print("✅ PASS: 配置管理器初始化成功")
        return True
    except Exception as e:
        print(f"❌ FAIL: 配置管理器初始化失败 - {str(e)}")
        return False


def test_read_config():
    """测试读取配置"""
    print("\n[测试2] 读取配置")
    try:
        manager = ConfigManager()
        config = manager._read_config()
        
        assert isinstance(config, dict)
        print(f"✅ PASS: 成功读取配置，包含 {len(config)} 个国家")
        
        # 显示已配置的国家
        if len(config) > 0:
            print("  已配置的国家:")
            for code in sorted(config.keys())[:5]:  # 只显示前5个
                print(f"    - {code}: {config[code].get('country_name', 'Unknown')}")
            if len(config) > 5:
                print(f"    ... 还有 {len(config) - 5} 个国家")
        
        return True
    except Exception as e:
        print(f"❌ FAIL: 读取配置失败 - {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_get_country_config():
    """测试获取国家配置"""
    print("\n[测试3] 获取国家配置")
    try:
        manager = ConfigManager()
        
        # 测试获取印尼配置
        config = manager.get_country_config("ID")
        
        if config is None:
            print("⚠️ WARN: 未找到印尼配置，可能配置文件为空")
            return True
        
        assert config.country_code == "ID"
        assert config.country_name == "Indonesia"
        assert len(config.grades) > 0
        assert len(config.subjects) > 0
        
        print(f"✅ PASS: 成功获取印尼配置")
        print(f"  国家代码: {config.country_code}")
        print(f"  国家名称: {config.country_name}")
        print(f"  年级数量: {len(config.grades)}")
        print(f"  学科数量: {len(config.subjects)}")
        
        # 检查是否有grade_subject_mappings
        if hasattr(config, 'grade_subject_mappings') and config.grade_subject_mappings:
            print(f"  年级-学科配对: {len(config.grade_subject_mappings)} 个年级")
        
        return True
    except Exception as e:
        print(f"❌ FAIL: 获取国家配置失败 - {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_get_all_countries():
    """测试获取所有国家"""
    print("\n[测试4] 获取所有国家列表")
    try:
        manager = ConfigManager()
        countries = manager.get_all_countries()
        
        assert isinstance(countries, list)
        print(f"✅ PASS: 成功获取 {len(countries)} 个国家")
        
        if len(countries) > 0:
            print("  国家列表:")
            for country in countries[:10]:  # 只显示前10个
                print(f"    - {country['country_code']}: {country['country_name']}")
        
        return True
    except Exception as e:
        print(f"❌ FAIL: 获取所有国家失败 - {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_update_country_config():
    """测试更新国家配置"""
    print("\n[测试5] 更新国家配置（使用测试数据）")
    try:
        manager = ConfigManager()
        
        # 创建测试配置
        test_profile = CountryProfile(
            country_code="TEST",
            country_name="Test Country",
            country_name_zh="测试国家",
            language_code="en",
            grades=[
                {"local_name": "Grade 1", "zh_name": "一年级"},
                {"local_name": "Grade 7", "zh_name": "七年级"}
            ],
            subjects=[
                {"local_name": "Mathematics", "zh_name": "数学"},
                {"local_name": "Physics", "zh_name": "物理"}
            ],
            grade_subject_mappings={
                "Grade 1": {
                    "available_subjects": [
                        {"local_name": "Mathematics", "zh_name": "数学", "is_core": True}
                    ],
                    "notes": "测试配置"
                }
            },
            domains=[],
            notes="这是一个测试配置"
        )
        
        # 更新配置
        manager.update_country_config(test_profile)
        
        # 验证更新成功
        config = manager.get_country_config("TEST")
        assert config is not None
        assert config.country_code == "TEST"
        assert config.country_name == "Test Country"
        assert len(config.grade_subject_mappings) > 0
        
        print("✅ PASS: 成功更新国家配置")
        print(f"  国家代码: {config.country_code}")
        print(f"  年级-学科配对: {len(config.grade_subject_mappings)} 个年级")
        
        # 清理测试数据
        manager.delete_country_config("TEST")
        print("  已清理测试数据")
        
        return True
    except Exception as e:
        print(f"❌ FAIL: 更新国家配置失败 - {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n[测试6] 向后兼容性测试")
    try:
        manager = ConfigManager()
        
        # 获取现有配置
        config = manager.get_country_config("ID")
        
        if config is None:
            print("⚠️ WARN: 未找到印尼配置，跳过兼容性测试")
            return True
        
        # 检查是否有grade_subject_mappings字段
        has_mappings = hasattr(config, 'grade_subject_mappings')
        
        if has_mappings:
            print("✅ PASS: 配置包含grade_subject_mappings字段")
            
            # 如果是空字典，说明旧配置自动兼容
            if not config.grade_subject_mappings:
                print("  ℹ️ 旧配置自动兼容（grade_subject_mappings为空）")
        else:
            print("❌ FAIL: 配置缺少grade_subject_mappings字段")
            return False
        
        return True
    except Exception as e:
        print(f"❌ FAIL: 向后兼容性测试失败 - {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试"""
    print("="*80)
    print("配置管理器测试套件")
    print("="*80)
    
    tests = [
        test_config_manager_initialization,
        test_read_config,
        test_get_country_config,
        test_get_all_countries,
        test_update_country_config,
        test_backward_compatibility,
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
