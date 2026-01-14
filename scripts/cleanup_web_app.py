#!/usr/bin/env python3
"""
清理 web_app.py 中的数据可视化和智能自动化功能
"""

import re
import sys

def clean_web_app():
    """清理web_app.py文件"""

    input_file = 'web_app.py'
    output_file = 'web_app_cleaned.py'

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 需要删除的路由
    routes_to_delete = [
        '/dashboard',
        '/stats_dashboard',
        '/global_map',
        '/compare',
        '/batch_discovery',
        '/health_status',
        '/sis_dashboard',
        '/api/health_check',
        '/api/admin/monitoring_dashboard',
        '/api/admin/optimization_status',
        '/api/admin/optimization_requests',
        '/api/admin/optimization_approve',
        '/api/admin/optimization_reject',
        '/api/admin/optimization_execute',
        '/api/admin/optimization_stats',
        '/api/admin/optimization_history',
        '/api/admin/trigger_sis',
        '/api/admin/sis_status',
    ]

    # 需要删除的导入
    imports_to_delete = [
        'from core.ab_testing import',
        'from core.analytics import',
        'from core.monitoring_system import',
        'from core.optimization_approval import',
        'from core.optimization_orchestrator import',
        'from core.prompt_optimizer import',
        'from core.screenshot_service import',
        'from core.feedback_collector import',
    ]

    # 删除标记的行
    output_lines = []
    skip_until_next_route = False
    deleted_count = 0

    for i, line in enumerate(lines):
        # 检查是否是需要删除的路由
        is_route_to_delete = False
        for route in routes_to_delete:
            if f"@app.route('{route}" in line or f'@app.route("{route}"' in line:
                is_route_to_delete = True
                skip_until_next_route = True
                deleted_count += 1
                print(f"标记删除路由: {route} (行 {i+1})")
                break

        # 检查是否是需要删除的导入
        is_import_to_delete = False
        for imp in imports_to_delete:
            if imp in line:
                is_import_to_delete = True
                deleted_count += 1
                print(f"标记删除导入: {imp.strip()} (行 {i+1})")
                break

        # 如果遇到下一个@app.route，停止跳过
        if skip_until_next_route and line.strip().startswith('@app.route'):
            skip_until_next_route = False

        # 跳过标记为删除的行
        if is_route_to_delete or is_import_to_delete or skip_until_next_route:
            continue

        output_lines.append(line)

    # 写入清理后的文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)

    print(f"\n✅ 清理完成！")
    print(f"   删除了 {deleted_count} 行代码")
    print(f"   原文件: {input_file} ({len(lines)} 行)")
    print(f"   新文件: {output_file} ({len(output_lines)} 行)")
    print(f"\n请检查新文件，确认无误后执行:")
    print(f"   mv {output_file} {input_file}")

if __name__ == '__main__':
    clean_web_app()
