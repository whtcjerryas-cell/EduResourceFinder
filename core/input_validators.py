#!/usr/bin/env python3
"""
输入验证模块 - 使用 Pydantic 进行请求验证
修复：输入验证缺失（P1 - Security）
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List


class SearchRequestValidator(BaseModel):
    """搜索请求验证模型"""
    country: str = Field(..., min_length=2, max_length=50, description="国家名称")
    grade: str = Field(..., min_length=1, max_length=50, description="年级")
    subject: str = Field(..., min_length=1, max_length=100, description="学科")
    semester: Optional[str] = Field("", max_length=20, description="学期")
    language: Optional[str] = Field("", max_length=20, description="语言")
    resource_type: Optional[str] = Field("all", pattern="^(all|video|playlist|document)$", description="资源类型")

    @field_validator('country', 'grade', 'subject')
    @classmethod
    def sanitize_input(cls, v: str) -> str:
        """移除危险字符，防止注入攻击"""
        if not v:
            raise ValueError('输入不能为空')

        # 移除危险字符
        dangerous_chars = ['<', '>', '"', "'", ';', '&', '|', '$', '\x00', '\n', '\r']
        for char in dangerous_chars:
            v = v.replace(char, '')

        # 去除首尾空格
        v = v.strip()

        if not v:
            raise ValueError('输入不能仅包含空格或危险字符')

        return v

    @field_validator('resource_type')
    @classmethod
    def validate_resource_type(cls, v: str) -> str:
        """验证资源类型"""
        valid_types = ['all', 'video', 'playlist', 'document']
        if v not in valid_types:
            raise ValueError(f'资源类型必须是以下之一: {", ".join(valid_types)}')
        return v


class UniversitySearchRequestValidator(BaseModel):
    """大学搜索请求验证模型"""
    university_name: str = Field(..., min_length=2, max_length=100, description="大学名称")
    major: str = Field(..., min_length=1, max_length=100, description="专业")
    degree_type: str = Field("本科", pattern="^(本科|专科|硕士|博士)$", description="学位类型")
    language: Optional[str] = Field("", max_length=20, description="语言")

    @field_validator('university_name', 'major')
    @classmethod
    def sanitize_input(cls, v: str) -> str:
        """移除危险字符"""
        dangerous_chars = ['<', '>', '"', "'", ';', '&', '|', '$', '\x00', '\n', '\r']
        for char in dangerous_chars:
            v = v.replace(char, '')
        return v.strip()


class VocationalSearchRequestValidator(BaseModel):
    """职业学校搜索请求验证模型"""
    school_name: str = Field(..., min_length=2, max_length=100, description="学校名称")
    major: str = Field(..., min_length=1, max_length=100, description="专业")
    language: Optional[str] = Field("", max_length=20, description="语言")

    @field_validator('school_name', 'major')
    @classmethod
    def sanitize_input(cls, v: str) -> str:
        """移除危险字符"""
        dangerous_chars = ['<', '>', '"', "'", ';', '&', '|', '$', '\x00', '\n', '\r']
        for char in dangerous_chars:
            v = v.replace(char, '')
        return v.strip()


class ManualReviewRequestValidator(BaseModel):
    """人工审核请求验证模型"""
    search_id: str = Field(..., min_length=1, max_length=100, description="搜索ID")
    action: str = Field(..., pattern="^(approve|reject|flag)$", description="操作类型")
    notes: Optional[str] = Field("", max_length=500, description="备注")

    @field_validator('search_id')
    @classmethod
    def validate_search_id(cls, v: str) -> str:
        """验证搜索ID格式"""
        v = v.strip()
        if not v:
            raise ValueError('搜索ID不能为空')
        # 只允许字母、数字、连字符和下划线
        if not all(c.isalnum() or c in ('-', '_') for c in v):
            raise ValueError('搜索ID只能包含字母、数字、连字符和下划线')
        return v


def validate_search_request(data: dict) -> tuple[bool, str, SearchRequestValidator]:
    """
    验证搜索请求

    Args:
        data: 请求数据字典

    Returns:
        (is_valid, error_message, validated_data)
    """
    try:
        validated = SearchRequestValidator(**data)
        return True, "", validated
    except Exception as e:
        error_msg = str(e)
        # 提取有用的错误信息
        if "Input should be a valid string" in error_msg:
            error_msg = "输入格式错误"
        elif "Field required" in error_msg:
            error_msg = "缺少必填字段"
        elif "at least" in error_msg and "characters" in error_msg:
            error_msg = "输入长度不足"
        elif "at most" in error_msg and "characters" in error_msg:
            error_msg = "输入长度超限"
        return False, error_msg, None


def validate_university_search_request(data: dict) -> tuple[bool, str, UniversitySearchRequestValidator]:
    """验证大学搜索请求"""
    try:
        validated = UniversitySearchRequestValidator(**data)
        return True, "", validated
    except Exception as e:
        return False, str(e), None


def validate_vocational_search_request(data: dict) -> tuple[bool, str, VocationalSearchRequestValidator]:
    """验证职业学校搜索请求"""
    try:
        validated = VocationalSearchRequestValidator(**data)
        return True, "", validated
    except Exception as e:
        return False, str(e), None


def validate_manual_review_request(data: dict) -> tuple[bool, str, ManualReviewRequestValidator]:
    """验证人工审核请求"""
    try:
        validated = ManualReviewRequestValidator(**data)
        return True, "", validated
    except Exception as e:
        return False, str(e), None
