#!/usr/bin/env python3
"""
测试：完全禁用代理后的API访问
"""

import os
import sys

# ========================================
# 步骤1: 完全清除代理环境变量
# ========================================
proxy_vars = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
              "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy"]

print("🔧 清除所有代理环境变量...")
for var in proxy_vars:
    if var in os.environ:
        del os.environ[var]
        print(f"  ✅ 已删除: {var}")

# 也设置为空，防止代码中读取
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""
os.environ["http_proxy"] = ""
os.environ["https_proxy"] = ""

print("\n✅ 代理已完全禁用\n")

# ========================================
# 步骤2: 验证没有代理
# ========================================
print("📋 验证代理设置:")
print(f"  HTTP_PROXY = '{os.getenv('HTTP_PROXY')}'")
print(f"  HTTPS_PROXY = '{os.getenv('HTTPS_PROXY')}'")
print()

# ========================================
# 步骤3: 测试公司内部API
# ========================================
from dotenv import load_dotenv
import requests

load_dotenv()

api_key = os.getenv("INTERNAL_API_KEY")
base_url = "https://hk-intra-paas.transsion.com/tranai-proxy/v1"

print("=" * 80)
print("🧪 测试公司内部API（无代理）")
print("=" * 80)
print()

# 测试使用 gemini-2.5-flash（快速模型）
print("📋 测试模型: gemini-2.5-flash")
print("-" * 80)

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
}

data = {
    "model": "gemini-2.5-flash",
    "messages": [
        {"role": "user", "content": "生成一个JSON数组: ['测试推荐理由']"}
    ],
    "max_tokens": 50,
    "temperature": 0.7
}

import time
start_time = time.time()

try:
    # 强制不使用代理
    proxies = {"http": None, "https": None}

    response = requests.post(
        f"{base_url}/chat/completions",
        headers=headers,
        json=data,
        proxies=proxies,  # 强制不使用代理
        timeout=30
    )

    elapsed = time.time() - start_time

    print(f"⏱️  响应时间: {elapsed:.2f} 秒")
    print(f"📊 状态码: {response.status_code}")

    if response.status_code == 200:
        print(f"✅ 成功！")
        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        print(f"📝 响应: {content}")
        print()
        print("🎉 恭喜！公司内部API可以正常使用！")
    else:
        print(f"❌ 失败")
        print(f"响应: {response.text[:300]}")

        if "405" in response.text:
            print()
            print("⚠️  仍然被WAF拦截")
            print("可能的原因:")
            print("  1. 系统代理设置（环境变量之外）")
            print("  2. 需要在macOS系统设置中关闭代理")
            print("  3. WAF规则最近更新了")

except Exception as e:
    print(f"❌ 错误: {e}")

print()
print("=" * 80)
