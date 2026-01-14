#!/usr/bin/env python3
"""
内存监控工具
用于监控和诊断内存使用情况
"""

import os
import sys
from datetime import datetime
from pathlib import Path

def get_memory_usage_simple():
    """获取当前进程的内存使用情况（不依赖psutil）"""
    try:
        import resource
        # 获取RSS内存（单位：KB）
        rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # macOS返回的是字节，Linux返回的是KB
        if sys.platform == 'darwin':
            rss_mb = rss_kb / 1024 / 1024
        else:
            rss_mb = rss_kb / 1024

        return {
            'rss_mb': round(rss_mb, 2),
            'platform': sys.platform
        }
    except Exception as e:
        return {'rss_mb': 0, 'platform': 'unknown', 'error': str(e)}

def print_memory_status():
    """打印当前内存使用情况"""
    memory = get_memory_usage_simple()

    print("=" * 60)
    print("📊 内存使用情况")
    print("=" * 60)
    print(f"平台: {memory['platform']}")

    if 'error' in memory:
        print(f"⚠️  无法获取内存信息: {memory['error']}")
    else:
        print(f"物理内存 (RSS): {memory['rss_mb']:.2f} MB")

        # 警告
        if memory['rss_mb'] > 1000:
            print("\n⚠️  警告: 内存使用超过1GB，建议清理")
        elif memory['rss_mb'] > 500:
            print("\n⚠️  注意: 内存使用较高")
        else:
            print("\n✅ 内存使用正常")

    print("=" * 60)

    return memory

def cleanup_screenshot_cache():
    """清理截图缓存"""
    import tempfile
    from pathlib import Path

    cache_dir = Path(tempfile.gettempdir()) / "screenshots"

    if not cache_dir.exists():
        print(f"❌ 缓存目录不存在: {cache_dir}")
        return

    # 统计
    files = list(cache_dir.glob("*.png"))
    total_size = sum(f.stat().st_size for f in files) / 1024 / 1024

    print(f"\n🗑️  清理截图缓存")
    print(f"   目录: {cache_dir}")
    print(f"   文件数: {len(files)}")
    print(f"   占用空间: {total_size:.2f} MB")

    # 删除所有文件
    count = 0
    for file in files:
        try:
            file.unlink()
            count += 1
        except Exception as e:
            print(f"   删除失败 {file.name}: {e}")

    print(f"   ✅ 已删除 {count} 个文件")

def check_playwright_processes():
    """检查Playwright浏览器进程（使用ps命令）"""
    print("\n🔍 检查Playwright浏览器进程")

    try:
        import subprocess
        # 查找Chromium进程
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True,
            timeout=5
        )

        lines = result.stdout.split('\n')
        chrome_processes = [line for line in lines if 'chrom' in line.lower() and 'headless' in line.lower()]

        if not chrome_processes:
            print("   ✅ 没有发现残留的浏览器进程")
        else:
            print(f"   ⚠️  发现 {len(chrome_processes)} 个浏览器进程")
            for proc in chrome_processes[:5]:  # 只显示前5个
                parts = proc.split()
                if len(parts) > 10:
                    print(f"   PID {parts[1]}: {parts[10][:50]}...")
            if len(chrome_processes) > 5:
                print(f"   ... 还有 {len(chrome_processes) - 5} 个进程")
            print("   💡 提示: 如果搜索已完成，这些进程应该已关闭")

    except Exception as e:
        print(f"   ⚠️  无法检查进程: {e}")

if __name__ == "__main__":
    print(f"\n🕐 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 显示内存使用
    memory = print_memory_status()

    # 检查浏览器进程
    check_playwright_processes()

    # 询问是否清理缓存
    if memory.get('rss_mb', 0) > 200:
        print("\n💡 检测到内存使用较高，是否清理截图缓存？")
        try:
            response = input("输入 y 清理缓存，其他键跳过: ").strip().lower()

            if response == 'y':
                cleanup_screenshot_cache()
                print("\n重新检查内存...")
                print_memory_status()
        except EOFError:
            # 非交互模式，跳过
            pass
    else:
        print("\n💡 提示: 可以手动清理缓存")
        try:
            response = input("是否清理截图缓存? (y/n): ").strip().lower()

            if response == 'y':
                cleanup_screenshot_cache()
        except EOFError:
            # 非交互模式，跳过
            pass

    print("\n✅ 内存监控完成")
