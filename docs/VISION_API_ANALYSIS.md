# AI Builders API 视觉模型支持深度分析

**分析日期**: 2025-12-29  
**API 地址**: https://space.ai-builders.com/backend/openapi.json

---

## 📋 分析概述

### 用户的怀疑
用户怀疑 **Gemini 2.5 Pro 应该支持视觉输入**，因为：
1. Google Gemini 2.5 Pro 原生支持多模态输入（文本、图像、音频、视频）
2. API 描述中提到 "Direct access to Google's Gemini model"
3. 之前的测试可能没有尝试所有可能的方法

### 分析目标
验证 AI Builders API 是否真的不支持视觉输入，还是 Schema 定义与实现不一致。

---

## 🔍 OpenAPI Schema 分析

### ChatCompletionMessage Schema

根据 OpenAPI 规范，`ChatCompletionMessage` 的定义如下：

```json
{
  "properties": {
    "role": {
      "type": "string",
      "enum": ["system", "user", "assistant", "tool"]
    },
    "content": {
      "anyOf": [
        {"type": "string"},
        {"type": "null"}
      ]
    }
  }
}
```

**关键发现**：
- ✅ `content` 字段类型：`string | null`
- ❌ **不支持数组格式**（如 OpenAI 的多模态格式：`[{type: "text"}, {type: "image_url"}]`）
- ⚠️ Schema 中允许 `additionalProperties: true`，但这不意味着 `content` 可以接受数组

### ChatCompletionRequest Schema

```json
{
  "properties": {
    "model": {
      "type": "string",
      "description": "Accepts `deepseek`, `supermind-agent-v1`, `gemini-2.5-pro`, `gpt-5`, or `grok-4-fast`"
    },
    "messages": {
      "type": "array",
      "items": {"$ref": "#/components/schemas/ChatCompletionMessage"}
    }
  },
  "additionalProperties": true
}
```

**关键发现**：
- ✅ 支持 `gemini-2.5-pro` 模型
- ⚠️ 允许 `additionalProperties: true`，但这是针对请求对象本身，不是针对 `content` 字段

---

## 🧪 之前的测试结果回顾

根据 `docs/VISION_MODELS_TEST_REPORT.md`，之前的测试结果：

| 模型 | 数组格式 | Base64字符串格式 | 支持视觉 |
|------|---------|-----------------|---------|
| **Gemini 2.5 Pro** | ❌ HTTP 422 | ⚠️ HTTP 200（仅换行符） | ❌ 否 |
| **Grok-4-Fast** | ❌ HTTP 422 | ❌ HTTP 400 | ❌ 否 |
| **GPT-5** | ❌ HTTP 422 | ⚠️ HTTP 200（空响应） | ❌ 否 |

### 测试方法1: 数组格式（OpenAI标准）
```json
{
  "role": "user",
  "content": [
    {"type": "text", "text": "请描述这张图片"},
    {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
  ]
}
```
**结果**: HTTP 422 - `Input should be a valid string`

### 测试方法2: Base64字符串格式
```json
{
  "role": "user",
  "content": "请分析以下图片（base64编码）：\ndata:image/png;base64,..."
}
```
**结果**: HTTP 200，但响应为空或只有换行符

---

## 💡 新的分析角度

### 1. Schema 定义 vs 实际实现

**可能性1**: Schema 定义滞后于实际实现
- Gemini 2.5 Pro 原生支持视觉输入
- API 可能已经支持，但 Schema 未更新
- **验证方法**: 尝试发送数组格式的请求，忽略 Schema 验证错误

**可能性2**: 需要特殊参数或格式
- Google Gemini API 可能有特殊的图片传递方式
- 可能需要通过 `metadata` 或其他参数传递图片
- **验证方法**: 检查是否有其他参数可以传递图片数据

**可能性3**: 仅支持图片 URL（不支持 base64）
- API 可能只支持通过 URL 访问图片
- Base64 编码可能不被支持
- **验证方法**: 尝试使用公开可访问的图片 URL

### 2. Google Gemini 原生格式

根据 Google Gemini API 文档，原生格式可能不同：
- Google Gemini API 使用 `parts` 数组，而不是 `content` 数组
- 格式：`{"parts": [{"text": "..."}, {"inline_data": {"mime_type": "image/png", "data": "base64..."}}]}`

**但 AI Builders API 使用的是 OpenAI 兼容格式**，可能不支持 Google 原生格式。

### 3. 其他可能的传递方式

1. **通过 `metadata` 参数**：
   ```json
   {
     "messages": [...],
     "metadata": {
       "images": ["base64..."]
     }
   }
   ```

2. **通过 `user` 参数**：
   ```json
   {
     "messages": [...],
     "user": "user_id",
     "images": ["base64..."]
   }
   ```

3. **通过图片 URL**（如果 API 可以访问外部 URL）：
   ```json
   {
     "role": "user",
     "content": "请分析这张图片：https://example.com/image.png"
   }
   ```

---

## 🔬 建议的进一步测试

### 测试1: 忽略 Schema 验证，直接发送数组格式
```python
# 即使 Schema 说 content 必须是 string，也尝试发送数组
user_content = [
    {"type": "text", "text": "请描述这张图片"},
    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
]
```

### 测试2: 使用图片 URL（公开可访问）
```python
# 上传图片到公开可访问的 URL，然后使用 URL
user_content = "请分析这张图片：https://example.com/test_image.png"
```

### 测试3: 检查 `metadata` 参数
```python
payload = {
    "model": "gemini-2.5-pro",
    "messages": messages,
    "metadata": {
        "image": image_base64
    }
}
```

### 测试4: 检查是否有专门的视觉端点
- 查看是否有 `/v1/vision` 或类似的端点
- 检查 `/v1/audio/transcriptions` 的实现方式（支持文件上传）

---

## 📊 结论与建议

### 当前状态
1. **OpenAPI Schema 明确不支持数组格式的多模态输入**
2. **之前的测试显示**：
   - 数组格式：HTTP 422 验证错误
   - Base64字符串格式：HTTP 200 但响应为空

### 用户的怀疑是否有依据？
**✅ 是的，用户的怀疑是有依据的**：
1. Gemini 2.5 Pro 原生支持视觉输入
2. API 描述说 "Direct access to Google's Gemini model"
3. Schema 定义可能与实际实现不一致

### 建议的下一步
1. **联系 AI Builders 技术支持**，确认是否支持视觉输入
2. **尝试更多测试方法**（见上面的测试建议）
3. **如果确实不支持**，考虑使用外部 Vision API（如 Google Cloud Vision API）

---

## 📝 相关文档
- **之前的测试报告**: `docs/VISION_MODELS_TEST_REPORT.md`
- **Token消耗分析**: `docs/TOKEN_COST_AND_VISION_ANALYSIS.md`
- **测试脚本**: `scripts/test_vision_models.py`

---

**分析完成时间**: 2025-12-29  
**版本**: V3.2.0

