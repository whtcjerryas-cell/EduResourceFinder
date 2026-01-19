#!/usr/bin/env python3
"""
语言匹配评分策略

评估内容语言与目标语言的匹配度
"""

from typing import Dict, Any, Optional
from scoring.base_strategy import BaseScoringStrategy


class LanguageScoringStrategy(BaseScoringStrategy):
    """
    语言匹配评分策略

    评估维度：
    1. 语言检测
    2. 标题语言匹配
    3. 摘要语言匹配
    4. 降级匹配（英语作为通用语言）
    """

    # 语言检测特征（Unicode范围和关键词）
    LANGUAGE_PATTERNS = {
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

    def __init__(self, weight: float = 1.0):
        """
        初始化语言匹配评分策略

        Args:
            weight: 策略权重
        """
        super().__init__(name="语言匹配", weight=weight)
        self.logger.info(f"✅ 语言匹配评分策略初始化: 支持语言 {len(self.LANGUAGE_PATTERNS)} 种")

    def score(self, result: Dict[str, Any], query: str, metadata: Optional[Dict] = None) -> float:
        """
        评估语言匹配度

        Args:
            result: 搜索结果
            query: 搜索查询
            metadata: 额外的元数据（包含target_language）

        Returns:
            评分值 (0.0 - 2.5)
        """
        title = result.get('title', '')
        snippet = result.get('snippet', '')

        # 从metadata获取目标语言
        target_language = None
        if metadata:
            target_language = metadata.get('target_language') or metadata.get('language')

        # 如果没有指定目标语言，不加分也不减分
        if not target_language or target_language not in self.LANGUAGE_PATTERNS:
            return 0.0

        # 检测标题和摘要的语言
        title_language = self.detect_language(title)
        snippet_language = self.detect_language(snippet)

        # 完全匹配：标题和摘要都是目标语言
        if title_language == target_language and snippet_language == target_language:
            self.logger.debug(f"  ✅ 完全匹配: 标题和摘要都是 {target_language} (+2.5)")
            return 2.5

        # 标题匹配：标题是目标语言
        if title_language == target_language:
            self.logger.debug(f"  ✅ 标题匹配: {title_language} == {target_language} (+2.0)")
            return 2.0

        # 摘要匹配：摘要包含目标语言
        if snippet_language == target_language:
            self.logger.debug(f"  ✅ 摘要匹配: {snippet_language} == {target_language} (+1.5)")
            return 1.5

        # 降级匹配：如果目标语言不是英语，但内容是英语，给部分分数
        if target_language != 'en' and (title_language == 'en' or snippet_language == 'en'):
            self.logger.debug(f"  ⚠️ 降级匹配: 英语内容 (+0.5)")
            return 0.5

        # 不匹配
        self.logger.debug(f"  ❌ 不匹配: 标题={title_language}, 摘要={snippet_language}, 目标={target_language}")
        return 0.0

    def detect_language(self, text: str) -> str:
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

        for lang_code, patterns in self.LANGUAGE_PATTERNS.items():
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

    def validate_result(self, result: Dict[str, Any]) -> bool:
        """
        验证结果是否包含文本内容

        Args:
            result: 搜索结果

        Returns:
            是否有文本内容
        """
        title = result.get('title', '')
        snippet = result.get('snippet', '')
        return bool(title or snippet)

    def get_text_language(self, text: str) -> str:
        """
        获取文本的语言

        Args:
            text: 输入文本

        Returns:
            语言代码
        """
        return self.detect_language(text)

    def is_language_match(self, text: str, target_language: str) -> bool:
        """
        判断文本是否匹配目标语言

        Args:
            text: 输入文本
            target_language: 目标语言

        Returns:
            是否匹配
        """
        detected_language = self.detect_language(text)
        return detected_language == target_language
