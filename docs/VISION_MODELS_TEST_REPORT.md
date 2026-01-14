# AI Builders 视觉模型支持测试报告

## 📋 测试概述

**测试日期**: 2025-12-29  
**测试目标**: 验证 AI Builders API 中的三个模型（Gemini 2.5 Pro、Grok-4-Fast、GPT-5）是否支持视觉输入  
**测试方法**: 
1. 数组格式（OpenAI标准多模态格式）
2. Base64字符串格式（将图片编码为base64字符串）

---

## 🧪 测试结果汇总

### 总体结论

**❌ 所有测试的模型都不支持视觉输入**

| 模型 | 数组格式 | Base64字符串格式 | 支持视觉 | Token消耗 |
|------|---------|-----------------|---------|-----------|
| **Gemini 2.5 Pro** | ❌ HTTP 422 | ⚠️ HTTP 200（仅换行符） | ❌ 否 | 24,763 tokens |
| **Grok-4-Fast** | ❌ HTTP 422 | ❌ HTTP 400 | ❌ 否 | N/A |
| **GPT-5** | ❌ HTTP 422 | ⚠️ HTTP 200（空响应） | ❌ 否 | 9,159 tokens |

---

## 📊 详细测试结果

### 1. Gemini 2.5 Pro

#### 测试方法1: 数组格式（OpenAI标准）
- **请求格式**: `[{type: "text"}, {type: "image_url", image_url: {url: "data:image/png;base64,..."}}]`
- **HTTP状态**: 422 (验证错误)
- **错误信息**: `Input should be a valid string`
- **结论**: API Schema不支持数组格式的`content`字段

#### 测试方法2: Base64字符串格式
- **请求格式**: 文本中包含完整的base64编码图片
- **HTTP状态**: 200 (成功)
- **响应内容**: **仅换行符（"\n"）**
- **Token消耗**: 
  - 输入: 24,763 tokens（base64编码占用大量token）
  - 输出: 0 tokens
  - 总计: 24,763 tokens
- **结论**: 虽然请求成功，但模型只返回换行符，说明无法处理base64编码的图片

#### 综合评价
- **支持视觉**: ❌ 否
- **成本**: 高（24,763 tokens，主要是base64编码占用）
- **响应质量**: 无响应
- **问题**: API Schema限制 + 模型无法处理base64字符串

---

### 2. Grok-4-Fast

#### 测试方法1: 数组格式（OpenAI标准）
- **请求格式**: `[{type: "text"}, {type: "image_url", image_url: {url: "data:image/png;base64,..."}}]`
- **HTTP状态**: 422 (验证错误)
- **错误信息**: `Input should be a valid string`
- **结论**: API Schema不支持数组格式的`content`字段

#### 测试方法2: Base64字符串格式
- **请求格式**: 文本中包含完整的base64编码图片
- **HTTP状态**: 400 (客户端错误)
- **错误信息**: `A tool_choice was set on the request but no tools were specified`
- **结论**: Grok-4-Fast对`tool_choice`参数有特殊要求，即使设置为`none`也会报错

#### 综合评价
- **支持视觉**: ❌ 否
- **成本**: N/A（请求失败）
- **响应质量**: N/A
- **问题**: API Schema限制 + 参数验证错误

---

### 3. GPT-5

#### 测试方法1: 数组格式（OpenAI标准）
- **请求格式**: `[{type: "text"}, {type: "image_url", image_url: {url: "data:image/png;base64,..."}}]`
- **HTTP状态**: 422 (验证错误)
- **错误信息**: `Input should be a valid string`
- **结论**: API Schema不支持数组格式的`content`字段

#### 测试方法2: Base64字符串格式
- **请求格式**: 文本中包含完整的base64编码图片（12,238字符）
- **HTTP状态**: 200 (成功)
- **响应内容**: **空字符串**
- **Token消耗**: 
  - 输入: 8,159 tokens（base64编码占用大量token）
  - 输出: 1,000 tokens（max_completion_tokens限制）
  - 总计: 9,159 tokens
