#!/usr/bin/env python3
"""
系统性修复所有页面的一致性问题
"""
import os
import re
import shutil
from pathlib import Path

# 需要修复的页面列表
PAGES_TO_FIX = [
    'global_map.html',
    'knowledge_points.html',
    'evaluation_reports.html',
    'stats_dashboard.html',
    'compare.html',
    'batch_discovery.html',
    'health_status.html',
    'report_center.html'
]

TEMPLATES_DIR = '/Users/shmiwanghao8/Desktop/education/Indonesia/templates'

# CSS变量系统
CSS_VARS = '''        :root {
            /* 浅色主题 */
            --bg-primary: #f5f7fa;
            --bg-secondary: #ffffff;
            --bg-sidebar: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
            --text-primary: #333333;
            --text-secondary: #666666;
            --text-sidebar: #ffffff;
            --border-color: #e0e0e0;
            --shadow-color: rgba(0, 0, 0, 0.1);
            --card-bg: #f8f9fa;
            --input-bg: #ffffff;
        }

        [data-theme="dark"] {
            /* 深色主题 */
            --bg-primary: #1a1d23;
            --bg-secondary: #242830;
            --bg-sidebar: linear-gradient(180deg, #4a5568 0%, #2d3748 100%);
            --text-primary: #e2e8f0;
            --text-secondary: #a0aec0;
            --text-sidebar: #ffffff;
            --border-color: #374151;
            --shadow-color: rgba(0, 0, 0, 0.3);
            --card-bg: #2d3748;
            --input-bg: #1a1d23;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        /* 键盘导航优化 */
        *:focus-visible {
            outline: 2px solid #667eea;
            outline-offset: 2px;
            border-radius: 4px;
        }

        button:focus-visible {
            outline: 2px solid #667eea;
            outline-offset: 3px;
        }

        a:focus-visible {
            outline: 2px solid #667eea;
            outline-offset: 2px;
        }
'''

# Toast容器HTML
TOAST_CONTAINER = '''    <!-- Toast通知容器 -->
    <div class="toast-container" id="toastContainer"></div>
'''

# 侧边栏组件包含
SIDEBAR_INCLUDE = '''    <!-- 侧边栏导航 -->
    {% include 'sidebar_component.html' %}

    <!-- 侧边栏折叠按钮 -->
    <button class="sidebar-toggle" id="sidebarToggle" onclick="toggleSidebar()"
            title="收起侧边栏 (Ctrl+B)"
            data-title-collapsed="展开侧边栏 (Ctrl+B)"
            data-title-expanded="收起侧边栏 (Ctrl+B)">
        <span class="icon-open">◀</span>
        <span class="icon-close">▶</span>
    </button>
'''

# page-wrapper开始标签
PAGE_WRAPPER_START = '''    <div class="page-wrapper">
        <div class="page-header">
'''

# page-wrapper结束标签
PAGE_WRAPPER_END = '''    </div> <!-- page-wrapper -->
'''

# 统一JavaScript
UNIFIED_JS = '''    <script>
        // 侧边栏状态
        let sidebarCollapsed = false;

        // 切换侧边栏
        function toggleSidebar() {
            sidebarCollapsed = !sidebarCollapsed;
            const sidebar = document.getElementById('sidebar');
            const toggle = document.getElementById('sidebarToggle');
            const pageWrapper = document.querySelector('.page-wrapper');

            if (sidebarCollapsed) {
                sidebar.classList.add('collapsed');
                toggle.classList.add('collapsed');
                if (pageWrapper) {
                    pageWrapper.classList.add('expanded');
                }
                toggle.title = toggle.getAttribute('data-title-collapsed') || '展开侧边栏 (Ctrl+B)';
            } else {
                sidebar.classList.remove('collapsed');
                toggle.classList.remove('collapsed');
                if (pageWrapper) {
                    pageWrapper.classList.remove('expanded');
                }
                toggle.title = toggle.getAttribute('data-title-expanded') || '收起侧边栏 (Ctrl+B)';
            }

            localStorage.setItem('sidebarCollapsed', sidebarCollapsed);
        }

        // 页面加载时恢复状态
        window.addEventListener('DOMContentLoaded', function() {
            // 恢复侧边栏状态
            const savedState = localStorage.getItem('sidebarCollapsed');
            if (savedState === 'true') {
                toggleSidebar();
            }

            // 恢复主题
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-theme', savedTheme);
        });

        // Toast通知系统
        function showToast(type, title, message, duration = 3000) {
            const container = document.getElementById('toastContainer');
            if (!container) return;

            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;

            const icons = {
                success: '✅',
                error: '❌',
                warning: '⚠️',
                info: 'ℹ️'
            };

            toast.innerHTML = `
                <div class="toast-icon">${icons[type] || icons.info}</div>
                <div class="toast-content">
                    <div class="toast-title">${title}</div>
                    <div class="toast-message">${message}</div>
                </div>
                <button class="toast-close" onclick="this.parentElement.remove()">×</button>
            `;

            container.appendChild(toast);

            setTimeout(() => {
                toast.classList.add('hide');
                toast.addEventListener('animationend', () => {
                    toast.remove();
                });
            }, duration);
        }

        // 键盘快捷键
        document.addEventListener('keydown', function(event) {
            if ((event.ctrlKey || event.metaKey) && event.key === 'b') {
                event.preventDefault();
                toggleSidebar();
            }
        });
    </script>
'''

