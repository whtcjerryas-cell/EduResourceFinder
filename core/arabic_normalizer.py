#!/usr/bin/env python3
"""
阿拉伯语标准化处理模块

功能：
1. 标准化阿拉伯语文本（处理拼写变体）
2. 提取年级信息
3. 提取学科信息
4. 判断年级/学科匹配
"""

import re
from typing import Dict, List, Optional, Tuple
from utils.logger_utils import get_logger

logger = get_logger('arabic_normalizer')


class ArabicNormalizer:
    """阿拉伯语标准化处理"""

    # 年级映射（阿拉伯语数字 → 中文）
    GRADE_MAPPING = {
        'اول': '一年级',
        'ثاني': '二年级',
        'ثالث': '三年级',
        'رابع': '四年级',
        'خامس': '五年级',
        'سادس': '六年级',
        'سابع': '七年级',
        'ثامن': '八年级',
        'تاسع': '九年级',
        'عاشر': '十年级',
        'حادي عشر': '十一年级',
        'ثاني عشر': '十二年级',
    }

    # 学科映射
    SUBJECT_MAPPING = {
        'رياضيات': '数学',
        'رياضيه': '数学',  # 变体
        'علوم': '科学',
        'فيزياء': '物理',
        'كيمياء': '化学',
        'احياء': '生物',
        'لغة عربية': '阿拉伯语',
        'لغة انجليزية': '英语',
        'دراسات اجتماعية': '社会研究',
    }

    # 年级关键词模式（更全面的匹配）
    GRADE_PATTERNS = {
        '一年级': [
            r'الصف[\s]+الاول',     # الصف الأول (标准)
            r'الصف[\s]+الأول',     # 带alif
            r'الصف[\s]+الإول',     # 带hamza
            r'صف[\s]+اول',         # 不带al
            r'للصف[\s]+الاول',     # للصف الأول
            r'للصف[\s]+الأول',
            r'للصف[\s]+الإول',
        ],
        '二年级': [
            r'الصف[\s]+الثاني',    # الصف الثاني
            r'الصف[\s]+الثانى',    # 变体
            r'صف[\s]+ثاني',
        ],
        '三年级': [
            r'الصف[\s]+الثالث',    # الصف الثالث
            r'الصف[\s]+الثالث',    # 变体
            r'صف[\s]+ثالث',
        ],
        '四年级': [
            r'الصف[\s]+الرابع',    # الصف الرابع
            r'الصف[\s]+الرابع',    # 变体
            r'صف[\s]+رابع',
        ],
        '五年级': [
            r'الصف[\s]+الخامس',    # الصف الخامس
            r'الصف[\s]+الخامس',    # 变体
            r'صف[\s]+خامس',
        ],
        '六年级': [
            r'الصف[\s]+السادس',    # الصف السادس
            r'الصف[\s]+السادس',    # 变体
            r'صف[\s]+سادس',        # 不带al
            r'للصف[\s]+سادس',     # للصف سادس
        ],
        '七年级': [
            r'الصف[\s]+السابع',
            r'صف[\s]+سابع',
        ],
        '八年级': [
            r'الصف[\s]+الثامن',
            r'صف[\s]+ثامن',
        ],
    }

    @staticmethod
    def normalize(text: str) -> str:
        """
        标准化阿拉伯语文本

        处理内容：
        1. 统一alif变体（إ أ آ ا → ا）
        2. 统一ya变体（ي ى → ي）
        3. 统一hamza变体（ؤ ئ ئ → ء）
        4. 统一ta marbuta（ة → ه）
        5. 标准化空格

        Args:
            text: 原始文本

        Returns:
            标准化后的文本
        """
        if not text:
            return text

        # 移除所有alif变体
        text = re.sub(r'[إأآا]', 'ا', text)

        # 移除所有ya变体
        text = re.sub(r'[يى]', 'ي', text)

        # 统一hamza（可选，保留基本形式）
        # text = re.sub(r'[ؤئء]', 'ء', text)

        # 移除ta marbuta（改为h）
        text = re.sub(r'ة', 'ه', text)

        # 标准化空格和标点
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text

    @staticmethod
    def extract_grade(title: str) -> Dict[str, any]:
        """
        从阿拉伯语标题中提取年级信息

        Args:
            title: 视频标题

        Returns:
            {
                "grade": "一年级/二年级/.../None",
                "grade_arabic": "الصف الأول/...",
                "confidence": "high/medium/low",
                "matched_pattern": "匹配的模式",
                "context": "上下文（20个字符）"
            }
        """
        if not title:
            return {
                "grade": None,
                "grade_arabic": None,
                "confidence": "low",
                "matched_pattern": None,
                "context": ""
            }

        # 标准化
        normalized = ArabicNormalizer.normalize(title)

        # 检查每个年级模式
        for grade_name, patterns in ArabicNormalizer.GRADE_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, normalized)
                if match:
                    # 提取上下文
                    start = max(0, match.start() - 10)
                    end = min(len(title), match.end() + 10)
                    context = title[start:end]

                    return {
                        "grade": grade_name,
                        "grade_arabic": match.group(0),
                        "confidence": "high",
                        "matched_pattern": pattern,
                        "context": context
                    }

        # 未找到明确年级
        return {
            "grade": None,
            "grade_arabic": None,
            "confidence": "low",
            "matched_pattern": None,
            "context": ""
        }

    @staticmethod
    def extract_subject(title: str) -> Dict[str, any]:
        """
        从阿拉伯语标题中提取学科信息

        Args:
            title: 视频标题

        Returns:
            {
                "subject": "数学/科学/.../None",
                "subject_arabic": "الرياضيات/...",
                "confidence": "high/medium/low",
                "context": "上下文"
            }
        """
        if not title:
            return {
                "subject": None,
                "subject_arabic": None,
                "confidence": "low",
                "context": ""
            }

        # 标准化
        normalized = ArabicNormalizer.normalize(title)

        # 检查每个学科
        for arabic_subject, chinese_subject in ArabicNormalizer.SUBJECT_MAPPING.items():
            if arabic_subject in normalized:
                # 提取上下文
                idx = normalized.find(arabic_subject)
                start = max(0, idx - 10)
                end = min(len(title), idx + len(arabic_subject) + 10)
                context = title[start:end]

                return {
                    "subject": chinese_subject,
                    "subject_arabic": arabic_subject,
                    "confidence": "high",
                    "context": context
                }

        # 未找到明确学科
        return {
            "subject": None,
            "subject_arabic": None,
            "confidence": "low",
            "context": ""
        }

    @staticmethod
    def check_grade_match(title: str, target_grade: str, grade_variants: List[str]) -> Dict[str, any]:
        """
        检查年级是否匹配

        Args:
            title: 视频标题
            target_grade: 目标年级（中文，如"一年级"）
            grade_variants: 目标年级的所有变体

        Returns:
            {
                "is_match": bool,
                "confidence": "high/medium/low",
                "identified_grade": "识别的年级",
                "reason": "判断理由"
            }
        """
        # 提取年级
        grade_info = ArabicNormalizer.extract_grade(title)

        if grade_info['grade'] is None:
            # 未找到明确年级
            return {
                "is_match": None,  # 无法判断
                "confidence": "low",
                "identified_grade": None,
                "reason": "标题中未找到明确的年级信息"
            }

        identified_grade = grade_info['grade']

        # 检查是否匹配
        if identified_grade == target_grade:
            return {
                "is_match": True,
                "confidence": "high",
                "identified_grade": identified_grade,
                "grade_arabic": grade_info['grade_arabic'],
                "reason": f"识别为{identified_grade}（{grade_info['grade_arabic']}），与目标匹配"
            }
        else:
            # 明确不匹配
            return {
                "is_match": False,
                "confidence": "high",
                "identified_grade": identified_grade,
                "grade_arabic": grade_info['grade_arabic'],
                "reason": f"识别为{identified_grade}（{grade_info['grade_arabic']}），与目标{target_grade}不符"
            }

    @staticmethod
    def check_subject_match(title: str, target_subject: str, subject_variants: List[str]) -> Dict[str, any]:
        """
        检查学科是否匹配

        Args:
            title: 视频标题
            target_subject: 目标学科（中文，如"数学"）
            subject_variants: 目标学科的所有变体

        Returns:
            {
                "is_match": bool,
                "confidence": "high/medium/low",
                "identified_subject": "识别的学科",
                "reason": "判断理由"
            }
        """
        # 提取学科
        subject_info = ArabicNormalizer.extract_subject(title)

        if subject_info['subject'] is None:
            # 未找到明确学科
            return {
                "is_match": None,  # 无法判断
                "confidence": "low",
                "identified_subject": None,
                "reason": "标题中未找到明确的学科信息"
            }

        identified_subject = subject_info['subject']

        # 检查是否匹配
        if identified_subject == target_subject:
            return {
                "is_match": True,
                "confidence": "high",
                "identified_subject": identified_subject,
                "subject_arabic": subject_info['subject_arabic'],
                "reason": f"识别为{identified_subject}（{subject_info['subject_arabic']}），与目标匹配"
            }
        else:
            # 明确不匹配
            return {
                "is_match": False,
                "confidence": "high",
                "identified_subject": identified_subject,
                "subject_arabic": subject_info['subject_arabic'],
                "reason": f"识别为{identified_subject}（{subject_info['subject_arabic']}），与目标{target_subject}不符"
            }

    @staticmethod
    def get_all_grade_variants(grade_chinese: str) -> List[str]:
        """
        获取某个年级的所有阿拉伯语变体

        Args:
            grade_chinese: 中文年级名称（如"一年级"）

        Returns:
            所有阿拉伯语变体列表
        """
        # 反向映射
        arabic_to_chinese = {}
        for arabic_num, chinese in ArabicNormalizer.GRADE_MAPPING.items():
            if chinese not in arabic_to_chinese:
                arabic_to_chinese[chinese] = []
            arabic_to_chinese[chinese].append(arabic_num)

        if grade_chinese not in arabic_to_chinese:
            return []

        variants = []
        for arabic_num in arabic_to_chinese[grade_chinese]:
            # 生成不同的变体
            variants.extend([
                f"الصف {arabic_num}",      # 带alif
                f"صف {arabic_num}",        # 不带alif
            ])

        return variants

    @staticmethod
    def is_arabic_text(text: str) -> bool:
        """
        判断文本是否包含阿拉伯语

        Args:
            text: 待判断文本

        Returns:
            是否包含阿拉伯语
        """
        if not text:
            return False

        # 阿拉伯语Unicode范围
        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        return arabic_chars > 3  # 至少3个阿拉伯语字符


