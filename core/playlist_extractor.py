#!/usr/bin/env python3
"""
YouTube播放列表信息提取器

从 search_engine_v2.py 中提取，消除重复代码。
提供高效的播放列表信息获取功能，支持并发处理。
"""

from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
from utils.logger_utils import get_logger

logger = get_logger('playlist_extractor')


class PlaylistExtractor:
    """YouTube播放列表信息提取器"""

    @staticmethod
    def extract_playlist_info(url: str, timeout: int = 3) -> Optional[Dict[str, Any]]:
        """
        提取播放列表信息（视频数量、总时长）

        Args:
            url: YouTube播放列表URL
            timeout: 超时时间（秒）

        Returns:
            包含 video_count 和 total_duration_minutes 的字典，失败返回 None
        """
        if not url or 'list=' not in url:
            return None

        try:
            import yt_dlp

            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,  # 快速提取
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)',
                },
                'extractor_args': {
                    'youtube': {
                        'player_client': ['ios'],
                    }
                },
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            if not info:
                return None

            entries = info.get('entries', [])
            if not entries:
                return None

            video_count = len(entries)

            # 计算总时长（分钟）
            total_duration_seconds = 0
            for entry in entries:
                duration = entry.get('duration', 0)
                if duration:
                    total_duration_seconds += duration

            total_duration_minutes = total_duration_seconds / 60 if total_duration_seconds > 0 else 0

            return {
                'video_count': video_count,
                'total_duration_minutes': total_duration_minutes
            }

        except Exception as e:
            logger.warning(f"获取播放列表信息失败: {str(e)[:100]}")
            return None

    @staticmethod
    def batch_extract_playlist_info(
        urls: list,
        max_workers: int = 20,
        timeout: int = 3
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        批量提取播放列表信息（并发）

        Args:
            urls: URL列表
            max_workers: 最大并发数
            timeout: 单个URL超时时间

        Returns:
            URL到播放列表信息的映射字典
        """
        if not urls:
            return {}

        results = {}
        success_count = 0
        fail_count = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_url = {
                executor.submit(PlaylistExtractor.extract_playlist_info, url, timeout): url
                for url in urls
            }

            # 收集结果
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    playlist_info = future.result(timeout=timeout)
                    results[url] = playlist_info
                    if playlist_info:
                        success_count += 1
                    else:
                        fail_count += 1
                except FuturesTimeoutError:
                    logger.warning(f"播放列表信息获取超时: {url[:60]}")
                    results[url] = None
                    fail_count += 1
                except Exception as e:
                    logger.warning(f"播放列表信息获取异常: {str(e)[:100]}")
                    results[url] = None
                    fail_count += 1

        logger.info(
            f"批量提取完成: 成功={success_count}, 失败={fail_count}, "
            f"总计={len(urls)}, 成功率={success_count/len(urls)*100:.1f}%"
        )

        return results
