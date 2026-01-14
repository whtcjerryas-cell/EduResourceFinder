#!/usr/bin/env python3
"""
年级-学科联动验证器
验证特定年级是否可以开设特定学科
"""

import json
import os
import logging
from typing import Dict, List, Optional, Any

# 配置日志
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class GradeSubjectValidator:
    """年级-学科联动验证器"""

    def __init__(self, rules_file: str = "data/config/grade_subject_rules.json"):
        """
        初始化验证器

        Args:
            rules_file: 规则配置文件路径
        """
        self.rules_file = rules_file
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict:
        """加载规则配置文件"""
        try:
            if not os.path.exists(self.rules_file):
                logger.warning(f"规则文件不存在: {self.rules_file}，使用默认规则")
                return self._get_default_rules()

            with open(self.rules_file, 'r', encoding='utf-8') as f:
                rules = json.load(f)
            logger.info(f"成功加载规则文件: {self.rules_file}")
            return rules
        except Exception as e:
            logger.error(f"加载规则文件失败: {str(e)}，使用默认规则")
            return self._get_default_rules()

    def _get_default_rules(self) -> Dict:
        """获取默认规则（当配置文件不存在时）"""
        return {
            "default_rules": {
                "primary_lower": {
                    "grades_patterns": ["1", "2", "Kelas 1", "Kelas 2"],
                    "excluded_subjects": ["Physics", "Chemistry", "物理", "化学"]
                },
                "primary_upper": {
                    "grades_patterns": ["3", "4", "5", "6"],
                    "excluded_subjects": ["Physics (Advanced)", "Chemistry (Advanced)"]
                },
                "junior_high": {
                    "grades_patterns": ["7", "8", "9"],
                    "included_subjects": ["Physics", "Chemistry", "Biology"]
                },
                "senior_high": {
                    "grades_patterns": ["10", "11", "12"],
                    "streams": {
                        "science": {
                            "required_subjects": ["Mathematics", "Physics", "Chemistry", "Biology"]
                        },
                        "social": {
                            "required_subjects": ["Mathematics", "Social Studies", "Economics"]
                        }
                    }
                }
            }
        }

    def _get_grade_level(self, grade: str) -> Optional[str]:
        """
        识别年级所属层级

        Args:
            grade: 年级名称（如 "Kelas 1", "Grade 10", "一年级"）

        Returns:
            层级名称（primary_lower, primary_upper, junior_high, senior_high）或 None
        """
        default_rules = self.rules.get("default_rules", {})

        # 首先尝试通过完整的年级名称模式匹配
        for level_name, level_rules in default_rules.items():
            # 跳过非字典类型的值（如 "description"）
            if not isinstance(level_rules, dict):
                continue

            patterns = level_rules.get("grades_patterns", [])
            for pattern in patterns:
                # 使用完整的单词边界匹配，避免部分匹配
                # 例如："Kelas 10" 不应该匹配 "1"
                pattern_lower = pattern.lower()
                grade_lower = grade.lower()

                # 精确匹配或完整单词匹配
                if pattern_lower == grade_lower:
                    return level_name

                # 检查pattern是否是grade的完整单词（前后有空格或边界）
                import re
                if re.search(r'\b' + re.escape(pattern_lower) + r'\b', grade_lower):
                    return level_name

        # 如果没有匹配到，尝试通过数字推断
        import re
        numbers = re.findall(r'\d+', grade)
        if numbers:
            # 取最后一个最大的数字（更可能是年级）
            grade_num = max(int(n) for n in numbers)
            if grade_num <= 2:
                return "primary_lower"
            elif grade_num <= 6:
                return "primary_upper"
            elif grade_num <= 9:
                return "junior_high"
            elif grade_num <= 12:
                return "senior_high"

        return None

    def validate(self, country_code: str, grade: str, subject: str) -> Dict[str, Any]:
        """
        验证年级-学科配对是否合法

        Args:
            country_code: 国家代码（如：ID, CN, US）
            grade: 年级名称
            subject: 学科名称

        Returns:
            {
                "valid": bool,
                "reason": str,
                "suggestions": [str]
            }
        """
        # 1. 查找年级所属层级
        grade_level = self._get_grade_level(grade)

        if not grade_level:
            return {
                "valid": True,
                "reason": "无法识别年级层级，默认允许",
                "suggestions": []
            }

        # 2. 检查该层级的排除规则
        default_rules = self.rules.get("default_rules", {})
        level_rules = default_rules.get(grade_level, {})

        excluded_subjects = level_rules.get("excluded_subjects", [])
        for excluded_subject in excluded_subjects:
            if excluded_subject.lower() in subject.lower() or subject.lower() in excluded_subject.lower():
                allowed_subjects = level_rules.get("allowed_subjects", [])
                reason = level_rules.get("reason", f"{grade}不符合{subject}的教学要求")

                return {
                    "valid": False,
                    "reason": reason,
                    "suggestions": allowed_subjects
                }

        # 3. 检查国家特殊规则
        country_specific_rules = self.rules.get("country_specific_rules", {})
        if country_code in country_specific_rules:
            country_rules = country_specific_rules[country_code]

            # 检查特定学科的起始年级
            if grade_level == "junior_high":
                junior_high_rules = country_rules.get("junior_high", {})

                # 检查物理起始年级
                physics_start = junior_high_rules.get("physics_start_grade")
                if physics_start and "physics" in subject.lower():
                    if not self._is_grade_after(grade, physics_start):
                        return {
                            "valid": False,
                            "reason": f"{country_code}的物理从{physics_start}开始",
                            "suggestions": ["Science", "Mathematics"]
                        }

                # 检查化学起始年级
                chemistry_start = junior_high_rules.get("chemistry_start_grade")
                if chemistry_start and "chemistry" in subject.lower():
                    if not self._is_grade_after(grade, chemistry_start):
                        return {
                            "valid": False,
                            "reason": f"{country_code}的化学从{chemistry_start}开始",
                            "suggestions": ["Science", "Mathematics"]
                        }

        return {
            "valid": True,
            "reason": "有效配对",
            "suggestions": []
        }

    def _is_grade_after(self, current_grade: str, start_grade: str) -> bool:
        """
        判断当前年级是否在起始年级之后

        Args:
            current_grade: 当前年级
            start_grade: 起始年级

        Returns:
            是否在起始年级之后
        """
        import re

        # 提取年级数字
        current_num = self._extract_grade_number(current_grade)
        start_num = self._extract_grade_number(start_grade)

        if current_num is None or start_num is None:
            return True  # 无法判断时默认允许

        return current_num >= start_num

    def _extract_grade_number(self, grade: str) -> Optional[int]:
        """从年级名称中提取数字"""
        import re

        # 尝试直接匹配数字
        numbers = re.findall(r'\d+', grade)
        if numbers:
            return int(numbers[0])

        # 匹配中文数字
        chinese_nums = {
            "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6,
            "七": 7, "八": 8, "九": 9, "十": 10, "十一": 11, "十二": 12
        }
        for chinese, num in chinese_nums.items():
            if chinese in grade:
                return num

        return None

    def get_available_subjects(
        self,
        country_code: str,
        grade: str,
        subjects: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        获取指定年级的所有可用学科

        Args:
            country_code: 国家代码
            grade: 年级名称
            subjects: 该国的所有学科列表

        Returns:
            可用学科列表（包含 is_core, is_allowed 等标记）
        """
        # 1. 识别年级层级
        grade_level = self._get_grade_level(grade)

        if not grade_level:
            # 无法识别层级，返回所有学科
            return [
                {
                    **subject,
                    "is_core": True,
                    "is_allowed": True,
                    "reason": "无法识别年级层级"
                }
                for subject in subjects
            ]

        # 2. 获取该层级的规则
        default_rules = self.rules.get("default_rules", {})
        level_rules = default_rules.get(grade_level, {})

        excluded_subjects = level_rules.get("excluded_subjects", [])
        allowed_subjects = level_rules.get("allowed_subjects", [])
        included_subjects = level_rules.get("included_subjects", [])

        # 3. 过滤学科
        available_subjects = []

        for subject in subjects:
            local_name = subject.get("local_name", "")
            zh_name = subject.get("zh_name", "")

            # 检查是否在排除列表中
            is_excluded = False
            for excluded in excluded_subjects:
                if excluded.lower() in local_name.lower() or \
                   excluded.lower() in zh_name.lower():
                    is_excluded = True
                    break

            if is_excluded:
                available_subjects.append({
                    **subject,
                    "is_core": False,
                    "is_allowed": False,
                    "reason": level_rules.get("reason", "该年级不开设此学科")
                })
                continue

            # 检查是否在包含列表中
            is_included = False
            if included_subjects:
                for included in included_subjects:
                    if included.lower() in local_name.lower() or \
                       included.lower() in zh_name.lower():
                        is_included = True
                        break

            # 核心学科判断
            is_core = self._is_core_subject(local_name, zh_name)

            available_subjects.append({
                **subject,
                "is_core": is_core or is_included,
                "is_allowed": True,
                "reason": "允许开设"
            })

        return available_subjects

    def _is_core_subject(self, local_name: str, zh_name: str) -> bool:
        """
        判断是否为核心学科

        Args:
            local_name: 当地语言名称
            zh_name: 中文名称

        Returns:
            是否为核心学科
        """
        core_keywords = [
            "matematika", "mathematics", "数学",
            "bahasa", "language", "语言",
            "ipa", "science", "科学",
            "ips", "social", "社会"
        ]

        name_lower = f"{local_name} {zh_name}".lower()

        for keyword in core_keywords:
            if keyword in name_lower:
                return True

        return False

    def get_streams_for_grade(
        self,
        country_code: str,
        grade: str
    ) -> List[Dict[str, Any]]:
        """
        获取指定年级的选科/分流信息（用于高中阶段）

        Args:
            country_code: 国家代码
            grade: 年级名称

        Returns:
            选科列表（如：[{stream_name: "science", required_subjects: [...]}]）
        """
        grade_level = self._get_grade_level(grade)

        if grade_level != "senior_high":
            return []

        default_rules = self.rules.get("default_rules", {})
        level_rules = default_rules.get("senior_high", {})

        streams = level_rules.get("streams", {})

        result = []
        for stream_name, stream_config in streams.items():
            result.append({
                "stream_name": stream_name,
                "required_subjects": stream_config.get("required_subjects", []),
                "optional_subjects": stream_config.get("optional_subjects", [])
            })

        return result


# ============================================================================
# 辅助函数
# ============================================================================

def get_validator() -> GradeSubjectValidator:
    """获取全局验证器实例"""
    return GradeSubjectValidator()


if __name__ == "__main__":
    # 测试代码
    validator = GradeSubjectValidator()

    print("\n=== 测试年级-学科验证 ===")

    # 测试1: 一年级不应该开设物理
    result1 = validator.validate("ID", "Kelas 1", "Fisika")
    print(f"\n测试1: {result1}")
    assert result1["valid"] == False, "一年级不应该开设物理"

    # 测试2: 七年级应该允许开设物理
    result2 = validator.validate("ID", "Kelas 7", "Fisika")
    print(f"\n测试2: {result2}")
    assert result2["valid"] == True, "七年级应该允许开设物理"

    # 测试3: 获取可用学科
    subjects = [
        {"local_name": "Matematika", "zh_name": "数学"},
        {"local_name": "Fisika", "zh_name": "物理"},
        {"local_name": "Kimia", "zh_name": "化学"}
    ]

    available1 = validator.get_available_subjects("ID", "Kelas 1", subjects)
    print(f"\n测试3: 一年级可用学科:")
    for subj in available1:
        print(f"  - {subj['local_name']}: allowed={subj['is_allowed']}, core={subj['is_core']}")

    available2 = validator.get_available_subjects("ID", "Kelas 10", subjects)
    print(f"\n测试4: 十年级可用学科:")
    for subj in available2:
        print(f"  - {subj['local_name']}: allowed={subj['is_allowed']}, core={subj['is_core']}")

    print("\n✅ 所有测试通过！")
