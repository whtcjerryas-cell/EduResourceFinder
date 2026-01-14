#!/usr/bin/env python3
"""
分析代码复杂度
"""

import re
import os

def analyze_web_app():
    """分析web_app.py的复杂度"""
    with open('web_app.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 统计
    total_lines = len(lines)
    route_count = sum(1 for line in lines if '@app.route' in line)
    function_count = sum(1 for line in lines if line.strip().startswith('def '))

    # 查找长函数
    function_starts = []
    for i, line in enumerate(lines):
        if line.strip().startswith('def '):
            function_starts.append((i, line.strip()))

    # 计算函数长度
    function_lengths = []
    for i, (start, definition) in enumerate(function_starts):
        end = function_starts[i + 1][0] if i + 1 < len(function_starts) else len(lines)
        length = end - start
        function_lengths.append((definition, length, start + 1))

    # 排序
    long_functions = sorted(function_lengths, key=lambda x: x[1], reverse=True)[:10]

    print("="*60)
    print("web_app.py 复杂度分析")
    print("="*60)
    print(f"\n总行数: {total_lines}")
    print(f"路由数量: {route_count}")
    print(f"函数数量: {function_count}")
    print(f"平均每个路由: {total_lines // route_count}行")

    print("\n" + "="*60)
    print("最长的10个函数:")
    print("="*60)

    for definition, length, line_num in long_functions:
        func_name = definition.replace('def ', '').split('(')[0]
        indicator = "🔴" if length > 200 else "🟡" if length > 100 else "🟢"
        print(f"{indicator} {func_name:40} : {length:4}行 (行{line_num})")

    print("\n" + "="*60)
    print("评估标准:")
    print("="*60)
    print("🟢 优秀: <50行")
    print("🟡 良好: 50-100行")
    print("🟠 可接受: 100-200行")
    print("🔴 需要重构: >200行")

    return {
        'total_lines': total_lines,
        'route_count': route_count,
        'function_count': function_count,
        'long_functions': long_functions
    }

if __name__ == '__main__':
    analyze_web_app()
