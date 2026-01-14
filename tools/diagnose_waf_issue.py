#!/usr/bin/env python3
"""
诊断公司内部API被WAF拦截的问题
排查方向：
1. 代理设置检查
2. 环境变量检查
3. 网络路由检查
4. DNS解析检查
5. 直接测试API（不使用OpenAI SDK）
6. 请求头对比
"""

import os
import sys
import socket
import requests
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

print("=" * 80)
print("🔍 诊断公司内部API WAF拦截问题")
print("=" * 80)
print()

# ========================================
# 1. 检查环境变量中的代理设置
# ========================================
print("📋 步骤1: 检查代理环境变量")
print("-" * 80)

proxy_vars = [
    "HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
    "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy"
]

has_proxy = False
for var in proxy_vars:
    value = os.getenv(var)
    if value:
        print(f"  ⚠️  {var} = {value}")
        has_proxy = True

if not has_proxy:
    print("  ✅ 未设置代理环境变量（正确）")

print()

# ========================================
# 2. 检查Python请求库的代理设置
# ========================================
print("📋 步骤2: 检查requests/urllib代理设置")
print("-" * 80)

import requests.utils
proxy_settings = requests.utils.getproxies()
if proxy_settings:
    print("  ⚠️  检测到代理设置:")
    for key, value in proxy_settings.items():
        print(f"    {key}: {value}")
else:
    print("  ✅ requests库未使用代理")

print()

# ========================================
# 3. DNS解析检查
# ========================================
print("📋 步骤3: DNS解析检查")
print("-" * 80)

api_domain = "hk-intra-paas.transsion.com"
try:
    ip_address = socket.gethostbyname(api_domain)
    print(f"  ✅ DNS解析成功: {api_domain} → {ip_address}")

    # 检查是否是内网IP
    private_ranges = [
        ("10.", "10.0.0.0/8"),
        ("172.16.", "172.16.0.0/12"),
        ("192.168.", "192.168.0.0/16"),
    ]

    is_private = False
    for prefix, cidr in private_ranges:
        if ip_address.startswith(prefix):
            print(f"  ✅ 解析到内网IP ({cidr}): {ip_address}")
            is_private = True
            break

    if not is_private:
        print(f"  ⚠️  解析到公网IP: {ip_address}")
        print(f"  💡 这可能不是内网地址！")

except Exception as e:
    print(f"  ❌ DNS解析失败: {e}")

print()

# ========================================
# 4. 网络连通性测试
# ========================================
print("📋 步骤4: 网络连通性测试")
print("-" * 80)

base_url = "https://hk-intra-paas.transsion.com/tranai-proxy/v1"

# 测试4: 不使用代理
print("  测试1: 直接连接（不使用代理）")
try:
    response = requests.get(
        f"{base_url}/models",
        timeout=10,
        proxies={"http": None, "https": None},  # 强制不使用代理
        headers={"User-Agent": "Mozilla/5.0"}
    )
    print(f"    ✅ 连接成功！状态码: {response.status_code}")
    if response.status_code == 405:
        print(f"    ⚠️  返回405（WAF拦截）")
except requests.exceptions.Timeout:
    print(f"    ❌ 连接超时")
except requests.exceptions.ConnectionError as e:
    print(f"    ❌ 连接失败: {e}")
except Exception as e:
    print(f"    ❌ 其他错误: {e}")

print()

