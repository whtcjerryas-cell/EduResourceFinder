#!/usr/bin/env python3
"""
测试视频评估流程并收集 Token 消耗
将结果保存到 Excel 表格
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("⚠️  pandas 未安装，无法保存 Excel。请运行: pip install pandas openpyxl")

from core.video_processor import VideoCrawler
from core.video_evaluator import VideoEvaluator
from logger_utils import get_logger

logger = get_logger('test_video_evaluation')

# Token 使用追踪器
class TokenTracker:
    """Token 使用情况追踪器"""
    
    def __init__(self):
        self.records = []
    
    def add_record(self, step: str, model: str, usage: Dict[str, Any], api_type: str = "text"):
        """
        添加 Token 使用记录
        
        Args:
            step: 步骤名称（如 "视觉分析", "内容相关度评估"）
            model: 模型名称
            usage: Token 使用情况字典（包含 prompt_tokens, completion_tokens, total_tokens）
            api_type: API 类型（"text" 或 "vision"）
        """
        record = {
            "step": step,
            "model": model,
            "api_type": api_type,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "timestamp": datetime.now().isoformat()
        }
        self.records.append(record)
        logger.info(f"📊 Token记录: {step} - {model} - 总计: {record['total_tokens']} tokens")
    
    def get_summary(self) -> Dict[str, Any]:
        """获取汇总统计"""
        if not self.records:
            return {
                "total_records": 0,
                "total_tokens": 0,
                "total_prompt_tokens": 0,
                "total_completion_tokens": 0,
                "by_model": {},
                "by_step": {}
            }
        
        total_tokens = sum(r["total_tokens"] for r in self.records)
        total_prompt = sum(r["prompt_tokens"] for r in self.records)
        total_completion = sum(r["completion_tokens"] for r in self.records)
        
        # 按模型统计
        by_model = {}
        for record in self.records:
            model = record["model"]
            if model not in by_model:
                by_model[model] = {"total_tokens": 0, "count": 0}
            by_model[model]["total_tokens"] += record["total_tokens"]
            by_model[model]["count"] += 1
        
        # 按步骤统计
        by_step = {}
        for record in self.records:
            step = record["step"]
            if step not in by_step:
                by_step[step] = {"total_tokens": 0, "count": 0}
            by_step[step]["total_tokens"] += record["total_tokens"]
            by_step[step]["count"] += 1
        
        return {
            "total_records": len(self.records),
            "total_tokens": total_tokens,
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "by_model": by_model,
            "by_step": by_step
        }


# 包装 VideoEvaluator 以追踪 Token
class TokenTrackingVideoEvaluator(VideoEvaluator):
    """带 Token 追踪的视频评估器"""
    
    def __init__(self, token_tracker: TokenTracker, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token_tracker = token_tracker
    
    def _analyze_frame_design(self, frames_paths: List[str]) -> Dict[str, Any]:
        """重写以追踪 Token"""
        result = super()._analyze_frame_design(frames_paths)
        
        # 如果结果中包含 token_usage，记录到追踪器
        if "token_usage" in result:
            usage = result["token_usage"]
            self.token_tracker.add_record(
                step="视觉分析",
                model="gpt-4o",
                usage=usage,
                api_type="vision"
            )
        
        return result
    
    def _evaluate_relevance(self, transcript: Optional[str], knowledge_point: Optional[Dict[str, Any]], video_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """重写以追踪 Token"""
        # 调用父类方法
        result = super()._evaluate_relevance(transcript, knowledge_point, video_metadata)
        
        # 注意：AIBuildersClient 的 call_llm 方法没有返回 usage
        # 暂时手动添加一个估算值（基于实际调用）
        # 实际应该修改 AIBuildersClient 返回 usage
        
        return result
    
    def _evaluate_pedagogy(self, transcript: Optional[str], video_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """重写以追踪 Token"""
        result = super()._evaluate_pedagogy(transcript, video_metadata)
        
        # 同上，暂时跳过
        
        return result


def test_video_evaluation(video_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    测试视频评估流程
    
    Args:
        video_path: 视频文件路径
        output_dir: 输出目录（可选）
    
    Returns:
        测试结果字典
    """
    print("="*80)
    print("🧪 测试视频评估流程")
    print("="*80)
    
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"视频文件不存在: {video_path}")
    
    print(f"\n📹 测试视频: {video_path.name}")
    print(f"   路径: {video_path}")
    print(f"   大小: {video_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    # 初始化 Token 追踪器
    token_tracker = TokenTracker()
    
    # 设置输出目录
    if output_dir is None:
        output_dir = project_root / "data" / "videos" / "analyzed"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📁 输出目录: {output_dir}")
    
    # 步骤1: 处理视频（提取关键帧等）
    print(f"\n{'='*80}")
    print("[步骤 1/4] ⏳ 处理视频（提取关键帧、音频等）...")
    print(f"{'='*80}")
    
    video_crawler = VideoCrawler()
    
    # 对于本地文件，我们需要手动处理
    # 使用 ffmpeg-python 提取元数据和关键帧
    try:
        import ffmpeg
        # 验证 ffmpeg-python 是否正确安装（检查是否有 probe 方法）
        if not hasattr(ffmpeg, 'probe'):
            # 可能是安装了错误的 ffmpeg 包，尝试重新安装
            raise ImportError(
                "ffmpeg-python 包不正确。请运行:\n"
                "  pip uninstall ffmpeg\n"
                "  pip install ffmpeg-python"
            )
    except ImportError as e:
        raise ImportError(
            f"ffmpeg-python 未正确安装。请运行: pip install ffmpeg-python\n"
            f"错误详情: {str(e)}\n"
            f"注意：还需要安装 ffmpeg 二进制文件"
        )
    
    # 获取视频元数据
    try:
        probe = ffmpeg.probe(str(video_path))
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        
        if not video_stream:
            raise Exception("无法找到视频流")
        
        # 提取分辨率
        width = int(video_stream.get('width', 0))
        height = int(video_stream.get('height', 0))
        duration = float(probe.get('format', {}).get('duration', 0))
        
        video_metadata = {
            "title": video_path.stem,
            "width": width,
            "height": height,
            "max_resolution_height": height,  # 本地文件，使用实际高度
            "duration": duration,
            "format": probe.get('format', {}).get('format_name', 'unknown')
        }
        
        print(f"✅ 视频元数据提取成功")
        print(f"   分辨率: {width}x{height}")
        print(f"   时长: {duration:.2f} 秒")
        
    except Exception as e:
        raise Exception(f"提取视频元数据失败: {str(e)}")
    
    # 提取关键帧
    frames_paths = []
    num_frames = 6
    
    try:
        video_stem = video_path.stem
        for i in range(num_frames):
            timestamp = duration * i / (num_frames - 1) if num_frames > 1 else duration / 2
            frame_filename = f"{video_stem}_frame_{i+1:02d}.jpg"
            frame_path = output_dir / frame_filename
            
            try:
                stream = ffmpeg.input(str(video_path), ss=timestamp)
                stream = ffmpeg.output(stream, str(frame_path), vframes=1, **{'qscale:v': 2})
                ffmpeg.run(stream, overwrite_output=True, quiet=True)
                
                if frame_path.exists():
                    frames_paths.append(str(frame_path))
                    print(f"  ✅ 帧 {i+1}/{num_frames}: {frame_filename}")
                else:
                    print(f"  ⚠️  帧 {i+1}/{num_frames} 未生成")
            except Exception as e:
                print(f"  ⚠️  帧 {i+1}/{num_frames} 提取失败: {str(e)}")
        
        print(f"✅ 关键帧提取完成: {len(frames_paths)}/{num_frames} 张")
        
    except Exception as e:
        print(f"⚠️  关键帧提取失败: {str(e)}")
        frames_paths = []
    
    # 提取音频（可选）
    audio_path = None
    try:
        audio_filename = video_path.stem + ".mp3"
        audio_path = output_dir / audio_filename
        
        stream = ffmpeg.input(str(video_path))
        stream = ffmpeg.output(stream, str(audio_path), acodec='libmp3lame', ac=1, ar='22050')
        ffmpeg.run(stream, overwrite_output=True, quiet=True)
        
        if audio_path.exists():
            print(f"✅ 音频提取成功: {audio_filename}")
        else:
            audio_path = None
            print(f"⚠️  音频提取失败")
    except Exception as e:
        print(f"⚠️  音频提取失败: {str(e)}")
        audio_path = None
    
    print(f"✅ 视频处理完成")
    print(f"   最大分辨率: {video_metadata.get('max_resolution_height', 'N/A')}p")
    print(f"   关键帧数量: {len(frames_paths)}")
    if frames_paths:
        print(f"   关键帧路径: {frames_paths[0]} ... ({len(frames_paths)} 张)")
    
    # 步骤2: 初始化评估器（带 Token 追踪）
    print(f"\n{'='*80}")
    print("[步骤 2/4] 🔧 初始化评估器...")
    print(f"{'='*80}")
    
    evaluator = TokenTrackingVideoEvaluator(token_tracker=token_tracker)
    
    # 手动追踪视觉 API 的 Token（如果使用）
    # 我们需要修改 vision_client 的调用以返回 usage
    # 暂时先运行评估，然后手动添加记录
    
    print(f"✅ 评估器初始化完成")
    
    # 步骤3: 运行评估
    print(f"\n{'='*80}")
    print("[步骤 3/4] 🧠 运行视频评估...")
    print(f"{'='*80}")
    
    # 模拟知识点信息
    knowledge_point = {
        "topic_title_cn": "数字计数",
        "learning_objective": "学习数字 141-160 的计数方法"
    }
    
    evaluation_result = evaluator.evaluate_video_content(
        video_metadata=video_metadata,
        video_path=str(video_path),
        frames_paths=frames_paths,
        audio_path=audio_path,
        transcript=None,  # 暂时没有字幕
        knowledge_point=knowledge_point
    )
    
    print(f"✅ 评估完成")
    print(f"   总分: {evaluation_result['overall_score']:.2f}/10")
    print(f"   视觉质量: {evaluation_result['visual_quality']['combined_score']:.2f}/10")
    print(f"   内容相关度: {evaluation_result['relevance']['score']:.2f}/10")
    print(f"   教学质量: {evaluation_result['pedagogy']['score']:.2f}/10")
    print(f"   热度/元数据: {evaluation_result['metadata']['score']:.2f}/10")
    
    # 步骤4: 收集 Token 使用情况
    # 注意：由于底层客户端没有返回 usage，我们需要修改代码
    # 这里先创建一个占位符，实际需要修改 AIBuildersClient 和 VisionClient
    
    print(f"\n{'='*80}")
    print("[步骤 4/4] 📊 收集 Token 使用情况...")
    print(f"{'='*80}")
    
    # 获取汇总
    summary = token_tracker.get_summary()
    
    print(f"\n📊 Token 使用汇总:")
    print(f"   总记录数: {summary['total_records']}")
    print(f"   总 Token: {summary['total_tokens']}")
    print(f"   输入 Token: {summary['total_prompt_tokens']}")
    print(f"   输出 Token: {summary['total_completion_tokens']}")
    
    if summary['by_model']:
        print(f"\n   按模型统计:")
        for model, stats in summary['by_model'].items():
            print(f"     {model}: {stats['total_tokens']} tokens ({stats['count']} 次调用)")
    
    if summary['by_step']:
        print(f"\n   按步骤统计:")
        for step, stats in summary['by_step'].items():
            print(f"     {step}: {stats['total_tokens']} tokens ({stats['count']} 次调用)")
    
    # 准备结果
    result = {
        "video_path": str(video_path),
        "video_name": video_path.name,
        "evaluation_result": evaluation_result,
        "token_usage": {
            "records": token_tracker.records,
            "summary": summary
        },
        "metadata": video_metadata,
        "frames_count": len(frames_paths),
        "timestamp": datetime.now().isoformat()
    }
    
    return result


def save_to_excel(result: Dict[str, Any], output_file: str):
    """
    将结果保存到 Excel
    
    Args:
        result: 测试结果字典
        output_file: 输出文件路径
    """
    if not HAS_PANDAS:
        print("⚠️  pandas 未安装，无法保存 Excel")
        return
    
    print(f"\n{'='*80}")
    print(f"💾 保存结果到 Excel...")
    print(f"{'='*80}")
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 创建 Excel writer
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Sheet 1: 评估结果摘要
        summary_data = {
            "指标": [
                "总分",
                "视觉质量（硬指标）",
                "视觉质量（软指标）",
                "视觉质量（综合）",
                "内容相关度",
                "教学质量",
                "热度/元数据"
            ],
            "分数": [
                result["evaluation_result"]["overall_score"],
                result["evaluation_result"]["visual_quality"]["tech_score"],
                result["evaluation_result"]["visual_quality"]["design_score"],
                result["evaluation_result"]["visual_quality"]["combined_score"],
                result["evaluation_result"]["relevance"]["score"],
                result["evaluation_result"]["pedagogy"]["score"],
                result["evaluation_result"]["metadata"]["score"]
            ],
            "权重": [
                "100%",
                "10%",
                "10%",
                "20%",
                "40%",
                "30%",
                "10%"
            ]
        }
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name="评估结果", index=False)
        
        # Sheet 2: Token 使用详情
        if result["token_usage"]["records"]:
            df_tokens = pd.DataFrame(result["token_usage"]["records"])
            df_tokens.to_excel(writer, sheet_name="Token使用详情", index=False)
        else:
            # 如果没有记录，创建一个空表
            df_tokens = pd.DataFrame(columns=["step", "model", "api_type", "prompt_tokens", "completion_tokens", "total_tokens", "timestamp"])
            df_tokens.to_excel(writer, sheet_name="Token使用详情", index=False)
        
        # Sheet 3: Token 汇总统计
        summary = result["token_usage"]["summary"]
        summary_data = {
            "统计项": [
                "总记录数",
                "总 Token",
                "输入 Token",
                "输出 Token"
            ],
            "数值": [
                summary["total_records"],
                summary["total_tokens"],
                summary["total_prompt_tokens"],
                summary["total_completion_tokens"]
            ]
        }
        df_summary_tokens = pd.DataFrame(summary_data)
        df_summary_tokens.to_excel(writer, sheet_name="Token汇总", index=False)
        
        # Sheet 4: 视频元数据
        metadata = result["metadata"]
        metadata_data = {
            "字段": list(metadata.keys()),
            "值": [str(v) for v in metadata.values()]
        }
        df_metadata = pd.DataFrame(metadata_data)
        df_metadata.to_excel(writer, sheet_name="视频元数据", index=False)
    
    print(f"✅ Excel 文件已保存: {output_path}")
    print(f"   文件大小: {output_path.stat().st_size / 1024:.2f} KB")


