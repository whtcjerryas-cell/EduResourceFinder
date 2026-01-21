#!/usr/bin/env python3
"""
播放列表处理器 - PlaylistProcessor
用于从播放列表URL中提取所有视频URL
"""

import os
from typing import List, Dict, Optional, Any
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

from utils.logger_utils import get_logger

logger = get_logger('playlist_processor')


class PlaylistProcessor:
    """
    播放列表处理器
    用于从播放列表URL中提取所有视频URL
    """
    
    def __init__(self):
        """初始化 PlaylistProcessor"""
        if yt_dlp is None:
            logger.error("❌ yt-dlp 未安装，请运行: pip install yt-dlp")
    
    def extract_videos_from_playlist(
        self,
        playlist_url: str,
        max_videos: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        从播放列表URL中提取所有视频URL

        Args:
            playlist_url: 播放列表URL（支持 YouTube, Bilibili 等）
            max_videos: 最大提取视频数量（None表示提取所有）

        Returns:
            {
                "success": bool,
                "playlist_title": str,
                "video_count": int,
                "videos": List[Dict],  # 每个视频包含 url, title, duration 等
                "error": str
            }
        """
        result = {
            "success": False,
            "playlist_title": "",
            "video_count": 0,
            "videos": [],
            "error": None
        }

        if yt_dlp is None:
            result["error"] = "yt-dlp 未安装"
            return result

        try:
            logger.info(f"📋 开始提取播放列表视频: {playlist_url}")

            # 验证YouTube播放列表ID格式
            import re
            if 'youtube.com' in playlist_url or 'youtu.be' in playlist_url:
                # 提取播放列表ID
                playlist_id_match = re.search(r'[?&]list=([^&]+)', playlist_url)
                if playlist_id_match:
                    playlist_id = playlist_id_match.group(1)
                    # 检查是否为有效的YouTube播放列表ID（以PL开头，后面跟字符串）
                    # 某些无效ID如PLY...会被yt-dlp拒绝
                    if not playlist_id.startswith('PL'):
                        logger.warning(f"⚠️ 无效的YouTube播放列表ID格式: {playlist_id}，跳过")
                        result["error"] = f"无效的播放列表ID格式: {playlist_id}"
                        return result

            # 配置 yt-dlp
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,  # 需要完整信息以获取视频URL
                'playlistend': max_videos if max_videos else None,
                'ignoreerrors': True,  # 遇到错误时继续处理
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
                # 添加重试和延迟
                'retries': 3,
                'fragment_retries': 3,
                'sleep_interval': 1,
                'max_sleep_interval': 3,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 提取播放列表信息
                info = ydl.extract_info(playlist_url, download=False)

            if not info:
                result["error"] = "无法提取播放列表信息"
                return result

            # 获取播放列表标题
            playlist_title = info.get('title', '未知播放列表')
            result["playlist_title"] = playlist_title

            # 提取视频列表
            entries = info.get('entries', [])
            if not entries:
                result["error"] = "播放列表为空或无法访问"
                return result

            videos = []
            for entry in entries:
                if not entry:
                    continue

                video_info = {
                    "url": entry.get('url', ''),
                    "title": entry.get('title', '未知标题'),
                    "duration": entry.get('duration', 0),
                    "id": entry.get('id', ''),
                }

                # 如果是YouTube，构建完整URL
                if 'youtube.com' in playlist_url or 'youtu.be' in playlist_url:
                    video_id = entry.get('id', '')
                    if video_id:
                        video_info["url"] = f"https://www.youtube.com/watch?v={video_id}"

                videos.append(video_info)

            result["success"] = True
            result["video_count"] = len(videos)
            result["videos"] = videos

            logger.info(f"✅ 成功提取 {len(videos)} 个视频")
            logger.info(f"   播放列表: {playlist_title}")

        except Exception as e:
            error_msg = f"提取播放列表失败: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            result["error"] = error_msg

        return result
    
    def is_playlist_url(self, url: str) -> bool:
        """
        判断URL是否为播放列表
        
        Args:
            url: 视频或播放列表URL
        
        Returns:
            True 如果是播放列表，False 如果是单个视频
        """
        # YouTube播放列表特征
        if 'youtube.com' in url or 'youtu.be' in url:
            if 'list=' in url or '/playlist' in url:
                return True
        
        # Bilibili播放列表特征
        if 'bilibili.com' in url:
            if '/playlist' in url or '/series' in url:
                return True
        
        return False

