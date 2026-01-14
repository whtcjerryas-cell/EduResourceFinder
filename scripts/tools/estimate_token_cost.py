#!/usr/bin/env python3
"""
估算播放列表评估的Token消耗
"""

import json
from typing import Dict, Any

def estimate_tokens(text: str) -> int:
    """
    粗略估算文本的token数量
    中文：约1.5字符 = 1 token
    英文：约4字符 = 1 token
    这里使用保守估算：1字符 ≈ 0.5 token
    """
    return int(len(text) * 0.5)

def estimate_video_evaluation_cost(
    video_count: int,
    avg_transcript_length: int = 2000,  # 平均字幕长度（字符）
    knowledge_point_length: int = 500,  # 知识点描述长度（字符）
    frames_count: int = 6  # 每个视频的关键帧数量
) -> Dict[str, Any]:
    """
    估算单个视频评估的token消耗
    
    Args:
        video_count: 视频数量
        avg_transcript_length: 平均字幕长度（字符）
        knowledge_point_length: 知识点描述长度（字符）
        frames_count: 关键帧数量
    
    Returns:
        估算结果字典
    """
    
    # 1. 视觉质量评估（Vision AI）
    # System Prompt: ~500字符
    vision_system_prompt = """你是一个教育视频质量评估专家，专门评估教学可视化的设计质量。

**重要说明**：
我将提供视频的截图。请注意，这些截图来自低分辨率版本，**请忽略压缩噪点和像素模糊**。
请专注于评估**教学可视化的设计质量**：

1. **板书/PPT排版**：是否拥挤？是否清晰易读？
2. **字体大小**：在移动端是否易读？
3. **视觉辅助**：是否使用了图表、动画等辅助理解？
4. **教师位置**：老师是否一直遮挡板书？
5. **色彩对比**：文字与背景对比度是否足够？
6. **内容组织**：信息层次是否清晰？

请给出0-10分的评分，并提供简短的评估理由。"""
    
    # User Prompt: ~300字符 + 关键帧路径
    vision_user_prompt_base = f"""请分析以下教学视频的关键帧（共{frames_count}张），评估其教学可视化设计质量。

**关键帧路径**：
[6个路径，每个约100字符]

**评估要求**：
1. 忽略低分辨率造成的像素模糊
2. 专注于评估教学设计的质量
3. 给出0-10分的评分
4. 提供简短的评估理由

请以JSON格式返回：
{{
    "score": 7.5,
    "details": "板书清晰，但配色单调，缺少图表辅助"
}}"""
    
    vision_input_tokens = estimate_tokens(vision_system_prompt + vision_user_prompt_base)
    vision_output_tokens = 200  # JSON响应约200 tokens
    vision_total_per_video = vision_input_tokens + vision_output_tokens
    
    # 2. 内容相关度评估
    # System Prompt: ~300字符
    relevance_system_prompt = """你是一个教育内容评估专家。你的任务是评估视频内容是否精确覆盖了指定的学习目标。

**评估标准**：
1. 视频内容是否直接讲解目标知识点？
2. 是否覆盖了学习目标中提到的所有关键概念？
3. 是否有无关内容或偏离主题？
4. 内容深度是否适合目标年级？

请给出0-10分的评分，并提供详细的评估理由。"""
    
    # User Prompt: ~400字符 + 学习目标 + 字幕（前2000字符）
    relevance_user_prompt_base = """请评估以下视频内容是否精确覆盖了指定的学习目标。

**学习目标**：
[知识点描述，约500字符]

**知识点主题**：
[主题名称，约50字符]

**视频字幕/转录文本**（前2000字符）：
[字幕文本，2000字符]

**评估要求**：
1. 判断视频内容是否直接讲解目标知识点
2. 评估是否覆盖了学习目标中的关键概念
3. 检查是否有无关内容
4. 给出0-10分的评分

请以JSON格式返回：
{{
    "score": 8.5,
    "details": "视频内容高度相关，完整覆盖了学习目标中的所有关键概念，讲解清晰准确"
}}"""
    
    relevance_input_tokens = estimate_tokens(
        relevance_system_prompt + 
        relevance_user_prompt_base + 
        " " * knowledge_point_length +  # 学习目标（用空格占位）
        " " * avg_transcript_length  # 字幕（前2000字符，用空格占位）
    )
    relevance_output_tokens = 300  # JSON响应约300 tokens
    relevance_total_per_video = relevance_input_tokens + relevance_output_tokens
    
    # 3. 教学质量评估
    # System Prompt: ~400字符
    pedagogy_system_prompt = """你是一个教学法评估专家。你的任务是评估教学视频的教学质量。

**评估维度**：
1. **讲解逻辑**：是否有清晰的引入->概念->例子->总结结构？
2. **语速**：是否适合目标学生？是否过快或过慢？
3. **引导性提问**：是否有适当的提问来引导学生思考？
4. **重点强调**：是否突出了关键概念？
5. **互动性**：是否有适当的互动元素？

请给出0-10分的评分，并提供详细的评估理由。"""
    
    # User Prompt: ~300字符 + 字幕（前2000字符）
    pedagogy_user_prompt_base = """请评估以下教学视频的教学质量。

**视频字幕/转录文本**（前2000字符）：
[字幕文本，2000字符]

**评估要求**：
1. 评估讲解逻辑是否清晰
2. 判断语速是否合适
3. 检查是否有引导性提问
4. 评估重点强调是否到位
5. 给出0-10分的评分

请以JSON格式返回：
{{
    "score": 7.5,
    "details": "讲解逻辑清晰，有引入和总结，但缺少引导性提问，语速稍快"
}}"""
    
    pedagogy_input_tokens = estimate_tokens(
        pedagogy_system_prompt + 
        pedagogy_user_prompt_base + 
        " " * avg_transcript_length  # 字幕（前2000字符，用空格占位）
    )
    pedagogy_output_tokens = 300  # JSON响应约300 tokens
    pedagogy_total_per_video = pedagogy_input_tokens + pedagogy_output_tokens
    
    # 4. 热度/元数据评估（纯代码逻辑，无LLM调用）
    metadata_total_per_video = 0
    
    # 单个视频总token消耗
    total_per_video = (
        vision_total_per_video +
        relevance_total_per_video +
        pedagogy_total_per_video +
        metadata_total_per_video
    )
    
    # 整个播放列表的总token消耗
    total_for_playlist = total_per_video * video_count
    
    return {
        "video_count": video_count,
        "per_video": {
            "vision_ai": {
                "input_tokens": vision_input_tokens,
                "output_tokens": vision_output_tokens,
                "total": vision_total_per_video
            },
            "relevance": {
                "input_tokens": relevance_input_tokens,
                "output_tokens": relevance_output_tokens,
                "total": relevance_total_per_video
            },
            "pedagogy": {
                "input_tokens": pedagogy_input_tokens,
                "output_tokens": pedagogy_output_tokens,
                "total": pedagogy_total_per_video
            },
            "metadata": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total": metadata_total_per_video
            },
            "total": total_per_video
        },
        "playlist_total": {
            "input_tokens": (
                vision_input_tokens + 
                relevance_input_tokens + 
                pedagogy_input_tokens
            ) * video_count,
            "output_tokens": (
                vision_output_tokens + 
                relevance_output_tokens + 
                pedagogy_output_tokens
            ) * video_count,
            "total": total_for_playlist
        },
        "cost_estimate": {
            "deepseek_per_1k_tokens": 0.00014,  # $0.14 per 1M tokens (输入+输出)
            "deepseek_total_usd": round(total_for_playlist * 0.00014 / 1000, 2),
            "gemini_per_1k_tokens": 0.0005,  # 估算值
            "gemini_total_usd": round(total_for_playlist * 0.0005 / 1000, 2)
        }
    }

