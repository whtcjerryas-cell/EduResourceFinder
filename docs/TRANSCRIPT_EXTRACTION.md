# 字幕/转录提取功能说明

## 📋 概述

视频评估系统现在支持智能字幕/转录提取，优先使用官方字幕，如果没有字幕则使用Whisper进行音频转录。

## 🔄 工作流程

```
视频URL
  ↓
步骤1: 尝试提取官方字幕（yt-dlp）
  ├─ 成功 → 使用字幕文本 ✅
  └─ 失败 → 步骤2
      ↓
步骤2: 使用Whisper进行音频转录
  ├─ 成功 → 使用转录文本 ✅
  └─ 失败 → 无文本（影响评估）⚠️
```

## 🎯 功能特性

### 1. 官方字幕提取（优先）

- **工具**: yt-dlp
- **支持格式**: VTT, SRT等
- **语言选择**: 
  - 支持首选语言列表（如 `['en', 'id', 'zh']`）
  - 自动选择最佳匹配语言
  - 支持自动生成的字幕（auto-generated captions）

### 2. Whisper音频转录（备选）

- **工具**: OpenAI Whisper（开源）
- **模型**: base模型（平衡速度和准确性）
- **语言检测**: 自动检测音频语言
- **特点**: 
  - 无需字幕文件
  - 支持多语言
  - 准确性高

## 📦 依赖安装

```bash
# 安装Whisper
pip install openai-whisper

# 注意：Whisper需要ffmpeg（通常已安装）
# macOS: brew install ffmpeg
# Linux: apt-get install ffmpeg
```

## 🔧 使用方法

### 在VideoCrawler中使用

```python
from core.video_processor import VideoCrawler

crawler = VideoCrawler()
result = crawler.process_video(
    video_url="https://www.youtube.com/watch?v=...",
    output_dir="./output",
    video_quality="480p",
    num_frames=6,
    extract_transcript=True,  # 启用字幕/转录提取
    preferred_languages=['en', 'id', 'zh']  # 首选语言
)

# 结果中包含：
# - transcript: 字幕/转录文本
# - transcript_source: "subtitle" 或 "whisper"
# - transcript_language: 检测到的语言代码
```

### 单独使用TranscriptExtractor

```python
from core.transcript_extractor import TranscriptExtractor

extractor = TranscriptExtractor()
result = extractor.extract_transcript(
    video_url="https://www.youtube.com/watch?v=...",
    audio_path="./audio.mp3",  # 如果已有音频文件
    output_dir="./subtitles",
    preferred_languages=['en', 'id']
)

if result["success"]:
    print(f"文本来源: {result['source']}")
    print(f"语言: {result['language']}")
    print(f"文本: {result['transcript']}")
```

## 📊 返回数据结构

```python
{
    "success": bool,              # 是否成功
    "transcript": str,            # 字幕/转录文本
    "source": str,                # "subtitle" 或 "whisper"
    "language": str,              # 语言代码（如 "en", "id", "zh"）
    "subtitle_path": str,         # 字幕文件路径（如果提取了字幕）
    "error": str                  # 错误信息（如果失败）
}
```

## ⚙️ 配置选项

### 首选语言列表

```python
# 示例：优先使用英语，其次印尼语，最后中文
preferred_languages = ['en', 'id', 'zh']

# 示例：只使用英语
preferred_languages = ['en']
```

### Whisper模型选择

在 `core/transcript_extractor.py` 中可以修改Whisper模型：

```python
# 可选模型（速度从快到慢，准确性从低到高）：
# - tiny: 最快，准确性最低
# - base: 平衡（默认）
# - small: 较慢，准确性较高
# - medium: 慢，准确性高
# - large: 最慢，准确性最高

model = whisper.load_model("base")  # 修改这里
```

## 🎓 评估影响

字幕/转录文本用于以下评估维度：

### 1. 内容相关度（40%权重）
- **需要**：字幕/转录文本 + 知识点信息
- ✅ **有官方字幕**：可以正常评估（最佳）
- ✅ **有Whisper转录**：**也可以正常评估**（Whisper准确性很高，通常与官方字幕效果相当）
- ❌ **完全没有文本**：无法评估（返回0分）

### 2. 教学质量（30%权重）
- **需要**：字幕/转录文本
- ✅ **有官方字幕**：可以正常评估（最佳）
- ✅ **有Whisper转录**：**也可以正常评估**（Whisper的准确性很高，对评估质量影响很小）
- ❌ **完全没有文本**：无法评估（返回0分）

### 📊 评估能力对比

| 文本来源 | 内容相关度评估 | 教学质量评估 | 说明 |
|---------|--------------|------------|------|
| ✅ 官方字幕 | ✅ 可以评估 | ✅ 可以评估 | 最佳选择，准确性最高 |
| ✅ Whisper转录 | ✅ **可以评估** | ✅ **可以评估** | **效果与官方字幕相当**，Whisper准确性很高 |
| ❌ 无文本 | ❌ 无法评估 | ❌ 无法评估 | 返回0分或默认分数 |

**重要说明**：
- ✅ **无论是官方字幕还是Whisper转录，只要有文本内容，都可以正常进行评估**
- ✅ **Whisper转录的准确性很高，通常不会影响评估质量**
- ❌ **只有在完全无法获取文本的情况下**（字幕提取失败 + Whisper转录失败），评估才会受影响

## ⚠️ 注意事项

1. **Whisper模型下载**：
   - 首次使用时会自动下载模型（约150MB）
   - 需要网络连接

2. **性能考虑**：
   - 官方字幕提取：快速（几秒）
   - Whisper转录：较慢（取决于音频长度，通常1-5分钟）

3. **语言支持**：
   - 官方字幕：取决于视频平台提供的语言
   - Whisper：支持99种语言

4. **准确性**：
   - 官方字幕：通常最准确
   - Whisper：准确性高，但可能不如官方字幕

## 🔍 故障排除

### 问题1: Whisper导入失败

```
ImportError: No module named 'whisper'
```

**解决方案**：
```bash
pip install openai-whisper
```

### 问题2: Whisper模型下载失败

**解决方案**：
- 检查网络连接
- 手动下载模型并放置到缓存目录

### 问题3: 字幕提取失败

**可能原因**：
- 视频没有字幕
- 网络问题
- yt-dlp版本过旧

**解决方案**：
- 更新yt-dlp: `pip install --upgrade yt-dlp`
- 检查视频是否有字幕
- 系统会自动降级到Whisper转录

## 📝 日志示例

```
📝 步骤1: 尝试提取官方字幕...
    [🔍 检查] 检查视频可用字幕...
    [✅ 发现] 找到 3 种字幕语言: ['en', 'id', 'zh']
    [📌 选择] 使用字幕语言: en
    [📄 文件] 字幕文件: subtitle.en.vtt
    [✅ 完成] 提取字幕成功，长度: 1234 字符
✅ 成功提取官方字幕（语言: en）
```

或（如果没有字幕）：

```
📝 步骤1: 尝试提取官方字幕...
    [⚠️ 结果] 视频没有可用字幕
⚠️  无法提取官方字幕: 视频没有可用字幕
📝 步骤2: 使用Whisper进行音频转录...
    [🎤 Whisper] 开始加载模型...
    [🎤 Whisper] 开始转录音频...
    [✅ Whisper] 转录成功，语言: en，长度: 1234 字符
✅ Whisper转录成功（语言: en）
```

