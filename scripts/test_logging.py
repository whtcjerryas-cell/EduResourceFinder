#!/usr/bin/env python3
"""
测试日志功能 - 模拟 web_app.py 的导入和使用
"""

import sys
import os

# 初始化日志系统（必须在导入其他模块之前）
from logger_utils import get_logger
logger = get_logger('test_web_app')

# 保存原始 print 函数
import builtins
_original_print = builtins.print

# 包装 print 函数，同时写入日志文件
def print(*args, **kwargs):
    """包装 print，同时写入日志文件"""
    # 先调用原始 print（输出到控制台）
    _original_print(*args, **kwargs)
    # 同时写入日志文件
    message = ' '.join(str(arg) for arg in args)
    if message.strip():  # 只记录非空消息
        logger.info(message)

# 替换全局 print（必须在导入其他模块之前）
builtins.print = print

print("="*80)
print("🧪 测试日志功能")
print("="*80)

# 现在导入其他模块
from search_engine_v2 import SearchEngineV2, SearchRequest

print("\n✅ 模块导入成功")

# 测试搜索
print("\n" + "="*80)
print("🔍 测试搜索功能")
print("="*80)

try:
    engine = SearchEngineV2()
    request = SearchRequest(
        country="ID",
        grade="Kelas 3",
        subject="Matematika"
    )
    
    print("\n开始执行搜索...")
    response = engine.search(request)
    
    print(f"\n✅ 搜索完成: {response.success}")
    print(f"   结果数量: {len(response.results)}")
    
except Exception as e:
    print(f"\n❌ 搜索失败: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("✅ 测试完成，请检查日志文件: search_system.log")
print("="*80)

