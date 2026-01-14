# Token消耗估算与视觉模型分析

## 📊 播放列表评估Token消耗估算

### 播放列表信息
- **播放列表URL**: https://www.youtube.com/playlist?list=PLoiFaDwrUoPRPL7TyukXLMNGCUHEaq_0A
- **假设视频数量**: 20个视频（需要实际获取播放列表信息确认）

### 单个视频评估Token消耗

根据 `core/video_evaluator.py` 的实现，每个视频需要以下LLM调用：

#### 1. Vision AI分析（视觉质量软指标）
- **System Prompt**: ~500字符
- **User Prompt**: ~300字符 + 关键帧路径（6张）
- **输入Token**: ~243 tokens
- **输出Token**: ~200 tokens（JSON响应）
- **小计**: **443 tokens/视频**

#### 2. 内容相关度评估
- **System Prompt**: ~300字符
- **User Prompt**: ~400字符 + 学习目标（~500字符）+ 字幕（前2000字符）
- **输入Token**: ~1,467 tokens
- **输出Token**: ~300 tokens（JSON响应）
- **小计**: **1,767 tokens/视频**

#### 3. 教学质量评估
- **System Prompt**: ~400字符
- **User Prompt**: ~300字符 + 字幕（前2000字符）
- **输入Token**: ~1,210 tokens
- **输出Token**: ~300 tokens（JSON响应）
- **小计**: **1,510 tokens/视频**

#### 4. 热度/元数据评估
- **纯代码逻辑**，无需LLM调用
- **小计**: **0 tokens**

### 单个视频总计
- **总Token**: **3,720 tokens/视频**
  - 输入: 2,920 tokens
  - 输出: 800 tokens

### 整个播放列表（20个视频）
- **总Token**: **74,400 tokens**
  - 输入: 58,400 tokens
  - 输出: 16,000 tokens

### 💰 成本估算

#### DeepSeek模型（推荐）
- **单价**: $0.14 / 1M tokens（输入+输出）
- **单视频成本**: $0.00052 USD
- **播放列表总成本**: **$0.01 USD**（20个视频）

#### Gemini模型（估算）
- **单价**: ~$0.50 / 1M tokens（估算值）
- **单视频成本**: $0.00186 USD
- **播放列表总成本**: **$0.04 USD**（20个视频）

### 💡 优化建议

1. **使用DeepSeek模型**：可以大幅降低成本（约75%）
2. **字幕截断**：只取前2000字符进行评估，避免过长字幕
3. **批量处理**：可以考虑批量评估多个视频，减少API调用开销
4. **缓存机制**：相同视频的评估结果可以缓存，避免重复评估
5. **并行处理**：多个视频可以并行评估，提高效率

---

## 👁️ AI Builders 视觉模型支持分析

### 当前支持的模型

根据代码和文档分析，AI Builders API 当前支持以下模型：

1. **`deepseek`**: Fast and cost-effective chat completions（纯文本生成）
2. **`gemini-2.5-pro`**: Direct access to Google's Gemini model
3. **`grok-4-fast`**: Passthrough to X.AI's Grok API
4. **`gpt-5`**: Passthrough to OpenAI-compatible providers

### 视觉能力分析

#### 📋 OpenAPI Schema 分析

根据 `https://space.ai-builders.com/backend/openapi.json` 的Schema定义：

**ChatCompletionMessage Schema**:
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

**结论**: 
- `content` 字段类型为 `string` 或 `null`
- **当前API规范不支持数组格式的多模态输入**（如OpenAI的 `[{type: "text"}, {type: "image_url"}]`）

#### ✅ Gemini 2.5 Pro（理论上支持，但API可能未暴露）
- **Google Gemini 2.5 Pro** 原生支持多模态输入（文本+图片）
- **API限制**: 当前OpenAPI Schema只定义 `content` 为字符串类型
- **可能情况**: 
  - API可能支持但Schema未更新
  - 或者需要通过特殊方式传递图片（如base64编码在文本中）
- **建议**: 需要实际测试验证

#### ❌ DeepSeek（不支持）
- **DeepSeek** 是纯文本模型，不支持视觉输入

#### ❓ Grok-4-Fast / GPT-5（未知）
- 需要查看具体API文档确认是否支持视觉输入
- 但根据OpenAPI Schema，可能也不支持多模态输入

### 当前实现状态

在 `core/video_evaluator.py` 的 `_analyze_frame_design` 方法中：

```python
def _analyze_frame_design(self, frames_paths: List[str]) -> Dict[str, Any]:
    # 这里应该调用Vision API，但当前我们使用LLM模拟
    # 实际实现时，应该使用真正的Vision API（如Gemini Vision）
    
    # 当前实现：只传递文本描述，没有实际发送图片
    response = self.client.call_llm(
        prompt=user_prompt,  # 只包含文本描述
        system_prompt=system_prompt,
        max_tokens=500,
        temperature=0.3,
        model="deepseek"
    )
```

### 🔍 如何启用真正的视觉分析

#### 方案1: 使用 Gemini 2.5 Pro Vision API

如果 AI Builders API 支持 Gemini 的多模态输入，可以修改 `call_gemini` 方法：

```python
def call_gemini_vision(
    self,
    prompt: str,
    image_paths: List[str],
    system_prompt: Optional[str] = None,
    max_tokens: int = 2000,
    temperature: float = 0.3
) -> str:
    """
    调用 Gemini Vision API（如果支持）
    
    Args:
        prompt: 文本提示词
        image_paths: 图片文件路径列表
        system_prompt: 系统提示词
        max_tokens: 最大生成token数
        temperature: 温度参数
    
    Returns:
        模型返回的文本内容
    """
    endpoint = f"{self.base_url}/v1/chat/completions"
    
    # 构建多模态消息
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    # 添加图片内容
    user_content = [{"type": "text", "text": prompt}]
    for image_path in image_paths:
        # 读取图片并转换为base64
        import base64
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_data}"
                }
            })
    
    messages.append({"role": "user", "content": user_content})
    
    payload = {
        "model": "gemini-2.5-pro",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    
    # ... 发送请求
```

#### 方案2: 使用外部Vision API

如果 AI Builders 不支持视觉输入，可以考虑：

1. **Google Cloud Vision API**: 专门的视觉分析API
2. **OpenAI GPT-4 Vision**: 如果可用
3. **Claude Vision**: Anthropic的视觉模型

### 📝 建议

1. **实际测试**: 
   - 尝试发送包含图片的请求（使用base64编码或URL）
   - 测试 `content` 字段是否接受数组格式（尽管Schema未定义）
   - 查看API响应，确认是否支持

2. **备选方案**:
   - **方案A**: 如果API不支持，使用外部Vision API（Google Cloud Vision API）
   - **方案B**: 保持当前的文本描述方式（成本更低，但准确性较低）
   - **方案C**: 使用OCR提取关键帧中的文字，然后进行文本分析

3. **当前实现**: 
   - 代码中 `_analyze_frame_design` 方法使用文本描述模拟视觉分析
   - 这是一个合理的折中方案，成本低且实现简单
   - 如果后续需要真正的视觉分析，可以集成外部Vision API

---

## 📋 总结

### Token消耗
- **单个视频**: ~3,720 tokens
- **20个视频播放列表**: ~74,400 tokens
- **成本（DeepSeek）**: ~$0.01 USD

### 视觉模型支持
- **当前状态**: 代码中未实现真正的视觉输入
- **Gemini 2.5 Pro**: 可能支持，需要验证API
- **建议**: 先测试API是否支持多模态输入，再决定实现方案

---

**更新日期**: 2025-12-29  
**版本**: V3.2.0

