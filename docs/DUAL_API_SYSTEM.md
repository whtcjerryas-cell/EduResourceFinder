# 双API系统使用指南

## 概述

系统支持两套LLM API系统，实现自动fallback机制：

1. **公司内部API**（优先使用）
   - Base URL: `https://uat-intra-paas.transsion.com/tranai-proxy/v1`
   - 模型: `gpt-4o`
   - 要求: 需要在内网环境使用
   - 支持: 文本生成、视觉分析

2. **AI Builders API**（备用）
   - Base URL: `https://space.ai-builders.com/backend`
   - 模型: `deepseek`, `gemini-2.5-pro`
   - 要求: 需要外网访问
   - 支持: 文本生成、Tavily搜索

## 工作原理

### Fallback机制

```
调用LLM
  ↓
尝试公司内部API
  ↓
成功？ → 是 → 返回结果
  ↓
  否
  ↓
切换到AI Builders API
  ↓
成功？ → 是 → 返回结果
  ↓
  否 → 抛出异常
```

### 优先级

1. **公司内部API优先**: 如果设置了 `INTERNAL_API_KEY` 且API可用，优先使用
2. **自动Fallback**: 如果公司内部API失败（网络错误、超时等），自动切换到AI Builders API
3. **透明切换**: 对上层代码完全透明，无需修改调用方式

## 配置

### 环境变量

在 `.env` 文件中配置：

```bash
# AI Builders API（必需，备用）
AI_BUILDER_TOKEN=your_ai_builder_token

# 公司内部API（可选，优先使用）
INTERNAL_API_KEY=your_internal_api_key
```

### 依赖安装

确保安装了 `openai` 库（用于公司内部API）：

```bash
pip install openai>=1.0.0
```

或使用requirements文件：

```bash
pip install -r requirements_v3.txt
```

## 使用方式

### 直接使用统一客户端

```python
from llm_client import UnifiedLLMClient

# 初始化（自动检测可用的API）
client = UnifiedLLMClient()

# 调用LLM（自动选择最佳API）
response = client.call_llm(
    prompt="请介绍Python编程语言",
    system_prompt="你是一个专业的编程教育助手。",
    max_tokens=500,
    temperature=0.3,
    model="deepseek"  # 对于公司内部API，会使用gpt-4o
)

print(response)
```

### 使用兼容的AIBuildersClient

现有代码无需修改，`AIBuildersClient` 会自动使用统一客户端：

```python
from search_strategist import AIBuildersClient

# 初始化（内部使用统一客户端）
client = AIBuildersClient()

# 调用方式不变
response = client.call_llm(
    prompt="请介绍Python编程语言",
    system_prompt="你是一个专业的编程教育助手。",
    max_tokens=500,
    temperature=0.3,
    model="deepseek"
)

print(response)
```

## API特性对比

| 特性 | 公司内部API | AI Builders API |
|------|------------|----------------|
| 文本生成 | ✅ gpt-4o | ✅ deepseek, gemini-2.5-pro |
| 视觉分析 | ✅ 支持 | ❌ 不支持 |
| Tavily搜索 | ❌ 不支持 | ✅ 支持 |
| 网络要求 | 内网 | 外网 |
| 成本 | 公司内部 | 按token计费 |

## 测试

运行测试脚本验证双API系统：

```bash
python scripts/test_dual_api_system.py
```

测试脚本会：
1. 检查环境变量配置
2. 测试统一LLM客户端
3. 测试公司内部API（如果可用）
4. 测试AI Builders API
5. 输出测试结果摘要

## 日志

系统会输出详细的日志，包括：

- API选择信息（使用哪个API）
- Fallback信息（如果发生fallback）
- 调用详情（请求/响应）

示例日志：

```
[✅] 公司内部API客户端初始化成功
[✅] AI Builders API客户端初始化成功
[🔄] 尝试使用公司内部API...
[🏢 公司内部API] 开始调用 gpt-4o
[📥 响应] Content: ...
```

如果发生fallback：

```
[⚠️] 公司内部API调用失败: Connection timeout
[🔄] 切换到AI Builders API...
[🌐 AI Builders API] 开始调用 deepseek
[📥 响应] Content: ...
```

## 故障排查

### 问题1: 公司内部API不可用

**症状**: 日志显示 "公司内部API客户端初始化失败"

**可能原因**:
- 不在内网环境
- `INTERNAL_API_KEY` 未设置或错误
- 网络连接问题

**解决方案**:
- 检查是否在内网环境
- 检查 `INTERNAL_API_KEY` 环境变量
- 系统会自动fallback到AI Builders API，无需手动处理

### 问题2: AI Builders API不可用

**症状**: 日志显示 "AI Builders API客户端初始化失败"

**可能原因**:
- `AI_BUILDER_TOKEN` 未设置或错误
- 网络连接问题

**解决方案**:
- 检查 `AI_BUILDER_TOKEN` 环境变量
- 检查网络连接
- 如果公司内部API可用，可以只使用公司内部API

### 问题3: 两个API都失败

**症状**: 抛出异常 "没有可用的API客户端"

**解决方案**:
- 确保至少设置了一个API密钥
- 检查网络连接
- 运行测试脚本诊断问题

## 代码结构

```
llm_client.py                    # 统一LLM客户端
├── InternalAPIClient          # 公司内部API客户端
├── AIBuildersAPIClient        # AI Builders API客户端
└── UnifiedLLMClient          # 统一客户端（带fallback）

search_strategist.py
└── AIBuildersClient           # 兼容性包装器（使用UnifiedLLMClient）

search_engine_v2.py
└── AIBuildersClient           # 兼容性包装器（使用UnifiedLLMClient）
```

## 更新日志

### V3.3.0 (2025-01-XX)

- ✅ 添加公司内部API支持
- ✅ 实现自动fallback机制
- ✅ 保持向后兼容性
- ✅ 添加测试脚本

---

**最后更新**: 2025-01-XX





