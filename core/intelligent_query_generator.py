#!/usr/bin/env python3
"""
查询生成器 - 生成教育视频搜索词

基于用户输入（国家、年级、学科），生成简单的搜索词。
注意：LLM智能生成功能已禁用，返回基础查询。
"""

from typing import Optional
from logger_utils import get_logger

logger = get_logger('query_generator')


def generate_query(
    country: str,
    grade: str,
    subject: str,
    semester: Optional[str] = None
) -> str:
    """
    生成基础搜索词

    Args:
        country: 国家（未使用，保留参数以保持接口兼容）
        grade: 年级
        subject: 学科
        semester: 学期（可选）

    Returns:
        搜索词，如："Mathematics Grade 3"
    """
    logger.info(f"[🔧 查询生成] 生成基础查询")

    # Simple query generation
    query = f"{subject} {grade}"
    if semester:
        query += f" {semester}"

    logger.info(f"[✅ 查询生成] 生成查询: \"{query}\"")
    return query


# ============================================================================
# 向后兼容的类包装器（用于保持测试兼容性）
# ============================================================================

class IntelligentQueryGenerator:
    """查询生成器类（向后兼容）"""

    def __init__(self, llm_client=None, config_manager=None):
        """
        初始化（参数已忽略，保持接口兼容）

        Args:
            llm_client: 忽略（保留用于接口兼容）
            config_manager: 忽略（保留用于接口兼容）
        """
        logger.info("[✅ QueryGenerator] 初始化完成（简化模式）")

    def generate_query(
        self,
        country: str,
        grade: str,
        subject: str,
        semester: Optional[str] = None
    ) -> str:
        """
        生成基础搜索词

        Args:
            country: 国家（未使用，保留参数以保持接口兼容）
            grade: 年级
            subject: 学科
            semester: 学期（可选）

        Returns:
            搜索词
        """
        return generate_query(country, grade, subject, semester)
