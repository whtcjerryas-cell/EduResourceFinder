"""
模式提取工具 - 从标题中提取年级和学科信息

遵循 agent-native 原则：
- 原子工具：只负责模式匹配，不编码业务逻辑
- 丰富输出：返回完整信息供Agent决策
- 配置驱动：使用国家配置中的patterns
"""

import re
import json
from typing import Dict, List, Any, Optional
from logger_utils import get_logger
from .config_tools import read_country_config

logger = get_logger('extraction_tools')


async def extract_grade_from_title(title: str, country_code: str) -> Dict[str, Any]:
    """
    从标题中提取年级信息（使用配置的模式匹配）

    Args:
        title: 资源标题
        country_code: 国家代码，如 ID, SA, CN

    Returns:
        {
            "success": True/False,
            "data": {
                "grade_id": "1",
                "grade_name": "一年级",
                "local_name": "Kelas 1",
                "confidence": "high"
            },
            "text": "识别年级：一年级 (Kelas 1)"
        }

        如果未识别到：
        {
            "success": False,
            "data": None,
            "text": "未识别到年级信息"
        }

    示例：
        >>> result = await extract_grade_from_title("Matematika Kelas 1 SD", "ID")
        >>> print(result['data'])
        {'grade_id': '1', 'grade_name': '一年级', 'local_name': 'Kelas 1', 'confidence': 'high'}

        >>> result = await extract_grade_from_title("مادة الرياضيات للصف الأول", "SA")
        >>> print(result['data'])
        {'grade_id': '1', 'grade_name': '一年级', 'local_name': 'الصف الأول', 'confidence': 'high'}
    """
    try:
        if not title or not title.strip():
            return {
                "success": False,
                "data": None,
                "text": "标题为空，无法识别年级"
            }

        # 1. 读取国家配置
        config_result = await read_country_config(country_code)

        if not config_result["success"]:
            return {
                "success": False,
                "data": None,
                "text": f"无法读取配置：{config_result.get('error', '未知错误')}"
            }

        config = config_result["data"]

        # 2. 获取年级模式和年级列表
        grade_patterns = config.get("grade_patterns", [])
        grades = config.get("grades", [])

        # 创建年级ID到年级信息的映射
        grade_map = {g["grade_id"]: g for g in grades}

        # 3. 依次尝试每个正则模式
        for pattern in grade_patterns:
            regex = pattern.get("regex")
            if not regex:
                continue

            try:
                match = re.search(regex, title, re.IGNORECASE)
                if match:
                    # 提取grade_id
                    grade_id = pattern.get("grade_id")

                    # 如果grade_id包含捕获组引用（如 $1），替换为匹配的文本
                    if "$" in grade_id and match.groups():
                        # 获取第一个捕获组
                        captured = match.group(1)
                        grade_id = grade_id.replace("$1", captured)

                    # 查找年级信息
                    grade_info = grade_map.get(grade_id)
                    if not grade_info:
                        logger.warning(f"模式匹配到年级ID {grade_id}，但在配置中找不到")
                        continue

                    confidence = pattern.get("confidence", "medium")

                    return {
                        "success": True,
                        "data": {
                            "grade_id": grade_id,
                            "grade_name": grade_info["zh_name"],
                            "local_name": grade_info["local_name"],
                            "en_name": grade_info.get("en_name", ""),
                            "confidence": confidence,
                            "matched_text": match.group(0),
                            "pattern_type": "config"
                        },
                        "text": f"识别年级：{grade_info['zh_name']} ({grade_info['local_name']})，置信度：{confidence}"
                    }

            except re.error as e:
                logger.error(f"正则表达式错误：{regex}, 错误：{e}")
                continue

        # 4. 未匹配到任何模式
        return {
            "success": False,
            "data": None,
            "text": "未识别到年级信息"
        }

    except Exception as e:
        logger.error(f"提取年级失败：{str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": None,
            "text": f"提取失败：{str(e)}"
        }


async def extract_subject_from_title(title: str, country_code: str) -> Dict[str, Any]:
    """
    从标题中提取学科信息（使用配置的关键词匹配）

    Args:
        title: 资源标题
        country_code: 国家代码，如 ID, SA, CN

    Returns:
        {
            "success": True/False,
            "data": {
                "subject_id": "math",
                "subject_name": "数学",
                "local_name": "Matematika",
                "confidence": "high"
            },
            "text": "识别学科：数学 (Matematika)"
        }

        如果未识别到：
        {
            "success": False,
            "data": None,
            "text": "未识别到学科信息"
        }

    示例：
        >>> result = await extract_subject_from_title("Matematika Kelas 1 SD", "ID")
        >>> print(result['data'])
        {'subject_id': 'math', 'subject_name': '数学', 'local_name': 'Matematika', 'confidence': 'high'}

        >>> result = await extract_subject_from_title("فيزياء الصف الأول", "SA")
        >>> print(result['data'])
        {'subject_id': 'physics', 'subject_name': '物理', 'local_name': 'الفيزياء', 'confidence': 'high'}
    """
    try:
        if not title or not title.strip():
            return {
                "success": False,
                "data": None,
                "text": "标题为空，无法识别学科"
            }

        # 1. 读取国家配置
        config_result = await read_country_config(country_code)

        if not config_result["success"]:
            return {
                "success": False,
                "data": None,
                "text": f"无法读取配置：{config_result.get('error', '未知错误')}"
            }

        config = config_result["data"]

        # 2. 获取学科模式和学科列表
        subject_patterns = config.get("subject_patterns", [])
        subjects = config.get("subjects", [])

        # 创建学科ID到学科信息的映射
        subject_map = {s["subject_id"]: s for s in subjects}

        # 3. 转换标题为小写用于匹配（保留原始标题用于显示）
        title_lower = title.lower()

        # 4. 按置信度排序尝试匹配（优先匹配高置信度的）
        sorted_patterns = sorted(
            subject_patterns,
            key=lambda p: p.get("confidence", "medium") == "high",
            reverse=True
        )

        for pattern in sorted_patterns:
            keyword = pattern.get("keyword", "").lower()
            if not keyword:
                continue

            # 检查关键词是否在标题中
            if keyword in title_lower:
                subject_id = pattern.get("subject_id")

                # 查找学科信息
                subject_info = subject_map.get(subject_id)
                if not subject_info:
                    logger.warning(f"关键词匹配到学科ID {subject_id}，但在配置中找不到")
                    continue

                confidence = pattern.get("confidence", "medium")

                return {
                    "success": True,
                    "data": {
                        "subject_id": subject_id,
                        "subject_name": subject_info["zh_name"],
                        "local_name": subject_info["local_name"],
                        "en_name": subject_info.get("en_name", ""),
                        "confidence": confidence,
                        "matched_keyword": keyword,
                        "pattern_type": "config"
                    },
                    "text": f"识别学科：{subject_info['zh_name']} ({subject_info['local_name']})，置信度：{confidence}"
                }

        # 5. 未匹配到任何模式
        return {
            "success": False,
            "data": None,
            "text": "未识别到学科信息"
        }

    except Exception as e:
        logger.error(f"提取学科失败：{str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": None,
            "text": f"提取失败：{str(e)}"
        }
