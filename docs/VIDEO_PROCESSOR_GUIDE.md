# VideoProcessorService 使用指南

## 📋 概述

`VideoProcessorService` 是一个用于下载视频并提取多模态数据的后端服务。它支持从 YouTube、Bilibili 等平台下载视频，并提取音频、关键帧和元数据。

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装 Python 包
pip install -r requirements_v3.txt

# macOS: 安装 ffmpeg 二进制文件
brew install ffmpeg

# Linux: 安装 ffmpeg 二进制文件
apt-get install ffmpeg
# 或
yum install ffmpeg
```

### 2. 基本使用

```python
from core.video_processor import VideoCrawler

# 创建实例
crawler = VideoCrawler()

# 处理视频
result = crawler.process_video(
    video_url="https://www.youtube.com/watch?v=VIDEO_ID",
    output_dir="./output",
    video_quality="480p",  # "360p", "480p", "720p", "best"
    num_frames=6  # 提取的关键帧数量
)

# 检查结果
if result["success"]:
    print(f"✅ 处理成功！")
    print(f"📹 视频: {result['video_path']}")
    print(f"🎵 音频: {result['audio_path']}")
    print(f"🖼️  关键帧: {len(result['frames_paths'])} 张")
    print(f"📊 元数据: {result['metadata']}")
else:
    print(f"❌ 处理失败: {result['error']}")
```

### 3. 便捷函数

```python
from core.video_processor import process_video

# 直接调用便捷函数
result = process_video(
    video_url="https://www.youtube.com/watch?v=VIDEO_ID",
    output_dir="./output"
)
```

## 📊 返回数据结构

`process_video` 方法返回一个字典，包含以下字段：

```python
{
    "success": bool,           # 是否成功
    "metadata": {              # 视频元数据
        "title": str,          # 标题
        "description": str,    # 描述（前500字符）
        "duration": int,       # 时长（秒）
        "upload_date": str,    # 上传日期
        "view_count": int,     # 观看次数
        "like_count": int,     # 点赞数
        "channel": str,        # 频道名称
        "channel_id": str,     # 频道ID
        "resolution": str,     # 分辨率（如 "1280x720"）
        "fps": float,          # 帧率
        "format": str,         # 格式
        "ext": str,            # 扩展名
        "url": str,            # 视频URL
        "tags": List[str],     # 标签（如果可用）
        "categories": List[str], # 分类（如果可用）
        "thumbnail": str,      # 缩略图URL（如果可用）
    },
    "audio_path": str,         # 音频文件路径（.mp3）
    "frames_paths": List[str], # 关键帧路径列表（.jpg）
    "video_path": str,         # 视频文件路径
    "error": str              # 错误信息（如果失败）
}
```

## ⚙️ 参数说明

### `process_video` 方法参数

- **`video_url`** (str, 必需): 视频URL
  - 支持平台: YouTube, Bilibili, 等 yt-dlp 支持的平台
  
- **`output_dir`** (str, 必需): 输出目录路径
  - 如果目录不存在，会自动创建
  
- **`video_quality`** (str, 可选): 视频质量，默认 `"480p"`
  - `"360p"`: 360p 视频 + 最佳音频
  - `"480p"`: 480p 视频 + 最佳音频
  - `"720p"`: 720p 视频 + 最佳音频
  - `"best"`: 最佳质量
  
- **`num_frames`** (int, 可选): 提取的关键帧数量，默认 `6`
  - 关键帧会均匀分布在视频时长中
  - 例如：6 帧会提取 0%, 20%, 40%, 60%, 80%, 100% 位置的帧

## 🎯 功能特性

### 1. 视频下载
- ✅ 支持多种视频平台（YouTube, Bilibili 等）
- ✅ 可配置视频质量（360p/480p/720p/best）
- ✅ 自动下载最佳音频
- ✅ 提取完整元数据

### 2. 音频提取
- ✅ 提取完整音频文件（.mp3 格式）
- ✅ 192kbps 音频比特率
- ✅ 使用 libmp3lame 编码器

### 3. 关键帧提取
- ✅ 均匀分布的关键帧提取
- ✅ 可配置帧数量（默认6张）
- ✅ 高质量 JPEG 格式（qscale:v=2）
- ✅ 自动避免视频末尾的不完整帧

### 4. 错误处理
- ✅ 完善的异常处理机制
- ✅ 详细的错误日志
- ✅ 依赖检查（yt-dlp, ffmpeg）
- ✅ 部分失败时仍返回可用结果

## 📝 使用示例

### 示例1: 下载教育视频

```python
from core.video_processor import VideoCrawler

crawler = VideoCrawler()

# 下载一个教育视频
result = crawler.process_video(
    video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    output_dir="./data/videos/math_lesson_1",
    video_quality="480p",
    num_frames=6
)

if result["success"]:
    print(f"视频标题: {result['metadata']['title']}")
    print(f"观看次数: {result['metadata']['view_count']:,}")
    print(f"时长: {result['metadata']['duration']} 秒")
    print(f"音频文件: {result['audio_path']}")
    print(f"关键帧数量: {len(result['frames_paths'])}")
