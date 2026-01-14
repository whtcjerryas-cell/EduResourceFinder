#!/usr/bin/env python3
"""
一键运行搜索并生成网页展示
"""

import os
import sys
import subprocess
from pathlib import Path


def run_search(input_file: str = None):
    """运行搜索脚本"""
    print("="*80)
    print("🔍 步骤 1: 执行搜索")
    print("="*80)
    
    if input_file:
        cmd = [sys.executable, "search_strategist.py", input_file]
    else:
        cmd = [sys.executable, "search_strategist.py"]
    
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode != 0:
        print("\n⚠️ 搜索过程出现错误")
        return None
    
    # 查找生成的 CSV 文件
    if input_file:
        csv_file = input_file.replace("_knowledge_points.json", "_playlists.csv")
    else:
        # 默认文件
        csv_file = "Knowledge Point/5. Final Panduan Mata Pelajaran Matematika_12_09_2025_Revisi 3_30-58_playlists.csv"
    
    if os.path.exists(csv_file):
        print(f"\n✅ 搜索完成，结果保存在: {csv_file}")
        return csv_file
    else:
        print(f"\n⚠️ 未找到输出文件: {csv_file}")
        return None


def generate_web_view(csv_file: str):
    """生成网页展示"""
    print("\n" + "="*80)
    print("🎨 步骤 2: 生成网页展示")
    print("="*80)
    
    cmd = [sys.executable, "generate_web_view.py", csv_file]
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode == 0:
        html_file = csv_file.replace(".csv", ".html")
        if os.path.exists(html_file):
            print(f"\n✅ 网页已生成: {html_file}")
            print(f"\n🌐 请在浏览器中打开:")
            print(f"   file://{os.path.abspath(html_file)}")
            return html_file
    
    return None


def main():
    """主函数"""
    print("\n" + "="*80)
    print("🚀 印尼 K12 视频播放列表搜索与展示系统")
    print("="*80 + "\n")
    
    # 确定输入文件
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "Knowledge Point/5. Final Panduan Mata Pelajaran Matematika_12_09_2025_Revisi 3_30-58_knowledge_points.json"
    
    if not os.path.exists(input_file):
        print(f"❌ 错误: 文件不存在: {input_file}")
        print("\n使用方法:")
        print(f"  python3 {sys.argv[0]} [知识点JSON文件路径]")
        return
    
    # 步骤 1: 执行搜索
    csv_file = run_search(input_file)
    
    if not csv_file:
        print("\n⚠️ 跳过网页生成步骤")
        return
    
    # 步骤 2: 生成网页
    html_file = generate_web_view(csv_file)
    
    if html_file:
        print("\n" + "="*80)
        print("✅ 全部完成！")
        print("="*80)
    else:
        print("\n⚠️ 网页生成失败")


if __name__ == "__main__":
    main()


