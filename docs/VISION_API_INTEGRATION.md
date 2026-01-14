# 小豆包平台视觉API集成文档

**更新日期**: 2025-12-29  
**版本**: V3.2.1

---

## 📋 概述

本项目已集成小豆包平台的视觉API，用于视频关键帧的视觉分析。小豆包平台使用 OpenAI 兼容格式，支持多模态输入（文本+图片）。

---

## 🔑 API 配置

### 环境变量

在 `.env` 文件中添加以下环境变量之一：

```bash
# 方式1: 使用 XIAODOUBAO_API_KEY
XIAODOUBAO_API_KEY=your_api_key_here

# 方式2: 使用 LINKAPI_API_KEY（别名）
LINKAPI_API_KEY=your_api_key_here
```

### API 端点

- **基础地址**: `https://api.linkapi.org`
- **端点**: `/v1/chat/completions`
- **格式**: OpenAI 兼容格式

---

## 📚 API 格式参考

### 小豆包平台文档

- **图片分析接口**: https://gpt-best.apifox.cn/api-139453850
- **视频分析接口**: https://gpt-best.apifox.cn/api-321040299

### 请求格式

```json
{
  "model": "gpt-4o",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "请分析这张图片"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/png;base64,..."
          }
        }
      ]
    }
  ],
  "max_tokens": 1000,
  "temperature": 0.3
}
```

**关键特点**：
- ✅ `content` 字段支持**数组格式**（与 OpenAI 标准一致）
- ✅ 支持 `data:image/png;base64,...` 格式的 base64 编码图片
- ✅ 支持多张图片（在数组中添加多个 `image_url` 对象）

---

## 🏗️ 代码实现

### 1. VisionClient 类

**文件**: `core/vision_client.py`

**主要方法**:
- `analyze_images()`: 分析多张图片
- `analyze_single_image()`: 分析单张图片（便捷方法）
- `_image_to_base64()`: 将图片文件转换为 base64 编码

**使用示例**:

```python
from core.vision_client import VisionClient

# 初始化客户端
client = VisionClient(api_key="your_api_key")

# 分析图片
result = client.analyze_images(
    image_paths=["frame1.jpg", "frame2.jpg"],
    prompt="请分析这些教学视频的关键帧",
    system_prompt="你是一个教育视频质量评估专家",
    model="gpt-4o",
    max_tokens=1000,
    temperature=0.3
)

if result["success"]:
    print(result["response"])
else:
    print(f"错误: {result['error']}")
```

### 2. VideoEvaluator 集成

**文件**: `core/video_evaluator.py`

**更新内容**:
- ✅ 支持 VisionClient 集成
- ✅ 自动降级到文本模拟（如果 VisionClient 不可用）
- ✅ 支持环境变量配置 API Key

**初始化**:

```python
from core.video_evaluator import VideoEvaluator

# 方式1: 从环境变量读取 API Key
evaluator = VideoEvaluator()

# 方式2: 显式传入 API Key
evaluator = VideoEvaluator(vision_api_key="your_api_key")
```

---

## 🔄 工作流程

### 视频评估流程

1. **视频处理**: 提取关键帧（6张均匀分布）
2. **视觉分析**: 
   - ✅ 如果 VisionClient 可用：使用小豆包平台视觉API分析图片
   - ⚠️ 如果 VisionClient 不可用：降级到文本模拟分析
3. **评分**: 基于视觉分析结果给出设计质量分数（0-10分）

### 降级机制

如果 VisionClient 初始化失败或 API 调用失败，系统会自动降级到文本模拟分析：

```python
# 优先使用视觉API
if self.vision_client:
    result = self.vision_client.analyze_images(...)
else:
    # 降级到文本模拟
    result = self._analyze_frame_design_fallback(...)
```

---

## 📊 支持的模型

根据小豆包平台文档，支持以下模型：

- **gpt-4o**: 支持图片分析（推荐）
- **gemini-2.5-pro-preview-05-06**: 支持视频分析

**当前实现使用**: `gpt-4o`（图片分析）

---

## 💰 成本估算

### Token 消耗

- **输入Token**: 
  - 文本: ~500 tokens（system prompt + user prompt）
  - 图片: 每张图片约 170 tokens（base64编码）
  - 6张关键帧: ~1,500 tokens
  - **总计**: ~2,000 tokens/视频

- **输出Token**: ~200 tokens（JSON响应）

- **总Token**: ~2,200 tokens/视频

### 成本（参考）

- **GPT-4o**: 约 $0.01-0.02 USD/视频（取决于实际定价）

---

## 🧪 测试

### 测试脚本

可以创建测试脚本验证视觉API：

```python
#!/usr/bin/env python3
from core.vision_client import VisionClient
from pathlib import Path

# 初始化客户端
client = VisionClient()

# 测试图片路径
test_image = Path("scripts/test_vision_image.png")

if test_image.exists():
    result = client.analyze_single_image(
        image_path=str(test_image),
        prompt="请详细描述这张图片的内容，包括颜色、形状、文字等",
        model="gpt-4o"
    )
    
    if result["success"]:
        print("✅ 视觉分析成功:")
        print(result["response"])
        print(f"\nToken 使用: {result['usage']}")
    else:
        print(f"❌ 视觉分析失败: {result['error']}")
else:
    print(f"❌ 测试图片不存在: {test_image}")
```

---

## ⚠️ 注意事项

1. **API Key 安全**: 
   - 不要将 API Key 提交到代码仓库
   - 使用环境变量或 `.env` 文件（已添加到 `.gitignore`）

2. **图片大小限制**:
   - 建议使用压缩后的图片（480p/360p）
   - Base64 编码会增加约 33% 的大小

3. **错误处理**:
   - 系统会自动降级到文本模拟
   - 不会因为视觉API失败而中断整个评估流程

4. **并发限制**:
   - 注意 API 的速率限制
   - 建议使用适当的延迟或队列机制

---

## 📝 更新日志

### V3.2.1 (2025-12-29)
- ✅ 集成小豆包平台视觉API
- ✅ 创建 VisionClient 类
- ✅ 更新 VideoEvaluator 支持视觉分析
- ✅ 实现自动降级机制
- ✅ 支持环境变量配置

---

## 🔗 相关文档

- **视觉模型测试报告**: `docs/VISION_MODELS_TEST_REPORT.md`
- **视觉API分析**: `docs/VISION_API_ANALYSIS.md`
- **Token消耗分析**: `docs/TOKEN_COST_AND_VISION_ANALYSIS.md`
- **小豆包平台文档**: 
  - https://gpt-best.apifox.cn/api-139453850
  - https://gpt-best.apifox.cn/api-321040299

---

**最后更新**: 2025-12-29  
**维护者**: AI Assistant