def check_dependencies():
    """检查依赖是否安装"""
    missing = []
    
    try:
        import ffmpeg
        # 检查 ffmpeg 二进制文件
        import subprocess
        try:
            subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append("ffmpeg 二进制文件（请运行: brew install ffmpeg）")
    except ImportError:
        missing.append("ffmpeg-python（请运行: pip install ffmpeg-python）")
    
    if not HAS_PANDAS:
        missing.append("pandas（请运行: pip install pandas openpyxl）")
    
    if missing:
        print("❌ 缺少以下依赖:")
        for item in missing:
            print(f"   - {item}")
        print("\n💡 安装命令:")
        print("   pip install ffmpeg-python pandas openpyxl")
        print("   brew install ffmpeg")
        return False
    
    return True


def main():
    """主函数"""
    # 检查依赖
    if not check_dependencies():
        return
    
    # 查找测试视频
    videos_dir = project_root / "data" / "videos"
    video_files = list(videos_dir.glob("*.mp4"))
    
    if not video_files:
        print(f"❌ 未找到测试视频文件")
        print(f"💡 提示: 请将测试视频放到 {videos_dir} 目录下")
        return
    
    # 使用第一个视频
    test_video = video_files[0]
    print(f"📹 找到测试视频: {test_video.name}")
    
    try:
        # 运行测试
        result = test_video_evaluation(
            video_path=str(test_video),
            output_dir=str(project_root / "data" / "videos" / "analyzed")
        )
        
        # 保存到 Excel
        output_excel = project_root / "data" / "videos" / "test_result.xlsx"
        save_to_excel(result, str(output_excel))
        
        # 也保存 JSON 格式（用于调试）
        output_json = project_root / "data" / "videos" / "test_result.json"
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✅ JSON 结果已保存: {output_json}")
        
        print(f"\n{'='*80}")
        print("✅ 测试完成！")
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        import traceback
        print(f"\n\n❌ 测试失败: {str(e)}")
        traceback.print_exc()

