#!/usr/bin/env python3
"""
主测试运行脚本
运行所有测试套件
"""

import sys
import os
import subprocess
from datetime import datetime


def print_header(text):
    """打印标题"""
    print("\n" + "="*80)
    print(text)
    print("="*80)


def run_test_suite(test_file, description):
    """运行单个测试套件"""
    print_header(f"运行测试套件: {description}")
    
    if not os.path.exists(test_file):
        print(f"❌ 错误: 测试文件不存在 - {test_file}")
        return False
    
    print(f"执行: python3 {test_file}")
    print("-"*80)
    
    result = subprocess.run(
        [sys.executable, test_file],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        capture_output=False
    )
    
    return result.returncode == 0


def main():
    """主函数"""
    print_header("教育系统自动化测试")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试套件列表
    test_suites = [
        ("tests/test_grade_subject_validator.py", "年级学科验证器测试"),
        ("tests/test_config_manager.py", "配置管理器测试"),
        ("tests/test_backend_integration.py", "后端集成测试"),
    ]
    
    # 运行所有测试套件
    results = {}
    for test_file, description in test_suites:
        success = run_test_suite(test_file, description)
        results[description] = success
    
    # 询问是否运行API测试
    print_header("API端点测试")
    print("⚠️ API测试需要web_app.py服务正在运行")
    print("   启动命令: python3 web_app.py")
    print("\n是否运行API测试？")
    print("  [1] 是 - 运行API测试")
    print("  [2] 否 - 跳过API测试")
    print("  [3] 取消 - 退出测试")
    
    choice = input("\n请选择 (1/2/3): ").strip()
    
    if choice == "1":
        api_success = run_test_suite(
            "tests/test_api_endpoints.py",
            "API端点测试"
        )
        results["API端点测试"] = api_success
    elif choice == "2":
        print("\n跳过API测试")
        results["API端点测试"] = None
    else:
        print("\n测试已取消")
        return 1
    
    # 打印测试总结
    print_header("测试总结")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    total = len(results)
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    
    for description, success in results.items():
        if success is True:
            status = "✅ PASS"
        elif success is False:
            status = "❌ FAIL"
        else:
            status = "⏭️  SKIP"
        
        print(f"  {status}: {description}")
    
    print()
    print(f"总计: {passed} 通过, {failed} 失败, {skipped} 跳过")
    
    if failed == 0:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️ {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试运行出错: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
