#!/usr/bin/env python3
"""
测试Excel导出功能
"""

import requests
import json

BASE_URL = "http://localhost:5004"

def test_excel_export():
    """测试Excel导出功能"""
    print("="*60)
    print("测试Excel导出功能")
    print("="*60)

    # 准备测试数据
    export_data = {
        "results": [
            {
                "title": "一年级数学课程",
                "url": "https://example.com/video1",
                "snippet": "这是一年级数学课程，涵盖基本加减法",
                "score": 9.5,
                "recommendation_reason": "内容完整，适合一年级学生学习",
                "resource_type": "视频",
                "search_engine": "Google"
            },
            {
                "title": "小学数学练习题",
                "url": "https://example.com/video2",
                "snippet": "包含大量练习题和讲解",
                "score": 8.8,
                "recommendation_reason": "练习丰富，有助于巩固知识",
                "resource_type": "播放列表",
                "search_engine": "Tavily"
            }
        ],
        "search_params": {
            "country": "CN",
            "grade": "Kelas 1",
            "subject": "Matematika"
        }
    }

    try:
        print("发送导出请求...")
        response = requests.post(
            f"{BASE_URL}/api/export_excel",
            json=export_data,
            timeout=30
        )

        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")

        if response.status_code == 200:
            # 检查是否是Excel文件
            content_type = response.headers.get('Content-Type', '')
            print(f"Content-Type: {content_type}")

            if 'excel' in content_type or 'spreadsheet' in content_type or 'xlsx' in content_type:
                # 保存Excel文件
                filename = 'test_export.xlsx'
                with open(filename, 'wb') as f:
                    f.write(response.content)

                file_size = len(response.content)
                print(f"✅ Excel导出成功！")
                print(f"   文件大小: {file_size} 字节")
                print(f"   已保存: {filename}")
                return True
            else:
                print(f"❌ 响应不是Excel格式")
                print(f"   Content-Type: {content_type}")
                return False
        else:
            print(f"❌ 导出失败")
            try:
                error_data = response.json()
                print(f"   错误信息: {error_data}")
            except:
                print(f"   响应内容: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ 导出测试异常: {str(e)}")
        return False


if __name__ == '__main__':
    success = test_excel_export()
    if success:
        print("\n🎉 Excel导出功能测试通过！")
    else:
        print("\n⚠️  Excel导出功能需要修复")