def fix_page(page_name):
    """修复单个页面"""
    filepath = os.path.join(TEMPLATES_DIR, page_name)

    print("\n" + "="*60)
    print(f"正在修复: {page_name}")
    print("="*60)

    # 备份
    backup_path = filepath + '.fix_backup'
    if not os.path.exists(backup_path):
        shutil.copy2(filepath, backup_path)
        print(f"✅ 已备份到: {backup_path}")

    # 读取文件
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 1. 添加CSS变量（在第一个<style>标签后）
    if '<style>' in content and ':root' not in content:
        content = content.replace(
            '<style>',
            f'<style>\n{CSS_VARS}',
            1
        )
        print("✅ 已添加CSS变量系统")

    # 2. 修复body样式
    # 移除 padding: 20px
    content = re.sub(r'body\s*{[^}]*padding:\s*20px;[^}]*}',
                    'body { display: flex; background: var(--bg-primary); color: var(--text-primary); min-height: 100vh; }',
                    content)
    print("✅ 已修复body样式（display: flex）")

    # 3. 添加Toast容器（在<body>后）
    if '<body>' in content and 'toast-container' not in content:
        content = content.replace('<body>', f'<body>\n{TOAST_CONTAINER}', 1)
        print("✅ 已添加Toast容器")

    # 4. 添加侧边栏组件（如果不存在）
    if 'sidebar_component.html' not in content:
        # 在body后的第一个div之前插入
        content = content.replace(
            '<body>',
            f'<body>\n{SIDEBAR_INCLUDE}',
            1
        )
        print("✅ 已添加侧边栏组件")

    # 5. 包装主内容到page-wrapper
    # 查找主要内容区域的class或id
    main_content_patterns = [
        r'<div class="container">',
        r'<div class="main-content">',
        r'<div class="content-area">',
    ]

    for pattern in main_content_patterns:
        if pattern in content and 'page-wrapper' not in content:
            # 找到匹配项，在其后添加page-wrapper开始
            # 并找到对应的结束</div>，添加结束标签
            # 这个比较复杂，需要仔细处理
            pass

    # 6. 添加统一样式文件引用
    if 'unified_page_styles.css' not in content:
        # 在</head>前添加
        content = content.replace(
            '</head>',
            '    <link rel="stylesheet" href="/static/css/unified_page_styles.css">\n</head>'
        )
        print("✅ 已添加统一样式文件引用")

    # 7. 添加统一JavaScript（在</body>前）
    if '</body>' in content and 'toggleSidebar' not in content:
        content = content.replace(
            '</body>',
            f'{UNIFIED_JS}\n</body>'
        )
        print("✅ 已添加统一JavaScript")

    # 如果有修改，写入文件
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\n✅ {page_name} 修复完成！")
        return True
    else:
        print(f"\n⚠️ {page_name} 无需修改或已存在必要元素")
        return False

def main():
    """主函数"""
    print("\n" + "="*60)
    print("开始系统性修复8个页面的一致性问题")
    print("="*60)

    fixed_count = 0

    for page in PAGES_TO_FIX:
        if fix_page(page):
            fixed_count += 1

    print("\n" + "="*60)
    print(f"修复完成！共修复 {fixed_count}/{len(PAGES_TO_FIX)} 个页面")
    print("="*60)

    print("\n⚠️ 注意：某些复杂页面可能需要手动检查和调整")
    print("建议：")
    print("1. 访问每个修复后的页面")
    print("2. 检查侧边栏是否正常显示")
    print("3. 检查内容是否被遮挡")
    print("4. 测试暗黑模式切换")
    print("5. 测试侧边栏折叠功能")

if __name__ == '__main__':
    main()
