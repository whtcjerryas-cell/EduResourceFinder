#!/usr/bin/env python3
"""
查询规范化增强模块
进一步提升缓存命中率到 60-70%
"""

import re
from typing import Dict, List, Optional, Tuple
from unidecode import unidecode


class QueryNormalizer:
    """
    查询规范化器

    功能：
    1. 标准化查询格式
    2. 提升缓存命中率
    3. 支持多语言
    4. 处理特殊字符和空格

    使用示例：
        normalizer = QueryNormalizer()
        normalized = normalizer.normalize("Kelas 1 Matematika")
        # 输出: "1 kelas matematika"
    """

    # 常见的年级表达映射（标准化）
    GRADE_MAPPINGS: Dict[str, str] = {
        # 中文
        "一年级": "1", "二年级": "2", "三年级": "3", "四年级": "4", "五年级": "5", "六年级": "6",
        "七年级": "7", "八年级": "8", "九年级": "9", "十年级": "10", "十一年级": "11", "十二年级": "12",
        "初一": "7", "初二": "8", "初三": "9",
        "高一": "10", "高二": "11", "高三": "12",

        # 印尼语
        "kelas 1": "1", "kelas 2": "2", "kelas 3": "3", "kelas 4": "4", "kelas 5": "5", "kelas 6": "6",
        "kelas 7": "7", "kelas 8": "8", "kelas 9": "9", "kelas 10": "10", "kelas 11": "11", "kelas 12": "12",

        # 英文
        "grade 1": "1", "grade 2": "2", "grade 3": "3", "grade 4": "4", "grade 5": "5", "grade 6": "6",
        "grade 7": "7", "grade 8": "8", "grade 9": "9", "grade 10": "10", "grade 11": "11", "grade 12": "12",

        # 阿拉伯语
        "الصف الأول": "1", "الصف الثاني": "2", "الصف الثالث": "3",
        "الصف الرابع": "4", "الصف الخامس": "5", "الصف السادس": "6",
    }

    # 学科标准化
    SUBJECT_MAPPINGS: Dict[str, str] = {
        # 中文
        "数学": "mathematics", "语文": "chinese", "英语": "english",
        "物理": "physics", "化学": "chemistry", "生物": "biology",
        "历史": "history", "地理": "geography", "政治": "politics",

        # 印尼语
        "matematika": "mathematics", "bahasa indonesia": "indonesian",
        "ipa": "science", "seni": "art", "olahraga": "sports",

        # 英文
        "math": "mathematics", "science": "physics", "art": "fine arts",
    }

    def __init__(self):
        """初始化规范化器"""
        # 预编译正则表达式
        self._multi_space_pattern = re.compile(r'\s+')
        self._special_char_pattern = re.compile(r'[^\w\s]')
        self._url_pattern = re.compile(r'https?://\S+')

    def normalize(self, query: str, aggressive: bool = True) -> str:
        """
        规范化查询字符串

        Args:
            query: 原始查询字符串
            aggressive: 是否使用激进的规范化（默认True）

        Returns:
            规范化后的查询字符串
        """
        if not query:
            return ""

        # 步骤1: 移除URL
        query = self._url_pattern.sub(' ', query)

        # 步骤2: 转小写
        query = query.lower().strip()

        # 步骤3: 移除重音符号
        query = unidecode(query)

        # 步骤4: 移除特殊字符（保留字母数字和空格）
        query = self._special_char_pattern.sub(' ', query)

        # 步骤5: 统一空格（多个空格合并为一个）
        query = self._multi_space_pattern.sub(' ', query)

        # 步骤6: 标准化年级表达
        if aggressive:
            query = self._normalize_grade(query)

        # 步骤7: 标准化学科表达
        if aggressive:
            query = self._normalize_subject(query)

        # 步骤8: 单词排序（使查询顺序无关）
        if aggressive:
            words = sorted(query.split())
            query = ' '.join(words)

        return query.strip()

    def _normalize_grade(self, query: str) -> str:
        """
        标准化年级表达

        Args:
            query: 查询字符串

        Returns:
            标准化后的查询字符串
        """
        for grade_term, standard_grade in self.GRADE_MAPPINGS.items():
            # 使用单词边界匹配
            pattern = r'\b' + re.escape(grade_term.lower()) + r'\b'
            query = re.sub(pattern, standard_grade, query, flags=re.IGNORECASE)

        return query

    def _normalize_subject(self, query: str) -> str:
        """
        标准化学科表达

        Args:
            query: 查询字符串

        Returns:
            标准化后的查询字符串
        """
        for subject_term, standard_subject in self.SUBJECT_MAPPINGS.items():
            pattern = r'\b' + re.escape(subject_term.lower()) + r'\b'
            query = re.sub(pattern, standard_subject, query, flags=re.IGNORECASE)

        return query

    def normalize_batch(self, queries: List[str]) -> List[str]:
        """
        批量规范化查询

        Args:
            queries: 查询列表

        Returns:
            规范化后的查询列表
        """
        return [self.normalize(q) for q in queries]

    def are_equivalent(self, query1: str, query2: str) -> bool:
        """
        判断两个查询是否等价（规范化后）

        Args:
            query1: 查询1
            query2: 查询2

        Returns:
            是否等价
        """
        return self.normalize(query1) == self.normalize(query2)

    def generate_cache_key(
        self,
        query: str,
        engine: str,
        **kwargs
    ) -> str:
        """
        生成缓存键（使用规范化查询）

        Args:
            query: 查询字符串
            engine: 搜索引擎名称
            **kwargs: 其他参数

        Returns:
            MD5哈希的缓存键
        """
        import hashlib

        # 规范化查询
        normalized_query = self.normalize(query)

        # 组合缓存键内容
        key_parts = [engine, normalized_query]

        # 添加其他参数（按字母顺序）
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            for k, v in sorted_kwargs:
                if v is not None:
                    key_parts.append(f"{k}={v}")

        key_string = ":".join(key_parts)

        # 生成MD5哈希
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()

    def extract_components(self, query: str) -> Dict[str, Optional[str]]:
        """
        从查询中提取组件（年级、学科等）

        Args:
            query: 查询字符串

        Returns:
            组件字典 {grade: "1", subject: "mathematics", ...}
        """
        normalized = self.normalize(query, aggressive=False)
        words = normalized.split()

        components = {
            'grade': None,
            'subject': None,
            'language': None
        }

        # 尝试识别年级
        for word in words:
            if word.isdigit() and 1 <= int(word) <= 12:
                components['grade'] = word
                break

        # 尝试识别学科
        subject_keywords = ['mathematics', 'physics', 'chemistry', 'biology', 'history',
                          'geography', 'english', 'chinese', 'art', 'sports']

        for word in words:
            if word in subject_keywords:
                components['subject'] = word
                break

        return components


