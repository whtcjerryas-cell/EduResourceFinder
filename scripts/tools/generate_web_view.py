#!/usr/bin/env python3
"""
生成搜索结果网页展示
"""

import os
import json
import csv
from typing import List, Dict, Any
from pathlib import Path


def load_playlist_results(csv_file: str) -> List[Dict[str, Any]]:
    """
    从 CSV 文件加载播放列表结果
    
    Args:
        csv_file: CSV 文件路径
    
    Returns:
        播放列表记录列表
    """
    if not os.path.exists(csv_file):
        return []
    
    records = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    
    return records


def load_knowledge_points(json_file: str) -> Dict[str, Any]:
    """
    加载知识点数据
    
    Args:
        json_file: JSON 文件路径
    
    Returns:
        知识点数据字典
    """
    if not os.path.exists(json_file):
        return {}
    
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def group_by_chapter(records: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    按章节分组播放列表记录
    
    Args:
        records: 播放列表记录列表
    
    Returns:
        按章节分组的字典
    """
    grouped = {}
    for record in records:
        key = f"{record['grade_level']}_{record['subject']}_{record['chapter_title']}"
        if key not in grouped:
            grouped[key] = {
                'grade_level': record['grade_level'],
                'subject': record['subject'],
                'chapter_title': record['chapter_title'],
                'playlists': []
            }
        grouped[key]['playlists'].append(record)
    
    return grouped


def generate_html(playlist_records: List[Dict[str, Any]], 
                  knowledge_points_data: Dict[str, Any] = None,
                  output_file: str = "playlist_results.html") -> str:
    """
    生成 HTML 网页（表格形式）
    
    Args:
        playlist_records: 播放列表记录列表
        knowledge_points_data: 知识点数据（可选）
        output_file: 输出文件路径
    
    Returns:
        HTML 文件路径
    """
    # 统计信息
    total_playlists = len(playlist_records)
    
    # 生成 HTML（表格形式）
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>印尼 K12 数学视频播放列表搜索结果</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header .subtitle {{
            font-size: 1em;
            opacity: 0.9;
        }}
        
        .stats {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}
        
        .stat-card {{
            background: rgba(255,255,255,0.2);
            padding: 10px 20px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }}
        
        .stat-number {{
            font-size: 1.8em;
            font-weight: bold;
        }}
        
        .stat-label {{
            font-size: 0.85em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 30px;
            overflow-x: auto;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            font-size: 0.95em;
        }}
        
        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        th {{
            padding: 15px 12px;
            text-align: left;
            font-weight: 600;
            font-size: 0.95em;
            white-space: nowrap;
        }}
        
        th:first-child {{
            border-top-left-radius: 8px;
        }}
        
        th:last-child {{
            border-top-right-radius: 8px;
        }}
        
        tbody tr {{
            border-bottom: 1px solid #e0e0e0;
            transition: background-color 0.2s;
        }}
        
        tbody tr:hover {{
            background-color: #f5f5f5;
        }}
        
        tbody tr:last-child {{
            border-bottom: none;
        }}
        
        td {{
            padding: 15px 12px;
            vertical-align: top;
        }}
        
        .country {{
            font-weight: 600;
            color: #333;
            white-space: nowrap;
        }}
        
        .subject {{
            color: #555;
            white-space: nowrap;
        }}
        
        .grade {{
            color: #666;
            white-space: nowrap;
        }}
        
        .url {{
            max-width: 400px;
            word-break: break-all;
        }}
        
        .url a {{
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }}
        
        .url a:hover {{
            color: #764ba2;
            text-decoration: underline;
        }}
        
        .attempt {{
            text-align: center;
            white-space: nowrap;
        }}
        
        .attempt-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
            background: #d4edda;
            color: #155724;
        }}
        
        .chapter {{
            color: #555;
            white-space: nowrap;
        }}
        
        .resource-type {{
            text-align: center;
            white-space: nowrap;
        }}
        
        .type-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        
        .type-badge.type-playlist {{
            background: #d4edda;
            color: #155724;
        }}
        
        .type-badge.type-channel {{
            background: #d1ecf1;
            color: #0c5460;
        }}
        
        .type-badge.type-video {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .search-query {{
            max-width: 200px;
            color: #666;
            font-size: 0.85em;
            word-break: break-all;
        }}
        
        .reason {{
            max-width: 300px;
            color: #666;
            font-size: 0.9em;
            line-height: 1.5;
        }}
        
        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }}
        
        .empty-state-icon {{
            font-size: 4em;
            margin-bottom: 20px;
        }}
        
        @media (max-width: 768px) {{
            .content {{
                padding: 15px;
            }}
            
            table {{
                font-size: 0.85em;
            }}
            
            th, td {{
                padding: 10px 8px;
            }}
            
            .url {{
                max-width: 200px;
            }}
            
            .reason {{
                max-width: 150px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 印尼 K12 数学视频播放列表</h1>
            <div class="subtitle">搜索结果展示</div>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{total_playlists}</div>
                    <div class="stat-label">播放列表</div>
                </div>
            </div>
        </div>
        
        <div class="content">
"""
    
    # 如果没有结果，显示空状态
    if not playlist_records:
        html_content += """
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <h2>暂无搜索结果</h2>
                <p>请先运行搜索脚本生成播放列表数据</p>
            </div>
        """
    else:
        # 生成表格
        html_content += """
            <table>
                <thead>
                    <tr>
                        <th>国家</th>
                        <th>学科</th>
                        <th>年级</th>
                        <th>章节</th>
                        <th>资源类型</th>
                        <th>URL 地址</th>
                        <th>搜索次数</th>
                        <th>搜索词</th>
                        <th>理由</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        for record in playlist_records:
            country = "印尼"  # 固定为国家
            subject = record.get('subject', '')
            grade_level = record.get('grade_level', '')
            chapter_title = record.get('chapter_title', '')
            url = record.get('playlist_url', '')
            attempt = record.get('attempt_number', '')
            search_query = record.get('search_query', '')
            reason = record.get('reason', f"匹配章节: {chapter_title}")
            
            # 判断资源类型
            resource_type = "播放列表/频道"
            if "Video Source" in reason or ("youtube.com/watch" in url and "list=" not in url):
                resource_type = "单集视频（系列）"
            elif "playlist" in url.lower() or "list=" in url.lower():
                resource_type = "播放列表"
            elif "channel" in url.lower() or "/c/" in url.lower() or "/@" in url.lower():
                resource_type = "频道"
            
            # 资源类型样式
            type_badge_class = "type-playlist" if resource_type == "播放列表" else "type-channel" if resource_type == "频道" else "type-video"
            
            html_content += f"""
                    <tr>
                        <td class="country">{country}</td>
                        <td class="subject">{subject}</td>
                        <td class="grade">{grade_level}</td>
                        <td class="chapter">{chapter_title}</td>
                        <td class="resource-type"><span class="type-badge {type_badge_class}">{resource_type}</span></td>
                        <td class="url"><a href="{url}" target="_blank">{url}</a></td>
                        <td class="attempt"><span class="attempt-badge">第 {attempt} 次</span></td>
                        <td class="search-query">{search_query[:50]}...</td>
                        <td class="reason">{reason}</td>
                    </tr>
"""
        
        html_content += """
                </tbody>
            </table>
"""
    
    html_content += """
        </div>
    </div>
</body>
</html>
"""
    
    # 保存 HTML 文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_file


def main():
    """主函数"""
    import sys
    
    # 确定输入文件
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        # 默认查找 CSV 文件
        csv_file = "/Users/shmiwanghao8/Desktop/education/Indonesia/Knowledge Point/5. Final Panduan Mata Pelajaran Matematika_12_09_2025_Revisi 3_30-58_playlists.csv"
    
    # 查找对应的知识点 JSON 文件
    json_file = csv_file.replace("_playlists.csv", "_knowledge_points.json")
    
    print(f"📖 读取播放列表数据: {csv_file}")
    playlist_records = load_playlist_results(csv_file)
    
    knowledge_points_data = None
    if os.path.exists(json_file):
        print(f"📚 读取知识点数据: {json_file}")
        knowledge_points_data = load_knowledge_points(json_file)
    
    if not playlist_records:
        print("⚠️ 未找到播放列表数据，将生成空页面")
    
    # 生成 HTML
    output_file = csv_file.replace(".csv", ".html")
    print(f"\n🎨 生成网页: {output_file}")
    html_path = generate_html(playlist_records, knowledge_points_data, output_file)
    
    print(f"\n✅ 完成！")
    print(f"📊 统计:")
    print(f"   - 播放列表数量: {len(playlist_records)}")
    print(f"   - 输出文件: {html_path}")
    print(f"\n🌐 请在浏览器中打开: file://{os.path.abspath(html_path)}")


if __name__ == "__main__":
    main()

