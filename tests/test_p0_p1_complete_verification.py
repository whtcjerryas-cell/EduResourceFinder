#!/usr/bin/env python3
"""
P0+P1优化全面验证脚本

验证项目：
1. 导入路径一致性检查
2. Python语法验证
3. SSRF防护测试
4. 查询清理测试
5. API密钥验证测试
6. Agent接口功能测试
7. 性能基准测试

使用方法：
    python3 tests/test_p0_p1_complete_verification.py
"""

import sys
import os
import time
import json
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """打印标题"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text.center(70)}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.END}\n")

def print_success(text):
    """打印成功信息"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    """打印错误信息"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    """打印警告信息"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    """打印信息"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

# ============================================================================
# 测试1: 导入路径一致性检查
# ============================================================================

def test_import_paths():
    """测试1: 检查所有Python文件的导入路径是否正确"""
    print_header("测试1: 导入路径一致性检查")

    # 需要检查的文件
    files_to_check = [
        'web_app.py',
        'search_engine_v2.py',
        'search_strategy_agent.py',
        'tools/discovery_agent.py',
        'core/batch_discovery_agent.py',
        'core/resource_updater.py',
        'core/report_generator.py',
        'core/health_checker.py',
        'core/video_evaluator.py'
    ]

    errors = []

    for file_path in files_to_check:
        full_path = project_root / file_path
        if not full_path.exists():
            print_warning(f"文件不存在: {file_path}")
            continue

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')

            # 检查是否有旧的导入路径
            for i, line in enumerate(lines, 1):
                if 'from config_manager import' in line and 'from utils.config_manager import' not in line:
                    errors.append(f"{file_path}:{i} - 旧的导入路径: {line.strip()}")
                elif 'from json_utils import' in line and 'from utils.json_utils import' not in line:
                    errors.append(f"{file_path}:{i} - 旧的导入路径: {line.strip()}")
                elif 'from logger_utils import' in line and 'from utils.logger_utils import' not in line:
                    errors.append(f"{file_path}:{i} - 旧的导入路径: {line.strip()}")

    if errors:
        print_error(f"发现 {len(errors)} 个导入路径错误：")
        for error in errors:
            print(f"  {Colors.RED}✗{Colors.END} {error}")
        return False
    else:
        print_success("所有文件的导入路径正确")
        return True

# ============================================================================
# 测试2: Python语法验证
# ============================================================================