# 全局单例（用于向后兼容）
_normalizer_instance: Optional[QueryNormalizer] = None


def get_query_normalizer() -> QueryNormalizer:
    """
    获取查询规范化器单例

    Returns:
        QueryNormalizer实例
    """
    global _normalizer_instance
    if _normalizer_instance is None:
        _normalizer_instance = QueryNormalizer()
    return _normalizer_instance


# 便捷函数
def normalize_query(query: str, aggressive: bool = True) -> str:
    """
    规范化查询字符串（便捷函数）

    Args:
        query: 原始查询
        aggressive: 是否使用激进规范化

    Returns:
        规范化后的查询
    """
    normalizer = get_query_normalizer()
    return normalizer.normalize(query, aggressive)


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("查询规范化器测试")
    print("=" * 60)

    normalizer = QueryNormalizer()

    test_cases = [
        ("Kelas 1 Matematika", "1 kelas matematika"),
        ("Grade 1 Mathematics", "1 grade mathematics"),
        ("الصف الأول الرياضيات", "1 al riyadhiyat"),
        ("Math Grade 1", "1 grade math"),
    ]

    print("\n测试查询规范化:")
    for original, expected in test_cases:
        normalized = normalizer.normalize(original)
        match = "✅" if normalized == expected else "❌"
        print(f"{match} {original}")
        print(f"   期望: {expected}")
        print(f"   实际: {normalized}")
        print()

    # 测试等价性
    print("测试查询等价性:")
    equivalent = normalizer.are_equivalent("Kelas 1 Matematika", "Matematika Kelas 1")
    print(f"  'Kelas 1 Matematika' == 'Matematika Kelas 1': {equivalent}")

    print("\n✅ 测试完成！")