if __name__ == "__main__":
    # 假设播放列表有20个视频
    video_count = 20
    
    print("="*80)
    print("📊 Token消耗估算")
    print("="*80)
    print(f"\n播放列表视频数量: {video_count}")
    print("\n假设条件:")
    print("  - 平均字幕长度: 2000字符")
    print("  - 知识点描述长度: 500字符")
    print("  - 每个视频关键帧数量: 6张")
    print("  - 使用模型: deepseek (成本较低)")
    
    result = estimate_video_evaluation_cost(video_count)
    
    print("\n" + "="*80)
    print("单个视频Token消耗:")
    print("="*80)
    print(f"  👁️  Vision AI分析:")
    print(f"     输入: {result['per_video']['vision_ai']['input_tokens']:,} tokens")
    print(f"     输出: {result['per_video']['vision_ai']['output_tokens']:,} tokens")
    print(f"     小计: {result['per_video']['vision_ai']['total']:,} tokens")
    
    print(f"\n  📚 内容相关度评估:")
    print(f"     输入: {result['per_video']['relevance']['input_tokens']:,} tokens")
    print(f"     输出: {result['per_video']['relevance']['output_tokens']:,} tokens")
    print(f"     小计: {result['per_video']['relevance']['total']:,} tokens")
    
    print(f"\n  🎓 教学质量评估:")
    print(f"     输入: {result['per_video']['pedagogy']['input_tokens']:,} tokens")
    print(f"     输出: {result['per_video']['pedagogy']['output_tokens']:,} tokens")
    print(f"     小计: {result['per_video']['pedagogy']['total']:,} tokens")
    
    print(f"\n  🔥 热度/元数据评估:")
    print(f"     小计: {result['per_video']['metadata']['total']:,} tokens (纯代码逻辑)")
    
    print(f"\n  📊 单个视频总计: {result['per_video']['total']:,} tokens")
    
    print("\n" + "="*80)
    print("整个播放列表Token消耗:")
    print("="*80)
    print(f"  输入Token: {result['playlist_total']['input_tokens']:,}")
    print(f"  输出Token: {result['playlist_total']['output_tokens']:,}")
    print(f"  总计: {result['playlist_total']['total']:,} tokens")
    
    print("\n" + "="*80)
    print("💰 成本估算:")
    print("="*80)
    print(f"  DeepSeek模型:")
    print(f"    单价: ${result['cost_estimate']['deepseek_per_1k_tokens']:.6f} / 1K tokens")
    print(f"    总成本: ${result['cost_estimate']['deepseek_total_usd']:.2f} USD")
    print(f"\n  Gemini模型 (估算):")
    print(f"    单价: ${result['cost_estimate']['gemini_per_1k_tokens']:.6f} / 1K tokens")
    print(f"    总成本: ${result['cost_estimate']['gemini_total_usd']:.2f} USD")
    
    print("\n" + "="*80)
    print("💡 优化建议:")
    print("="*80)
    print("  1. 使用DeepSeek模型可以大幅降低成本")
    print("  2. 如果字幕很长，可以只取前2000字符进行评估")
    print("  3. Vision AI分析可以批量处理多个关键帧")
    print("  4. 可以考虑缓存评估结果，避免重复评估")
    print("="*80)

