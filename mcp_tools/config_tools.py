"""
配置管理工具 - 读取国家教育配置

遵循 agent-native 原则：
- 原子工具：只负责读取配置，不编码业务逻辑
- 丰富输出：返回完整配置信息供Agent决策
"""

import json
import os
from typing import Dict, List, Any
from logger_utils import get_logger

logger = get_logger('config_tools')

# 配置文件路径
CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'data/config/countries_config.json'
)


async def read_country_config(country_code: str) -> Dict[str, Any]:
    """
    读取国家教育配置（年级、学科、语言规则）

    Args:
        country_code: 国家代码，如 ID, SA, CN

    Returns:
        {
            "success": True/False,
            "data": {
                "country_code": "ID",
                "country_name": "Indonesia",
                "grades": [...],
                "subjects": [...],
                "grade_patterns": [...],
                "subject_patterns": [...]
            },
            "text": "人类可读的摘要"
        }

    示例:
        >>> result = await read_country_config("ID")
        >>> print(result['text'])
        已加载 Indonesia 配置：
        - 年级：13 个（Kelas 1 - Kelas 12）
        - 学科：10 个
        - 年级模式：1 条
        - 学科模式：10 条
    """
    try:
        if not os.path.exists(CONFIG_FILE):
            return {
                "success": False,
                "error": f"配置文件不存在：{CONFIG_FILE}",
                "data": None
            }

        # 读取所有配置
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            all_configs = json.load(f)

        # 检查国家代码是否存在
        if country_code not in all_configs:
            available = list(all_configs.keys())
            logger.warning(f"国家代码 {country_code} 不存在，可用：{available}")

            return {
                "success": False,
                "error": f"国家代码 {country_code} 不存在",
                "available_countries": available,
                "data": None
            }

        config = all_configs[country_code]

        # 构建返回数据
        grades = config.get('grades', [])
        subjects = config.get('subjects', [])
        grade_patterns = config.get('grade_patterns', [])
        subject_patterns = config.get('subject_patterns', [])

        # 构建人类可读的摘要
        text = f"""已加载 {config['country_name']} 配置：
- 年级：{len(grades)} 个（{grades[0]['local_name'] if grades else 'N/A'} - {grades[-1]['local_name'] if grades else 'N/A'}）
- 学科：{len(subjects)} 个
- 年级模式：{len(grade_patterns)} 条
- 学科模式：{len(subject_patterns)} 条

## 年级列表
{chr(10).join(f"  {i+1}. {g['local_name']} = {g['zh_name']} (ID: {g['grade_id']})" for i, g in enumerate(grades[:5]))}{chr(10) + f"  ... 还有 {len(grades)-5} 个" if len(grades) > 5 else ""}

## 学科列表
{chr(10).join(f"  {i+1}. {s['local_name']} = {s['zh_name']} (ID: {s['subject_id']})" for i, s in enumerate(subjects[:5]))}{chr(10) + f"  ... 还有 {len(subjects)-5} 个" if len(subjects) > 5 else ""}"""

        return {
            "success": True,
            "data": {
                "country_code": config["country_code"],
                "country_name": config["country_name"],
                "language_code": config["language_code"],
                "grades": grades,
                "subjects": subjects,
                "grade_patterns": grade_patterns,
                "subject_patterns": subject_patterns,
                "url_filter_rules": config.get("url_filter_rules", {})
            },
            "text": text.strip()
        }

    except Exception as e:
        logger.error(f"读取配置失败：{str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": None
        }


async def list_available_countries(limit: int = 50) -> Dict[str, Any]:
    """
    列出所有已配置的国家

    Args:
        limit: 最大返回数量

    Returns:
        {
            "success": True/False,
            "data": [
                {
                    "code": "ID",
                    "name": "Indonesia",
                    "language": "id",
                    "grade_count": 13,
                    "subject_count": 10
                },
                ...
            ],
            "text": "人类可读的列表"
        }

    示例:
        >>> result = await list_available_countries()
        >>> print(result['text'])
        可用国家：
        - ID: Indonesia (id, 13年级, 10学科)
        - SA: Saudi Arabia (ar, 6年级, 5学科)
        """
    try:
        if not os.path.exists(CONFIG_FILE):
            return {
                "success": False,
                "error": f"配置文件不存在：{CONFIG_FILE}",
                "data": []
            }

        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            all_configs = json.load(f)

        countries = []
        for code, config in all_configs.items():
            countries.append({
                "code": code,
                "name": config.get("country_name", "Unknown"),
                "language": config.get("language_code", "unknown"),
                "grade_count": len(config.get("grades", [])),
                "subject_count": len(config.get("subjects", [])),
                "has_grade_patterns": len(config.get("grade_patterns", [])) > 0,
                "has_subject_patterns": len(config.get("subject_patterns", [])) > 0
            })

        # 限制数量
        countries = sorted(countries, key=lambda x: x["code"])[:limit]

        # 构建人类可读的列表
        lines = []
        for c in countries:
            status = ""
            if c["has_grade_patterns"]:
                status += "✓年级模式 "
            if c["has_subject_patterns"]:
                status += "✓学科模式"

            lines.append(f"- {c['code']}: {c['name']} ({c['language']}, {c['grade_count']}年级, {c['subject_count']}学科) {status}")

        return {
            "success": True,
            "data": countries,
            "text": "可用国家：\n" + "\n".join(lines)
        }

    except Exception as e:
        logger.error(f"列出国家失败：{str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": []
        }