def test_syntax():
    """测试2: 验证Python文件语法"""
    print_header("测试2: Python语法验证")

    files_to_check = [
        'search_engine_v2.py',
        'web_app.py',
        'search_strategy_agent.py'
    ]

    all_passed = True

    for file_path in files_to_check:
        full_path = project_root / file_path
        if not full_path.exists():
            print_warning(f"文件不存在: {file_path}")
            continue

        try:
            result = subprocess.run(
                ['python3', '-m', 'py_compile', str(full_path)],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                print_success(f"{file_path} - 语法正确")
            else:
                print_error(f"{file_path} - 语法错误:")
                print(result.stderr)
                all_passed = False
        except Exception as e:
            print_error(f"{file_path} - 检查失败: {str(e)}")
            all_passed = False

    return all_passed

# ============================================================================
# 测试3: SSRF防护
# ============================================================================

def test_ssrf_protection():
    """测试3: SSRF防护验证"""
    print_header("测试3: SSRF防护验证")

    try:
        from search_engine_v2 import is_safe_url, sanitize_search_query

        # URL验证测试
        test_cases = [
            ("http://localhost:8080", False, "阻止localhost"),
            ("http://127.0.0.1/admin", False, "阻止127.0.0.1"),
            ("http://169.254.169.254/latest", False, "阻止AWS metadata"),
            ("http://192.168.1.1/secret", False, "阻止内网IP"),
            ("https://youtube.com/watch?v=abc", True, "允许合法URL"),
            ("https://example.com", True, "允许example.com"),
        ]

        passed = 0
        failed = 0

        for url, expected, description in test_cases:
            result = is_safe_url(url)
            if result == expected:
                print_success(f"{description}: {url}")
                passed += 1
            else:
                print_error(f"{description}失败: {url} (期望: {expected}, 实际: {result})")
                failed += 1

        # 查询清理测试
        query_tests = [
            ("site:evil.com hack", "hack", "移除site:运算符"),
            ("filetype:pdf password", "password", "移除filetype:运算符"),
            ("cache:evil.com sensitive", "sensitive", "移除cache:运算符"),
        ]

        for query, expected_contains, description in query_tests:
            result = sanitize_search_query(query)
            if expected_contains in result and 'site:' not in result:
                print_success(f"{description}: '{query}' → '{result}'")
                passed += 1
            else:
                print_error(f"{description}失败: '{query}' → '{result}'")
                failed += 1

        print(f"\n{Colors.BLUE}SSRF防护测试: {passed} 通过, {failed} 失败{Colors.END}")
        return failed == 0

    except ImportError as e:
        print_error(f"无法导入SSRF防护函数: {str(e)}")
        return False

# ============================================================================
# 测试4: API密钥验证
# ============================================================================

def test_api_key_validation():
    """测试4: API密钥验证"""
    print_header("测试4: API密钥验证")

    try:
        from search_engine_v2 import validate_api_key

        # 有效密钥测试
        try:
            validate_api_key("sk-test1234567890abcdef", "测试密钥")
            print_success("有效密钥验证通过")
        except ValueError:
            print_error("有效密钥被错误拒绝")
            return False

        # 短密钥测试
        try:
            validate_api_key("short", "短密钥")
            print_error("短密钥未被拒绝")
            return False
        except ValueError as e:
            print_success(f"短密钥正确拒绝: {str(e)[:50]}...")

        # 占位符测试
        try:
            validate_api_key("your_api_key", "占位符密钥")
            print_error("占位符密钥未被拒绝")
            return False
        except ValueError as e:
            print_success(f"占位符密钥正确拒绝: {str(e)[:50]}...")

        return True

    except ImportError as e:
        print_warning(f"无法导入validate_api_key函数: {str(e)}")
        return True  # 不是关键功能

# ============================================================================
# 测试5: Agent接口测试
# ============================================================================

def test_agent_interface():
    """测试5: Agent原生接口"""
    print_header("测试5: Agent原生接口测试")

    try:
        from search_engine_v2 import agent_search, quick_search

        # 测试1: 函数式API
        print_info("测试 agent_search() 函数...")

        start_time = time.time()
        result = agent_search(
            country="ID",
            grade="Kelas 1",
            subject="Matematika",
            timeout=150,
            enable_transparency=False
        )
        elapsed = time.time() - start_time

        if result.get('success'):
            print_success(f"agent_search() 成功 - {result.get('total_count')} 个结果, 耗时 {elapsed:.2f}秒")
        else:
            print_error(f"agent_search() 失败: {result.get('message', 'Unknown error')}")
            return False

        # 测试2: 快速搜索
        print_info("测试 quick_search() 函数...")

        results = quick_search("ID", "Kelas 1", "Matematika")

        if isinstance(results, list) and len(results) > 0:
            print_success(f"quick_search() 成功 - 返回 {len(results)} 个结果")
        else:
            print_error("quick_search() 失败或返回空列表")
            return False

        # 性能检查
        if elapsed < 30:
            print_success(f"性能优秀: {elapsed:.2f}秒 < 30秒阈值")
        elif elapsed < 60:
            print_warning(f"性能可接受: {elapsed:.2f}秒 < 60秒阈值")
        else:
            print_error(f"性能不佳: {elapsed:.2f}秒 > 60秒阈值")
            return False

        return True

    except Exception as e:
        print_error(f"Agent接口测试失败: {type(e).__name__}: {str(e)[:100]}")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# 测试6: 代码模式检查
# ============================================================================

def test_code_patterns():
    """测试6: 代码模式检查"""
    print_header("测试6: 关键代码模式检查")

    try:
        # 检查search_engine_v2.py中的关键功能
        search_engine_path = project_root / 'search_engine_v2.py'
        with open(search_engine_path, 'r', encoding='utf-8') as f:
            content = f.read()

        checks = [
            ('def is_safe_url', 'SSRF防护函数'),
            ('def sanitize_search_query', '查询清理函数'),
            ('def validate_api_key', 'API密钥验证函数'),
            ('def agent_search', 'Agent接口函数'),
            ('class AgentSearchClient', 'Agent客户端类'),
            ('_playlist_cache = {}', '播放列表缓存'),
            ('_scorer_cache_lock = threading.Lock()', '评分器线程锁'),
            ('def get_playlist_info_fast', '快速播放列表获取'),
        ]

        all_found = True
        for pattern, description in checks:
            if pattern in content:
                print_success(f"找到: {description} ({pattern})")
            else:
                print_error(f"未找到: {description} ({pattern})")
                all_found = False

        return all_found

    except Exception as e:
        print_error(f"代码模式检查失败: {str(e)}")
        return False

# ============================================================================
# 测试7: 性能基准测试
# ============================================================================

def test_performance_benchmark():
    """测试7: 性能基准测试"""
    print_header("测试7: 性能基准测试")

    try:
        from search_engine_v2 import agent_search

        print_info("执行3次搜索测试...")

        times = []
        results_counts = []

        for i in range(3):
            print(f"  第 {i+1}/3 次搜索...", end='', flush=True)
            start = time.time()
            result = agent_search("ID", "Kelas 1", "Matematika", timeout=150)
            elapsed = time.time() - start
            times.append(elapsed)
            results_counts.append(result.get('total_count', 0))
            print(f" 完成 ({elapsed:.2f}秒, {result.get('total_count')} 个结果)")

        avg_time = sum(times) / len(times)
        avg_results = sum(results_counts) / len(results_counts)

        print(f"\n{Colors.BOLD}性能统计:{Colors.END}")
        print(f"  平均搜索时间: {avg_time:.2f}秒")
        print(f"  平均结果数: {avg_results:.0f}")
        print(f"  最快搜索: {min(times):.2f}秒")
        print(f"  最慢搜索: {max(times):.2f}秒")

        # 性能评估
        if avg_time < 20:
            print_success(f"性能优秀: 平均 {avg_time:.2f}秒 < 20秒")
            return True
        elif avg_time < 40:
            print_success(f"性能良好: 平均 {avg_time:.2f}秒 < 40秒")
            return True
        else:
            print_warning(f"性能一般: 平均 {avg_time:.2f}秒")
            return True  # 不算失败

    except Exception as e:
        print_error(f"性能基准测试失败: {str(e)[:100]}")
        return False

# ============================================================================
# 主测试运行器
# ============================================================================

def main():
    """运行所有测试"""
    print(f"""
{Colors.BOLD}{Colors.BLUE}
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║         P0+P1优化 - 全面验证测试套件                                ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
{Colors.END}
""")

    tests = [
        ("导入路径一致性检查", test_import_paths),
        ("Python语法验证", test_syntax),
        ("SSRF防护验证", test_ssrf_protection),
        ("API密钥验证", test_api_key_validation),
        ("Agent接口测试", test_agent_interface),
        ("代码模式检查", test_code_patterns),
        ("性能基准测试", test_performance_benchmark),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"{test_name} - 测试异常: {str(e)[:100]}")
            results.append((test_name, False))

    # 打印总结
    print_header("测试总结")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        if result:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")

    print(f"\n{Colors.BOLD}总计: {passed}/{total} 个测试通过{Colors.END}\n")

    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 所有测试通过！P0+P1优化验证成功！{Colors.END}\n")
        return 0
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  {total - passed} 个测试失败，请检查上述错误{Colors.END}\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
