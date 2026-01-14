#!/usr/bin/env python3
"""
智能结果评分模块
基于多个因素对搜索结果进行智能评分
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse
from logger_utils import get_logger
from llm_client import InternalAPIClient

# ✅ 新增：导入配置管理器
from config_manager import get_config_manager

# ✅ 新增：导入阿拉伯语标准化模块
from core.arabic_normalizer import ArabicNormalizer

# ✅ 安全修复：导入输入净化模块（防止LLM提示注入）
from core.input_sanitizer import sanitize_llm_input, sanitize_metadata

logger = get_logger('result_scorer')


class IntelligentResultScorer:
    """
    智能结果评分器

    评分维度:
    1. URL质量和可信度
    2. 标题相关性
    3. 内容完整性
    4. 来源权威性
    5. 资源类型匹配度
    """

    def __init__(self, country_code: str = None):
        """
        初始化评分器

        Args:
            country_code: 国家代码 (如: IQ, ID, CN)，用于加载知识库
        """
        # 初始化知识库管理器（如果提供了country_code）
        self.kb_manager = None
        if country_code:
            try:
                from core.knowledge_base_manager import get_knowledge_base_manager
                self.kb_manager = get_knowledge_base_manager(country_code)
                logger.info(f"[✅ 评分器] 已加载 {country_code} 知识库")
            except ImportError:
                logger.warning(f"[⚠️ 评分器] 无法导入知识库管理器")
            except Exception as e:
                logger.warning(f"[⚠️ 评分器] 知识库初始化失败: {e}")

        # 初始化LLM客户端（使用Gemini 2.5 Flash进行评分）
        try:
            self.llm_client = InternalAPIClient(model_type='fast_inference')  # 使用fast_inference模型
            logger.info(f"✅ LLM客户端初始化成功，模型: {self.llm_client.model}")
        except Exception as e:
            logger.warning(f"⚠️ LLM客户端初始化失败: {str(e)}，将使用规则评分")
            self.llm_client = None

        # 可信域名列表（加分）
        self.trusted_domains = {
            # 国际教育平台
            'khanacademy.org': 3.0,
            'coursera.org': 2.5,
            'edx.org': 2.5,
            'udemy.com': 2.0,

            # 视频平台
            'youtube.com': 2.0,
            'youtube-nocookie.com': 2.0,
            'vimeo.com': 1.5,

            # 印尼教育平台
            'kemdikbud.go.id': 3.0,
            'ruangguru.com': 2.5,
            'zenius.net': 2.5,
            'quipper.com': 2.0,
            'brainly.co.id': 1.5,

            # 俄罗斯教育平台
            'uchi.ru': 2.5,
            'znaika.ru': 2.5,
            'interneturok.ru': 2.5,
            'infourok.ru': 2.0,
            'videouroki.net': 2.0,
            'reshuege.ru': 2.0,

            # 中国教育平台
            'bilibili.com': 2.0,
            'icourse163.org': 2.5,

            # 印度教育平台
            'byju.com': 2.5,
            'vedantu.com': 2.0,
            'unacademy.com': 2.0,

            # 教育机构
            '.edu': 2.0,
            '.ac.': 1.5,
            '.gov.': 1.5,
        }

        # 低质量域名（减分）
        self.low_quality_domains = {
            'bit.ly': -1.0,
            'tinyurl.com': -1.0,
            'short.link': -1.0,
        }

        # 教育关键词（加分）
        self.educational_keywords = [
            'lesson', 'tutorial', 'course', 'lecture', 'education',
            'learn', 'study', 'school', 'class', 'teacher',
            '课程', '教程', '学习', '教学', '课程',
            'урок', 'обучение', 'лекция',  # 俄语
            'pelajaran', 'pembelajaran', 'belajar',  # 印尼语
        ]

        # 视频相关关键词
        self.video_keywords = [
            'video', 'youtube', 'watch', 'vimeo',
            '视频', '影片',
            'видео',  # 俄语
            'video',  # 印尼语
        ]

        # 播放列表关键词（加分）
        self.playlist_keywords = [
            'playlist', 'series', 'complete course',
            'playlist', 'complete', 'full course',
            '播放列表', '完整', '全套',
            'плейлист', 'полный курс',  # 俄语
            'daftar putar', 'lengkap',  # 印尼语
        ]

        # 语言检测特征（Unicode范围和关键词）
        self.language_patterns = {
            'ar': {  # 阿拉伯语
                'unicode_ranges': [(0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF)],
                'keywords': ['ال', 'في', 'من', 'على', 'أن', 'التي', 'كورس', 'درس', 'تعليم'],
                'sample_chars': ['ا', 'ب', 'ت', 'ث', 'ج']
            },
            'en': {  # 英语
                'unicode_ranges': [(0x0000, 0x007F)],
                'keywords': ['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can',
                             'with', 'this', 'that', 'from', 'they', 'have', 'been', 'grade',
                             'lesson', 'course', 'physics', 'math', 'complete', 'video'],
                'sample_chars': ['a', 'b', 'c', 'd', 'e']
            },
            'id': {  # 印尼语
                'unicode_ranges': [(0x0000, 0x007F)],
                'keywords': ['yang', 'dan', 'untuk', 'dari', 'dengan', 'adalah', 'pelajaran', 'belajar'],
                'sample_chars': ['a', 'b', 'c', 'd', 'e']
            },
            'zh': {  # 中文
                'unicode_ranges': [(0x4E00, 0x9FFF), (0x3400, 0x4DBF)],
                'keywords': ['的', '是', '在', '和', '有', '学习', '课程', '教学'],
                'sample_chars': ['中', '文', '课', '程', '学']
            },
            'ru': {  # 俄语
                'unicode_ranges': [(0x0400, 0x04FF)],
                'keywords': ['и', 'в', 'на', 'что', 'для', 'урок', 'обучение', 'лекция'],
                'sample_chars': ['а', 'б', 'в', 'г', 'д']
            },
            'es': {  # 西班牙语
                'unicode_ranges': [(0x0000, 0x007F)],
                'keywords': ['el', 'la', 'de', 'que', 'y', 'lección', 'curso', 'aprender'],
                'sample_chars': ['a', 'b', 'c', 'd', 'e']
            },
            'fr': {  # 法语
                'unicode_ranges': [(0x0000, 0x007F)],
                'keywords': ['le', 'de', 'et', 'un', 'il', 'cours', 'leçon', 'apprendre'],
                'sample_chars': ['a', 'b', 'c', 'd', 'e']
            },
            'pt': {  # 葡萄牙语
                'unicode_ranges': [(0x0000, 0x007F)],
                'keywords': ['o', 'de', 'a', 'e', 'para', 'lição', 'curso', 'aprender'],
                'sample_chars': ['a', 'b', 'c', 'd', 'e']
            },
            'hi': {  # 印地语
                'unicode_ranges': [(0x0900, 0x097F)],
                'keywords': ['के', 'में', 'की', 'है', 'पाठ', 'पाठ्यक्रम', 'सीखना'],
                'sample_chars': ['क', 'ख', 'ग', 'घ', 'ङ']
            },
            'th': {  # 泰语
                'unicode_ranges': [(0x0E00, 0x0E7F)],
                'keywords': ['ที่', 'และ', 'ของ', 'มี', 'บทเรียน', 'หลักสูตร', 'เรียน'],
                'sample_chars': ['ก', 'ข', 'ฃ', 'ค', 'ฅ']
            },
            'vi': {  # 越南语
                'unicode_ranges': [(0x1EA0, 0x1EF9), (0x0000, 0x007F)],
                'keywords': ['của', 'và', 'cho', 'không', 'bài', 'khóa', 'học'],
                'sample_chars': ['a', 'ă', 'â', 'b', 'c']
            },
        }

        # ✅ 添加识别缓存（纯LLM方案）
        self._grade_extraction_cache = {}  # {title: grade}
        self._subject_extraction_cache = {}  # {title: subject}
        self._cache_max_size = 1000  # 最多缓存1000条

        logger.info("✅ 智能结果评分器初始化完成")

    def _cache_get(self, cache_dict: Dict, key: str, default=None):
        """从缓存获取"""
        return cache_dict.get(key, default)

    def _cache_set(self, cache_dict: Dict, key: str, value):
        """设置缓存，LRU淘汰"""
        if len(cache_dict) >= self._cache_max_size:
            # 删除最早的10%
            num_to_remove = self._cache_max_size // 10
            for i, k in enumerate(list(cache_dict.keys())):
                if i >= num_to_remove:
                    break
                del cache_dict[k]
        cache_dict[key] = value

    def score_result(self, result: Dict[str, Any], query: str, metadata: Optional[Dict] = None) -> float:
        """
        对单个搜索结果进行评分

        评分维度：
        - 基础分: 3.0 (所有结果都有)
        - 标题相关性: 0-3.0分 (最重要)
        - 内容完整性: 0-1.5分
        - 来源可信度: 0-2.0分
        - 资源类型匹配: 0-1.0分
        - 播放列表加分: 0-1.0分
        - 语言匹配度: 0-2.5分 (根据目标国家语言)
        - 播放列表丰富度: 0-1.5分 (视频数量和总时长)
        - 教育内容加分: 0-0.5分

        Args:
            result: 搜索结果字典
            query: 搜索查询
            metadata: 额外的元数据（国家、年级、学科）

        Returns:
            评分 (0.0 - 10.0)
        """
        # 降低基础分，增加区分度
        score = 3.0  # 基础分（从5.0降低到3.0）
        url = result.get('url', '').lower()
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()

        # 1. 标题相关性评分 (0-3.0分) - 最重要
        score += self._score_title_relevance(title, query, snippet)

        # 2. 内容完整性评分 (0-1.5分)
        score += self._score_content_completeness(snippet) * 1.5

        # 3. 来源可信度评分 (0-2.0分) - 避免重复加分
        score += self._score_source_credibility_v2(url)

        # 4. 资源类型评分 (0-1.0分)
        score += self._score_resource_type(url, title, snippet)

        # 5. 播放列表加分 (0-1.0分) - 增加播放列表权重
        score += self._score_playlist_bonus_v2(url, title, snippet)

        # 6. 语言匹配度评分 (0-2.5分) - 根据目标国家语言
        if metadata:
            target_language = metadata.get('language_code')
            if target_language:
                score += self._score_language_matching(title, snippet, target_language)

        # 7. 播放列表丰富度评分 (0-1.5分) - 基于视频数量和总时长
        playlist_info = result.get('playlist_info')  # {video_count, total_duration_minutes}
        if playlist_info:
            score += self._score_playlist_richness(playlist_info)

        # 8. 教育内容加分 (0-0.5分)
        score += self._score_educational_content(title, snippet) * 0.5

        # 确保评分在 0-10 范围内
        return max(0.0, min(10.0, score))

    def _score_url_quality(self, url: str) -> float:
        """评分URL质量"""
        if not url:
            return 0.0

        score = 0.0

        # HTTPS 加分
        if url.startswith('https://'):
            score += 0.3

        # 检查可信域名
        for domain, bonus in self.trusted_domains.items():
            if domain in url:
                score += bonus
                break

        # 检查低质量域名
        for domain, penalty in self.low_quality_domains.items():
            if domain in url:
                score += penalty
                break

        # 检查教育域名
        if '.edu' in url or '.ac.' in url or '.gov.' in url:
            score += 0.5

        return score

    def _score_title_relevance(self, title: str, query: str, snippet: str = "") -> float:
        """
        评分标题相关性（最重要的评分维度）

        Args:
            title: 标题
            query: 搜索查询
            snippet: 摘要（可选）

        Returns:
            评分 (0.0 - 3.0)
        """
        if not title or not query:
            return 0.0

        score = 0.0
        query_lower = query.lower()
        combined = f"{title} {snippet}".lower()

        # 1. 完全匹配查询 (0-1.5分)
        if query_lower in combined:
            score += 1.5

        # 2. 关键词匹配度 (0-1.0分)
        query_words = set(query_lower.split())
        combined_words = set(combined.split())
        overlap = len(query_words & combined_words)

        if overlap >= 3:
            score += 1.0
        elif overlap >= 2:
            score += 0.7
        elif overlap >= 1:
            score += 0.4

        # 3. 年级和学科匹配 (0-0.5分)
        # 检查是否包含明确的年级和学科信息
        grade_keywords = ['grade', 'kelas', '年级', 'class', 'primary', 'secondary']
        subject_keywords = ['math', 'science', 'english', 'arabic', '数学', '科学']

        has_grade = any(kw in combined for kw in grade_keywords)
        has_subject = any(kw in combined for kw in subject_keywords)

        if has_grade and has_subject:
            score += 0.5
        elif has_grade or has_subject:
            score += 0.2

        return min(score, 3.0)

    def _score_content_completeness(self, snippet: str) -> float:
        """评分内容完整性"""
        if not snippet:
            return 0.0

        # 根据描述长度评分
        length = len(snippet)

        if length >= 200:
            return 1.0
        elif length >= 150:
            return 0.8
        elif length >= 100:
            return 0.6
        elif length >= 50:
            return 0.3
        else:
            return 0.0

    def _score_source_credibility(self, url: str) -> float:
        """评分来源可信度"""
        if not url:
            return 0.0

        score = 0.0

        try:
            domain = urlparse(url).netloc.lower()

            # 知名教育平台
            if 'khanacademy.org' in domain:
                score += 3.0
            elif 'kemdikbud.go.id' in domain or 'moe.gov' in domain:
                score += 3.0
            elif any(edu in domain for edu in ['ruangguru', 'zenius', 'uchi.ru', 'byju']):
                score += 2.5
            elif 'youtube.com' in domain:
                score += 1.5
            elif '.edu' in domain:
                score += 2.0

            # 官方政府网站
            if '.gov.' in domain:
                score += 1.5

        except Exception:
            pass

        return score

    def _score_resource_type(self, url: str, title: str, snippet: str) -> float:
        """评分资源类型"""
        score = 0.0
        combined = f"{url} {title} {snippet}".lower()

        # 视频资源加分
        for keyword in self.video_keywords:
            if keyword in combined:
                score += 0.5
                break

        return score

    def _score_playlist_bonus(self, url: str, title: str, snippet: str) -> float:
        """播放列表加分"""
        combined = f"{url} {title} {snippet}".lower()

        for keyword in self.playlist_keywords:
            if keyword in combined:
                return 0.5

        return 0.0

    def _score_educational_content(self, title: str, snippet: str) -> float:
        """教育内容加分"""
        combined = f"{title} {snippet}".lower()

        matches = sum(1 for kw in self.educational_keywords if kw in combined)

        if matches >= 3:
            return 0.5
        elif matches >= 2:
            return 0.3
        elif matches >= 1:
            return 0.1

        return 0.0

    def _score_source_credibility_v2(self, url: str) -> float:
        """
        评分来源可信度（改进版 - 避免重复加分）

        只在一个维度评分，避免重复加分：
        - 官方教育平台: 2.0分
        - YouTube: 1.0分（降低分数）
        - 教育机构: 1.5分
        - 政府网站: 1.5分
        - 其他: 0.5分

        Args:
            url: URL

        Returns:
            评分 (0.0 - 2.0)
        """
        if not url:
            return 0.0

        try:
            domain = urlparse(url).netloc.lower()

            # 官方教育平台（最高分）
            if any(edu in domain for edu in [
                'khanacademy.org',
                'kemdikbud.go.id',
                'ruangguru.com',
                'zenius.net',
                'uchi.ru',
                'byju.com'
            ]):
                return 2.0

            # 教育机构或政府网站
            if '.edu' in domain or '.gov.' in domain or 'ac.' in domain:
                return 1.5

            # YouTube（降低分数，避免所有YouTube内容都高分）
            if 'youtube.com' in domain or 'youtu.be' in domain:
                return 1.0

            # 其他视频平台
            if any(v in domain for v in ['vimeo.com', 'bilibili.com', 'dailymotion.com']):
                return 0.8

            # HTTPS网站（基础加分）
            if url.startswith('https://'):
                return 0.5

        except Exception:
            pass

        return 0.0

    def _score_playlist_bonus_v2(self, url: str, title: str, snippet: str) -> float:
        """
        播放列表加分（改进版 - 增加区分度）

        评分标准：
        - 明确的播放列表URL: 1.0分
        - 标题包含"complete"/"full course": 0.8分
        - 标题包含"playlist"/"series": 0.5分
        - 其他: 0分

        Args:
            url: URL
            title: 标题
            snippet: 摘要

        Returns:
            评分 (0.0 - 1.0)
        """
        combined = f"{url} {title} {snippet}".lower()

        # 1. 明确的播放列表URL（最高分）
        if any(indicator in url.lower() for indicator in ['playlist?', 'list=', '/videos']):
            return 1.0

        # 2. 标题包含完整课程关键词
        complete_keywords = ['complete course', 'full course', 'all lessons',
                           'كامل', 'شامل', 'دورة كاملة',  # 阿拉伯语
                           '完整', '全套', '全部']
        if any(kw in combined for kw in complete_keywords):
            return 0.8

        # 3. 标题包含播放列表关键词
        playlist_keywords = ['playlist', 'series', 'collection',
                          'قائمة التشغيل', 'سلسلة',  # 阿拉伯语
                          '播放列表', '系列']
        if any(kw in combined for kw in playlist_keywords):
            return 0.5

        return 0.0

    def _detect_language(self, text: str) -> str:
        """
        检测文本的语言

        Args:
            text: 要检测的文本

        Returns:
            语言代码（如 'ar', 'en', 'zh'），如果无法检测则返回 'unknown'
        """
        if not text:
            return 'unknown'

        # 统计每个语言的得分
        language_scores = {}

        for lang_code, patterns in self.language_patterns.items():
            score = 0.0

            # 1. 检查Unicode字符范围
            for char in text:
                char_code = ord(char)
                for range_start, range_end in patterns['unicode_ranges']:
                    if range_start <= char_code <= range_end:
                        score += 1.0
                        break

            # 2. 检查关键词匹配
            text_lower = text.lower()
            for keyword in patterns['keywords']:
                if keyword in text_lower:
                    score += 0.5

            # 标准化得分（除以文本长度，避免长文本占优）
            if len(text) > 0:
                score = score / len(text) * 100

            language_scores[lang_code] = score

        # 返回得分最高的语言
        if not language_scores:
            return 'unknown'

        best_language = max(language_scores, key=language_scores.get)

        # 如果最高分太低，返回unknown
        if language_scores[best_language] < 0.5:
            return 'unknown'

        return best_language

    def _score_language_matching(self, title: str, snippet: str, target_language: str) -> float:
        """
        评分语言匹配度

        评分标准：
        - 完全匹配（标题和摘要都是目标语言）: 2.5分
        - 部分匹配（标题是目标语言）: 2.0分
        - 部分匹配（摘要包含目标语言）: 1.5分
        - 英语作为通用语言的降级匹配: 0.5分
        - 不匹配: 0分

        Args:
            title: 标题
            snippet: 摘要
            target_language: 目标语言代码（如 'ar', 'en', 'id'）

        Returns:
            评分 (0.0 - 2.5)
        """
        if not target_language or target_language not in self.language_patterns:
            # 如果没有目标语言或不支持，不加分也不减分
            return 0.0

        # 检测标题和摘要的语言
        title_language = self._detect_language(title)
        snippet_language = self._detect_language(snippet)

        # 完全匹配：标题和摘要都是目标语言
        if title_language == target_language and snippet_language == target_language:
            return 2.5

        # 标题匹配：标题是目标语言
        if title_language == target_language:
            return 2.0

        # 摘要匹配：摘要包含目标语言
        if snippet_language == target_language:
            return 1.5

        # 降级匹配：如果目标语言不是英语，但内容是英语，给部分分数
        if target_language != 'en' and (title_language == 'en' or snippet_language == 'en'):
            return 0.5

        # 不匹配
        return 0.0

    def _score_playlist_richness(self, playlist_info: Dict[str, Any]) -> float:
        """
        评分播放列表丰富度（基于视频数量和总时长）

        评分标准：
        - 视频数量 >= 20: 0.75分
        - 视频数量 >= 10: 0.6分
        - 视频数量 >= 5: 0.4分
        - 视频数量 < 5: 0.2分
        - 总时长 >= 300分钟 (5小时): 0.75分
        - 总时长 >= 120分钟 (2小时): 0.5分
        - 总时长 >= 60分钟 (1小时): 0.3分
        - 总时长 < 60分钟: 0.1分

        Args:
            playlist_info: 播放列表信息 {video_count, total_duration_minutes}

        Returns:
            评分 (0.0 - 1.5)
        """
        video_count = playlist_info.get('video_count', 0)
        total_duration = playlist_info.get('total_duration_minutes', 0)

        score = 0.0

        # 1. 视频数量评分 (0-0.75分)
        if video_count >= 20:
            score += 0.75
        elif video_count >= 10:
            score += 0.6
        elif video_count >= 5:
            score += 0.4
        elif video_count > 0:
            score += 0.2

        # 2. 总时长评分 (0-0.75分)
        if total_duration >= 300:  # 5小时以上
            score += 0.75
        elif total_duration >= 120:  # 2小时以上
            score += 0.5
        elif total_duration >= 60:  # 1小时以上
            score += 0.3
        elif total_duration > 0:
            score += 0.1

        return min(score, 1.5)

    def _evaluate_with_llm(self, result: Dict[str, Any], query: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        使用LLM（Gemini 2.5 Pro）评估结果并生成质量分数和推荐理由

        改进：
        1. 集成阿拉伯语标准化（规则验证）
        2. 双保险机制：规则验证 + LLM评分
        3. 优化评分Prompt，强调年级匹配

        Args:
            result: 搜索结果字典
            query: 搜索查询
            metadata: 额外的元数据（国家、年级、学科）

        Returns:
            包含score和recommendation_reason的字典
        """
        if not self.llm_client:
            return None

        try:
            # 🔍 调试：确认函数被调用
            title_debug = result.get('title', 'Unknown')[:50]
            logger.info(f"[🔍 _evaluate_with_llm] 开始评估: {title_debug}...")

            # ✅ 新增：步骤0.5 - MCP工具验证（支持印尼语等多语言）
            logger.info(f"[🔍 _evaluate_with_llm] 准备调用MCP工具同步包装...")
            mcp_based_validation = self._validate_with_mcp_tools_sync(result, metadata)
            logger.info(f"[🔍 _evaluate_with_llm] MCP工具同步包装返回: {mcp_based_validation is not None}")

            if mcp_based_validation and mcp_based_validation.get('confidence') == 'high':
                # MCP工具有高置信度的结果，直接使用
                logger.info(f"[✅ MCP工具验证] 使用MCP工具评分: {mcp_based_validation['score']}")
                logger.info(f"   理由: {mcp_based_validation['reason']}")

                return {
                    'score': mcp_based_validation['score'],
                    'recommendation_reason': mcp_based_validation['reason'],
                    'evaluation_method': 'MCP Tools',
                    'mcp_validation': mcp_based_validation
                }

            # ✅ 新增：步骤1 - 规则验证（阿拉伯语标准化）
            rule_based_validation = self._validate_with_rules(result, metadata)
            if rule_based_validation and rule_based_validation.get('confidence') == 'high':
                # 规则验证有高置信度的结果，直接使用
                logger.info(f"[✅ 规则验证] 使用规则评分: {rule_based_validation['score']}")
                logger.info(f"   理由: {rule_based_validation['reason']}")

                return {
                    'score': rule_based_validation['score'],
                    'recommendation_reason': rule_based_validation['reason'],
                    'evaluation_method': 'Rule-based (Arabic)',
                    'rule_validation': rule_based_validation
                }

            # 构建评估提示词
            title = result.get('title', '')
            url = result.get('url', '')
            snippet = result.get('snippet', '')
            playlist_info = result.get('playlist_info', {})

            # 获取元数据信息（兼容两种字段名格式）
            country = metadata.get('country_name', metadata.get('country', '')) if metadata else ''
            grade = metadata.get('grade', metadata.get('grade_name', '')) if metadata else ''
            subject = metadata.get('subject', metadata.get('subject_name', '')) if metadata else ''

            # 播放列表信息
            playlist_extra = ""
            if playlist_info:
                video_count = playlist_info.get('video_count', 0)
                total_duration = playlist_info.get('total_duration_minutes', 0)
                playlist_extra = f"\n- 播放列表视频数量: {video_count} 个\n- 播放列表总时长: {total_duration} 分钟"

            # ✅ MCP工具增强信息
            enrichment_info = []

            # 视频缩略图分析
            if result.get('video_analysis'):
                video_analysis = result['video_analysis']
                if video_analysis.get('thumbnail_url'):
                    enrichment_info.append(f"- 视频缩略图URL: {video_analysis['thumbnail_url']}")

            # 网页内容
            if result.get('web_content'):
                web_content = result['web_content']
                if web_content.get('summary'):
                    content_summary = web_content['summary'][:300]
                    enrichment_info.append(f"- 网页内容摘要: {content_summary}")

            enrichment_text = "\n".join(enrichment_info) if enrichment_info else ""
            if enrichment_text:
                enrichment_text = f"\n【MCP工具增强信息】\n{enrichment_text}"

            system_prompt = """你是一个精准的教育资源评分专家。请严格按照以下规则评分：

【🚨 评分维度】（总分10分）
1. ⭐ 年级匹配度（0-3分）【最关键】：
   - 完全匹配（如：目标一年级，标题一年级）：3分
   - 相近年级（±1年级）：1-2分
   - 年级不符（如：目标一年级，标题八年级）：0分

2. ⭐ 学科匹配度（0-3分）【关键】：
   - 完全匹配（如：目标数学，标题数学）：3分
   - 相关学科：1-2分
   - 学科不符（如：目标艺术，标题数学）：0分

3. 资源质量（0-2分）：
   - 官方/权威机构（.gov, .edu, 教育部）：2分
   - YouTube/知名平台：1.5分
   - 个人/非官方：1分

4. 内容完整性（0-2分）：
   - 完整课程/播放列表（≥10视频）：2分
   - 部分内容：1分
   - 碎片内容：0分

【🔴 评分规则 - 必须遵守】

✅ 正确评分：
- 年级正确 + 学科正确 → 8-10分（高分）
- 年级正确 + 学科相关 → 7-8分
- 年级不明确 + 学科正确 → 5-7分
- 年级不明确 + 学科相关 → 3-5分

❌ 错误评分（必须大幅减分）：
- 年级不符 → 必须给 ≤5分（不管其他因素）
- 学科不符 → 必须给 ≤5分（不管其他因素）
- 年级和学科都不符 → 必须给 ≤3分

【🚨 关键：识别明显无关的内容（最高优先级）】

以下类型的资源**必须直接给 0-2分**，即使标题中没有明确的年级/学科信息：

1. **非教育类网站**（必须识别并给0分）：
   - ❌ 汽车网站：Rivian, Tesla, Ford, BMW, Mercedes, Toyota, Honda, car, automotive
   - ❌ 音乐/乐器：drums, guitar, piano, violin, instrument, music library, audio, band
   - ❌ 游戏相关：game, gaming, gameplay, streamer, twitch, steam, esport
   - ❌ 电商购物：shop, store, buy, purchase, price, sale, discount, amazon, ebay
   - ❌ 新闻媒体：news, breaking news, latest updates, rumors, gossip（除非明确是教育新闻）

2. **识别标准**（必须严格执行）：
   - 如果**域名**或**标题**包含上述关键词 → 直接给 **0-2分**
   - 不要认为"可能是教学资源"而给高分
   - 宁可错杀（给低分），不可放过（给高分）
   - 即使是YouTube视频，如果内容明显无关，也必须给低分

3. **评分示例**（必须参考）：
   - 标题："Rivian News, Latest Software Updates" → {"score":0.0,"reason":"明显无关：汽车新闻网站，非教育内容"}
   - 标题："Fotis Benardo Drums | The Ultra Realistic Metal Drum Library" → {"score":0.0,"reason":"明显无关：音乐库网站，非教育内容"}
   - 标题："wtfastpwner - Twitch" → {"score":0.0,"reason":"明显无关：游戏直播，非教育内容"}
   - 标题："AVATAR:Realms Collide Official Webshop" → {"score":0.0,"reason":"明显无关：游戏商店，非教育内容"}
   - 标题："Kelas 1 SD Kurikulum Merdeka - Matematika" → {"score":9.5,"reason":"年级和学科完全匹配（一年级 数学），来自可信平台"}

【⚠️ 特别注意：阿拉伯语年级识别】

阿拉伯语年级表达（必须正确识别）：
- "الصف الأول" = "الصف الاول" = "صف اول" = 一年级 ✅
- "الصف الثاني" = "صف ثاني" = 二年级
- "الصف الثالث" = "صف ثالث" = 三年级
- "الصف السادس" = "صف سادس" = 六年级 ❌（如果目标是一年级）

🚨 常见错误（必须避免）：
- ❌ 六年级（الصف السادس）被识别为一年级 → 错误！应该给≤3分
- ❌ 一年级（الصف الأول）被识别为不符 → 错误！应该给≥8分

【🎯 评分流程】
第1步：仔细检查标题，识别年级和学科
第2步：判断年级是否匹配（最关键）
第3步：判断学科是否匹配
第4步：根据规则评分（年级不符必须低分）
第5步：生成推荐理由（必须说明匹配/不匹配原因）

【📝 输出格式】
返回JSON：{"score":8.5,"reason":"具体理由"}
- score：0-10的浮点数，保留一位小数
- reason：中文，30-80字，必须包含：
  ✅ 年级匹配情况（如："年级正确（一年级）"）
  ✅ 学科匹配情况（如："学科正确（数学）"）
  ❌ 如果不匹配，明确指出（如："年级不符（标题六年级，目标一年级）"）
"""

            # 📚 构建知识库增强信息
            knowledge_section = ""
            if self.kb_manager and self.kb_manager.knowledge:
                knowledge = self.kb_manager.knowledge

                # 添加年级表达
                target_grade_key = f"Grade {grade.split()[-1]}" if grade and grade.startswith("Grade") else f"Grade {grade}" if grade else ""
                if 'grade_expressions' in knowledge and knowledge['grade_expressions']:
                    knowledge_section = "\n【📚 知识库 - 年级表达参考】\n"

                    # 优先显示目标年级的表达
                    if target_grade_key and target_grade_key in knowledge['grade_expressions']:
                        grade_info = knowledge['grade_expressions'][target_grade_key]
                        variants = grade_info.get('local_variants', [])
                        if variants:
                            variant_list = []
                            for v in variants:
                                if 'arabic' in v:
                                    variant_list.append(f"{v['arabic']}")
                                elif 'english' in v:
                                    note = f" ({v.get('note', '')})" if v.get('note') else ''
                                    variant_list.append(f"{v['english']}{note}")
                            knowledge_section += f"✅ {target_grade_key} 的正确表达: {', '.join(variant_list)}\n"

                        # 添加常见错误
                        mistakes = grade_info.get('common_mistakes', [])
                        if mistakes:
                            knowledge_section += "\n⚠️ 常见错误（必须避免）:\n"
                            for m in mistakes:
                                knowledge_section += f"  ❌ {m['mistake']}\n"
                                knowledge_section += f"  ✅ {m['correction']}\n"

                    # 显示其他年级（最多3个）
                    other_grades = [g for g in knowledge['grade_expressions'].keys() if g != target_grade_key]
                    for other_grade in other_grades[:3]:
                        grade_info = knowledge['grade_expressions'][other_grade]
                        variants = grade_info.get('local_variants', [])
                        if variants:
                            variant_list = []
                            for v in variants[:2]:  # 只显示前2个
                                if 'arabic' in v:
                                    variant_list.append(v['arabic'])
                                elif 'english' in v:
                                    variant_list.append(v['english'])
                            if variant_list:
                                knowledge_section += f"• {other_grade}: {', '.join(variant_list)}\n"

                # 添加关键阿拉伯语术语（CRITICAL）
                if 'critical_arabic_terms' in knowledge and knowledge['critical_arabic_terms']:
                    knowledge_section += "\n【🔑 关键阿拉伯语术语（必须正确识别）】\n"

                    # 教育级别
                    if 'education_levels' in knowledge['critical_arabic_terms']:
                        knowledge_section += "\n📖 教育级别后缀:\n"
                        for level in knowledge['critical_arabic_terms']['education_levels']:
                            knowledge_section += f"  • \"{level['arabic']}\" = {level['english']} ({level['grade_range']})\n"
                            knowledge_section += f"    {level['note']}\n"

                    # 数字
                    if 'numbers' in knowledge['critical_arabic_terms']:
                        knowledge_section += "\n🔢 关键数字:\n"
                        for num in knowledge['critical_arabic_terms']['numbers'][:3]:  # 最多3个
                            knowledge_section += f"  • \"{num['arabic']}\" = {num['english']} ({num['number']}) - {num['note']}\n"

                    # 年级关键词示例
                    if 'grade_keywords' in knowledge['critical_arabic_terms']:
                        for kw in knowledge['critical_arabic_terms']['grade_keywords']:
                            if 'examples' in kw:
                                knowledge_section += f"\n⚠️ \"{kw['pattern']}\" 必须检查修饰词:\n"
                                for ex in kw['examples']:
                                    status = "✅ 正确" if ex.get('correct') else "❌ 错误"
                                    knowledge_section += f"  • {status}: \"{ex['text']}\" = {ex['grade']}\n"

                # 添加学科关键词
                if 'subject_keywords' in knowledge and knowledge['subject_keywords']:
                    knowledge_section += "\n【📚 知识库 - 学科关键词参考】\n"
                    for subject_key, subject_info in knowledge['subject_keywords'].items():
                        variants = subject_info.get('local_variants', [])
                        if variants:
                            variant_list = []
                            for v in variants:
                                if 'arabic' in v:
                                    variant_list.append(v['arabic'])
                                elif 'english' in v:
                                    variant_list.append(v['english'])
                            knowledge_section += f"• {subject_key}: {', '.join(variant_list)}\n"

                # 添加LLM已知问题
                if 'llm_insights' in knowledge and knowledge['llm_insights']:
                    insights = knowledge['llm_insights']
                    if 'accuracy_issues' in insights and insights['accuracy_issues']:
                        # 只显示未修复的问题
                        pending_issues = [i for i in insights['accuracy_issues']
                                        if i.get('status') != 'fixed'][:3]  # 最多3个
                        if pending_issues:
                            knowledge_section += "\n【⚠️ 已知LLM识别问题（必须注意）】\n"
                            for issue in pending_issues:
                                knowledge_section += f"• 问题: {issue.get('issue', '')}\n"
                                knowledge_section += f"  修复: {issue.get('fix', '')}\n"

            # ✅ 安全修复：净化所有用户输入，防止提示注入
            # Issue #036: LLM Prompt Injection Vulnerability - FIXED
            safe_grade = sanitize_llm_input(grade or '', max_length=50)
            safe_subject = sanitize_llm_input(subject or '', max_length=50)
            safe_query = sanitize_llm_input(query or '', max_length=200)
            safe_title = sanitize_llm_input(result.get('title', ''), max_length=200)
            safe_snippet = sanitize_llm_input(result.get('snippet', ''), max_length=500)

            user_prompt = f"""请评估以下教育资源：

【目标信息】
- 目标年级：{safe_grade}
- 目标学科：{safe_subject}
- 搜索查询：{safe_query}
{knowledge_section}

【资源信息】
- 标题：{safe_title}
- 描述：{safe_snippet}
{playlist_extra}
{enrichment_text}

【评估步骤】
第1步：从标题中识别年级（支持多语言）
  - 中文：一年级、二年级、...、十二年级
  - ⚠️ 中文初中/高中表达（关键！）：
    • 初一 = 七年级 (Grade 7)
    • 初二 = 八年级 (Grade 8)
    • 初三 = 九年级 (Grade 9)
    • 高一 = 十年级 (Grade 10)
    • 高二 = 十一年级 (Grade 11)
    • 高三 = 十二年级 (Grade 12)
  - 阿拉伯语：الصف الأول (一年级), الصف الثامن (八年级), ...
  - 印尼语：Kelas 1, Kelas 2, ...
  - 英文：Grade 1, Grade 2, ...

第2步：从标题中识别学科
  - 中文：数学、语文、英语、艺术、体育、...
  - 阿拉伯语：الرياضيات (数学), التربية الفنية (艺术), ...
  - 印尼语：Matematika, Bahasa Indonesia, Seni, ...

第3步：对比匹配度并评分
  - 年级匹配度：0-3分
  - 学科匹配度：0-3分
  - 资源质量：0-2分
  - 内容完整性：0-2分

第4步：生成推荐理由
  - 必须说明年级是否匹配
  - 必须说明学科是否匹配
  - 如果不匹配，明确指出差异

【示例】
目标：一年级 数学
标题：一年级数学加减法教学
输出：{{"score":9.0,"reason":"年级和学科完全匹配，来自权威平台，完整课程"}}

目标：五年级 数学
标题：初三数学全册-九年级数学-上册-下册
输出：{{"score":3.0,"reason":"年级不符（标题初三=九年级，目标五年级），学科匹配"}}

目标：一年级 阿拉伯语
标题：艺术教育 - 八年级 - 第一学期
输出：{{"score":2.0,"reason":"年级不符（目标一年级，标题八年级），学科不符（目标阿拉伯语，标题艺术），不推荐"}}

现在请评估并返回JSON：{{"score":分数,"reason":"理由"}}"""

            # 📊 记录LLM调用开始
            from core.search_log_collector import get_log_collector
            import time
            llm_start = time.time()

            # 调用LLM
            response = self.llm_client.call_llm(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=1000,  # 增加到1000，避免JSON被截断
                temperature=0.3
            )

            # 📊 记录LLM调用结束
            llm_elapsed = time.time() - llm_start
            try:
                log_collector = get_log_collector()
                if log_collector.current_log:
                    # 获取模型信息
                    model_name = getattr(self.llm_client, 'model', 'gemini-2.5-flash')
                    provider = getattr(self.llm_client, 'provider', 'Internal API')

                    # 🔥 不截断prompt和response
                    log_collector.record_llm_call(
                        model_name=model_name,
                        function="智能评分",
                        provider=provider,
                        prompt=user_prompt,  # 🔥 完整提示词
                        input_data=f"标题: {title}, 目标: {grade} {subject}",
                        output_data=response,  # 🔥 完整输出
                        execution_time=llm_elapsed
                    )
                    logger.debug(f"[📊 日志] LLM调用已记录: {model_name}, 功能=智能评分, 耗时={llm_elapsed:.2f}秒")
            except Exception as e:
                logger.warning(f"[📊 日志] 记录LLM调用失败: {str(e)}")

            # ✅ 改进：更鲁棒的JSON解析
            response = response.strip()

            # 1. ✅ 首先清理响应：移除代码块标记（优先处理）
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
                logger.debug("移除```json代码块标记")
            elif '```' in response:
                response = response.split('```')[1].split('```')[0].strip()
                logger.debug("移除```代码块标记")

            # 2. 尝试直接解析
            try:
                result_data = json.loads(response)
            except json.JSONDecodeError as e1:
                logger.warning(f"JSON解析失败（第一次尝试），尝试清理响应: {str(e1)[:100]}")

                # 3. 尝试补全被截断的JSON（常见问题：reason字段没有闭合引号）
                # 如果JSON以逗号截断，尝试补全
                if response.endswith(',') or not response.rstrip().endswith('}'):
                    # 检查是否有未闭合的reason字段
                    reason_match = re.search(r'"reason"\s*:\s*"([^"]*$)', response)
                    if reason_match:
                        # reason字段被截断，补全引号和闭合
                        response = response[:reason_match.start()] + '"reason": "' + reason_match.group(1) + '"}'
                        logger.info(f"补全被截断的reason字段")
                    else:
                        # 简单补全：添加闭合引号和括号
                        if response.count('"') % 2 != 0:  # 奇数个引号说明有未闭合的字符串
                            response += '"'
                        if not response.rstrip().endswith('}'):
                            response += '}'

                # 4. 清理响应中的换行符和特殊字符
                lines = response.split('\n')
                cleaned_lines = []
                for line in lines:
                    # 保留JSON结构，但清理reason字符串值中的换行
                    if '"reason":' in line:
                        # 移除reason字段中的换行符
                        line = line.replace('\n', ' ').replace('\r', ' ')
                    cleaned_lines.append(line)
                response = ' '.join(cleaned_lines)

                # 5. 移除尾随逗号
                response = re.sub(r',\s*}', '}', response)
                response = re.sub(r',\s*]', ']', response)

                # 6. 再次尝试解析
                try:
                    result_data = json.loads(response)
                except json.JSONDecodeError as e2:
                    logger.warning(f"JSON解析失败（第二次尝试），尝试正则提取: {str(e2)[:100]}")

                    # 7. 使用正则表达式兜底提取
                    score_match = re.search(r'"score"\s*:\s*([\d.]+)', response)
                    reason_match = re.search(r'"reason"\s*:\s*"([^"]+)', response)  # 允许reason包含逗号

                    if score_match and reason_match:
                        score = float(score_match.group(1))
                        reason = reason_match.group(1)
                        # 限制reason长度，避免包含多余内容
                        if len(reason) > 100:
                            reason = reason[:100]
                        logger.info(f"✅ 通过正则提取成功: score={score}, reason={reason[:30]}...")
                    else:
                        # 8. 完全失败，返回None使用规则评分
                        logger.error(f"无法解析LLM响应，响应内容: {response[:200]}")
                        return None

            # 验证和提取数据
            if isinstance(result_data, dict):
                score = float(result_data.get('score', 5.0))
                reason = result_data.get('reason', '根据搜索匹配度推荐')
            else:
                # 如果result_data不是dict（正则提取的情况），直接使用提取的值
                pass

            # 确保分数在0-10范围内
            score = max(0.0, min(10.0, score))

            logger.info(f"✅ LLM评估成功: score={score:.1f}, reason={reason[:30]}...")

            return {
                'score': round(score, 1),
                'recommendation_reason': reason
            }

        except Exception as e:
            logger.warning(f"⚠️ LLM评估失败: {str(e)[:100]}，将使用规则评分")
            return None

    def evaluate_with_visual(
        self,
        result: Dict[str, Any],
        screenshot_path: str,
        query: str,
        metadata: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        使用视觉快速评估器评估结果（基于网页截图）

        Args:
            result: 搜索结果字典
            screenshot_path: 截图文件路径
            query: 搜索查询
            metadata: 元数据（国家、年级、学科、语言）

        Returns:
            包含score和recommendation_reason的字典，失败返回None
        """
        try:
            from core.visual_quick_evaluator import get_visual_quick_evaluator

            # 获取视觉评估器
            visual_evaluator = get_visual_quick_evaluator()

            # 提取评估参数
            title = result.get('title', '')
            url = result.get('url', '')

            # 从metadata中提取信息
            country_name = metadata.get('country_name', '') if metadata else ''
            grade_name = metadata.get('grade_name', '') if metadata else ''
            subject_name = metadata.get('subject_name', '') if metadata else ''
            language_code = metadata.get('language_code', 'en') if metadata else 'en'

            # 语言代码映射（国家代码 -> 语言代码）
            language_mapping = {
                'Iraq': 'ar',  # 伊拉克 -> 阿拉伯语
                'Indonesia': 'id',  # 印尼 -> 印尼语
                'China': 'zh',  # 中国 -> 中文
                'Russia': 'ru',  # 俄罗斯 -> 俄语
                'India': 'en',  # 印度 -> 英语
            }
            target_language = language_mapping.get(country_name, language_code) if metadata else language_code

            logger.info(f"🔍 [视觉评估] 标题={title[:50]}..., 年级={grade_name}, 语言={target_language}")

            # 调用完整评估
            evaluation_result = visual_evaluator.evaluate_full(
                screenshot_path=screenshot_path,
                title=title,
                target_grade=grade_name,
                subject=subject_name,
                target_language=target_language
            )

            if not evaluation_result:
                logger.warning("视觉评估失败，返回None")
                return None

            # 提取总分和推荐理由
            overall_score = evaluation_result.get('overall_score', 5.0)
            recommendation = evaluation_result.get('recommendation', '')

            logger.info(f"✅ [视觉评估] 成功: 总分={overall_score}, 推荐={recommendation[:30]}...")

            return {
                'score': round(overall_score, 1),
                'recommendation_reason': recommendation,
                'evaluation_method': 'Visual',
                'evaluation_details': evaluation_result.get('breakdown', {})
            }

        except Exception as e:
            logger.warning(f"⚠️ 视觉评估异常: {str(e)[:100]}")
            return None

    # ========== MCP多模态工具增强函数 ==========

    def _is_video_url(self, url: str) -> bool:
        """判断是否为视频URL"""
        video_domains = [
            'youtube.com', 'youtu.be', 'vimeo.com',
            'bilibili.com', 'dailymotion.com'
        ]
        return any(domain in url.lower() for domain in video_domains)


    def _enrich_result_with_mcp_tools(
        self,
        result: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        使用MCP工具丰富搜索结果信息

        Args:
            result: 搜索结果（包含url）
            metadata: 元数据

        Returns:
            丰富后的结果（添加了web_content, video_info等）
        """
        url = result.get('url', '')

        # 如果URL已经处理过，跳过
        if 'mcp_enriched' in result:
            return result

        # 优先级1: 对于YouTube等视频URL，获取缩略图分析
        if self._is_video_url(url):
            try:
                logger.debug(f"[MCP工具] 正在分析视频缩略图: {url[:50]}")

                # 使用MCP视频分析工具
                video_info = self._analyze_video_with_mcp(url)
                if video_info:
                    result['video_analysis'] = video_info
                    result['mcp_enriched'] = True
                    logger.debug(f"[MCP工具] 视频分析完成: {url[:50]}")
            except Exception as e:
                logger.warning(f"[MCP工具] 视频分析失败: {str(e)[:100]}")

        # 优先级2: 对于一般URL，提取网页内容（可选，避免过度调用）
        # 注意：webReader调用较慢，仅当snippet为空或过短时才调用
        elif url and not result.get('snippet'):
            try:
                snippet_length = len(result.get('snippet', ''))
                if snippet_length < 50:  # snippet太短才补充
                    logger.debug(f"[MCP工具] 正在提取网页内容: {url[:50]}")

                    # 使用MCP webReader工具
                    web_content = self._fetch_web_content_with_mcp(url)
                    if web_content:
                        result['web_content'] = web_content
                        result['snippet'] = web_content.get('summary', web_content.get('content', '')[:500])
                        result['mcp_enriched'] = True
                        logger.debug(f"[MCP工具] 网页内容提取完成: {len(result.get('snippet', ''))} 字符")
            except Exception as e:
                logger.warning(f"[MCP工具] 网页内容提取失败: {str(e)[:100]}")

        return result


    def _analyze_video_with_mcp(self, url: str) -> Optional[Dict]:
        """
        使用MCP工具分析视频（通过缩略图）

        注意：这里使用analyze_image工具分析视频缩略图
        需要提供视频的缩略图URL
        """
        try:
            # 从YouTube URL提取视频ID，获取缩略图
            if 'youtube.com' in url or 'youtu.be' in url:
                import re
                video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', url)
                if video_id_match:
                    video_id = video_id_match.group(1)
                    thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

                    # ⚠️ 注意：这里调用MCP工具需要特殊处理
                    # 由于MCP工具是通过系统调用的，这里先返回URL
                    # 实际的MCP调用将在LLM评估阶段通过prompt传入
                    return {
                        'type': 'video_thumbnail_url',
                        'thumbnail_url': thumbnail_url,
                        'note': 'MCP图像分析将在LLM评估时进行'
                    }
        except Exception as e:
            logger.warning(f"视频缩略图分析失败: {str(e)}")

        return None


    def _fetch_web_content_with_mcp(self, url: str) -> Optional[Dict]:
        """
        使用MCP webReader工具提取网页内容

        ⚠️ 注意：为了避免阻塞，这里只返回URL
        实际的MCP调用将在需要时通过外部处理
        """
        try:
            # ⚠️ 为了性能考虑，暂时不直接调用MCP webReader
            # 如果需要启用，可以在外部通过MCP工具调用
            return {
                'type': 'web_content_url',
                'url': url,
                'note': 'MCP网页内容提取将在需要时进行'
            }
        except Exception as e:
            logger.warning(f"网页内容提取失败: {str(e)}")

        return None

    def score_results(self, results: List[Dict[str, Any]], query: str, metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        对多个结果进行评分和排序

        Args:
            results: 搜索结果列表
            query: 搜索查询
            metadata: 额外的元数据

        Returns:
            评分并排序后的结果列表
        """
        import concurrent.futures

        logger.info(f"📊 开始评估 {len(results)} 个搜索结果，使用 Gemini 2.5 Flash 模型（并发模式）")

        # 🚀 并发评估（最多5个同时进行，避免过载）
        MAX_WORKERS = 5
        scored_results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # 提交所有评估任务
            future_to_result = {
                executor.submit(self._evaluate_single_result, result, query, metadata): (idx, result)
                for idx, result in enumerate(results)
            }

            # 等待完成并收集结果
            completed_count = 0
            for future in concurrent.futures.as_completed(future_to_result):
                idx, original_result = future_to_result[future]
                try:
                    scored_result = future.result(timeout=30)  # 单个评估最多30秒
                    scored_result['original_index'] = idx  # 保留原始顺序
                    scored_results.append(scored_result)
                    completed_count += 1

                    # 每5个结果打印一次进度
                    if completed_count % 5 == 0:
                        logger.info(f"  进度: {completed_count}/{len(results)} 个结果已评估")
                except Exception as e:
                    logger.error(f"结果评估失败 (索引{idx}): {str(e)[:100]}")
                    # 降级到规则评分
                    score = self.score_result(original_result, query, metadata)
                    original_result['score'] = round(score, 2)
                    original_result['recommendation_reason'] = self._generate_recommendation_reason(original_result, score)
                    original_result['evaluation_method'] = 'Rule-based'
                    original_result['original_index'] = idx
                    scored_results.append(original_result)
                    completed_count += 1

        # ❌ 移除排序：排序会破坏original_index的对应关系
        # scored_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        # 排序应该在search_engine_v2.py中完成，在正确匹配分数之后

        # 统计评估方法
        llm_count = sum(1 for r in scored_results if r.get('evaluation_method') == 'LLM')
        rule_count = len(scored_results) - llm_count

        logger.info(f"✅ 评估完成: {len(results)}个结果 (LLM: {llm_count}, 规则: {rule_count})")

        return scored_results

    def _evaluate_single_result(self, result: Dict[str, Any], query: str, metadata: Optional[Dict]) -> Dict[str, Any]:
        """
        评估单个结果（并发执行）

        Args:
            result: 搜索结果字典
            query: 搜索查询
            metadata: 额外的元数据

        Returns:
            评分后的结果字典
        """
        # ✅ 使用MCP工具丰富结果信息（视频缩略图、网页内容等）
        try:
            result = self._enrich_result_with_mcp_tools(result, metadata or {})
        except Exception as e:
            logger.warning(f"MCP工具丰富失败: {str(e)[:100]}")

        # 优先使用LLM评估（生成一致的分数和推荐理由）
        llm_evaluation = self._evaluate_with_llm(result, query, metadata)

        if llm_evaluation:
            # LLM评估成功
            result['score'] = llm_evaluation['score']
            result['recommendation_reason'] = llm_evaluation['recommendation_reason']
            # ✅ 使用LLM评估返回的评估方法（可能是 'MCP Tools', 'LLM' 等）
            result['evaluation_method'] = llm_evaluation.get('evaluation_method', 'LLM')

            # ✅ 后处理验证：纠正LLM的明显错误（但跳过MCP Tools）
            try:
                result = self._validate_and_correct_score(result, metadata)
            except Exception as e:
                logger.warning(f"评分验证失败: {str(e)[:100]}")
        else:
            # LLM评估失败，降级到规则评分
            score = self.score_result(result, query, metadata)
            result['score'] = round(score, 2)
            result['recommendation_reason'] = self._generate_recommendation_reason(result, score)
            result['evaluation_method'] = 'Rule-based'

            # ✅ 规则评分也需要验证
            try:
                result = self._validate_and_correct_score(result, metadata)
            except Exception as e:
                logger.warning(f"评分验证失败: {str(e)[:100]}")

        return result

    # ========== 多语言年级/学科识别函数 ==========

    def _extract_grade_from_title(
        self,
        title: str,
        target_grade: str,
        language_hint: str = 'auto'
    ) -> Optional[str]:
        """
        使用LLM从标题中提取年级信息并标准化为中文（纯LLM方案）

        Args:
            title: 标题文本（任意语言）
            target_grade: 目标年级（如："一年级"、"الصف الأول / 一年级"）
            language_hint: 语言提示（可选：zh, ar, ru, id, en, fr, es, auto）

        Returns:
            标准化的年级中文名称（如：一年级、二年级、...、十二年级）
            如果无法识别或无法匹配，返回None
        """
        # ✅ 缓存检查
        cache_key = f"{title}|{target_grade}"
        cached_result = self._cache_get(self._grade_extraction_cache, cache_key)
        if cached_result is not None:
            logger.debug(f"[缓存命中] 年级识别：{title[:50]} → {cached_result}")
            return cached_result

        if not self.llm_client:
            return None

        try:
            # 从混合格式的target_grade中提取中文部分
            if '/' in target_grade:
                target_grade_zh = target_grade.split('/')[-1].strip()
            else:
                # 如果target_grade是纯外文，需要LLM翻译
                target_grade_zh = target_grade

            # 构建识别prompt
            prompt = f"""请从以下标题中提取年级信息，并判断是否与目标年级匹配。

【目标年级】
{target_grade_zh}

【标题】
{title}

【任务】
1. 识别标题中的年级信息（支持任意语言）
2. 将标题中的年级翻译成中文（一年级到十二年级）
3. 判断标题年级是否与目标年级匹配

【输出格式】（严格JSON）
{{
  "detected_grade": "识别出的年级中文名",
  "target_grade": "{target_grade_zh}",
  "is_match": true/false,
  "confidence": "high/medium/low"
}}

【示例】
目标年级：一年级
标题：الصف الثاني - الرياضيات
输出：{{"detected_grade":"二年级","target_grade":"一年级","is_match":false,"confidence":"high"}}

目标年级：八年级
标题：التربية الفنية - الصف الثامن
输出：{{"detected_grade":"八年级","target_grade":"八年级","is_match":true,"confidence":"high"}}

现在请处理上述标题并返回JSON："""

            # 调用LLM（使用配置的快速推理模型）
            config_manager = get_config_manager()
            models = config_manager.get_llm_models()
            fast_model = models.get('fast_inference', 'gemini-2.5-pro')

            logger.info(f"[📡 LLM调用] 使用快速推理模型: {fast_model}")
            response = self.llm_client.call_llm(
                prompt=prompt,
                max_tokens=100,
                temperature=0.1,
                model=fast_model
            )

            # 解析响应
            import json
            import re

            # ✅ 清理响应：移除代码块标记
            response_clean = response.strip()
            if '```json' in response_clean:
                response_clean = response_clean.split('```json')[1].split('```')[0].strip()
            elif '```' in response_clean:
                response_clean = response_clean.split('```')[1].split('```')[0].strip()

            # 提取JSON
            json_match = re.search(r'\{[^{}]*\}', response_clean)
            if json_match:
                result_data = json.loads(json_match.group())
                detected_grade = result_data.get('detected_grade', '')

                # 验证年级名称是否有效
                valid_grades = [
                    '一年级', '二年级', '三年级', '四年级', '五年级', '六年级',
                    '七年级', '八年级', '九年级', '高一', '高二', '高三', '十二年级'
                ]

                if detected_grade in valid_grades:
                    logger.debug(f"LLM识别年级：{title[:50]} → {detected_grade}")
                    # ✅ 缓存结果
                    self._cache_set(self._grade_extraction_cache, cache_key, detected_grade)
                    return detected_grade

            logger.warning(f"LLM年级识别失败或返回无效：{response[:100]}")
            return None

        except Exception as e:
            logger.warning(f"LLM年级识别异常: {str(e)[:100]}")
            return None


    def _extract_subject_from_title(
        self,
        title: str,
        target_subject: str,
        language_hint: str = 'auto'
    ) -> Optional[str]:
        """
        使用LLM从标题中提取学科信息并标准化为中文（纯LLM方案）

        Args:
            title: 标题文本（任意语言）
            target_subject: 目标学科（如："体育"、"التربية البدنية / 体育"）
            language_hint: 语言提示

        Returns:
            标准化的学科中文名称
        """
        # ✅ 缓存检查
        cache_key = f"{title}|{target_subject}"
        cached_result = self._cache_get(self._subject_extraction_cache, cache_key)
        if cached_result is not None:
            logger.debug(f"[缓存命中] 学科识别：{title[:50]} → {cached_result}")
            return cached_result

        if not self.llm_client:
            return None

        try:
            # 从混合格式的target_subject中提取中文部分
            if '/' in target_subject:
                target_subject_zh = target_subject.split('/')[-1].strip()
            else:
                target_subject_zh = target_subject

            # 构建识别prompt
            prompt = f"""请从以下标题中提取学科信息，并判断是否与目标学科匹配。

【目标学科】
{target_subject_zh}

【标题】
{title}

【任务】
1. 识别标题中的学科/课程类型（支持任意语言）
2. 将标题中的学科翻译成中文
3. 判断标题学科是否与目标学科匹配

【常见学科类型】
数学、语文、英语、阿拉伯语、俄语、法语、西班牙语、艺术、美术、音乐、体育、科学、物理、化学、生物、历史、地理等

【输出格式】（严格JSON）
{{
  "detected_subject": "识别出的学科中文名",
  "target_subject": "{target_subject_zh}",
  "is_match": true/false,
  "confidence": "high/medium/low"
}}

【示例】
目标学科：数学
标题：الرياضيات - الصف الثامن
输出：{{"detected_subject":"数学","target_subject":"数学","is_match":true,"confidence":"high"}}

目标学科：艺术
标题：التربية الفنية - الصف الثامن
输出：{{"detected_subject":"艺术","target_subject":"艺术","is_match":true,"confidence":"high"}}

现在请处理上述标题并返回JSON："""

            # 调用LLM（使用配置的快速推理模型）
            config_manager = get_config_manager()
            models = config_manager.get_llm_models()
            fast_model = models.get('fast_inference', 'gemini-2.5-pro')

            logger.info(f"[📡 LLM调用] 使用快速推理模型: {fast_model}")
            response = self.llm_client.call_llm(
                prompt=prompt,
                max_tokens=100,
                temperature=0.1,
                model=fast_model
            )

            # 解析响应
            import json
            import re

            # ✅ 清理响应：移除代码块标记
            response_clean = response.strip()
            if '```json' in response_clean:
                response_clean = response_clean.split('```json')[1].split('```')[0].strip()
            elif '```' in response_clean:
                response_clean = response_clean.split('```')[1].split('```')[0].strip()

            json_match = re.search(r'\{[^{}]*\}', response_clean)
            if json_match:
                result_data = json.loads(json_match.group())
                detected_subject = result_data.get('detected_subject', '')

                # 验证学科名称是否合理
                if detected_subject and len(detected_subject) >= 2:
                    logger.debug(f"LLM识别学科：{title[:50]} → {detected_subject}")
                    # ✅ 缓存结果
                    self._cache_set(self._subject_extraction_cache, cache_key, detected_subject)
                    return detected_subject

            logger.warning(f"LLM学科识别失败或返回无效：{response[:100]}")
            return None

        except Exception as e:
            logger.warning(f"LLM学科识别异常: {str(e)[:100]}")
            return None

    # ========== 推荐/验证相关函数 ==========

    def _validate_with_mcp_tools_sync(
        self,
        result: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        同步包装器，用于在同步上下文中调用MCP工具

        Args:
            result: 搜索结果字典
            metadata: 元数据（国家、年级、学科）

        Returns:
            验证结果，如果无法判断则返回None
        """
        title = result.get('title', 'Unknown')[:50]
        logger.info(f"[🔧 MCP工具同步包装] 开始调用: {title}...")

        import asyncio
        import threading

        try:
            # 尝试获取运行中的事件循环
            loop = asyncio.get_running_loop()
            # 如果有运行中的事件循环，在新线程中运行MCP工具验证
            logger.info("[🔄 MCP工具验证] 检测到运行中的事件循环，在新线程中执行MCP验证")

            # 在新线程中创建新的事件循环来运行异步函数
            result_container = [None]
            exception_container = [None]

            def run_in_new_thread():
                try:
                    logger.info(f"[🔧 线程开始] 开始在新线程中运行MCP验证: {title[:50]}")
                    # 在新线程中创建新的事件循环
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        logger.info(f"[🔧 事件循环] 开始运行异步MCP验证")
                        mcp_result = new_loop.run_until_complete(
                            self._validate_with_mcp_tools(result, metadata)
                        )
                        logger.info(f"[🔧 异步完成] MCP验证返回，类型={type(mcp_result)}, 是否None={mcp_result is None}")
                        result_container[0] = mcp_result
                        logger.info(f"[✅ MCP工具验证] 完成: score={mcp_result.get('score') if mcp_result else 'None'}")
                        logger.info(f"[✅ MCP工具验证] 存储到result_container: {type(mcp_result)}")
                        if mcp_result:
                            logger.info(f"[✅ MCP工具验证] result keys: {list(mcp_result.keys()) if isinstance(mcp_result, dict) else 'N/A'}")
                        else:
                            logger.warning(f"[⚠️ MCP工具验证] mcp_result is None!")
                    finally:
                        # 等待所有任务完成后再关闭
                        pending = asyncio.all_tasks(new_loop)
                        if pending:
                            new_loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                        new_loop.close()
                except Exception as e:
                    logger.error(f"[❌ MCP工具验证] 线程执行异常: {str(e)}", exc_info=True)
                    exception_container[0] = e

            thread = threading.Thread(target=run_in_new_thread)
            thread.start()
            thread.join(timeout=15)  # ✅ 增加超时到15秒

            if exception_container[0]:
                logger.error(f"[❌ MCP工具验证] 线程异常: {str(exception_container[0])}")
                return None  # ✅ 返回None而不是抛出异常

            if thread.is_alive():
                logger.warning("[⚠️ MCP工具验证] 线程超时（15秒），MCP验证未完成")
                return None

            logger.info(f"[📊 MCP工具验证] 返回: {result_container[0] is not None}")
            if result_container[0] is not None:
                logger.info(f"[📊 MCP工具验证] 返回类型: {type(result_container[0])}, 内容: {str(result_container[0])[:200]}")
            else:
                logger.error(f"[❌ MCP工具验证] result_container[0] is None!")
            return result_container[0]

        except RuntimeError:
            # 没有运行中的事件循环，可以安全使用asyncio.run
            try:
                return asyncio.run(self._validate_with_mcp_tools(result, metadata))
            except Exception as e:
                logger.error(f"[❌ MCP工具验证] 同步调用失败: {str(e)}")
                return None

    async def _validate_with_mcp_tools(
        self,
        result: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        使用MCP工具进行验证评分（支持多语言）

        优先级：MCP工具验证 > 规则验证 > LLM评分
        用于快速、准确地识别年级/学科匹配问题

        支持的国家：印尼（ID）等

        Args:
            result: 搜索结果字典
            metadata: 元数据（国家、年级、学科）

        Returns:
            验证结果，如果无法判断则返回None
            {
                "score": 评分,
                "confidence": "high/medium/low",
                "reason": "理由",
                "identified_grade": "识别的年级",
                "identified_subject": "识别的学科"
            }
        """
        title = result.get('title', '')
        url = result.get('url', '')
        if not title:
            return None

        # 提取目标年级和学科
        target_grade = metadata.get('grade', '')
        target_subject = metadata.get('subject', '')
        target_country = metadata.get('country', '')

        # 只处理已配置国家（印尼等）
        # 从target_country提取国家代码
        country_code = None
        if target_country:
            # 尝试从国家名称或代码中提取
            if 'Indonesia' in target_country or 'ID' in target_country or '印尼' in target_country:
                country_code = 'ID'
            # 未来可以添加更多国家
            # elif 'Saudi Arabia' in target_country or 'SA' in target_country:
            #     country_code = 'SA'

        if not country_code:
            return None

        logger.info(f"[🔍 MCP工具验证] 检查{country_code}国家标题: {title[:60]}...")

        try:
            # 导入MCP工具
            from mcp_tools import (
                extract_grade_from_title,
                extract_subject_from_title,
                validate_grade_match,
                validate_url_quality
            )

            # 1. 验证URL质量（优先检查，应该尽早过滤低质量URL）
            logger.info(f"[🔍 URL验证] 开始调用validate_url_quality...")
            url_result = await validate_url_quality(url, title)
            logger.info(f"[🔍 URL验证] validate_url_quality返回，success={url_result.get('success')}")

            url_quality_info = None
            if url_result.get("success"):
                url_quality_info = url_result["data"]
                logger.info(f"  MCP URL质量: {url_quality_info['quality']}")
                logger.info(f"  MCP URL完整数据: filter={url_quality_info.get('filter')}, reason={url_quality_info.get('reason')}")
            else:
                logger.warning(f"  MCP URL验证失败: {url_result}")

            # 2. 处理URL过滤（如果URL应该被过滤，直接返回）
            logger.info(f"[🔍 URL过滤检查] url_quality_info存在={url_quality_info is not None}, filter={url_quality_info.get('filter') if url_quality_info else 'N/A'}")
            if url_quality_info and url_quality_info.get('filter'):
                # 应该过滤的URL（社交媒体等）
                score = 0.0
                reason = f"不推荐（{url_quality_info['reason']}）"

                logger.warning(f"[🚨 MCP工具验证] URL应过滤: {score}")
                logger.warning(f"   理由: {reason}")
                logger.warning(f"[✅ MCP工具验证] 返回URL过滤结果，退出函数")

                return {
                    'score': score,
                    'confidence': 'high',
                    'reason': reason,
                    'identified_grade': None,
                    'identified_subject': None,
                    'validation_type': 'url_filter',
                    'url_quality': url_quality_info
                }
            else:
                logger.info(f"[ℹ️ URL过滤检查] URL不需要过滤或无法判断，继续处理")

            # 3. 提取年级
            grade_result = await extract_grade_from_title(title, country_code)

            identified_grade_info = None
            identified_grade = None
            if grade_result.get("success"):
                identified_grade_info = grade_result["data"]
                identified_grade = identified_grade_info.get("local_name") or identified_grade_info.get("grade_name")
                logger.info(f"  MCP识别年级: {identified_grade_info['grade_name']} ({identified_grade_info['local_name']})")
            else:
                logger.info(f"  MCP无法识别年级")
                # 如果无法识别年级，仍然继续检查学科（但稍后可能返回None）

            # 4. 提取学科
            subject_result = await extract_subject_from_title(title, country_code)

            identified_subject_info = None
            identified_subject = None
            if subject_result.get("success"):
                identified_subject_info = subject_result["data"]
                identified_subject = identified_subject_info.get("local_name") or identified_subject_info.get("subject_name")
                logger.info(f"  MCP识别学科: {identified_subject_info['subject_name']} ({identified_subject_info['local_name']})")

            # 5. 验证年级匹配
            if identified_grade and target_grade:
                # 规范化年级名称（处理 "Kelas 1 / 一年级" 这种格式）
                normalized_target = target_grade.split('/')[0].strip() if '/' in target_grade else target_grade

                validation_result = await validate_grade_match(normalized_target, identified_grade, country_code)

                if validation_result.get("success"):
                    match_info = validation_result["data"]
                    is_match = match_info.get("match", False)

                    if not is_match:
                        # 年级不匹配，强制低分
                        score = 2.0  # 强制低分

                        reason_parts = []
                        reason_parts.append(f"年级不符（目标{match_info['target_grade_name']}，标题{match_info['identified_grade_name']}）")

                        # 检查学科
                        if identified_subject and target_subject:
                            normalized_subject = target_subject.split('/')[0].strip() if '/' in target_subject else target_subject
                            if identified_subject == normalized_subject or \
                               identified_subject_info.get('subject_name') == normalized_subject:
                                score = 2.5  # 学科正确，但年级不符
                                reason_parts.append(f"学科正确（{identified_subject}）")

                        reason = "，".join(reason_parts) + "，不推荐"

                        logger.warning(f"[🚨 MCP工具验证] 年级不符，强制低分: {score}")
                        logger.warning(f"   理由: {reason}")

                        return {
                            'score': score,
                            'confidence': 'high',
                            'reason': reason,
                            'identified_grade': identified_grade,
                            'identified_subject': identified_subject,
                            'validation_type': 'grade_mismatch',
                            'match_info': match_info
                        }

            # 6. 年级匹配，给高分
            if identified_grade:
                score = 9.0  # 基础分

                reason_parts = [
                    f"年级匹配（{identified_grade_info['grade_name']}）"
                ]

                # 检查学科
                if identified_subject and target_subject:
                    normalized_subject = target_subject.split('/')[0].strip() if '/' in target_subject else target_subject
                    if identified_subject == normalized_subject or \
                       identified_subject_info.get('subject_name') == normalized_subject:
                        score = 9.5  # 学科也正确
                        reason_parts.append(f"学科匹配（{identified_subject_info['subject_name']}）")
                    else:
                        score = 8.0  # 学科相关
                        reason_parts.append(f"学科相关（{identified_subject_info['subject_name']}）")

                # URL质量加分
                if url_quality_info:
                    score_adjustment = url_quality_info.get('score_adjustment', 0)
                    if score_adjustment > 0:
                        score += score_adjustment
                        if url_quality_info.get('reason') == 'youtube_playlist':
                            reason_parts.append("YouTube播放列表")
                        elif url_quality_info.get('reason') == 'trusted_platform':
                            reason_parts.append("来自可信平台")

                score = min(score, 10.0)  # 最高10分
                reason = "，".join(reason_parts) + "，来自可信平台" if score_adjustment > 0 else "，高度匹配"

                logger.info(f"[✅ MCP工具验证] 年级匹配，给高分: {score}")
                logger.info(f"   理由: {reason}")

                return {
                    'score': score,
                    'confidence': 'high',
                    'reason': reason,
                    'identified_grade': identified_grade,
                    'identified_subject': identified_subject,
                    'validation_type': 'grade_match',
                    'url_quality': url_quality_info
                }

            # 无法用MCP工具判断
            logger.info(f"[ℹ️ MCP工具验证] 无法明确判断，交给规则验证或LLM")
            return None

        except ImportError as e:
            logger.warning(f"[⚠️ MCP工具验证] 无法导入MCP工具: {e}")
            return None
        except Exception as e:
            logger.error(f"[❌ MCP工具验证] 验证失败: {str(e)}", exc_info=True)
            logger.error(f"[❌ MCP工具验证] 结果标题: {title[:80] if title else 'N/A'}")
            logger.error(f"[❌ MCP工具验证] URL: {url[:80] if url else 'N/A'}")
            return None

    def _validate_with_rules(
        self,
        result: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        使用规则验证评分（阿拉伯语标准化）

        优先级：规则验证 > LLM评分
        用于快速、准确地识别明显的年级/学科匹配问题

        Args:
            result: 搜索结果字典
            metadata: 元数据（国家、年级、学科）

        Returns:
            验证结果，如果无法判断则返回None
            {
                "score": 评分,
                "confidence": "high/medium/low",
                "reason": "理由",
                "identified_grade": "识别的年级",
                "identified_subject": "识别的学科"
            }
        """
        title = result.get('title', '')
        if not title:
            return None

        # 提取目标年级和学科
        target_grade = metadata.get('grade', '')
        target_subject = metadata.get('subject', '')
        target_country = metadata.get('country', '')

        # 判断是否是阿拉伯语内容
        if not ArabicNormalizer.is_arabic_text(title):
            return None

        logger.info(f"[🔍 规则验证] 检查阿拉伯语标题: {title[:60]}...")

        # 提取年级
        grade_info = ArabicNormalizer.extract_grade(title)
        # 提取学科
        subject_info = ArabicNormalizer.extract_subject(title)

        identified_grade = grade_info['grade']
        identified_subject = subject_info['subject']

        logger.info(f"  识别年级: {identified_grade} ({grade_info['grade_arabic']})")
        logger.info(f"  识别学科: {identified_subject} ({subject_info['subject_arabic'] if subject_info['subject_arabic'] else 'N/A'})")

        # 规则1: 明确的年级不符
        if identified_grade and identified_grade != target_grade:
            # 年级不符，强制低分
            score = 3.0  # 强制低分

            reason_parts = [
                f"识别为{identified_grade}（{grade_info['grade_arabic']}）"
            ]

            # 检查学科
            if identified_subject and identified_subject == target_subject:
                score = 3.0  # 学科正确，但年级不符
                reason_parts.append(f"学科正确（{identified_subject}）")
            else:
                score = 2.0  # 年级和学科都不符
                if identified_subject:
                    reason_parts.append(f"学科不符（{identified_subject}，目标{target_subject}）")
                else:
                    reason_parts.append(f"学科未明确")

            reason = "，".join(reason_parts) + f"，与目标{target_grade}不符，大幅减分"

            logger.warning(f"[🚨 规则验证] 年级不符，强制低分: {score}")
            logger.warning(f"   理由: {reason}")

            return {
                'score': score,
                'confidence': 'high',
                'reason': reason,
                'identified_grade': identified_grade,
                'identified_subject': identified_subject,
                'validation_type': 'grade_mismatch'
            }

        # 规则2: 明确的年级匹配
        if identified_grade and identified_grade == target_grade:
            # 年级正确，给高分
            score = 9.0  # 基础分

            reason_parts = [
                f"年级正确（{identified_grade} - {grade_info['grade_arabic']}）"
            ]

            # 检查学科
            if identified_subject and identified_subject == target_subject:
                score = 9.5  # 学科也正确，给更高分
                reason_parts.append(f"学科正确（{identified_subject}）")
            elif identified_subject:
                score = 8.0  # 学科相关
                reason_parts.append(f"学科相关（{identified_subject}）")
            else:
                reason_parts.append("学科匹配（数学）")

            # 检查是否是播放列表
            if 'playlist' in result.get('url', '').lower() or 'list' in result.get('url', '').lower():
                score += 0.5  # 播放列表加分
                reason_parts.append("完整播放列表")

            score = min(score, 10.0)  # 最高10分
            reason = "，".join(reason_parts) + "，高度匹配"

            logger.info(f"[✅ 规则验证] 年级正确，给高分: {score}")
            logger.info(f"   理由: {reason}")

            return {
                'score': score,
                'confidence': 'high',
                'reason': reason,
                'identified_grade': identified_grade,
                'identified_subject': identified_subject,
                'validation_type': 'grade_match'
            }

        # 规则3: 年级不明确，但学科正确
        if not identified_grade and identified_subject and identified_subject == target_subject:
            score = 6.0  # 中等分

            reason = f"学科正确（{identified_subject}），但年级不明确，给中等分"

            logger.info(f"[⚠️ 规则验证] 年级不明确，给中等分: {score}")
            logger.info(f"   理由: {reason}")

            return {
                'score': score,
                'confidence': 'medium',
                'reason': reason,
                'identified_grade': None,
                'identified_subject': identified_subject,
                'validation_type': 'grade_unclear'
            }

        # 无法用规则判断
        logger.info(f"[ℹ️ 规则验证] 无法明确判断，交给LLM")
        return None

    def _extract_grade_subject_batch(
        self,
        results: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        批量提取所有结果的年级和学科信息（优化性能）.

        Issue #037: Sequential LLM Calls Bottleneck - FIXED
        将原本的 N×2 次LLM调用（每个结果2次调用）优化为1次批量调用.

        Args:
            results: 搜索结果列表
            metadata: 元数据（包含grade, subject, language_code）

        Returns:
            提取结果列表，每个元素包含 {"grade": str|null, "subject": str|null}
        """
        if not self.llm_client or not results:
            # 返回空结果列表
            return [{"grade": None, "subject": None} for _ in results]

        target_grade = metadata.get('grade', '')
        target_subject = metadata.get('subject', '')
        language = metadata.get('language_code', 'zh')

        # 处理混合格式的年级/学科
        if '/' in target_grade:
            target_grade = target_grade.split('/')[-1].strip()
        if '/' in target_subject:
            target_subject = target_subject.split('/')[-1].strip()

        try:
            # 构建批量提取的prompt
            result_lines = []
            for idx, result in enumerate(results):
                title = result.get('title', '')[:100]  # 限制长度
                result_lines.append(f"{idx + 1}. {title}")

            prompt = f"""从以下{len(results)}个资源标题中批量提取年级和学科信息。

【目标年级】{target_grade}
【目标学科】{target_subject}
【语言】{language}

【资源标题】
{chr(10).join(result_lines)}

【任务】
为每个标题提取年级和学科，返回JSON数组格式。

【输出格式】（严格JSON数组）
[
  {{"grade": "提取的年级中文名或null", "subject": "提取的学科中文名或null"}},
  ...
]

注意：
1. 如果标题中没有年级信息，返回null
2. 如果标题中没有学科信息，返回null
3. 年级必须是中文（一年级到十二年级）
4. 学科必须是中文（数学、语文、英语、艺术、体育等）
5. 只返回JSON数组，不要其他内容

现在请处理并返回JSON数组："""

            # 单次LLM调用提取所有结果（优化：120秒→3-6秒）
            logger.info(f"[🚀 批量提取] 使用1次LLM调用提取{len(results)}个结果的年级和学科")
            response = self.llm_client.call_llm(
                prompt=prompt,
                max_tokens=50 * len(results),  # 每个结果约50 tokens
                temperature=0.3,
                model='gemini-2.5-flash'  # 使用快速模型
            )

            # 解析批量响应
            import json
            import re

            # 清理响应
            response_clean = response.strip()
            if '```json' in response_clean:
                response_clean = response_clean.split('```json')[1].split('```')[0].strip()
            elif '```' in response_clean:
                response_clean = response_clean.split('```')[1].split('```')[0].strip()

            # 提取JSON数组
            json_match = re.search(r'\[.*\]', response_clean, re.DOTALL)
            if json_match:
                extractions = json.loads(json_match.group())

                # 验证并补充结果
                if isinstance(extractions, list):
                    # 补充缺失的结果
                    while len(extractions) < len(results):
                        extractions.append({"grade": None, "subject": None})

                    # 截断多余的结果
                    extractions = extractions[:len(results)]

                    logger.info(f"[✅ 批量提取成功] 提取了{len(extractions)}个结果")
                    return extractions

        except Exception as e:
            logger.warning(f"[⚠️ 批量提取失败] {e}，将回退到逐个提取")

        # 回退：逐个提取（仍比原始的2×N次调用更优）
        logger.info(f"[🔄 回退到逐个提取] 使用缓存优化的逐个提取")
        fallback_results = []
        for result in results:
            grade = self._extract_grade_from_title(
                result.get('title', ''),
                target_grade,
                language
            )
            subject = self._extract_subject_from_title(
                result.get('title', ''),
                target_subject,
                language
            )
            fallback_results.append({
                "grade": grade,
                "subject": subject
            })

        return fallback_results

    def _validate_and_correct_score(
        self,
        result: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        验证并纠正LLM评分的明显错误

        检查项：
        1. 年级不匹配 → 大幅降分
        2. 学科不匹配 → 大幅降分
        3. 年级/学科匹配 → 更新推荐理由，使其更具体

        Args:
            result: 包含score和recommendation_reason的结果字典
            metadata: 元数据（grade, subject, language_code）

        Returns:
            验证并纠正后的结果字典
        """
        # ✅ 如果评估方法是MCP Tools，说明已经过MCP工具验证，跳过后处理验证
        # （MCP工具的验证更准确，不需要LLM再次验证）
        evaluation_method = result.get('evaluation_method', '')
        if evaluation_method == 'MCP Tools':
            logger.debug(f"[✅ 跳过后处理验证] 评估方法为MCP Tools，评分已验证")
            return result

        title = result.get('title', '')
        score = result.get('score', 5.0)
        reason = result.get('recommendation_reason', '')

        # 获取目标年级和学科
        target_grade = metadata.get('grade', '') if metadata else ''
        target_subject = metadata.get('subject', '') if metadata else ''
        language = metadata.get('language_code', 'zh') if metadata else 'zh'

        # ✅ 处理混合格式的年级（如："الصف الأول / 一年级" → "一年级"）
        if '/' in target_grade:
            # 提取中文部分
            target_grade = target_grade.split('/')[1].strip() if len(target_grade.split('/')) > 1 else target_grade.split('/')[0].strip()

        # ✅ 处理混合格式的学科（如："التربية البدنية / 体育" → "体育"）
        if '/' in target_subject:
            # 提取中文部分
            target_subject = target_subject.split('/')[1].strip() if len(target_subject.split('/')) > 1 else target_subject.split('/')[0].strip()

        # ✅ 优先使用MCP工具提取年级和学科（更准确）
        extracted_grade = None
        extracted_subject = None

        # 获取国家代码
        country_code = metadata.get('country', 'ID') if metadata else 'ID'

        # 尝试使用MCP工具提取
        try:
            from mcp_tools import extract_grade_from_title, extract_subject_from_title
            import asyncio
            import threading

            def extract_with_mcp():
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        # 提取年级
                        grade_result = new_loop.run_until_complete(
                            extract_grade_from_title(title, country_code)
                        )
                        if grade_result.get('success') and grade_result.get('data'):
                            nonlocal extracted_grade
                            extracted_grade = grade_result['data'].get('grade_name', '')

                        # 提取学科
                        subject_result = new_loop.run_until_complete(
                            extract_subject_from_title(title, country_code)
                        )
                        if subject_result.get('success') and subject_result.get('data'):
                            nonlocal extracted_subject
                            extracted_subject = subject_result['data'].get('subject_name', '')
                    finally:
                        new_loop.close()
                except Exception as e:
                    logger.debug(f"[MCP提取失败] {str(e)[:50]}")

            # 在新线程中执行
            thread = threading.Thread(target=extract_with_mcp)
            thread.start()
            thread.join(timeout=5)  # 5秒超时

            if extracted_grade or extracted_subject:
                logger.info(f"[✅ MCP后处理提取] 年级={extracted_grade}, 学科={extracted_subject}")
        except Exception as e:
            logger.debug(f"[MCP后处理失败] {str(e)[:50]}")

        # ❌ 降级：如果MCP工具未提取到，使用LLM提取（可能不准确）
        if not extracted_grade:
            extracted_grade = self._extract_grade_from_title(title, target_grade, language)
        if not extracted_subject:
            extracted_subject = self._extract_subject_from_title(title, target_subject, language)

        # 检查年级匹配情况
        grade_matched = (extracted_grade and target_grade and extracted_grade == target_grade)
        grade_mismatched = (extracted_grade and target_grade and extracted_grade != target_grade)
        grade_unrecognized = (not extracted_grade)  # ⚠️ 年级无法识别

        # 检查学科匹配情况
        subject_matched = (extracted_subject and target_subject and extracted_subject == target_subject)
        subject_mismatched = (extracted_subject and target_subject and extracted_subject != target_subject)
        subject_unrecognized = (not extracted_subject)  # ⚠️ 学科无法识别

        # ⚠️ 优先处理无法识别年级/学科但给高分的情况
        if grade_unrecognized and score > 7.0:
            # 年级无法识别但给高分 → 降分
            logger.warning(
                f"[评分验证] 年级无法识别但给高分：title={title[:50]}, "
                f"score={score}, target_grade={target_grade}"
            )

            # 降分到中等分数
            score = 5.0
            reason = "年级无法从标题中识别，无法确认是否匹配，建议谨慎使用"

        elif subject_unrecognized and score > 7.0:
            # 学科无法识别但给高分 → 降分
            logger.warning(
                f"[评分验证] 学科无法识别但给高分：title={title[:50]}, "
                f"score={score}, target_subject={target_subject}"
            )

            # 降分
            score = max(score - 2.0, 5.0)
            reason = "学科无法从标题中识别，相关性不明确"

        # 处理明确的不匹配情况
        elif grade_mismatched:
            # 年级不匹配，大幅降分
            logger.warning(
                f"[评分验证] 年级不匹配：目标={target_grade}, "
                f"标题={title[:50]}, 提取={extracted_grade}"
            )

            # 修正分数（最多3分）
            if score > 3.0:
                score = 2.0

            # 修正推荐理由
            if subject_mismatched:
                # 年级和学科都不匹配
                reason = (
                    f"年级和学科都不匹配（目标：{target_grade} {target_subject}，"
                    f"标题：{extracted_grade} {extracted_subject}），不推荐"
                )
            else:
                reason = (
                    f"年级不匹配（目标：{target_grade}，标题：{extracted_grade}），"
                    f"不推荐用于当前查询"
                )

        elif subject_mismatched:
            # 学科不匹配，大幅降分
            logger.warning(
                f"[评分验证] 学科不匹配：目标={target_subject}, "
                f"标题={title[:50]}, 提取={extracted_subject}"
            )

            # 修正分数（最多3分）
            if score > 3.0:
                score = 2.0

            # 修正推荐理由
            reason = (
                f"学科不匹配（目标：{target_subject}，标题：{extracted_subject}），"
                f"不推荐用于当前查询"
            )

        elif grade_matched and subject_matched:
            # ✅ 年级和学科都匹配，更新推荐理由使其更具体
            logger.debug(
                f"[评分验证] 完全匹配：目标={target_grade} {target_subject}, "
                f"提取={extracted_grade} {extracted_subject}"
            )

            # 在原有推荐理由前添加匹配信息
            match_info = f"年级和学科完全匹配（{target_grade} {target_subject}）"
            if match_info not in reason:
                reason = f"{match_info}、{reason}"

        # 更新结果
        result['score'] = score
        result['recommendation_reason'] = reason
        result['validated'] = True

        return result


    def _generate_recommendation_reason(self, result: Dict[str, Any], score: float) -> str:
        """生成推荐理由"""
        reasons = []

        if score >= 8.0:
            reasons.append("高质量教育资源")
        elif score >= 6.0:
            reasons.append("相关性较高的内容")

        url = result.get('url', '').lower()
        title = result.get('title', '').lower()

        # 检查可信来源
        for domain in self.trusted_domains.keys():
            if domain in url:
                reasons.append(f"来自可信平台 {domain}")
                break

        # 检查播放列表
        combined = f"{url} {title}"
        if any(kw in combined for kw in ['playlist', '播放列表', 'complete', '完整']):
            reasons.append("完整课程/播放列表")

        # 检查视频内容
        if any(kw in combined for kw in self.video_keywords):
            reasons.append("视频资源")

        return "、".join(reasons) if reasons else "根据搜索匹配度推荐"

    # ========================================================================
    # 知识库集成方法
    # ========================================================================

    def get_grade_variants_from_kb(self, grade: str) -> List[str]:
        """
        从知识库获取年级的所有已知表达

        Args:
            grade: 年级 (如: "2", "Grade 2")

        Returns:
            该年级的所有已知表达列表
        """
        if self.kb_manager:
            variants = self.kb_manager.get_grade_variants(grade)
            if variants:
                logger.debug(f"[📚 知识库] 找到 {grade} 的 {len(variants)} 个表达")
            return variants
        return []

    def get_subject_variants_from_kb(self, subject: str) -> List[str]:
        """
        从知识库获取学科的所有已知表达

        Args:
            subject: 学科 (如: "Mathematics", "Math")

        Returns:
            该学科的所有已知表达列表
        """
        if self.kb_manager:
            variants = self.kb_manager.get_subject_variants(subject)
            if variants:
                logger.debug(f"[📚 知识库] 找到 {subject} 的 {len(variants)} 个表达")
            return variants
        return []

    def validate_score_with_kb(self, title: str, score: float, reasoning: str,
                               target_grade: str) -> Tuple[bool, str]:
        """
        使用知识库验证评分是否合理

        Args:
            title: 结果标题
            score: LLM评分
            reasoning: LLM理由
            target_grade: 目标年级

        Returns:
            (is_valid, message) - 是否合理，以及说明
        """
        if not self.kb_manager:
            return True, "无知识库"

        # 获取目标年级的所有表达
        grade_variants = self.get_grade_variants_from_kb(target_grade)

        if not grade_variants:
            # 知识库中没有这个年级的信息
            return True, "知识库无该年级信息"

        # 检查标题是否包含年级的任何表达
        title_lower = title.lower()

        # 对于阿拉伯语，需要特殊处理（词根匹配）
        grade_mentioned = False
        for variant in grade_variants:
            variant_lower = variant.lower()
            # 直接子串匹配
            if variant_lower in title_lower:
                grade_mentioned = True
                break

            # 阿拉伯语特殊处理：提取词根并检查
            # "الصف" (the grade) 可能以 "للصف" (for the grade), "بالصف" (in the grade) 等形式出现
            arabic_words = [w for w in variant_lower.split() if any('\u0600' <= c <= '\u06FF' for c in w)]
            if arabic_words:
                # 对于每个阿拉伯词，检查其词根是否在标题中
                all_words_found = True
                for word in arabic_words:
                    # 去掉定冠词 "ال" (al-)
                    root = word[2:] if word.startswith('ال') else word
                    # 检查词根或带不同前缀的形式
                    found = (
                        word in title_lower or  # 完整匹配
                        root in title_lower or  # 词根匹配
                        f'ل{word}' in title_lower or  # 带"ل"前缀
                        f'ل{root}' in title_lower or  # ل+词根
                        f'ب{word}' in title_lower or  # 带"ب"前缀
                        f'ك{word}' in title_lower  # 带"ك"前缀
                    )
                    if not found:
                        all_words_found = False
                        break

                if all_words_found:
                    grade_mentioned = True
                    break

        if grade_mentioned:
            # 标题明确提到了年级
            # 检查reasoning是否声称年级不匹配/未提及，但评分又很低
            mismatch_keywords = ["未提及", "不匹配", "不符", "年级不符", "显示为"]
            has_mismatch_claim = any(kw in reasoning for kw in mismatch_keywords)

            if has_mismatch_claim and score < 6.0:
                # LLM说"未提及"但实际上标题提到了
                error_msg = f"标题包含年级表达但LLM未识别: {title}"
                logger.warning(f"[📚 知识库] ⚠️ 可疑评分: {error_msg}")
                logger.warning(f"   年级变体: {grade_variants}")
                logger.warning(f"   评分: {score}, 理由: {reasoning}")

                # 记录到知识库
                self.kb_manager.record_llm_mistake(
                    mistake_type="grade_detection_failure",
                    example=f"{title} (评分: {score}, 理由: {reasoning})",
                    correction=f"标题包含年级表达: {grade_variants}",
                    severity="high"
                )

                return False, error_msg

        return True, "OK"

    def record_llm_mistake(self, mistake_type: str, example: str,
                          correction: str, severity: str = "high"):
        """
        记录LLM错误到知识库

        Args:
            mistake_type: 错误类型
            example: 错误示例
            correction: 修正方案
            severity: 严重程度
        """
        if self.kb_manager:
            self.kb_manager.record_llm_mistake(mistake_type, example, correction, severity)


# 全局单例
_global_scorer: Optional[IntelligentResultScorer] = None


def get_result_scorer() -> IntelligentResultScorer:
    """获取全局结果评分器实例"""
    global _global_scorer
    if _global_scorer is None:
        _global_scorer = IntelligentResultScorer()
    return _global_scorer


def get_result_scorer_with_kb(country_code: str) -> IntelligentResultScorer:
    """
    获取带知识库的结果评分器实例

    Args:
        country_code: 国家代码 (如: IQ, ID, CN)

    Returns:
        带知识库的评分器实例
    """
    return IntelligentResultScorer(country_code=country_code)


IntelligentResultScorer.get_result_scorer_with_kb = staticmethod(get_result_scorer_with_kb)


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("智能结果评分测试")
    print("=" * 50)

    scorer = IntelligentResultScorer()

    # 测试结果
    test_results = [
        {
            "title": "Kelas 10 Matematika: Lengkap Video Pembelajaran",
            "url": "https://www.youtube.com/playlist?list=example",
            "snippet": "Video pembelajaran matematika lengkap untuk kelas 10. Cover aljabar, geometri, statistik, dan banyak lagi. 200+ video tersedia."
        },
        {
            "title": "Math Tutorial",
            "url": "https://bit.ly/math123",
            "snippet": "Short math tutorial"
        },
        {
            "title": "Khan Academy: Mathematics Grade 10",
            "url": "https://www.khanacademy.org/math/grade-10",
            "snippet": "Comprehensive mathematics courses for grade 10 students including algebra, geometry, and more. Interactive lessons and practice exercises."
        }
    ]

    query = "Kelas 10 Matematika"

    print(f"\n搜索查询: {query}\n")
    print(f"{'标题':<60} {'评分':<10} {'推荐理由'}")
    print("-" * 100)

    scored_results = scorer.score_results(test_results, query)

    for result in scored_results:
        title = result['title'][:57] + "..." if len(result['title']) > 60 else result['title']
        score = result['score']
        reason = result['recommendation_reason']
        print(f"{title:<60} {score:<10.2f} {reason}")

    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