# 测试5: 使用代理（如果设置了）
if has_proxy:
    print("  测试2: 使用系统代理")
    try:
        response = requests.get(
            f"{base_url}/models",
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        print(f"    ✅ 连接成功！状态码: {response.status_code}")
    except Exception as e:
        print(f"    ❌ 连接失败: {e}")

    print()

# ========================================
# 5. 测试OpenAI SDK调用
# ========================================
print("📋 步骤5: 测试OpenAI SDK调用（查看实际请求头）")
print("-" * 80)

try:
    from openai import OpenAI

    api_key = os.getenv("INTERNAL_API_KEY")
    if not api_key:
        print("  ⚠️  未设置 INTERNAL_API_KEY 环境变量")
    else:
        print(f"  ✅ API Key已设置 (长度: {len(api_key)})")

        # 创建客户端，禁用代理
        import httpx
        timeout_config = httpx.Timeout(
            connect=10.0,
            read=30.0,
            write=10.0,
            pool=10.0
        )

        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout_config,
            http_client=httpx.Client(
                timeout=timeout_config,
                proxy=None  # 禁用代理（httpx使用proxy参数）
            )
        )

        print("  🔄 发送测试请求...")
        try:
            # 尝试列出模型
            models = client.models.list()
            print(f"  ✅ API调用成功！找到 {len(models.data)} 个模型")
            for model in models.data[:5]:
                print(f"    - {model.id}")
        except Exception as e:
            error_str = str(e)
            print(f"  ❌ API调用失败: {error_str[:200]}")

            if "405" in error_str:
                print()
                print("  🔍 WAF拦截详细分析:")
                print(f"    - 错误类型: APIStatusError")
                print(f"    - 可能原因:")
                print(f"      1. User-Agent被识别为自动化工具")
                print(f"      2. 请求头缺少必要的浏览器特征")
                print(f"      3. IP地址不在白名单")
                print(f"      4. 需要VPN或内网认证")

except ImportError:
    print("  ⚠️  未安装OpenAI SDK")

print()

# ========================================
# 6. 对比请求头
# ========================================
print("📋 步骤6: 请求头对比")
print("-" * 80)

print("  浏览器请求头示例:")
print("    User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
print("    Accept: */*")
print("    Accept-Language: zh-CN,zh;q=0.9")
print("    Connection: keep-alive")
print()

print("  OpenAI SDK默认请求头:")
print("    User-Agent: openai/Python (可能被WAF识别)")
print("    Authorization: Bearer <token>")
print("    Content-Type: application/json")
print()

# ========================================
# 7. 解决方案建议
# ========================================
print("=" * 80)
print("💡 解决方案建议")
print("=" * 80)
print()

solutions = [
    {
        "优先级": "🔥 高",
        "方案": "添加自定义User-Agent",
        "说明": "在OpenAI客户端中添加浏览器类型的User-Agent",
        "代码": """
http_client=httpx.Client(
    headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
)
        """
    },
    {
        "优先级": "🔥 高",
        "方案": "确认内网连接",
        "说明": "确认你确实在内网环境，检查VPN状态",
        "检查": "运行命令: ping hk-intra-paas.transsion.com"
    },
    {
        "优先级": "⚡ 中",
        "方案": "添加内网IP白名单",
        "说明": "联系API管理员，将你的IP加入白名单",
        "联系人": "API管理员或IT部门"
    },
    {
        "优先级": "⚡ 中",
        "方案": "使用AI Builders API作为备用",
        "说明": "在公司内部API无法使用时，自动切换到AI Builders",
        "状态": "✅ 已实现"
    },
    {
        "优先级": "💡 低",
        "方案": "联系IT部门确认WAF规则",
        "说明": "询问WAF拦截的具体原因和如何解决",
        "提供": "Trace ID和请求时间"
    }
]

for i, solution in enumerate(solutions, 1):
    print(f"{i}. {solution['优先级']} {solution['方案']}")
    print(f"   说明: {solution['说明']}")
    if '代码' in solution:
        print(f"   代码:{solution['代码']}")
    if '检查' in solution:
        print(f"   检查: {solution['检查']}")
    if '联系人' in solution:
        print(f"   联系: {solution['联系人']}")
    if '状态' in solution:
        print(f"   状态: {solution['状态']}")
    print()

# ========================================
# 8. 下一步行动
# ========================================
print("=" * 80)
print("🎯 建议的下一步行动")
print("=" * 80)
print()
print("1. 立即检查: 确认你是否在内网环境（不是VPN）")
print("2. 运行命令: curl -I https://hk-intra-paas.transsion.com/tranai-proxy/v1/models")
print("3. 如果curl也返回405，说明是网络环境问题")
print("4. 如果curl成功，说明是OpenAI SDK的问题（需要修改请求头）")
print()
