#!/usr/bin/env python3
"""
测试国家发现功能 - 伊拉克
"""

import requests
import json

print("=" * 80)
print("🧪 测试：伊拉克(Iraq)国家发现")
print("=" * 80)
print()

# 测试请求
request_data = {
    "country_name": "Iraq"
}

print(f"📤 请求:")
print(f"  国家名称: {request_data['country_name']}")
print()

print("🔍 正在发送请求...")
response = requests.post(
    "http://localhost:5001/api/discover_country",
    json=request_data,
    timeout=120,
    headers={"Content-Type": "application/json"}
)

print(f"⏱️  响应时间: {response.elapsed.total_seconds():.2f} 秒")
print()

if response.status_code != 200:
    print(f"❌ 请求失败，状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    exit(1)

result = response.json()

print(f"✅ 请求成功!")
print()

if not result.get('success'):
    print(f"❌ 国家发现失败:")
    print(f"   消息: {result.get('message', '未知错误')}")
    exit(1)

profile = result.get('profile', {})

print("=" * 80)
print("📋 提取的国家配置:")
print("=" * 80)
print()

print(f"✅ 国家代码: {profile.get('country_code', 'N/A')}")
print(f"✅ 国家名称: {profile.get('country_name', 'N/A')}")
print(f"✅ 中文名称: {profile.get('country_name_zh', 'N/A')}")
print(f"✅ 语言代码: {profile.get('language_code', 'N/A')}")
print(f"✅ 年级数量: {len(profile.get('grades', []))}")
print(f"✅ 学科数量: {len(profile.get('subjects', []))}")
print(f"✅ 域名数量: {len(profile.get('domains', []))}")
print()

# 验证国家代码
country_code = profile.get('country_code', '')
if country_code == 'IQ':
    print("✅ 国家代码正确! (IQ = Iraq)")
else:
    print(f"⚠️  国家代码可能不正确: {country_code} (期望: IQ)")

print()
print("=" * 80)
