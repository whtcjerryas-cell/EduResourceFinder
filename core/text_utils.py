#!/usr/bin/env python3
"""
文本清理工具
用于清理搜索结果中的标题、描述等文本
"""

import re
from typing import Optional

def clean_title(title: str, url: str = "") -> str:
    """
    清理视频/资源标题
    
    Args:
        title: 原始标题
        url: 相关URL（用于判断来源）
    
    Returns:
        清理后的标题
    """
    if not title:
        return "未知标题"
    
    # 移除常见的后缀模式
    patterns_to_remove = [
        r'\s*-\s*YouTube$',
        r'\s*-\s*YouTube\s*\w*$',
        r'\s*\|\s*YouTube$',
        r'\s*\|\s*YouTube\s*\w*$',
        r'\s*on\s+YouTube$',
        r'\s*\(\s*Video\s*\)$',
        r'\s*\(\s*\d{4}\s*\)$',  # 年份
        r'\s*\[\s*HD\s*\]$',
        r'\s*\[\s*\d+[pP]\s*\]$',  # 1080p, 720p等
        r'\s*-\s*Video\s*$',
        r'\s*-\s*Watch\s+Online\s*$',
    ]
    
    cleaned = title
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # 清理多余的空格和标点
    cleaned = cleaned.strip()
    cleaned = re.sub(r'\s+', ' ', cleaned)  # 多个空格变为一个
    cleaned = re.sub(r'\s*[,，。．、]\s*$', '', cleaned)  # 移除结尾的标点
    
    # 如果是YouTube频道页面，清理特定格式
    if '/channel/' in url or '/c/' in url or '/user/' in url:
        # 移除 "- YouTube" 等后缀后，可能还有其他后缀
        cleaned = re.sub(r'\s*-\s*[^-\s]*\s*$', '', cleaned)  # 移除最后的 - XXX 部分
    
    return cleaned if cleaned else title


def clean_snippet(snippet: str) -> str:
    """
    清理摘要文本
    
    Args:
        snippet: 原始摘要
    
    Returns:
        清理后的摘要
    """
    if not snippet:
        return ""
    
    # 移除URL链接
    cleaned = re.sub(r'https?://[^\s]+', '', snippet)
    
    # 移除常见的垃圾文本
    patterns_to_remove = [
        r'\.\.\.$',
        r'Learn more at.*$',
        r'Visit.*for more.*$',
        r'Subscribe for.*$',
    ]
    
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # 限制长度
    if len(cleaned) > 500:
        cleaned = cleaned[:500] + "..."
    
    return cleaned.strip()


def extract_video_info(title: str, url: str) -> dict:
    """
    从标题和URL中提取视频信息
    
    Args:
        title: 标题
        url: URL
    
    Returns:
        包含清理后标题、类型等信息的字典
    """
    is_playlist = any(indicator in url.lower() for indicator in [
        'playlist?', 'list=', '/videos'
    ])
    
    is_channel = any(indicator in url.lower() for indicator in [
        '/channel/', '/c/', '/user/'
    ])
    
    is_video = 'watch?v=' in url or 'youtu.be/' in url
    
    cleaned_title = clean_title(title, url)
    
    return {
        'cleaned_title': cleaned_title,
        'original_title': title,
        'is_playlist': is_playlist,
        'is_channel': is_channel,
        'is_video': is_video,
        'resource_type': '播放列表' if is_playlist else ('频道' if is_channel else '视频')
    }
