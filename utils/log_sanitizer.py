#!/usr/bin/env python3
"""
日志脱敏工具 - 防止敏感信息泄露到日志
修复：敏感信息日志泄露（P1 - Security）
"""
import re
import json
from typing import Any, Dict, List, Tuple


class LogSanitizer:
    """日志脱敏工具类 - 自动过滤敏感信息"""

    # 敏感信息正则表达式模式列表
    SENSITIVE_PATTERNS: List[Tuple[str, str]] = [
        # API 密钥模式（多种格式）
        (r'Bearer\s+sk-[a-zA-Z0-9]{32,}', '[API_KEY_REDACTED]'),
        (r'sk-[a-zA-Z0-9]{32,}', '[API_KEY_REDACTED]'),
        (r'AI_BUILDER_TOKEN["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{20,}', '[API_KEY_REDACTED]'),
        (r'XIAODOUBAO_API_KEY["\']?\s*[:=]\s*["\']?sk-[a-zA-Z0-9]{20,}', '[API_KEY_REDACTED]'),
        (r'INTERNAL_API_KEY["\']?\s*[:=]\s*["\']?sk-[a-zA-Z0-9]{20,}', '[API_KEY_REDACTED]'),
        (r'METASO_API_KEY["\']?\s*[:=]\s*["\']?mk-[a-zA-Z0-9]{20,}', '[API_KEY_REDACTED]'),
        (r'TAVILY_API_KEY["\']?\s*[:=]\s*["\']?tvly-[a-zA-Z0-9]{20,}', '[API_KEY_REDACTED]'),
        (r'GOOGLE_API_KEY["\']?\s*[:=]\s*["\']?AIza[a-zA-Z0-9\-]{35}', '[API_KEY_REDACTED]'),
        (r'BAIDU_API_KEY["\']?\s*[:=]\s*["\']?[a-zA-Z0-9\-]{20,}', '[API_KEY_REDACTED]'),
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{20,}', '[API_KEY_REDACTED]'),

        # 密码模式
        (r'password["\']?\s*[:=]\s*["\']?[^\s"\']+', '[PASSWORD_REDACTED]'),
        (r'passwd["\']?\s*[:=]\s*["\']?[^\s"\']+', '[PASSWORD_REDACTED]'),

        # Token 模式
        (r'token["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{20,}', '[TOKEN_REDACTED]'),
        (r'access[_-]?token["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{20,}', '[TOKEN_REDACTED]'),
        (r'refresh[_-]?token["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{20,}', '[TOKEN_REDACTED]'),
        (r'auth["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{20,}', '[AUTH_REDACTED]'),

        # 个人信息模式
        (r'email["\']?\s*[:=]\s*["\']?[^@\s]+@[^@\s]+\.[^@\s]+', '[EMAIL_REDACTED]'),
        (r'phone["\']?\s*[:=]\s*["\']?\d{10,}', '[PHONE_REDACTED]'),
        (r'mobile["\']?\s*[:=]\s*["\']?\d{10,}', '[PHONE_REDACTED]'),

        # 其他敏感信息
        (r'secret["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{10,}', '[SECRET_REDACTED]'),
        (r'private[_-]?key["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_\-/+=]{20,}', '[PRIVATE_KEY_REDACTED]'),
    ]

    # 敏感字段名列表（用于字典脱敏）
    SENSITIVE_FIELD_NAMES = {
        'password', 'passwd', 'api_key', 'apikey', 'api-key',
        'secret', 'token', 'access_token', 'refresh_token', 'auth_token',
        'private_key', 'privatekey', 'authorization', 'auth',
        'email', 'email_address', 'phone', 'mobile', 'telephone',
        'ssn', 'social_security', 'credit_card', 'cvv',
        'bearer', 'authentication', 'session_id', 'sessionid',
    }

    @classmethod
    def sanitize(cls, message: Any) -> str:
        """
        脱敏字符串消息

        Args:
            message: 要脱敏的消息（可以是任意类型）

        Returns:
            脱敏后的字符串
        """
        if not isinstance(message, str):
            message = str(message)

        # 应用所有脱敏规则
        for pattern, replacement in cls.SENSITIVE_PATTERNS:
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)

        return message

    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any], max_length: int = 200) -> Dict[str, Any]:
        """
        脱敏字典数据（递归处理嵌套字典）

        Args:
            data: 要脱敏的字典
            max_length: 字符串字段的最大长度（防止日志过大）

        Returns:
            脱敏后的字典
        """
        if not isinstance(data, dict):
            return {'data': cls.sanitize(str(data))}

        sanitized = {}
        for key, value in data.items():
            # 检查字段名是否为敏感字段
            if key.lower() in cls.SENSITIVE_FIELD_NAMES:
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, dict):
                # 递归处理嵌套字典
                sanitized[key] = cls.sanitize_dict(value, max_length)
            elif isinstance(value, list):
                # 处理列表
                sanitized[key] = cls.sanitize_list(value, max_length)
            elif isinstance(value, str):
                # 脱敏字符串值，并限制长度
                sanitized_value = cls.sanitize(value)
                if len(sanitized_value) > max_length:
                    sanitized_value = sanitized_value[:max_length] + '...[truncated]'
                sanitized[key] = sanitized_value
            else:
                # 其他类型保持不变
                sanitized[key] = value

        return sanitized

    @classmethod
    def sanitize_list(cls, data: List[Any], max_length: int = 200) -> List[Any]:
        """
        脱敏列表数据

        Args:
            data: 要脱敏的列表
            max_length: 字符串元素的最大长度

        Returns:
            脱敏后的列表
        """
        if not isinstance(data, list):
            return [cls.sanitize(str(data))]

        sanitized = []
        for item in data:
            if isinstance(item, dict):
                sanitized.append(cls.sanitize_dict(item, max_length))
            elif isinstance(item, list):
                sanitized.append(cls.sanitize_list(item, max_length))
            elif isinstance(item, str):
                sanitized_item = cls.sanitize(item)
                if len(sanitized_item) > max_length:
                    sanitized_item = sanitized_item[:max_length] + '...[truncated]'
                sanitized.append(sanitized_item)
            else:
                sanitized.append(item)

        # 限制列表长度（防止日志过大）
        if len(sanitized) > 10:
            sanitized = sanitized[:10] + [f'...[{len(sanitized)-10} more items truncated]']

        return sanitized

    @classmethod
    def sanitize_json(cls, data: Any) -> str:
        """
        脱敏并转换为JSON字符串（用于日志记录）

        Args:
            data: 要脱敏的数据

        Returns:
            脱敏后的JSON字符串
        """
        if isinstance(data, dict):
            sanitized = cls.sanitize_dict(data)
        elif isinstance(data, list):
            sanitized = cls.sanitize_list(data)
        else:
            sanitized = cls.sanitize(str(data))

        try:
            return json.dumps(sanitized, ensure_ascii=False, indent=2)
        except Exception:
            return str(sanitized)

    @classmethod
    def is_safe(cls, message: str) -> bool:
        """
        检查消息是否安全（不包含敏感信息）

        Args:
            message: 要检查的消息

        Returns:
            True 如果安全，False 如果包含敏感信息
        """
        for pattern, _ in cls.SENSITIVE_PATTERNS:
            if re.search(pattern, message, flags=re.IGNORECASE):
                return False
        return True


# 便捷函数
def safe_log(message: Any) -> str:
    """便捷函数：脱敏消息用于日志记录"""
    return LogSanitizer.sanitize(message)


def safe_log_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """便捷函数：脱敏字典用于日志记录"""
    return LogSanitizer.sanitize_dict(data)


def safe_log_json(data: Any) -> str:
    """便捷函数：脱敏并转换为JSON用于日志记录"""
    return LogSanitizer.sanitize_json(data)
