#!/usr/bin/env python3
"""
字幕/转录提取器 - TranscriptExtractor
优先使用官方字幕，如果没有则使用Whisper进行音频转录
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Optional, Any

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

try:
    import whisper
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False

from logger_utils import get_logger

logger = get_logger('transcript_extractor')


class TranscriptExtractor:
    """
    字幕/转录提取器
    优先使用官方字幕，如果没有则使用Whisper进行音频转录
    """
    
    def __init__(self):
        """初始化 TranscriptExtractor"""
        if yt_dlp is None:
            logger.warning("⚠️  yt-dlp 未安装，无法提取字幕")
        if not HAS_WHISPER:
            logger.warning("⚠️  whisper 未安装，无法进行音频转录。请运行: pip install openai-whisper")
    
    def extract_transcript(
        self,
        video_url: str,
        audio_path: Optional[str] = None,
        output_dir: Optional[str] = None,
        preferred_languages: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        提取视频字幕/转录文本
        
        策略：
        1. 优先尝试提取官方字幕（使用yt-dlp）
        2. 如果没有官方字幕，使用Whisper进行音频转录
        
        Args:
            video_url: 视频URL
            audio_path: 音频文件路径（如果已提取，用于Whisper转录）
            output_dir: 输出目录（用于保存字幕文件）
            preferred_languages: 首选字幕语言列表（如 ['en', 'id', 'zh']）
        
        Returns:
            {
                "success": bool,
                "transcript": str,  # 字幕/转录文本
                "source": str,  # "subtitle" 或 "whisper"
                "language": str,  # 检测到的语言
                "subtitle_path": str,  # 字幕文件路径（如果提取了字幕）
                "error": str
            }
        """
        result = {
            "success": False,
            "transcript": "",
            "source": "",
            "language": "",
            "subtitle_path": None,
            "error": None
        }
        
        # 步骤1: 尝试提取官方字幕
        logger.info(f"📝 步骤1: 尝试提取官方字幕...")
        subtitle_result = self._extract_subtitles(video_url, output_dir, preferred_languages)
        
        if subtitle_result["success"]:
            logger.info(f"✅ 成功提取官方字幕（语言: {subtitle_result.get('language', 'unknown')}）")
            result.update({
                "success": True,
                "transcript": subtitle_result["transcript"],
                "source": "subtitle",
                "language": subtitle_result.get("language", "unknown"),
                "subtitle_path": subtitle_result.get("subtitle_path")
            })
            return result
        
        logger.warning(f"⚠️  无法提取官方字幕: {subtitle_result.get('error', '未知错误')}")
        
        # 步骤2: 如果没有字幕，使用Whisper进行音频转录
        if not audio_path:
            result["error"] = "无音频文件路径，无法进行Whisper转录"
            logger.error(f"❌ {result['error']}")
            return result
        
        if not HAS_WHISPER:
            result["error"] = "Whisper未安装，无法进行音频转录"
            logger.error(f"❌ {result['error']}")
            return result
        
        logger.info(f"📝 步骤2: 使用Whisper进行音频转录...")
        whisper_result = self._transcribe_with_whisper(audio_path)
        
        if whisper_result["success"]:
            logger.info(f"✅ Whisper转录成功（语言: {whisper_result.get('language', 'unknown')}）")
            result.update({
                "success": True,
                "transcript": whisper_result["transcript"],
                "source": "whisper",
                "language": whisper_result.get("language", "unknown")
            })
        else:
            result["error"] = whisper_result.get("error", "Whisper转录失败")
            logger.error(f"❌ {result['error']}")
        
        return result
    
    def _extract_subtitles(
        self,
        video_url: str,
        output_dir: Optional[str] = None,
        preferred_languages: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        使用yt-dlp提取官方字幕
        
        Args:
            video_url: 视频URL
            output_dir: 输出目录
            preferred_languages: 首选语言列表（如 ['en', 'id', 'zh']）
        
        Returns:
            {
                "success": bool,
                "transcript": str,
                "language": str,
                "subtitle_path": str,
                "error": str
            }
        """
        result = {
            "success": False,
            "transcript": "",
            "language": "",
            "subtitle_path": None,
            "error": None
        }
        
        if yt_dlp is None:
            result["error"] = "yt-dlp 未安装"
            return result
        
        try:
            # 步骤1: 检查可用字幕
            logger.info(f"    [🔍 检查] 检查视频可用字幕...")
            check_opts = {
                'quiet': True,
                'no_warnings': True,
                'listsubtitles': True,  # 列出可用字幕
            }
            
            available_subtitles = {}
            with yt_dlp.YoutubeDL(check_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                available_subtitles = info.get('subtitles', {})
                # 也检查自动生成的字幕
                auto_subs = info.get('automatic_captions', {})
                if auto_subs:
                    available_subtitles.update(auto_subs)
            
            if not available_subtitles:
                result["error"] = "视频没有可用字幕"
                logger.info(f"    [⚠️ 结果] {result['error']}")
                return result
            
            logger.info(f"    [✅ 发现] 找到 {len(available_subtitles)} 种字幕语言: {list(available_subtitles.keys())}")
            
            # 步骤2: 选择最佳字幕语言
            selected_lang = self._select_best_subtitle_language(available_subtitles, preferred_languages)
            
            if not selected_lang:
                result["error"] = "无法选择合适的字幕语言"
                return result
            
            logger.info(f"    [📌 选择] 使用字幕语言: {selected_lang}")
            
            # 步骤3: 下载字幕
            if output_dir:
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
            else:
                output_path = Path("./temp_subtitles")
                output_path.mkdir(parents=True, exist_ok=True)
            
            download_opts = {
                'writesubtitles': True,
                'writeautomaticsub': True,  # 也下载自动生成的字幕
                'subtitleslangs': [selected_lang],
                'subtitlesformat': 'vtt',  # 使用VTT格式（更易解析）
                'skip_download': True,  # 只下载字幕，不下载视频
                'outtmpl': str(output_path / 'subtitle.%(ext)s'),
                'quiet': False,
                # 添加HTTP头以绕过403错误
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                },
                # YouTube特定配置
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web'],  # 使用Android客户端（更稳定）
                    }
                },
                # 添加重试机制
                'retries': 3,
                'fragment_retries': 3,
            }
            
            with yt_dlp.YoutubeDL(download_opts) as ydl:
                ydl.download([video_url])
            
            # 步骤4: 查找并解析字幕文件
            subtitle_files = list(output_path.glob(f"subtitle.{selected_lang}.*"))
            if not subtitle_files:
                # 尝试查找其他格式
                subtitle_files = list(output_path.glob(f"subtitle.*"))
            
            if not subtitle_files:
                result["error"] = "字幕文件未找到"
                return result
            
            subtitle_path = subtitle_files[0]
            logger.info(f"    [📄 文件] 字幕文件: {subtitle_path.name}")
            
            # 步骤5: 解析字幕文件（VTT格式）
            transcript = self._parse_vtt_subtitle(subtitle_path)
            
            if not transcript:
                result["error"] = "字幕文件解析失败"
                return result
            
            result["success"] = True
            result["transcript"] = transcript
            result["language"] = selected_lang
            result["subtitle_path"] = str(subtitle_path)
            
            logger.info(f"    [✅ 完成] 提取字幕成功，长度: {len(transcript)} 字符")
            
        except Exception as e:
            error_msg = f"提取字幕失败: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            result["error"] = error_msg
        
        return result
    
    def _select_best_subtitle_language(
        self,
        available_subtitles: Dict[str, Any],
        preferred_languages: Optional[list] = None
    ) -> Optional[str]:
        """
        选择最佳字幕语言
        
        Args:
            available_subtitles: 可用字幕字典
            preferred_languages: 首选语言列表（优先级从高到低）
        
        Returns:
            选中的语言代码（如 'en', 'id', 'zh'）
        """
        if not available_subtitles:
            return None
        
        available_langs = list(available_subtitles.keys())
        
        # 如果有首选语言列表，按优先级选择
        if preferred_languages:
            for lang in preferred_languages:
                if lang in available_langs:
                    return lang
                # 也尝试匹配变体（如 'en-US' 匹配 'en'）
                for available_lang in available_langs:
                    if available_lang.startswith(lang) or lang in available_lang:
                        return available_lang
        
        # 如果没有首选语言，优先选择常见语言
        common_languages = ['en', 'id', 'zh', 'zh-CN', 'zh-TW', 'es', 'fr', 'de', 'ja', 'ko']
        for lang in common_languages:
            if lang in available_langs:
                return lang
        
        # 如果都不匹配，返回第一个可用语言
        return available_langs[0]
    
    def _parse_vtt_subtitle(self, subtitle_path: Path) -> str:
        """
        解析VTT格式字幕文件
        
        Args:
            subtitle_path: 字幕文件路径
        
        Returns:
            纯文本字幕内容
        """
        try:
            with open(subtitle_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # VTT格式解析
            lines = content.split('\n')
            transcript_lines = []
            
            for line in lines:
                line = line.strip()
                # 跳过VTT头部和元数据
                if not line or line.startswith('WEBVTT') or line.startswith('NOTE') or '-->' in line:
                    continue
                # 跳过时间戳行
                if ':' in line and ('-->' in line or line.count(':') >= 2):
                    continue
                # 收集文本行
                if line:
                    transcript_lines.append(line)
            
            transcript = ' '.join(transcript_lines)
            
            # 清理多余空格
            transcript = ' '.join(transcript.split())
            
            return transcript
            
        except Exception as e:
            logger.error(f"解析VTT字幕失败: {str(e)}")
            return ""
    
    def _transcribe_with_whisper(self, audio_path: str) -> Dict[str, Any]:
        """
        使用Whisper进行音频转录
        
        Args:
            audio_path: 音频文件路径
        
        Returns:
            {
                "success": bool,
                "transcript": str,
                "language": str,
                "error": str
            }
        """
        result = {
            "success": False,
            "transcript": "",
            "language": "",
            "error": None
        }
        
        if not HAS_WHISPER:
            result["error"] = "Whisper未安装"
            return result
        
        if not os.path.exists(audio_path):
            result["error"] = f"音频文件不存在: {audio_path}"
            return result
        
        try:
            logger.info(f"    [🎤 Whisper] 开始加载模型...")
            # 使用base模型（平衡速度和准确性）
            # 可选模型: tiny, base, small, medium, large
            model = whisper.load_model("base")
            
            logger.info(f"    [🎤 Whisper] 开始转录音频...")
            transcription = model.transcribe(
                audio_path,
                language=None,  # 自动检测语言
                task="transcribe",  # 转录任务
                fp16=False,  # 不使用FP16（兼容性更好）
                verbose=False
            )
            
            transcript = transcription.get("text", "").strip()
            detected_language = transcription.get("language", "unknown")
            
            if transcript:
                result["success"] = True
                result["transcript"] = transcript
                result["language"] = detected_language
                logger.info(f"    [✅ Whisper] 转录成功，语言: {detected_language}，长度: {len(transcript)} 字符")
            else:
                result["error"] = "Whisper转录结果为空"
                logger.warning(f"    [⚠️ Whisper] {result['error']}")
            
        except Exception as e:
            error_msg = f"Whisper转录失败: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            result["error"] = error_msg
        
        return result

