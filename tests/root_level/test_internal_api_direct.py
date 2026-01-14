#!/usr/bin/env python3
"""
直接测试公司内部API，不使用OpenAI SDK
找出WAF拦截的真正原因
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# 清除代理
for key in list(os.environ.keys()):
    if 'proxy' in key.lower():
        del os.environ[key]

print("=" * 80)
print("🔍 直接测试公司内部API（不使用OpenAI SDK）")
print("=" * 80)
print()

api_key = os.getenv("INTERNAL_API_KEY")
base_url = "https://hk-intra-paas.transsion.com/tranai-proxy/v1"

# 测试1: GET请求 - /models
print("📋 测试1: GET /models (列出模型)")
print("-" * 80)

headers1 = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

try:
    response = requests.get(
        f"{base_url}/models",
        headers=headers1,
        timeout=10
    )
    print(f"状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print(f"响应内容: {response.text[:200]}")
except Exception as e:
    print(f"错误: {e}")

print()

# 测试2: POST请求 - /chat/completions (使用真实的API key)
print("📋 测试2: POST /chat/completions (使用API key)")
print("-" * 80)

headers2 = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

data = {
    "model": "gpt-4o",
    "messages": [
        {"role": "user", "content": "Hello"}
    ],
    "max_tokens": 10
}

try:
    response = requests.post(
        f"{base_url}/chat/completions",
        headers=headers2,
        json=data,
        timeout=30
    )
    print(f"状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")

    if response.status_code == 200:
        print(f"✅ 成功！API调用正常")
        print(f"响应: {response.text}")
    else:
        print(f"响应内容: {response.text[:500]}")

except Exception as e:
    print(f"错误: {e}")

print()

# 测试3: 检查响应头中的关键信息
print("📋 测试3: 分析WAF响应特征")
print("-" * 80)

try:
    response = requests.get(
        f"{base_url}/models",
        timeout=10
    )

    # 检查WAF特征
    waf_indicators = {
        "服务器": response.headers.get("Server", ""),
        "Set-Cookie": response.headers.get("Set-Cookie", ""),
        "状态码": response.status_code,
        "Content-Type": response.headers.get("Content-Type", ""),
    }

    print("WAF特征分析:")
    for key, value in waf_indicators.items():
        print(f"  {key}: {value}")

    # 判断是否是WAF
    if response.status_code in [403, 405]:
        print()
        print("⚠️  确认被WAF拦截！")
        print()
        print("可能的原因:")
        print("  1. IP地址不在白名单")
        print("  2. User-Agent被识别")
        print("  3. 需要内网认证或VPN")
        print("  4. API Key权限不足")
        print("  5. 请求频率限制")
        print()
        print("建议:")
        print("  1. 联系API管理员确认访问权限")
        print("  2. 确认是否需要连接公司内网")
        print("  3. 检查API Key是否有效")
        print("  4. 询问WAF白名单配置")

except Exception as e:
    print(f"错误: {e}")

print()
print("=" * 80)