```

### 示例2: 批量处理视频

```python
from core.video_processor import VideoCrawler
from pathlib import Path

crawler = VideoCrawler()
video_urls = [
    "https://www.youtube.com/watch?v=VIDEO_1",
    "https://www.youtube.com/watch?v=VIDEO_2",
    "https://www.youtube.com/watch?v=VIDEO_3",
]

results = []
for i, url in enumerate(video_urls, 1):
    print(f"\n处理视频 {i}/{len(video_urls)}: {url}")
    result = crawler.process_video(
        video_url=url,
        output_dir=f"./data/videos/video_{i}",
        video_quality="480p",
        num_frames=6
    )
    results.append(result)
    
    if result["success"]:
        print(f"✅ 成功: {result['video_path']}")
    else:
        print(f"❌ 失败: {result['error']}")

# 统计结果
success_count = sum(1 for r in results if r["success"])
print(f"\n总计: {success_count}/{len(results)} 成功")
```

### 示例3: 集成到搜索系统

```python
from core.video_processor import VideoCrawler
from search_engine_v2 import SearchEngineV2

# 搜索视频
search_engine = SearchEngineV2()
search_result = search_engine.search(...)

# 处理搜索结果中的第一个视频
if search_result.results:
    first_video = search_result.results[0]
    video_url = first_video.url
    
    crawler = VideoCrawler()
    process_result = crawler.process_video(
        video_url=video_url,
        output_dir=f"./data/processed/{first_video.title}",
        video_quality="480p",
        num_frames=6
    )
    
    if process_result["success"]:
        # 使用提取的数据进行进一步分析
        audio_path = process_result["audio_path"]
        frames_paths = process_result["frames_paths"]
        metadata = process_result["metadata"]
        
        # ... 进行 AI 评估或其他处理 ...
```

## 🔧 故障排除

### 问题1: `yt-dlp 未安装`

**错误信息**: `❌ yt-dlp 未安装，请运行: pip install yt-dlp`

**解决方案**:
```bash
pip install yt-dlp
```

### 问题2: `ffmpeg-python 未安装`

**错误信息**: `❌ ffmpeg-python 未安装，请运行: pip install ffmpeg-python`

**解决方案**:
```bash
pip install ffmpeg-python
```

### 问题3: `ffmpeg 二进制文件未找到`

**错误信息**: `ffmpeg 二进制文件未找到，请安装: brew install ffmpeg (macOS)`

**解决方案**:
- **macOS**: `brew install ffmpeg`
- **Linux**: `apt-get install ffmpeg` 或 `yum install ffmpeg`
- **Windows**: 从 https://ffmpeg.org/download.html 下载并添加到 PATH

### 问题4: 视频下载失败

**可能原因**:
1. 视频URL无效或视频已删除
2. 网络连接问题
3. 平台限制（需要登录或地区限制）

**解决方案**:
- 检查视频URL是否有效
- 检查网络连接
- 查看详细错误日志

### 问题5: 音频提取失败

**可能原因**:
1. 视频文件损坏
2. ffmpeg 编码器问题

**解决方案**:
- 检查视频文件是否完整下载
- 尝试重新下载视频
- 检查 ffmpeg 版本和编码器支持

### 问题6: 关键帧提取失败

**可能原因**:
1. 视频时长无法获取
2. 视频文件损坏
3. ffmpeg 提取失败

**解决方案**:
- 检查视频元数据是否正确
- 尝试减少关键帧数量
- 检查视频文件完整性

## 📚 API 参考

### `VideoCrawler` 类

#### `__init__(self)`
初始化 VideoCrawler 实例。

#### `process_video(self, video_url: str, output_dir: str, video_quality: str = "480p", num_frames: int = 6) -> Dict[str, Any]`
处理视频的主要方法。

**参数**:
- `video_url`: 视频URL
- `output_dir`: 输出目录
- `video_quality`: 视频质量（"360p", "480p", "720p", "best"）
- `num_frames`: 关键帧数量

**返回**: 处理结果字典

### 便捷函数

#### `process_video(video_url: str, output_dir: str, video_quality: str = "480p", num_frames: int = 6) -> Dict[str, Any]`
便捷函数，直接调用 `VideoCrawler().process_video()`。

## 🧪 测试

运行测试脚本验证功能：

```bash
python3 scripts/test_video_processor.py
```

## 📝 注意事项

1. **存储空间**: 视频文件可能很大，确保有足够的磁盘空间
2. **网络带宽**: 下载视频需要稳定的网络连接
3. **版权**: 请遵守视频平台的版权和使用条款
4. **速率限制**: 某些平台可能有下载速率限制
5. **依赖版本**: 确保 `yt-dlp` 和 `ffmpeg` 版本是最新的

## 🔗 相关文档

- [yt-dlp 文档](https://github.com/yt-dlp/yt-dlp)
- [ffmpeg-python 文档](https://github.com/kkroening/ffmpeg-python)
- [项目 SOP 文档](docs/SOP_V3_COMPLETE_FINAL.md)

---

**更新日期**: 2025-12-29  
**版本**: V3.2.0





