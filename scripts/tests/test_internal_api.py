#!/usr/bin/env python3
"""
测试公司内部API的简单脚本
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

# 从环境变量读取配置
api_key = os.getenv("INTERNAL_API_KEY")
base_url = "https://hk-intra-paas.transsion.com/tranai-proxy/v1"

if not api_key:
    print("❌ 错误: 未找到 INTERNAL_API_KEY 环境变量")
    exit(1)

# 初始化客户端
client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

# 测试调用
print(f"✅ 使用 API: {base_url}")
print(f"✅ API Key: {api_key[:20]}...")
print("\n正在测试 API 调用...\n")

try:
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello! 请用中文回复，并告诉我你的模型名称。"}
        ]
    )
    
    print("✅ API 调用成功！")
    print(f"\n回复: {completion.choices[0].message.content}")
    
except Exception as e:
    print(f"❌ API 调用失败: {str(e)}")
    exit(1)




