#!/usr/bin/env python3
"""
辅助工具函数 - 提取的公共逻辑
"""

import uuid
import contextvars
from typing import Dict, Any, Optional
from logger_utils import get_logger

logger = get_logger('helpers')


# ============================================================================
# Request ID 上下文管理
# ============================================================================

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar('request_id', default='')


def get_request_id() -> str:
    """获取当前请求的 request_id"""
    return request_id_var.get('')


def set_request_id(request_id: str):
    """设置当前请求的 request_id"""
    request_id_var.set(request_id)


def generate_request_id() -> str:
    """生成新的 request_id"""
    return str(uuid.uuid4())[:8]


# ============================================================================
# 请求参数验证
# ============================================================================

def validate_search_params(data: Dict[str, Any]) -> tuple[bool, str, Dict[str, Any]]:
    """
    验证搜索请求参数

    Args:
        data: 请求数据字典

    Returns:
        (is_valid, error_message, parsed_params)
    """
    if not data:
        return False, "请求数据为空", {}

    country = (data.get('country') or '').strip()
    grade = (data.get('grade') or '').strip()
    subject = (data.get('subject') or '').strip()

    if not country or not grade or not subject:
        return False, "请提供国家、年级和学科", {}

    semester_val = data.get('semester')
    semester = (semester_val.strip() if semester_val and isinstance(semester_val, str) else '') or None

    language_val = data.get('language')
    language = (language_val.strip() if language_val and isinstance(language_val, str) else '') or None

    resource_type = data.get('resourceType', 'all').strip()

    parsed_params = {
        'country': country,
        'grade': grade,
        'subject': subject,
        'semester': semester,
        'language': language,
        'resource_type': resource_type
    }

    return True, "", parsed_params


# ============================================================================
# 响应格式化
# ============================================================================

def create_success_response(data: Any, message: str = "成功") -> Dict[str, Any]:
    """创建成功响应"""
    return {
        "success": True,
        "message": message,
        "data": data
    }


def create_error_response(message: str, status_code: int = 500) -> Dict[str, Any]:
    """创建错误响应"""
    return {
        "success": False,
        "message": message,
        "status_code": status_code
    }


def create_search_response(results: list, query: str = "", total_count: int = 0,
                          playlist_count: int = 0, video_count: int = 0) -> Dict[str, Any]:
    """创建搜索响应"""
    return {
        "success": True,
        "query": query,
        "results": results,
        "message": "",
        "total_count": total_count,
        "playlist_count": playlist_count,
        "video_count": video_count
    }


# ============================================================================
# 中文显示名称获取
# ============================================================================

def get_chinese_display_names(config_manager, search_params: Dict[str, Any]) -> tuple[str, str, str]:
    """
    获取国家、年级、学科的中文显示名称

    Args:
        config_manager: 配置管理器实例
        search_params: 搜索参数字典

    Returns:
        (country_zh, grade_zh, subject_zh)
    """
    country_code = search_params.get('country', '')
    grade_local = search_params.get('grade', '')
    subject_local = search_params.get('subject', '')

    # 优先使用前端传递的中文文本
    country_zh = search_params.get('countryText', country_code)
    grade_zh = search_params.get('gradeText', grade_local)
    subject_zh = search_params.get('subjectText', subject_local)

    # 如果前端没有提供中文文本，尝试从配置获取
    if country_zh == country_code or grade_zh == grade_local or subject_zh == subject_local:
        try:
            if country_code:
                country_config = config_manager.get_country_config(country_code.upper())
                if country_config:
                    # 只在需要时覆盖
                    if country_zh == country_code:
                        country_zh = country_config.country_name_zh or country_config.country_name

                    # 查找年级的中文名称
                    if grade_zh == grade_local:
                        for grade_info in country_config.grades:
                            if grade_info['local_name'] == grade_local:
                                grade_zh = grade_info['zh_name']
                                break

                    # 查找学科的中文名称
                    if subject_zh == subject_local:
                        for subject_info in country_config.subjects:
                            if subject_info['local_name'] == subject_local:
                                subject_zh = subject_info['zh_name']
                                break
        except Exception as e:
            logger.warning(f"[中文名称] 获取失败: {str(e)}")

    return country_zh, grade_zh, subject_zh
