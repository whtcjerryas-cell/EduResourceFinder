#!/usr/bin/env python3
"""
小批量验证搜索结果并生成 HTML
自动处理搜索和 HTML 生成流程
"""

import json
import os
import sys
import csv
import time

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from search_strategist import SearchStrategist, AIBuildersClient
from generate_web_view import generate_html


def create_test_data():
    """创建测试用的知识点数据（只包含2个章节）"""
    test_data = {
        "knowledge_points": [
            {
                "grade_level": "Fase A (Kelas 1-2)",
                "subject": "Matematika",
                "chapter_title": "Bilangan",
                "topic_title": "Mengenal Bilangan 1-10",
                "description": "Mengenal dan menulis bilangan 1 sampai 10"
            },
            {
                "grade_level": "Fase A (Kelas 1-2)",
                "subject": "Matematika",
                "chapter_title": "Bilangan",
                "topic_title": "Mengenal Bilangan 11-20",
                "description": "Mengenal dan menulis bilangan 11 sampai 20"
            },
            {
                "grade_level": "Fase A (Kelas 1-2)",
                "subject": "Matematika",
                "chapter_title": "Geometri",
                "topic_title": "Mengenal Bangun Datar",
                "description": "Mengenal bentuk-bentuk bangun datar sederhana"
            }
        ]
    }
    
    test_file = "test_knowledge_points.json"
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已创建测试数据文件: {test_file}")
    print(f"📊 包含 {len(test_data['knowledge_points'])} 个知识点")
    print(f"📚 章节: Bilangan (2个知识点), Geometri (1个知识点)")
    
    return test_file


def main():
    """主函数"""
    print("="*80)
    print("🧪 小批量验证搜索结果并生成 HTML")
    print("="*80)
    print("\n📝 测试目标:")
    print("  1. 验证优化后的搜索策略")
    print("  2. 验证搜索结果质量")
    print("  3. 生成 HTML 表格展示结果")
    print("\n" + "-"*80)
    
    # 创建测试数据
    print("\n[步骤 1] 创建测试数据...")
    test_file = create_test_data()
    
    # 读取测试数据
    print(f"\n[步骤 2] 读取测试数据: {test_file}")
    with open(test_file, 'r', encoding='utf-8') as f:
        syllabus_data = json.load(f)
    
    # 初始化客户端和策略器
    print("\n[步骤 3] 初始化搜索客户端...")
    try:
        llm_client = AIBuildersClient()
        print("✅ AI Builders 客户端初始化成功")
        
        # 使用 Tavily 搜索
        strategist = SearchStrategist(llm_client, search_engine="ai-builders")
        print("✅ 搜索策略器初始化成功")
        
        # 执行搜索
        print("\n[步骤 4] 开始执行搜索...")
        print("⚠️  注意: 这将调用真实的 API，可能需要一些时间")
        print("   每个章节最多尝试5次搜索，找到高质量资源后停止\n")
        
        playlist_records = strategist.search_for_playlists(syllabus_data)
        
        # 显示结果
        print("\n" + "="*80)
        print("📊 搜索结果统计")
        print("="*80)
        print(f"✅ 找到的资源数量: {len(playlist_records)}")
        
        if playlist_records:
            # 统计资源类型
            playlist_count = sum(1 for r in playlist_records if "playlist" in r.playlist_url.lower() or "list=" in r.playlist_url.lower())
            video_count = sum(1 for r in playlist_records if "youtube.com/watch" in r.playlist_url and "list=" not in r.playlist_url)
            channel_count = sum(1 for r in playlist_records if "channel" in r.playlist_url.lower() or "/c/" in r.playlist_url.lower())
            
            print(f"\n📈 资源类型统计:")
            print(f"  - 播放列表: {playlist_count} 个")
            print(f"  - 单集视频（系列）: {video_count} 个")
            print(f"  - 频道: {channel_count} 个")
            
            print(f"\n📋 详细结果:")
            for i, record in enumerate(playlist_records, 1):
                resource_type = "播放列表" if "playlist" in record.playlist_url.lower() or "list=" in record.playlist_url.lower() else "视频（系列）" if "youtube.com/watch" in record.playlist_url else "频道"
                print(f"\n{i}. [{resource_type}] {record.chapter_title}")
                print(f"   URL: {record.playlist_url}")
                print(f"   搜索词: {record.search_query}")
                print(f"   尝试次数: {record.attempt_number}")
            
            # 保存结果到 CSV
            output_file = "test_playlists.csv"
            print(f"\n[步骤 5] 保存结果到 CSV: {output_file}")
            
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'grade_level', 'subject', 'chapter_title', 
                    'playlist_url', 'search_query', 'attempt_number', 'reason'
                ])
                writer.writeheader()
                for record in playlist_records:
                    writer.writerow(record.model_dump())
            
            print(f"✅ CSV 文件已保存: {output_file}")
            
            # 生成 HTML 网页
            print(f"\n[步骤 6] 生成 HTML 网页...")
            html_file = output_file.replace(".csv", ".html")
            html_path = generate_html(playlist_records, syllabus_data, html_file)
            
            print(f"\n" + "="*80)
            print(f"✅ 完成！")
            print(f"="*80)
            print(f"\n📊 最终统计:")
            print(f"  - 找到资源: {len(playlist_records)} 个")
            print(f"  - CSV 文件: {output_file}")
            print(f"  - HTML 文件: {html_path}")
            print(f"\n🌐 请在浏览器中打开 HTML 文件查看结果:")
            print(f"   file://{os.path.abspath(html_path)}")
            
        else:
            print("\n⚠️  未找到任何资源")
            print("   可能的原因:")
            print("   1. LLM 评估返回空响应（需要检查 API）")
            print("   2. 搜索词不够精确")
            print("   3. 网络上确实没有相关资源")
        
        print("\n" + "="*80)
        print("✅ 测试完成！")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 即使出错，也尝试生成 HTML（如果有部分结果）
        if 'playlist_records' in locals() and playlist_records:
            print(f"\n⚠️  虽然出现错误，但已找到 {len(playlist_records)} 个资源，尝试生成 HTML...")
            try:
                output_file = "test_playlists.csv"
                with open(output_file, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=[
                        'grade_level', 'subject', 'chapter_title', 
                        'playlist_url', 'search_query', 'attempt_number', 'reason'
                    ])
                    writer.writeheader()
                    for record in playlist_records:
                        writer.writerow(record.model_dump())
                
                html_file = output_file.replace(".csv", ".html")
                html_path = generate_html(playlist_records, syllabus_data, html_file)
                print(f"✅ HTML 已生成: {html_path}")
            except:
                pass
        
        sys.exit(1)


if __name__ == "__main__":
    main()

