#!/usr/bin/env python3
"""
视频处理服务 - VideoProcessorService
用于下载视频并提取多模态数据（音频、关键帧、元数据）
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

try:
    import ffmpeg
except ImportError:
    ffmpeg = None

from utils.logger_utils import get_logger

logger = get_logger('video_processor')


class VideoCrawler:
    """
    视频爬虫类，负责下载视频并提取多模态数据
    """
    
    def __init__(self):
        """初始化 VideoCrawler"""
        if yt_dlp is None:
            logger.error("❌ yt-dlp 未安装，请运行: pip install yt-dlp")
        if ffmpeg is None:
            logger.error("❌ ffmpeg-python 未安装，请运行: pip install ffmpeg-python")
            logger.warning("⚠️  注意：还需要安装 ffmpeg 二进制文件: brew install ffmpeg (macOS) 或 apt-get install ffmpeg (Linux)")
    
    def process_video(
        self,
        video_url: str,
        output_dir: str,
        video_quality: str = "480p",
        num_frames: int = 6,
        extract_transcript: bool = True,
        preferred_languages: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        处理视频：下载、提取音频和关键帧
        
        Args:
            video_url: 视频URL（支持 YouTube, Bilibili, 等）
            output_dir: 输出目录路径
            video_quality: 视频质量 ("360p", "480p", "720p", "best")
            num_frames: 提取的关键帧数量（默认6张）
            extract_transcript: 是否提取字幕/转录（默认True）
            preferred_languages: 首选字幕语言列表（如 ['en', 'id', 'zh']）
        
        Returns:
            字典包含：
            {
                "success": bool,
                "metadata": dict,  # 视频元数据
                "audio_path": str,  # 音频文件路径
                "frames_paths": List[str],  # 关键帧路径列表
                "video_path": str,  # 视频文件路径
                "transcript": str,  # 字幕/转录文本（如果提取）
                "transcript_source": str,  # "subtitle" 或 "whisper"（如果提取）
                "transcript_language": str,  # 字幕/转录语言（如果提取）
                "error": str  # 错误信息（如果失败）
            }
        """
        result = {
            "success": False,
            "metadata": {},
            "audio_path": None,
            "frames_paths": [],
            "video_path": None,
            "transcript": None,
            "transcript_source": None,
            "transcript_language": None,
            "error": None
        }
        
        try:
            # 创建输出目录
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 输出目录: {output_path.absolute()}")
            
            # 检查是否是播放列表URL，如果是则提取第一个视频
            actual_video_url = video_url
            if 'youtube.com' in video_url and ('list=' in video_url or '/playlist' in video_url):
                logger.info(f"📋 检测到播放列表URL，提取第一个视频...")
                try:
                    from core.playlist_processor import PlaylistProcessor
                    playlist_processor = PlaylistProcessor()
                    playlist_result = playlist_processor.extract_videos_from_playlist(video_url, max_videos=1)
                    if playlist_result.get('success') and playlist_result.get('videos'):
                        first_video = playlist_result['videos'][0]
                        actual_video_url = first_video.get('url', video_url)
                        logger.info(f"✅ 提取到第一个视频: {first_video.get('title', 'N/A')}")
                        logger.info(f"   视频URL: {actual_video_url}")
                    else:
                        # 如果提取失败，尝试使用网页抓取获取播放列表的第一个视频
                        logger.warning(f"⚠️ 播放列表提取失败，尝试网页抓取方法...")
                        import re
                        import urllib.request
                        import urllib.parse
                        playlist_id_match = re.search(r'list=([^&]+)', video_url)
                        if playlist_id_match:
                            playlist_id = playlist_id_match.group(1)
                            logger.info(f"   播放列表ID: {playlist_id}")
                            # 方法1: 尝试使用yt-dlp的webpage方式
                            try:
                                import yt_dlp
                                # 使用webpage_downloader来获取播放列表页面内容
                                ydl_opts = {
                                    'quiet': True,
                                    'no_warnings': True,
                                    'extract_flat': False,  # 需要完整信息
                                    'playlistend': 1,
                                    'http_headers': {
                                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                                    },
                                    'extractor_args': {
                                        'youtube': {
                                            'player_client': ['web'],  # 只使用web客户端
                                            'skip': ['dash', 'hls'],  # 跳过某些格式
                                        }
                                    },
                                    'ignoreerrors': True,  # 忽略错误继续处理
                                }
                                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                    # 尝试使用不同的URL格式
                                    test_urls = [
                                        video_url,
                                        f"https://www.youtube.com/playlist?list={playlist_id}",
                                        f"https://youtube.com/playlist?list={playlist_id}"
                                    ]
                                    for test_url in test_urls:
                                        try:
                                            info = ydl.extract_info(test_url, download=False)
                                            if info:
                                                # 检查是否是播放列表
                                                if '_type' in info and info['_type'] == 'playlist':
                                                    entries = list(info.get('entries', []))
                                                    if entries and entries[0]:
                                                        first_entry = entries[0]
                                                        video_id = first_entry.get('id', '') or first_entry.get('url', '').split('watch?v=')[-1].split('&')[0]
                                                        if video_id:
                                                            actual_video_url = f"https://www.youtube.com/watch?v={video_id}"
                                                            logger.info(f"✅ 备用方法成功，提取到视频ID: {video_id}")
                                                            logger.info(f"   视频URL: {actual_video_url}")
                                                            break
                                                # 如果直接是视频信息
                                                elif 'id' in info:
                                                    video_id = info['id']
                                                    actual_video_url = f"https://www.youtube.com/watch?v={video_id}"
                                                    logger.info(f"✅ 提取到视频ID: {video_id}")
                                                    logger.info(f"   视频URL: {actual_video_url}")
                                                    break
                                        except Exception as e_test:
                                            logger.debug(f"   测试URL失败 {test_url}: {str(e_test)[:100]}")
                                            continue
                            except Exception as e2:
                                logger.warning(f"⚠️ 备用方法也失败: {str(e2)[:200]}")
                                # 最后尝试：如果URL中包含v=参数，直接使用
                                video_match = re.search(r'[?&]v=([^&]+)', video_url)
                                if video_match:
                                    video_id = video_match.group(1)
                                    actual_video_url = f"https://www.youtube.com/watch?v={video_id}"
                                    logger.info(f"✅ 从URL中提取到视频ID: {video_id}")
                                    logger.info(f"   视频URL: {actual_video_url}")
                                else:
                                    logger.warning(f"⚠️ 无法提取播放列表视频，将返回错误")
                                    result["error"] = f"无法从播放列表提取视频。yt-dlp当前版本无法识别此播放列表页面。建议：1) 使用播放列表中的单个视频URL进行评估；2) 或使用批量评估功能。错误详情: {playlist_result.get('error', '未知错误')[:200]}"
                                    return result
                except Exception as e:
                    logger.warning(f"⚠️ 播放列表处理失败: {str(e)[:200]}")
                    # 如果actual_video_url仍然是播放列表URL，返回错误
                    if 'playlist' in actual_video_url.lower() and 'watch?v=' not in actual_video_url:
                        result["error"] = f"无法从播放列表提取视频。yt-dlp当前版本无法识别此播放列表页面。建议：1) 使用播放列表中的单个视频URL进行评估；2) 或使用批量评估功能。错误详情: {str(e)[:200]}"
                        logger.error(f"❌ {result['error']}")
                        return result
            
            # 检查actual_video_url是否是有效的视频URL
            if 'playlist' in actual_video_url.lower() and 'watch?v=' not in actual_video_url:
                result["error"] = "无法从播放列表提取视频URL。yt-dlp当前版本无法识别此播放列表页面。建议：1) 使用播放列表中的单个视频URL进行评估；2) 或使用批量评估功能。"
                logger.error(f"❌ {result['error']}")
                return result
            
            # 步骤1: 下载视频和提取元数据
            logger.info(f"🎬 开始处理视频: {actual_video_url}")
            download_result = self._download_video(actual_video_url, output_path, video_quality)
            
            # 检查 download_result 是否为 None（防止异常情况）
            if download_result is None:
                result["error"] = "视频下载失败: 下载函数返回了None"
                logger.error(f"❌ {result['error']}")
                return result
            
            if not download_result.get("success", False):
                result["error"] = download_result.get("error", "视频下载失败")
                logger.error(f"❌ {result['error']}")
                return result
            
            video_path = download_result["video_path"]
            metadata = download_result["metadata"]
            result["video_path"] = str(video_path)
            result["local_file_path"] = str(video_path)  # 添加本地文件路径字段
            result["metadata"] = metadata
            
            logger.info(f"✅ 视频下载成功: {video_path}")
            logger.info(f"📊 元数据: {json.dumps(metadata, indent=2, ensure_ascii=False)}")
            
            # 步骤2: 提取音频
            logger.info("🎵 开始提取音频...")
            audio_result = self._extract_audio(video_path, output_path)
            
            if audio_result["success"]:
                result["audio_path"] = str(audio_result["audio_path"])
                logger.info(f"✅ 音频提取成功: {result['audio_path']}")
            else:
                logger.warning(f"⚠️  音频提取失败: {audio_result.get('error')}")
            
            # 步骤3: 提取关键帧
            logger.info(f"🖼️  开始提取 {num_frames} 张关键帧...")
            frames_result = self._extract_keyframes(video_path, output_path, num_frames)
            
            if frames_result["success"]:
                result["frames_paths"] = [str(p) for p in frames_result["frames_paths"]]
                logger.info(f"✅ 关键帧提取成功: {len(result['frames_paths'])} 张")
            else:
                logger.warning(f"⚠️  关键帧提取失败: {frames_result.get('error')}")
            
            # 步骤4: 提取字幕/转录（如果启用）
            if extract_transcript:
                logger.info("📝 开始提取字幕/转录...")
                try:
                    from core.transcript_extractor import TranscriptExtractor
                    transcript_extractor = TranscriptExtractor()
                    transcript_result = transcript_extractor.extract_transcript(
                        video_url=video_url,
                        audio_path=result["audio_path"],
                        output_dir=str(output_path),
                        preferred_languages=preferred_languages
                    )
                    
                    if transcript_result["success"]:
                        result["transcript"] = transcript_result["transcript"]
                        result["transcript_source"] = transcript_result["source"]
                        result["transcript_language"] = transcript_result.get("language", "unknown")
                        logger.info(f"✅ 字幕/转录提取成功（来源: {result['transcript_source']}, 语言: {result['transcript_language']}）")
                        logger.info(f"    文本长度: {len(result['transcript'])} 字符")
                    else:
                        logger.warning(f"⚠️  字幕/转录提取失败: {transcript_result.get('error')}")
                except ImportError as e:
                    logger.warning(f"⚠️  TranscriptExtractor 不可用: {str(e)}")
                except Exception as e:
                    logger.warning(f"⚠️  字幕/转录提取异常: {str(e)}")
            
            result["success"] = True
            logger.info("🎉 视频处理完成！")
            
        except Exception as e:
            error_msg = f"处理视频时发生异常: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            result["error"] = error_msg
        
        return result
    
    def _download_video(
        self,
        video_url: str,
        output_dir: Path,
        video_quality: str = "480p"
    ) -> Dict[str, Any]:
        """
        下载视频（性能优化版本）
        
        核心逻辑：
        1. 先提取元数据，获取最大分辨率高度（用于评分）
        2. 然后下载低清版（bestaudio + worstvideo[height>=360]）用于内容分析
        
        Returns:
            {
                "success": bool,
                "video_path": Path,
                "metadata": dict,  # 包含 max_resolution_height
                "error": str
            }
        """
        """
        使用 yt-dlp 下载视频
        
        核心逻辑：
        1. 先提取元数据，获取最大分辨率高度（用于评分）
        2. 然后下载低清版（bestaudio + worstvideo[height>=360]）用于内容分析
        
        Returns:
            {
                "success": bool,
                "video_path": Path,
                "metadata": dict,  # 包含 max_resolution_height
                "error": str
            }
        """
        if yt_dlp is None:
            return {
                "success": False,
                "video_path": None,
                "metadata": {},
                "error": "yt-dlp 未安装"
            }
        
        try:
            logger.info(f"📥 步骤1: 提取视频元数据（不下载）...")
            
            # 步骤1: 先提取元数据，获取最大分辨率
            extract_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                # 添加HTTP头以绕过403错误
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                },
                # YouTube特定配置 - 尝试多个客户端
                'extractor_args': {
                    'youtube': {
                        'player_client': ['ios', 'android', 'web'],  # 优先使用iOS，然后是Android，最后是Web
                    }
                },
                # 添加重试和延迟
                'retries': 5,
                'fragment_retries': 5,
                'sleep_interval': 1,
                'max_sleep_interval': 3,
            }
            
            with yt_dlp.YoutubeDL(extract_opts) as ydl:
                # 提取信息（不下载）
                info = ydl.extract_info(video_url, download=False)
            
            # 获取视频ID或标题作为文件名
            video_id = info.get('id', 'video')
            video_title = info.get('title', 'video')
            safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).strip()[:100]
            
            # 查找所有可用格式，找到最大分辨率高度
            formats = info.get('formats', [])
            max_resolution_height = 0
            
            logger.info(f"    [🔍 分析] 分析可用格式，查找最大分辨率...")
            logger.info(f"    [📊 格式总数] {len(formats)} 个格式")
            
            # 方法1: 从所有格式中查找最大分辨率（包括视频+音频组合格式）
            for fmt in formats:
                height = fmt.get('height')
                # 只考虑视频格式（有视频流）
                if height and isinstance(height, (int, float)) and fmt.get('vcodec') != 'none':
                    height_int = int(height)
                    max_resolution_height = max(max_resolution_height, height_int)
                    logger.debug(f"    [📊 格式] {fmt.get('format_id', 'N/A')}: {height_int}p (vcodec: {fmt.get('vcodec', 'N/A')})")
            
            # 方法2: 如果没有找到，尝试从 info 本身获取
            if max_resolution_height == 0:
                height = info.get('height', 0)
                if height:
                    max_resolution_height = int(height)
                    logger.info(f"    [📊 元数据] 从主信息获取分辨率: {max_resolution_height}p")
            
            # 方法3: 尝试使用yt-dlp的best格式来获取最大分辨率
            if max_resolution_height == 0 or max_resolution_height <= 360:
                try:
                    # 尝试获取best格式的信息
                    best_format_opts = {
                        'format': 'best',
                        'quiet': True,
                        'no_warnings': True,
                    }
                    with yt_dlp.YoutubeDL(best_format_opts) as ydl_best:
                        best_info = ydl_best.extract_info(video_url, download=False)
                        best_height = best_info.get('height', 0)
                        if best_height and best_height > max_resolution_height:
                            max_resolution_height = int(best_height)
                            logger.info(f"    [📊 Best格式] 从best格式获取分辨率: {max_resolution_height}p")
                except Exception as e:
                    logger.debug(f"    [⚠️ Best格式] 获取失败: {str(e)}")
            
            # 方法4: 尝试从 requested_formats 获取（如果存在）
            if max_resolution_height == 0:
                requested_formats = info.get('requested_formats', [])
                for fmt in requested_formats:
                    height = fmt.get('height')
                    if height and isinstance(height, (int, float)) and fmt.get('vcodec') != 'none':
                        height_int = int(height)
                        max_resolution_height = max(max_resolution_height, height_int)
                        logger.debug(f"    [📊 请求格式] 发现分辨率: {height_int}p")
            
            # 方法5: 尝试从 format_id 解析（YouTube格式ID规则）
            # YouTube格式ID: 18=360p, 22=720p, 37=1080p, 38=3072p等
            if max_resolution_height == 0:
                format_id = info.get('format_id', '')
                format_map = {
                    '18': 360, '22': 720, '37': 1080, '38': 3072,
                    '133': 240, '134': 360, '135': 480, '136': 720, '137': 1080, '138': 2160
                }
                if format_id in format_map:
                    max_resolution_height = format_map[format_id]
                    logger.info(f"    [📊 格式ID] 从格式ID {format_id} 推断分辨率: {max_resolution_height}p")
            
            # 如果仍然为0或很低，使用默认值1080p（假设YouTube视频至少支持1080p）
            if max_resolution_height == 0 or max_resolution_height <= 360:
                logger.warning(f"    [⚠️ 警告] 检测到的分辨率较低 ({max_resolution_height}p)，尝试使用1080p作为默认值")
                # 先尝试1080p，如果失败再降级
                max_resolution_height = 1080
            
            logger.info(f"    [✅ 完成] 最大分辨率高度: {max_resolution_height}p")
            
            # 步骤2: 下载低清版（bestaudio + worstvideo[height>=360]）
            logger.info(f"📥 步骤2: 下载低清版视频（用于内容分析）...")
            
            # 根据 video_quality 参数和实际可用分辨率选择格式
            # 如果视频最大分辨率低于请求质量，自动降级到可用分辨率
            if video_quality == "360p":
                # 如果视频最大分辨率低于360p，使用实际最大分辨率
                if max_resolution_height < 360:
                    format_selector = f'bestaudio[ext=m4a]/bestaudio+worstvideo[height>={max_resolution_height}]/worstvideo[height>={max_resolution_height}]/worst[height>={max_resolution_height}]/worst'
                else:
                    format_selector = 'bestaudio[ext=m4a]/bestaudio+worstvideo[height>=360]/worstvideo[height>=360]/worst[height>=360]/worst'
            elif video_quality == "480p":
                # 如果视频最大分辨率低于480p，使用实际最大分辨率
                if max_resolution_height < 480:
                    format_selector = f'bestaudio[ext=m4a]/bestaudio+worstvideo[height>={max_resolution_height}]/worstvideo[height>={max_resolution_height}]/worst[height>={max_resolution_height}]/worst'
                else:
                    format_selector = 'bestaudio[ext=m4a]/bestaudio+worstvideo[height>=480]/worstvideo[height>=480]/worst[height>=480]/worst'
            else:
                # 默认使用360p，但如果视频最大分辨率低于360p，使用实际最大分辨率
                if max_resolution_height < 360:
                    format_selector = f'bestaudio[ext=m4a]/bestaudio+worstvideo[height>={max_resolution_height}]/worstvideo[height>={max_resolution_height}]/worst[height>={max_resolution_height}]/worst'
                else:
                    format_selector = 'bestaudio[ext=m4a]/bestaudio+worstvideo[height>=360]/worstvideo[height>=360]/worst[height>=360]/worst'
            
            logger.info(f"    [⚙️ 配置] 下载格式: {format_selector} (视频最大分辨率: {max_resolution_height}p)")
            
            download_opts = {
                'format': format_selector,
                'outtmpl': str(output_dir / f'{safe_title}.%(ext)s'),
                'quiet': False,
                'no_warnings': False,
                'writeinfojson': True,  # 保存元数据JSON
                'writesubtitles': False,
                'writeautomaticsub': False,
                # 添加HTTP头以绕过403错误
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                },
                # YouTube特定配置 - 尝试多个客户端
                'extractor_args': {
                    'youtube': {
                        'player_client': ['ios', 'android', 'web'],  # 优先使用iOS，然后是Android，最后是Web
                    }
                },
                # 添加重试机制和延迟
                'retries': 5,
                'fragment_retries': 5,
                'file_access_retries': 5,
                'sleep_interval': 1,
                'max_sleep_interval': 3,
            }
            
            try:
                with yt_dlp.YoutubeDL(download_opts) as ydl:
                    # 实际下载
                    ydl.download([video_url])
            except yt_dlp.utils.DownloadError as e:
                error_str = str(e)
                # 如果格式选择失败或DRM保护，尝试使用更通用的格式
                if "Requested format is not available" in error_str or "DRM protected" in error_str:
                    logger.warning(f"⚠️ 指定格式不可用或受DRM保护，尝试使用通用格式...")
                    # 排除DRM保护的格式，优先选择非DRM格式
                    download_opts['format'] = 'bestvideo[ext=mp4][height<=480]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480]/best'
                    download_opts['check_formats'] = True  # 自动检查格式并降级
                    logger.info(f"    [⚙️ 重试] 使用格式: {download_opts['format']}")
                    try:
                        with yt_dlp.YoutubeDL(download_opts) as ydl:
                            ydl.download([video_url])
                    except yt_dlp.utils.DownloadError as e2:
                        # 最后一次尝试：使用最简单的格式
                        logger.warning(f"⚠️ 再次失败，尝试最简单的格式...")
                        download_opts['format'] = 'worstvideo+worstaudio/worst'
                        try:
                            with yt_dlp.YoutubeDL(download_opts) as ydl:
                                ydl.download([video_url])
                        except yt_dlp.utils.DownloadError as e3:
                            # 所有重试都失败，抛出异常
                            raise e3
                else:
                    # 不是格式问题，直接抛出异常
                    raise
            
            # 查找下载的文件（无论第一次下载成功还是重试成功，都会执行到这里）
            video_ext = info.get('ext', 'mp4')
            video_filename = f"{safe_title}.{video_ext}"
            video_path = output_dir / video_filename
            
            # 如果文件不存在，尝试查找其他可能的文件名
            if not video_path.exists():
                # 查找目录中最新创建的视频文件
                video_files = list(output_dir.glob(f"*.{video_ext}"))
                if video_files:
                    video_path = max(video_files, key=lambda p: p.stat().st_mtime)
                else:
                    # 尝试其他常见格式
                    for ext in ['mp4', 'webm', 'mkv', 'flv']:
                        video_files = list(output_dir.glob(f"*.{ext}"))
                        if video_files:
                            video_path = max(video_files, key=lambda p: p.stat().st_mtime)
                            break
            
            # 提取元数据（包含最大分辨率高度）
            metadata = {
                "title": info.get('title', ''),
                "description": info.get('description', '')[:500],  # 限制长度
                "duration": info.get('duration', 0),
                "upload_date": info.get('upload_date', ''),
                "view_count": info.get('view_count', 0),
                "like_count": info.get('like_count', 0),
                "channel": info.get('uploader', ''),
                "channel_id": info.get('channel_id', ''),
                "resolution": f"{info.get('width', 0)}x{info.get('height', 0)}",
                "max_resolution_height": max_resolution_height,  # 关键：服务器支持的最大分辨率高度
                "fps": info.get('fps', 0),
                "format": info.get('format', ''),
                "ext": info.get('ext', ''),
                "url": video_url,
            }
            
            logger.info(f"    [📊 元数据] 最大分辨率: {max_resolution_height}p（服务器支持）")
            logger.info(f"    [📊 元数据] 本地下载分辨率: {info.get('height', 'N/A')}p（用于分析）")
            
            # 尝试读取 info.json（如果存在）
            info_json_path = output_dir / f"{safe_title}.info.json"
            if info_json_path.exists():
                try:
                    with open(info_json_path, 'r', encoding='utf-8') as f:
                        full_info = json.load(f)
                        # 补充更多元数据
                        metadata.update({
                            "tags": full_info.get('tags', []),
                            "categories": full_info.get('categories', []),
                            "thumbnail": full_info.get('thumbnail', ''),
                        })
                except Exception as e:
                    logger.warning(f"⚠️  读取 info.json 失败: {e}")
            
            if not video_path.exists():
                return {
                    "success": False,
                    "video_path": None,
                    "metadata": metadata,
                    "error": f"视频文件未找到: {video_filename}"
                }
            
            logger.info(f"✅ 视频下载完成: {video_path.name}")
            return {
                "success": True,
                "video_path": video_path,
                "metadata": metadata,
                "error": None
            }
        
        except Exception as e:
            error_msg = f"下载视频失败: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            return {
                "success": False,
                "video_path": None,
                "metadata": {},
                "error": error_msg
            }
    
    def _get_format_selector(self, quality: str) -> str:
        """
        根据质量要求生成 yt-dlp 格式选择器
        
        注意：此方法已废弃，现在统一使用 bestaudio + worstvideo[height>=360]
        保留此方法以保持向后兼容
        
        Args:
            quality: "360p", "480p", "720p", "best"
        
        Returns:
            yt-dlp 格式选择器字符串
        """
        # 统一使用低清版下载策略
        return 'bestaudio[ext=m4a]+worstvideo[ext=mp4][height>=360]/worst[height>=360]'
    
    def _extract_audio(
        self,
        video_path: Path,
        output_dir: Path
    ) -> Dict[str, Any]:
        """
        使用 ffmpeg 提取音频
        
        Returns:
            {
                "success": bool,
                "audio_path": Path,
                "error": str
            }
        """
        if ffmpeg is None:
            return {
                "success": False,
                "audio_path": None,
                "error": "ffmpeg-python 未安装"
            }
        
        try:
            # 检查 ffmpeg 是否可用
            try:
                subprocess.run(['ffmpeg', '-version'], 
                             capture_output=True, 
                             check=True, 
                             timeout=5)
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                return {
                    "success": False,
                    "audio_path": None,
                    "error": "ffmpeg 二进制文件未找到，请安装: brew install ffmpeg (macOS)"
                }
            
            # 生成音频输出路径
            audio_filename = video_path.stem + ".mp3"
            audio_path = output_dir / audio_filename
            
            logger.info(f"🎵 提取音频: {video_path.name} -> {audio_filename}")
            
            # 使用 ffmpeg-python 提取音频
            stream = ffmpeg.input(str(video_path))
            stream = ffmpeg.output(stream, str(audio_path), acodec='libmp3lame', audio_bitrate='192k')
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            if not audio_path.exists():
                return {
                    "success": False,
                    "audio_path": None,
                    "error": "音频文件未生成"
                }
            
            logger.info(f"✅ 音频提取完成: {audio_path.name}")
            return {
                "success": True,
                "audio_path": audio_path,
                "error": None
            }
        
        except Exception as e:
            error_msg = f"提取音频失败: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            return {
                "success": False,
                "audio_path": None,
                "error": error_msg
            }
    
    def _extract_keyframes(
        self,
        video_path: Path,
        output_dir: Path,
        num_frames: int = 6
    ) -> Dict[str, Any]:
        """
        使用 ffmpeg 提取关键帧（均匀分布）
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
            num_frames: 提取的帧数
        
        Returns:
            {
                "success": bool,
                "frames_paths": List[Path],
                "error": str
            }
        """
        if ffmpeg is None:
            return {
                "success": False,
                "frames_paths": [],
                "error": "ffmpeg-python 未安装"
            }
        
        try:
            # 检查 ffmpeg 是否可用
            try:
                subprocess.run(['ffmpeg', '-version'], 
                             capture_output=True, 
                             check=True, 
                             timeout=5)
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                return {
                    "success": False,
                    "frames_paths": [],
                    "error": "ffmpeg 二进制文件未找到，请安装: brew install ffmpeg (macOS)"
                }
            
            # 获取视频时长
            probe = ffmpeg.probe(str(video_path))
            duration = float(probe['streams'][0].get('duration', 0))
            
            if duration == 0:
                # 尝试从 format 获取
                duration = float(probe.get('format', {}).get('duration', 0))
            
            if duration == 0:
                return {
                    "success": False,
                    "frames_paths": [],
                    "error": "无法获取视频时长"
                }
            
            logger.info(f"📹 视频时长: {duration:.2f} 秒")
            
            # 计算关键帧时间点（均匀分布）
            if num_frames == 1:
                timestamps = [duration / 2]  # 中间位置
            else:
                timestamps = [duration * i / (num_frames - 1) for i in range(num_frames)]
                # 避免在最后一秒提取（可能不完整）
                timestamps = [min(t, duration - 0.5) for t in timestamps]
            
            frames_paths = []
            video_stem = video_path.stem
            
            logger.info(f"🖼️  提取关键帧时间点: {[f'{t:.2f}s' for t in timestamps]}")
            
            for i, timestamp in enumerate(timestamps):
                frame_filename = f"{video_stem}_frame_{i+1:02d}.jpg"
                frame_path = output_dir / frame_filename
                
                try:
                    # 使用 ffmpeg 提取帧
                    stream = ffmpeg.input(str(video_path), ss=timestamp)
                    # 使用字典传递带冒号的参数
                    stream = ffmpeg.output(stream, str(frame_path), vframes=1, **{'qscale:v': 2})
                    ffmpeg.run(stream, overwrite_output=True, quiet=True)
                    
                    if frame_path.exists():
                        frames_paths.append(frame_path)
                        logger.debug(f"  ✅ 帧 {i+1}/{num_frames}: {frame_filename} ({timestamp:.2f}s)")
                    else:
                        logger.warning(f"  ⚠️  帧 {i+1}/{num_frames} 未生成: {frame_filename}")
                
                except Exception as e:
                    logger.warning(f"  ⚠️  提取帧 {i+1} 失败: {e}")
                    continue
            
            if len(frames_paths) == 0:
                return {
                    "success": False,
                    "frames_paths": [],
                    "error": "未能提取任何关键帧"
                }
            
            logger.info(f"✅ 成功提取 {len(frames_paths)}/{num_frames} 张关键帧")
            return {
                "success": True,
                "frames_paths": frames_paths,
                "error": None
            }
        
        except Exception as e:
            error_msg = f"提取关键帧失败: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            return {
                "success": False,
                "frames_paths": [],
                "error": error_msg
            }


# 便捷函数
def process_video(
    video_url: str,
    output_dir: str,
    video_quality: str = "480p",
    num_frames: int = 6
) -> Dict[str, Any]:
    """
    便捷函数：处理视频
    
    Args:
        video_url: 视频URL
        output_dir: 输出目录
        video_quality: 视频质量 ("360p", "480p", "720p", "best")
        num_frames: 关键帧数量
    
    Returns:
        处理结果字典
    """
    crawler = VideoCrawler()
    return crawler.process_video(video_url, output_dir, video_quality, num_frames)


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python video_processor.py <video_url> [output_dir]")
        sys.exit(1)
    
    video_url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./output"
    
    print(f"🎬 开始处理视频: {video_url}")
    result = process_video(video_url, output_dir)
    
    print("\n" + "="*50)
    print("处理结果:")
    print("="*50)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result["success"]:
        print("\n✅ 处理成功！")
        print(f"📹 视频: {result['video_path']}")
        print(f"🎵 音频: {result['audio_path']}")
        print(f"🖼️  关键帧: {len(result['frames_paths'])} 张")
    else:
        print(f"\n❌ 处理失败: {result.get('error')}")

