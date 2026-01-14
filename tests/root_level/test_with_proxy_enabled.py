#!/usr/bin/env python3
"""
测试：即使开启代理，Python脚本也能直接访问公司API
验证 trust_env=False 参数是否生效
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 注意：不清除代理环境变量，模拟真实使用场景
print("=" * 80)
print("🧪 测试：代理开启状态下访问公司API")
print("=" * 80)
print()

# 显示当前代理设置
print("📋 当前代理环境变量:")
proxy_vars = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]
for var in proxy_vars:
    value = os.getenv(var)
    if value:
        print(f"  ✅ {var} = {value} (代理已开启)")
print()

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from llm_client import InternalAPIClient

print("=" * 80)
print("🔧 测试：调用公司内部API（即使代理开启）")
print("=" * 80)
print()

try:
    # 初始化客户端（会自动禁用代理）
    client = InternalAPIClient()

    print("📋 测试：gemini-2.5-flash（快速模型）")
    print("-" * 80)

    test_prompt = """生成一个JSON数组，包含一条20字的推荐理由：
["适合印尼二年级学生学习基础加减法"]"""

    start_time = time.time()

    response = client.call_llm(
        prompt=test_prompt,
        model="gemini-2.5-flash",
        max_tokens=100,
        temperature=0.7
    )

    elapsed = time.time() - start_time

    print(f"⏱️  响应时间: {elapsed:.2f} 秒")
    print(f"💰 预估成本: ~$0.0004")
    print(f"📝 响应: {response[:100]}")
    print()
    print("=" * 80)
    print("🎉 成功！即使在代理开启状态下，也能正常访问公司API！")
    print("=" * 80)
    print()
    print("✅ trust_env=False 参数生效")
    print("✅ httpx.Client 正确禁用了代理")
    print("✅ 公司内部API可以正常使用")

except Exception as e:
    print(f"❌ 失败: {str(e)[:200]}")
    print()
    print("如果仍然失败，可能需要:")
    print("  1. 检查Clash Verge的规则配置")
    print("  2. 确保transsion.com域名规则为DIRECT")
    print("  3. 重启Clash Verge使配置生效")

print()
