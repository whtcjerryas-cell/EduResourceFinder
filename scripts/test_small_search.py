#!/usr/bin/env python3
"""
小范围测试脚本 - 验证搜索功能可靠性
只测试1-2个章节，快速验证代码是否正常工作
"""

import json
import os
import sys

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from search_strategist import SearchStrategist, AIBuildersClient


def create_test_data():
    """创建测试用的知识点数据（只包含1-2个章节）"""
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
                "chapter_title": "Bilangan",
                "topic_title": "Penjumlahan Bilangan",
                "description": "Melakukan penjumlahan bilangan sederhana"
            },
            {
                "grade_level": "Fase A (Kelas 1-2)",
                "subject": "Matematika",
                "chapter_title": "Geometri",
                "topic_title": "Mengenal Bangun Datar",
                "description": "Mengenal bentuk-bentuk bangun datar sederhana"
            },
            {
                "grade_level": "Fase A (Kelas 1-2)",
                "subject": "Matematika",
                "chapter_title": "Geometri",
                "topic_title": "Mengenal Bangun Ruang",
                "description": "Mengenal bentuk-bentuk bangun ruang sederhana"
            }
        ]
    }
    
    test_file = "test_knowledge_points.json"
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已创建测试数据文件: {test_file}")
    print(f"📊 包含 {len(test_data['knowledge_points'])} 个知识点")
    print(f"📚 章节: Bilangan (3个知识点), Geometri (2个知识点)")
    
    return test_file


def main():
    """主函数"""
    print("="*80)
    print("🧪 小范围搜索功能测试")
    print("="*80)
    print("\n📝 测试目标:")
    print("  1. 验证 Tavily 搜索接口是否正常工作")
    print("  2. 验证搜索结果解析是否正确")
    print("  3. 验证 LLM 评估功能是否正常")
    print("  4. 验证输出结果的质量和可靠性")
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
        
        # 执行搜索（只搜索2个章节）
        print("\n[步骤 4] 开始执行搜索...")
        print("⚠️  注意: 这将调用真实的 API，可能需要一些时间")
        print("   每个章节最多尝试5次搜索，找到高质量资源后停止\n")
        
        playlist_records = strategist.search_for_playlists(syllabus_data)
        
        # 显示结果
        print("\n" + "="*80)
        print("📊 搜索结果统计")
        print("="*80)
        print(f"✅ 找到的播放列表数量: {len(playlist_records)}")
        
        if playlist_records:
            print("\n📋 详细结果:")
            for i, record in enumerate(playlist_records, 1):
                print(f"\n{i}. 章节: {record.chapter_title}")
                print(f"   URL: {record.playlist_url}")
                print(f"   搜索词: {record.search_query}")
                print(f"   尝试次数: {record.attempt_number}")
                print(f"   理由: {record.reason[:100]}...")
            
            # 保存结果
            output_file = test_file.replace("_knowledge_points.json", "_playlists.csv")
            output_file = "test_playlists.csv"
            
            import csv
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'grade_level', 'subject', 'chapter_title', 
                    'playlist_url', 'search_query', 'attempt_number', 'reason'
                ])
                writer.writeheader()
                for record in playlist_records:
                    writer.writerow(record.model_dump())
            
            print(f"\n💾 结果已保存到: {output_file}")
            
            # 生成 HTML 网页
            print(f"\n[步骤 5] 生成 HTML 网页...")
            try:
                from generate_web_view import generate_html
                html_file = output_file.replace(".csv", ".html")
                html_path = generate_html(playlist_records, syllabus_data, html_file)
                print(f"✅ HTML 网页已生成: {html_path}")
                print(f"🌐 请在浏览器中打开: file://{os.path.abspath(html_path)}")
            except Exception as e:
                print(f"⚠️  HTML 生成失败: {str(e)}")
                import traceback
                traceback.print_exc()
            
            # 结果质量评估
            print("\n" + "="*80)
            print("📈 结果质量评估")
            print("="*80)
            
            youtube_count = sum(1 for r in playlist_records if "youtube.com" in r.playlist_url)
            playlist_count = sum(1 for r in playlist_records if "playlist" in r.playlist_url or "list=" in r.playlist_url)
            
            print(f"✅ YouTube 链接: {youtube_count}/{len(playlist_records)}")
            print(f"✅ 播放列表链接: {playlist_count}/{len(playlist_records)}")
            
            if playlist_count > 0:
                print("\n🎉 测试成功！找到了播放列表资源")
            elif youtube_count > 0:
                print("\n⚠️  找到了 YouTube 视频，但可能不是播放列表")
            else:
                print("\n⚠️  未找到 YouTube 播放列表，可能需要调整搜索策略")
        else:
            print("\n⚠️  未找到任何播放列表")
            print("   可能的原因:")
            print("   1. 搜索词不够精确")
            print("   2. 网络上确实没有相关资源")
            print("   3. LLM 评估标准过于严格")
        
        print("\n" + "="*80)
        print("✅ 测试完成！")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 清理测试文件（可选）
        # if os.path.exists(test_file):
        #     os.remove(test_file)
        pass


if __name__ == "__main__":
    main()

