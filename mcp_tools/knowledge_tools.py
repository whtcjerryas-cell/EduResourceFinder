"""
知识库工具 - 管理学习的年级/学科表达模式

遵循 agent-native 原则：
- CRUD完整性：创建、读取、更新（验证）、删除
- 丰富输出：返回完整的学习记录和统计信息
- 自学习：Agent可以从搜索结果中学习新模式
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from logger_utils import get_logger

logger = get_logger('knowledge_tools')

# 知识库目录
KNOWLEDGE_BASE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'data/knowledge_base'
)


def _get_knowledge_file(country_code: str, pattern_type: str) -> str:
    """获取知识库文件路径"""
    country_dir = os.path.join(KNOWLEDGE_BASE_DIR, country_code)
    os.makedirs(country_dir, exist_ok=True)

    filename = f"{pattern_type}_patterns.json"
    return os.path.join(country_dir, filename)


def _generate_pattern_id() -> str:
    """生成唯一的模式ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    import random
    random_suffix = random.randint(1000, 9999)
    return f"pattern_{timestamp}_{random_suffix}"


async def record_pattern_learning(
    country_code: str,
    pattern_type: str,
    local_expression: str,
    standard_name: str,
    source: str,
    confidence: float = 0.8,
    examples: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    记录新学到的年级/学科表达模式

    Args:
        country_code: 国家代码，如 ID, SA, CN
        pattern_type: 模式类型，"grade" 或 "subject"
        local_expression: 本地表达，如 "Kelas 1", "الصف الأول"
        standard_name: 标准中文名，如 "一年级"
        source: 来源，如 "llm_extraction", "user_feedback", "search_result"
        confidence: 置信度（0-1）
        examples: 示例列表（可选）

    Returns:
        {
            "success": True/False,
            "data": {
                "pattern_id": "pattern_20260113123456_1234",
                "country_code": "ID",
                "pattern_type": "grade",
                "local_expression": "Kelas 1",
                "standard_name": "一年级",
                "confidence": 0.8,
                "status": "pending_verification",
                "created_at": "2026-01-13T12:34:56Z"
            },
            "text": "已记录新模式：Kelas 1 = 一年级 (待验证)"
        }

    示例：
        >>> result = await record_pattern_learning(
        ...     "ID", "grade", "Kelas 1", "一年级",
        ...     "llm_extraction", 0.9
        ... )
        >>> print(result['text'])
        已记录新模式：Kelas 1 = 一年级 (待验证)
    """
    try:
        # 1. 验证输入
        if pattern_type not in ["grade", "subject"]:
            return {
                "success": False,
                "data": None,
                "text": f"无效的模式类型：{pattern_type}，必须是 'grade' 或 'subject'"
            }

        if not local_expression or not local_expression.strip():
            return {
                "success": False,
                "data": None,
                "text": "本地表达不能为空"
            }

        if not standard_name or not standard_name.strip():
            return {
                "success": False,
                "data": None,
                "text": "标准名称不能为空"
            }

        confidence = max(0.0, min(1.0, confidence))  # 限制在0-1之间

        # 2. 生成模式ID
        pattern_id = _generate_pattern_id()

        # 3. 构建模式记录
        pattern = {
            "pattern_id": pattern_id,
            "country_code": country_code,
            "pattern_type": pattern_type,
            "local_expression": local_expression.strip(),
            "standard_name": standard_name.strip(),
            "source": source,
            "confidence": confidence,
            "status": "pending_verification",
            "usage_count": 0,
            "success_count": 0,
            "success_rate": 0.0,
            "examples": examples or [],
            "created_at": datetime.now().isoformat() + "Z",
            "verified_at": None,
            "last_used_at": None
        }

        # 4. 读取现有知识库
        knowledge_file = _get_knowledge_file(country_code, pattern_type)

        if os.path.exists(knowledge_file):
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                patterns = json.load(f)
        else:
            patterns = []

        # 5. 添加新模式
        patterns.append(pattern)

        # 6. 保存到文件
        with open(knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(patterns, f, ensure_ascii=False, indent=2)

        logger.info(f"记录新模式 [{country_code}][{pattern_type}]: {local_expression} = {standard_name} (ID: {pattern_id})")

        return {
            "success": True,
            "data": pattern,
            "text": f"已记录新模式：{local_expression} = {standard_name} (待验证，ID: {pattern_id})"
        }

    except Exception as e:
        logger.error(f"记录模式学习失败：{str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": None,
            "text": f"记录失败：{str(e)}"
        }


async def list_learned_patterns(
    country_code: Optional[str] = None,
    pattern_type: Optional[str] = None,
    status: Optional[str] = None,
    min_confidence: Optional[float] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    列出已学习的模式

    Args:
        country_code: 国家代码（可选，不指定则返回所有国家）
        pattern_type: 模式类型 "grade" 或 "subject"（可选）
        status: 状态过滤 "pending_verification", "verified", "rejected"（可选）
        min_confidence: 最小置信度（可选）
        limit: 最大返回数量

    Returns:
        {
            "success": True/False,
            "data": [
                {
                    "pattern_id": "pattern_xxx",
                    "country_code": "ID",
                    "pattern_type": "grade",
                    "local_expression": "Kelas 1",
                    "standard_name": "一年级",
                    "confidence": 0.9,
                    "status": "verified",
                    "usage_count": 150,
                    "success_rate": 0.95
                },
                ...
            ],
            "text": "学到的模式（5条）：\n- Kelas 1 = 一年级 (verified, 使用150次, 成功率95%)\n- ..."
        }

    示例：
        >>> result = await list_learned_patterns("ID", "grade", "verified")
        >>> print(result['text'])
        学到的模式（13条）：
        - Kelas 1 = 一年级 (verified, 使用150次, 成功率95%)
        - Kelas 6 = 六年级 (verified, 使用120次, 成率92%)
    """
    try:
        all_patterns = []

        # 1. 确定要读取的文件
        if country_code:
            # 读取指定国家的文件
            countries = [country_code]
        else:
            # 读取所有国家的文件
            if not os.path.exists(KNOWLEDGE_BASE_DIR):
                return {
                    "success": True,
                    "data": [],
                    "text": "学到的模式（0条）：暂无学习记录"
                }
            countries = [
                d for d in os.listdir(KNOWLEDGE_BASE_DIR)
                if os.path.isdir(os.path.join(KNOWLEDGE_BASE_DIR, d))
            ]

        # 2. 读取所有模式文件
        for country in countries:
            # 确定要读取的模式类型
            types_to_read = [pattern_type] if pattern_type else ["grade", "subject"]

            for ptype in types_to_read:
                knowledge_file = _get_knowledge_file(country, ptype)

                if not os.path.exists(knowledge_file):
                    continue

                try:
                    with open(knowledge_file, 'r', encoding='utf-8') as f:
                        patterns = json.load(f)
                        all_patterns.extend(patterns)
                except Exception as e:
                    logger.warning(f"读取知识库文件失败 {knowledge_file}: {e}")
                    continue

        # 3. 应用过滤器
        filtered_patterns = all_patterns

        if status:
            filtered_patterns = [p for p in filtered_patterns if p.get("status") == status]

        if min_confidence is not None:
            filtered_patterns = [p for p in filtered_patterns if p.get("confidence", 0) >= min_confidence]

        # 4. 按创建时间倒序排序
        filtered_patterns.sort(key=lambda p: p.get("created_at", ""), reverse=True)

        # 5. 限制数量
        filtered_patterns = filtered_patterns[:limit]

        # 6. 构建人类可读的列表
        lines = []
        for p in filtered_patterns:
            status_emoji = {
                "pending_verification": "⏳",
                "verified": "✅",
                "rejected": "❌"
            }.get(p.get("status", "unknown"), "❓")

            usage = p.get("usage_count", 0)
            success_rate = p.get("success_rate", 0.0)

            line = f"{status_emoji} {p['local_expression']} = {p['standard_name']} ({p.get('status', 'unknown')}"
            if usage > 0:
                line += f", 使用{usage}次"
            if success_rate > 0:
                line += f", 成功率{success_rate*100:.0f}%"
            line += ")"

            lines.append(line)

        return {
            "success": True,
            "data": filtered_patterns,
            "text": f"学到的模式（{len(filtered_patterns)}条）：\n" + "\n".join(lines)
        }

    except Exception as e:
        logger.error(f"列出学习模式失败：{str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": [],
            "text": f"列出失败：{str(e)}"
        }


async def verify_pattern(
    pattern_id: str,
    verified: bool,
    country_code: Optional[str] = None,
    pattern_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    验证学到的模式（人工审核）

    Args:
        pattern_id: 模式ID
        verified: 是否验证通过
        country_code: 国家代码（可选，如果提供可以加快查找）
        pattern_type: 模式类型（可选）

    Returns:
        {
            "success": True/False,
            "data": {
                "pattern_id": "pattern_xxx",
                "status": "verified" / "rejected",
                "verified_at": "2026-01-13T12:34:56Z"
            },
            "text": "模式已验证 (ID: pattern_xxx)" / "模式已拒绝 (ID: pattern_xxx)"
        }

    示例：
        >>> result = await verify_pattern("pattern_xxx", True)
        >>> print(result['text'])
        模式已验证 (ID: pattern_xxx)
    """
    try:
        # 1. 确定要搜索的文件
        if country_code and pattern_type:
            # 直接读取指定文件
            files_to_check = [(country_code, pattern_type)]
        else:
            # 搜索所有文件
            if not os.path.exists(KNOWLEDGE_BASE_DIR):
                return {
                    "success": False,
                    "data": None,
                    "text": f"未找到模式：{pattern_id}"
                }

            files_to_check = []
            for country in os.listdir(KNOWLEDGE_BASE_DIR):
                country_dir = os.path.join(KNOWLEDGE_BASE_DIR, country)
                if os.path.isdir(country_dir):
                    for ptype in ["grade", "subject"]:
                        knowledge_file = _get_knowledge_file(country, ptype)
                        if os.path.exists(knowledge_file):
                            files_to_check.append((country, ptype))

        # 2. 搜索模式
        found_pattern = None
        found_file = None

        for country, ptype in files_to_check:
            knowledge_file = _get_knowledge_file(country, ptype)

            with open(knowledge_file, 'r', encoding='utf-8') as f:
                patterns = json.load(f)

            for p in patterns:
                if p.get("pattern_id") == pattern_id:
                    found_pattern = p
                    found_file = knowledge_file
                    break

            if found_pattern:
                break

        if not found_pattern:
            return {
                "success": False,
                "data": None,
                "text": f"未找到模式：{pattern_id}"
            }

        # 3. 更新状态
        found_pattern["status"] = "verified" if verified else "rejected"
        found_pattern["verified_at"] = datetime.now().isoformat() + "Z"

        # 4. 保存更新
        # 重新读取文件确保数据最新
        country = found_pattern["country_code"]
        ptype = found_pattern["pattern_type"]
        knowledge_file = _get_knowledge_file(country, ptype)

        with open(knowledge_file, 'r', encoding='utf-8') as f:
            patterns = json.load(f)

        # 更新匹配的模式
        for i, p in enumerate(patterns):
            if p.get("pattern_id") == pattern_id:
                patterns[i] = found_pattern
                break

        # 保存
        with open(knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(patterns, f, ensure_ascii=False, indent=2)

        logger.info(f"验证模式 [{pattern_id}]: {found_pattern['status']}")

        return {
            "success": True,
            "data": {
                "pattern_id": pattern_id,
                "status": found_pattern["status"],
                "verified_at": found_pattern["verified_at"]
            },
            "text": f"模式{'已验证' if verified else '已拒绝'} (ID: {pattern_id})"
        }

    except Exception as e:
        logger.error(f"验证模式失败：{str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": None,
            "text": f"验证失败：{str(e)}"
        }


async def update_pattern_usage(
    pattern_id: str,
    success: bool,
    country_code: Optional[str] = None,
    pattern_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    更新模式使用统计（内部工具，用于跟踪模式效果）

    Args:
        pattern_id: 模式ID
        success: 是否成功匹配
        country_code: 国家代码（可选）
        pattern_type: 模式类型（可选）

    Returns:
        {
            "success": True/False,
            "data": {
                "pattern_id": "pattern_xxx",
                "usage_count": 151,
                "success_count": 144,
                "success_rate": 0.953
            }
        }
    """
    try:
        # 类似 verify_pattern 的逻辑，找到模式并更新统计
        if not country_code or not pattern_type:
            # 搜索所有文件
            if not os.path.exists(KNOWLEDGE_BASE_DIR):
                return {"success": False, "data": None}

            for country in os.listdir(KNOWLEDGE_BASE_DIR):
                country_dir = os.path.join(KNOWLEDGE_BASE_DIR, country)
                if os.path.isdir(country_dir):
                    for ptype in ["grade", "subject"]:
                        knowledge_file = _get_knowledge_file(country, ptype)
                        if os.path.exists(knowledge_file):
                            with open(knowledge_file, 'r', encoding='utf-8') as f:
                                patterns = json.load(f)

                            for p in patterns:
                                if p.get("pattern_id") == pattern_id:
                                    country_code = country
                                    pattern_type = ptype
                                    found_pattern = p
                                    break
                            if found_pattern:
                                break
                        if found_pattern:
                            break
                    if found_pattern:
                        break
        else:
            knowledge_file = _get_knowledge_file(country_code, pattern_type)
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                patterns = json.load(f)

            for p in patterns:
                if p.get("pattern_id") == pattern_id:
                    found_pattern = p
                    break

        if not found_pattern:
            return {"success": False, "data": None}

        # 更新统计
        found_pattern["usage_count"] = found_pattern.get("usage_count", 0) + 1
        if success:
            found_pattern["success_count"] = found_pattern.get("success_count", 0) + 1

        # 计算成功率
        usage = found_pattern["usage_count"]
        success_count = found_pattern.get("success_count", 0)
        found_pattern["success_rate"] = success_count / usage if usage > 0 else 0.0

        found_pattern["last_used_at"] = datetime.now().isoformat() + "Z"

        # 保存
        knowledge_file = _get_knowledge_file(country_code, pattern_type)
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            patterns = json.load(f)

        for i, p in enumerate(patterns):
            if p.get("pattern_id") == pattern_id:
                patterns[i] = found_pattern
                break

        with open(knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(patterns, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "data": {
                "pattern_id": pattern_id,
                "usage_count": found_pattern["usage_count"],
                "success_count": found_pattern.get("success_count", 0),
                "success_rate": found_pattern["success_rate"]
            }
        }

    except Exception as e:
        logger.error(f"更新模式统计失败：{str(e)}")
        return {"success": False, "error": str(e)}
