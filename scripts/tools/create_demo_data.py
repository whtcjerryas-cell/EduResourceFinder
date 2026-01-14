#!/usr/bin/env python3
"""
创建演示数据用于测试网页展示
"""

import csv
import os

def create_demo_csv():
    """创建演示 CSV 数据"""
    demo_data = [
        {
            'grade_level': 'Fase A (Kelas 1-2)',
            'subject': 'Matematika',
            'chapter_title': 'Bilangan',
            'playlist_url': 'https://www.youtube.com/playlist?list=PL1234567890',
            'search_query': 'Playlist Matematika Kelas 1-2 Bilangan full video',
            'attempt_number': '1',
            'reason': '匹配章节: Bilangan | 找到高质量播放列表，包含完整的数字学习视频'
        },
        {
            'grade_level': 'Fase A (Kelas 1-2)',
            'subject': 'Matematika',
            'chapter_title': 'Bilangan',
            'playlist_url': 'https://www.youtube.com/playlist?list=PL0987654321',
            'search_query': 'Kumpulan video pembelajaran Matematika Kelas 1-2 Bilangan',
            'attempt_number': '2',
            'reason': '匹配章节: Bilangan | 第二次尝试找到的补充资源'
        },
        {
            'grade_level': 'Fase A (Kelas 1-2)',
            'subject': 'Matematika',
            'chapter_title': 'Aljabar',
            'playlist_url': 'https://www.youtube.com/playlist?list=PL1122334455',
            'search_query': 'Playlist Matematika Kelas 1-2 Aljabar full video',
            'attempt_number': '1',
            'reason': '匹配章节: Aljabar | 包含代数基础概念的完整课程'
        },
        {
            'grade_level': 'Fase A (Kelas 1-2)',
            'subject': 'Matematika',
            'chapter_title': 'Pengukuran',
            'playlist_url': 'https://www.youtube.com/playlist?list=PL5566778899',
            'search_query': 'Video pembelajaran Matematika Kelas 1-2 Pengukuran lengkap',
            'attempt_number': '1',
            'reason': '匹配章节: Pengukuran | 测量主题的完整视频集合'
        },
        {
            'grade_level': 'Fase A (Kelas 1-2)',
            'subject': 'Matematika',
            'chapter_title': 'Geometri',
            'playlist_url': 'https://www.youtube.com/playlist?list=PL9988776655',
            'search_query': 'Matematika Kelas 1-2 Geometri playlist',
            'attempt_number': '1',
            'reason': '匹配章节: Geometri | 几何形状和空间概念的系列视频'
        },
        {
            'grade_level': 'Fase A (Kelas 1-2)',
            'subject': 'Matematika',
            'chapter_title': 'Analisis Data dan Peluang',
            'playlist_url': 'https://www.youtube.com/playlist?list=PL4433221100',
            'search_query': 'Playlist lengkap Matematika Kelas 1-2 Analisis Data',
            'attempt_number': '2',
            'reason': '匹配章节: Analisis Data dan Peluang | 数据分析和概率的完整课程'
        }
    ]
    
    output_file = "/Users/shmiwanghao8/Desktop/education/Indonesia/Knowledge Point/5. Final Panduan Mata Pelajaran Matematika_12_09_2025_Revisi 3_30-58_playlists.csv"
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'grade_level', 'subject', 'chapter_title', 
            'playlist_url', 'search_query', 'attempt_number', 'reason'
        ])
        writer.writeheader()
        writer.writerows(demo_data)
    
    print(f"✅ 已创建演示数据: {output_file}")
    print(f"📊 共 {len(demo_data)} 条记录")
    
    return output_file

if __name__ == "__main__":
    create_demo_csv()

