#!/usr/bin/env python3
"""
快速检查日志功能是否正常工作
"""

import os
import sys

print("="*80)
print("🔍 日志功能诊断")
print("="*80)

# 检查 1: 日志文件是否存在
log_file = "search_system.log"
print(f"\n[检查 1] 日志文件: {log_file}")
if os.path.exists(log_file):
    size = os.path.getsize(log_file)
    print(f"    ✅ 文件存在，大小: {size} 字节")
else:
    print(f"    ⚠️ 文件不存在（将在首次使用时创建）")

# 检查 2: 日志模块是否可以导入
print(f"\n[检查 2] 导入日志模块...")
try:
    from utils.logger_utils import get_logger
    print("    ✅ logger_utils 导入成功")
except ImportError as e:
    print(f"    ❌ logger_utils 导入失败: {str(e)}")
    sys.exit(1)

# 检查 3: 初始化日志系统
print(f"\n[检查 3] 初始化日志系统...")
try:
    logger = get_logger('diagnostic')
    print("    ✅ 日志系统初始化成功")
except Exception as e:
    print(f"    ❌ 日志系统初始化失败: {str(e)}")
    sys.exit(1)

# 检查 4: 测试日志写入
print(f"\n[检查 4] 测试日志写入...")
try:
    logger.info("这是一条测试日志消息")
    print("    ✅ 日志写入成功")
except Exception as e:
    print(f"    ❌ 日志写入失败: {str(e)}")
    sys.exit(1)

# 检查 5: 测试 print 包装
print(f"\n[检查 5] 测试 print 包装...")
try:
    import builtins
    _original_print = builtins.print
    def test_print(*args, **kwargs):
        _original_print(*args, **kwargs)
        message = ' '.join(str(arg) for arg in args)
        if message.strip():
            logger.info(message)
    builtins.print = test_print
    
    print("这是一条通过 print 的测试消息")
    print("    ✅ print 包装工作正常")
except Exception as e:
    print(f"    ❌ print 包装失败: {str(e)}")
    import traceback
    traceback.print_exc()

# 检查 6: 验证日志文件内容
print(f"\n[检查 6] 验证日志文件内容...")
if os.path.exists(log_file):
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print(f"    ✅ 日志文件包含 {len(lines)} 行")
        if lines:
            print(f"    最后一行: {lines[-1].strip()[:80]}...")
else:
    print("    ⚠️ 日志文件尚未创建")

# 检查 7: 检查模块导入
print(f"\n[检查 7] 检查关键模块...")
modules_to_check = [
    'search_engine_v2',
    'discovery_agent',
    'config_manager',
    'logger_utils'
]

for module_name in modules_to_check:
    try:
        __import__(module_name)
        print(f"    ✅ {module_name} 可以导入")
    except ImportError as e:
        print(f"    ❌ {module_name} 导入失败: {str(e)}")

print("\n" + "="*80)
print("✅ 诊断完成")
print("="*80)
print(f"\n📝 日志文件位置: {os.path.abspath(log_file)}")
print("💡 提示: 如果 Web 应用正在运行，请重启它以使日志功能生效")
print("="*80)

