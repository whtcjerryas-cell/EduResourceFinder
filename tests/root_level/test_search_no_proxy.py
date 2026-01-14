#!/usr/bin/env python3
"""测试搜索功能（无代理）"""

import requests
import json

# 测试搜索API
url = "http://localhost:5001/api/search"
payload = {
    "country": "ID",
    "grade": "Kelas 1",
    "subject": "Matematika",
    "topic": "penjumlahan"
}

print("=" * 60)
print("测试搜索功能（无代理）")
print("=" * 60)
print(f"\n请求参数: {json.dumps(payload, indent=2, ensure_ascii=False)}")

try:
    print("\n正在发送请求...")
    response = requests.post(url, json=payload, timeout=30)

    print(f"\n状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"✅ 搜索成功!")
            print(f"找到 {data.get('total_count', 0)} 条结果")
            print(f"搜索引擎: {', '.join(data.get('engines_used', []))}")
            print(f"\n前3条结果:")
            for i, result in enumerate(data.get('results', [])[:3], 1):
                print(f"  {i}. {result.get('title', 'N/A')[:60]}...")
        else:
            print(f"❌ 搜索失败: {data.get('message', 'Unknown error')}")
    else:
        print(f"❌ HTTP错误: {response.status_code}")
        print(f"响应: {response.text[:500]}")

except Exception as e:
    print(f"❌ 请求异常: {str(e)}")

print("\n" + "=" * 60)