# 测试代码
if __name__ == "__main__":
    # 测试用例
    test_titles = [
        "شرح هياكل الرياضيات الفصل الاول 24/25",
        "شرح رياضيات صف سادس منهج إماراتي وزاري",
        "مادة الرياضيات للصف الاول",
        "الرياضيات الصف الأول - منهاج الأردن",
        "سلسلة شرح دروس الرياضيات للصف الأول الفصل الاول",
    ]

    print("="*80)
    print("阿拉伯语标准化测试")
    print("="*80)

    for title in test_titles:
        print(f"\n标题: {title}")
        print("-"*80)

        # 提取年级
        grade_info = ArabicNormalizer.extract_grade(title)
        print(f"年级: {grade_info['grade']}")
        print(f"阿拉伯语: {grade_info['grade_arabic']}")
        print(f"置信度: {grade_info['confidence']}")

        # 提取学科
        subject_info = ArabicNormalizer.extract_subject(title)
        print(f"学科: {subject_info['subject']}")
        print(f"阿拉伯语: {subject_info['subject_arabic']}")

        # 检查年级匹配（目标：一年级）
        grade_match = ArabicNormalizer.check_grade_match(title, "一年级", [])
        print(f"年级匹配: {grade_match['is_match']}")
        print(f"理由: {grade_match['reason']}")
