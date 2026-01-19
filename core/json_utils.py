#!/usr/bin/env python3
"""
JSON 工具模块

提供从 LLM 响应中提取 JSON 的工具函数
"""

import re
import json
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def extract_json_array(text: str) -> Optional[List[Dict[str, Any]]]:
    """
    从文本中提取 JSON 数组

    支持多种格式：
    1. 纯 JSON 数组
    2. 带代码块标记的 JSON (```json ... ```)
    3. 嵌入在文本中的 JSON

    Args:
        text: 包含 JSON 数组的文本

    Returns:
        提取的 JSON 数组，如果解析失败返回 None

    示例:
        >>> text = '```json\\n[{"a":1},{"b":2}]\\n```'
        >>> extract_json_array(text)
        [{"a": 1}, {"b": 2}]
    """
    if not text or not isinstance(text, str):
        return None

    # 方法1: 尝试直接解析（纯 JSON）
    text = text.strip()
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass

    # 方法2: 提取代码块中的 JSON
    # 匹配 ```json ... ``` 或 ``` ... ```
    code_block_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
    matches = re.findall(code_block_pattern, text, re.DOTALL | re.IGNORECASE)

    for match in matches:
        try:
            data = json.loads(match.strip())
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            continue

    # 方法3: 查找所有可能的 JSON 数组
    # 匹配 [ ... ] 模式
    array_pattern = r'\[\s*\{.*?\}\s*(?:,\s*\{.*?\}\s*)*\]'
    matches = re.findall(array_pattern, text, re.DOTALL)

    for match in matches:
        try:
            data = json.loads(match)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            continue

    # 方法4: 尝试修复常见的 JSON 格式问题
    try:
        # 移除所有换行符和多余空格
        cleaned = re.sub(r'\s+', ' ', text)
        # 查找 JSON 数组
        array_start = cleaned.find('[')
        array_end = cleaned.rfind(']')

        if array_start != -1 and array_end > array_start:
            json_str = cleaned[array_start:array_end + 1]
            data = json.loads(json_str)
            if isinstance(data, list):
                return data
    except (json.JSONDecodeError, ValueError):
        pass

    logger.warning(f"无法从文本中提取有效的 JSON 数组。文本长度: {len(text)}")
    logger.debug(f"文本内容（前500字符）: {text[:500]}")

    return None


def extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    """
    从文本中提取 JSON 对象

    Args:
        text: 包含 JSON 对象的文本

    Returns:
        提取的 JSON 对象，如果解析失败返回 None

    示例:
        >>> text = '```json\\n{"score": 8.5, "reason": "good"}\\n```'
        >>> extract_json_object(text)
        {"score": 8.5, "reason": "good"}
    """
    if not text or not isinstance(text, str):
        return None

    # 方法1: 尝试直接解析
    text = text.strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    # 方法2: 提取代码块中的 JSON
    code_block_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
    matches = re.findall(code_block_pattern, text, re.DOTALL | re.IGNORECASE)

    for match in matches:
        try:
            data = json.loads(match.strip())
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            continue

    # 方法3: 查找所有可能的 JSON 对象
    object_pattern = r'\{\s*"[^"]+"\s*:\s*.*?\}'
    matches = re.findall(object_pattern, text, re.DOTALL)

    for match in matches:
        try:
            data = json.loads(match)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            continue

    logger.warning(f"无法从文本中提取有效的 JSON 对象。文本长度: {len(text)}")
    logger.debug(f"文本内容（前500字符）: {text[:500]}")

    return None


def safe_json_loads(text: str, default: Any = None) -> Any:
    """
    安全的 JSON 解析，失败时返回默认值

    Args:
        text: JSON 字符串
        default: 解析失败时的默认值

    Returns:
        解析后的 Python 对象，或默认值
    """
    if not text or not isinstance(text, str):
        return default

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.debug(f"JSON 解析失败: {e}")
        return default


def validate_json_array(text: str, min_length: int = 0) -> bool:
    """
    验证文本是否包含有效的 JSON 数组

    Args:
        text: 要验证的文本
        min_length: 数组的最小长度

    Returns:
        是否为有效的 JSON 数组
    """
    data = extract_json_array(text)

    if data is None:
        return False

    if not isinstance(data, list):
        return False

    if len(data) < min_length:
        return False

    return True


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("JSON 工具测试")
    print("=" * 60)

    # 测试1: 纯 JSON 数组
    test1 = '[{"a": 1, "b": 2}, {"c": 3, "d": 4}]'
    result1 = extract_json_array(test1)
    print(f"\n测试1 - 纯 JSON 数组:")
    print(f"  输入: {test1}")
    print(f"  结果: {result1}")
    print(f"  状态: {'✅' if result1 else '❌'}")

    # 测试2: 带代码块标记
    test2 = '''```json
[
  {"index": 0, "score": 8.5, "reason": "优秀资源"},
  {"index": 1, "score": 3.0, "reason": "年级不符"}
]
```'''
    result2 = extract_json_array(test2)
    print(f"\n测试2 - 带代码块标记:")
    print(f"  输入: {test2[:50]}...")
    print(f"  结果: {result2}")
    print(f"  状态: {'✅' if result2 else '❌'}")

    # 测试3: 嵌入在文本中
    test3 = '''评分结果如下：
[{"score": 9, "reason": "完美匹配"}, {"score": 5, "reason": "一般"}]
以上是评分结果。'''
    result3 = extract_json_array(test3)
    print(f"\n测试3 - 嵌入在文本中:")
    print(f"  输入: {test3}")
    print(f"  结果: {result3}")
    print(f"  状态: {'✅' if result3 else '❌'}")

    # 测试4: 无效 JSON
    test4 = '这不是有效的 JSON'
    result4 = extract_json_array(test4)
    print(f"\n测试4 - 无效 JSON:")
    print(f"  输入: {test4}")
    print(f"  结果: {result4}")
    print(f"  状态: {'✅' if result4 is None else '❌'}")

    # 测试5: JSON 对象
    test5 = '{"score": 8.5, "reason": "good resource"}'
    result5 = extract_json_object(test5)
    print(f"\n测试5 - JSON 对象:")
    print(f"  输入: {test5}")
    print(f"  结果: {result5}")
    print(f"  状态: {'✅' if result5 else '❌'}")

    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)