- **结论**: 虽然请求成功，但模型返回空响应，说明无法处理base64编码的图片

#### 综合评价
- **支持视觉**: ❌ 否
- **成本**: 高（9,159 tokens，主要是base64编码占用）
- **响应质量**: 无响应
- **问题**: API Schema限制 + 模型无法处理base64字符串 + 成本高

---

## 💰 Token消耗对比

| 模型 | 输入Token | 输出Token | 总计Token | 成本估算（DeepSeek价格） |
|------|-----------|-----------|-----------|-------------------------|
| Gemini 2.5 Pro | 24,763 | 0 | 24,763 | $0.003467 |
| GPT-5 | 8,159 | 1,000 | 9,159 | $0.001282 |
| Grok-4-Fast | N/A | N/A | N/A | N/A |

**注意**: Gemini 2.5 Pro和GPT-5的token消耗高主要是因为base64编码的图片数据占用了大量token。即使如此，模型也无法处理图片内容。

---

## 🔍 问题分析

### 1. API Schema限制

根据OpenAPI Schema定义，`ChatCompletionMessage`的`content`字段类型为：
```json
{
  "content": {
    "anyOf": [
      {"type": "string"},
      {"type": "null"}
    ]
  }
}
```

**结论**: API规范明确只支持字符串类型，不支持数组格式的多模态输入。

### 2. 模型能力限制

即使使用base64字符串格式：
- **Gemini 2.5 Pro**: 返回空响应，说明无法从base64字符串中提取图片信息
- **GPT-5**: 返回空响应，说明无法从base64字符串中提取图片信息
- **Grok-4-Fast**: 请求失败，无法测试

**结论**: 模型本身可能支持视觉输入，但通过AI Builders API无法使用此功能。

---

## 💡 建议与解决方案

### 方案1: 使用外部Vision API（推荐）

如果项目需要视觉分析功能，建议使用专门的Vision API：

1. **Google Cloud Vision API**
   - 支持图片分析、OCR、标签识别等
   - 成本: $1.50 / 1,000张图片（前1,000张免费）

2. **OpenAI GPT-4 Vision API**
   - 如果可用，支持多模态输入
   - 成本: 根据token消耗计算

3. **Claude Vision API**
   - Anthropic的视觉模型
   - 支持图片分析

### 方案2: 保持当前实现（文本描述）

当前`core/video_evaluator.py`中的`_analyze_frame_design`方法使用文本描述模拟视觉分析：

**优点**:
- 成本低（~443 tokens/视频）
- 实现简单
- 无需额外API

**缺点**:
- 准确性较低
- 无法真正"看到"图片内容

### 方案3: OCR + 文本分析

使用OCR提取关键帧中的文字，然后进行文本分析：

1. 使用OCR工具（如Tesseract、Google Cloud Vision OCR）提取文字
2. 将提取的文字作为输入发送给LLM
3. LLM基于文字内容评估设计质量

**优点**:
- 可以获取图片中的文字信息
- 成本适中
- 准确性较高

**缺点**:
- 无法评估视觉设计（颜色、布局等）

---

## 📈 成本对比

### 当前实现（文本描述）
- **Token消耗**: ~443 tokens/视频
- **成本**: ~$0.000062 USD/视频（DeepSeek）

### 如果使用外部Vision API
- **Google Cloud Vision API**: $1.50 / 1,000张图片
- **每张关键帧**: $0.0015 USD
- **6张关键帧**: $0.009 USD/视频

**结论**: 当前文本描述方案成本更低，但准确性较低。

---

## 🎯 最终建议

1. **短期**: 保持当前的文本描述方案，成本低且实现简单
2. **中期**: 如果预算允许，集成Google Cloud Vision API进行真正的视觉分析
3. **长期**: 如果AI Builders API未来支持视觉输入，可以迁移到原生API

---

## 📝 测试文件

- **测试脚本**: `scripts/test_vision_models.py`
- **测试图片**: `scripts/test_vision_image.png`
- **测试结果**: `scripts/vision_test_results.json`

---

**报告生成时间**: 2025-12-29  
**测试版本**: V3.2.0

