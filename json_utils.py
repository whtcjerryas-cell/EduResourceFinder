#!/usr/bin/env python3
"""
JSON 解析工具模块 - 统一的 JSON 提取和解析逻辑
处理 LLM 返回的各种格式的 JSON（Markdown代码块、单引号、尾部逗号等）
"""

import json
import re
import ast
from typing import Any, Optional, Union
from logger_utils import get_logger

# 初始化日志记录器
logger = get_logger('json_utils')


def extract_and_parse_json(text: str, expected_type: Optional[type] = None) -> Union[dict, list, None]:
    """
    通用的 JSON 提取和解析函数
    
    功能：
    1. 使用正则表达式自动去除 ```json 和 ``` 标记
    2. 如果 json.loads 失败，尝试使用 ast.literal_eval 作为备选（处理 Python 风格的单引号字典）
    3. 如果返回的是文本包含 JSON，尝试通过正则提取 {...} 或 [...] 结构
    4. 添加详细的错误日志，如果解析彻底失败，打印出原始文本以便 Debug
    
    Args:
        text: 包含 JSON 的文本
        expected_type: 期望的类型（dict 或 list），如果提供，会验证返回类型
    
    Returns:
        解析后的 JSON 对象（dict 或 list），如果解析失败返回 None
    """
    if not text or not isinstance(text, str):
        logger.warning(f"[JSON解析] 输入为空或不是字符串: {type(text)}")
        return None
    
    original_text = text
    logger.debug(f"[JSON解析] 开始解析，原始文本长度: {len(text)} 字符")
    logger.debug(f"[JSON解析] 原始文本（前200字符）: {text[:200]}...")
    
    # ========================================================================
    # 步骤1: 尝试提取 JSON 结构（对象或数组）
    # ========================================================================
    json_str = None
    
    # 方法1: 查找最外层的 JSON 对象 {...}
    json_obj_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if json_obj_match:
        json_str = json_obj_match.group(0)
        logger.debug(f"[JSON解析] 方法1: 找到 JSON 对象，长度: {len(json_str)} 字符")
    
    # 方法2: 查找最外层的 JSON 数组 [...]
    json_array_match = re.search(r'\[[\s\S]*?\]', text, re.DOTALL)
    if json_array_match:
        array_str = json_array_match.group(0)
        # 如果数组比对象更长，或者没有找到对象，使用数组
        if not json_str or len(array_str) > len(json_str):
            json_str = array_str
            logger.debug(f"[JSON解析] 方法2: 找到 JSON 数组，长度: {len(json_str)} 字符")
    
    # 如果没找到，使用完整文本
    if not json_str:
        json_str = text
        logger.debug(f"[JSON解析] 方法3: 使用完整文本")
    
    # ========================================================================
    # 步骤2: 清理 JSON 字符串
    # ========================================================================
    logger.debug(f"[JSON解析] 步骤2: 清理 JSON 字符串...")
    
    # 移除 Markdown 代码块标记
    json_str = json_str.strip()
    
    # 移除 ```json 前缀
    if json_str.startswith('```json'):
        json_str = json_str[7:]
        logger.debug(f"[JSON解析] 移除 ```json 前缀")
    elif json_str.startswith('```'):
        json_str = json_str[3:]
        logger.debug(f"[JSON解析] 移除 ``` 前缀")
    
    # 移除 ``` 后缀
    if json_str.endswith('```'):
        json_str = json_str[:-3]
        logger.debug(f"[JSON解析] 移除 ``` 后缀")
    
    json_str = json_str.strip()
    
    # 移除可能的引号包裹（如果整个字符串被引号包裹）
    if (json_str.startswith('"') and json_str.endswith('"')) or \
       (json_str.startswith("'") and json_str.endswith("'")):
        json_str = json_str[1:-1]
        logger.debug(f"[JSON解析] 移除引号包裹")
    
    json_str = json_str.strip()
    
    logger.debug(f"[JSON解析] 清理后长度: {len(json_str)} 字符")
    logger.debug(f"[JSON解析] 清理后的 JSON（前300字符）: {json_str[:300]}...")
    
    # ========================================================================
    # 步骤3: 尝试解析 JSON
    # ========================================================================
    
    # 方法1: 标准 JSON 解析
    try:
        logger.debug(f"[JSON解析] 方法1: 尝试标准 JSON 解析...")
        data = json.loads(json_str)
        logger.info(f"[JSON解析] ✅ 标准 JSON 解析成功")
        
        # 验证类型
        if expected_type and not isinstance(data, expected_type):
            logger.warning(f"[JSON解析] ⚠️ 类型不匹配: 期望 {expected_type.__name__}, 实际 {type(data).__name__}")
            # 尝试转换
            if expected_type == list and isinstance(data, dict):
                data = [data]
            elif expected_type == dict and isinstance(data, list) and len(data) > 0:
                data = data[0]
        
        return data
        
    except json.JSONDecodeError as e:
        logger.warning(f"[JSON解析] ❌ 标准 JSON 解析失败: {str(e)}")
        logger.debug(f"[JSON解析] 错误位置: {e.pos if hasattr(e, 'pos') else '未知'}")
        logger.debug(f"[JSON解析] 错误行: {e.lineno if hasattr(e, 'lineno') else '未知'}")
        logger.debug(f"[JSON解析] 错误列: {e.colno if hasattr(e, 'colno') else '未知'}")
        
        # 方法2: 尝试修复常见的 JSON 问题
        try:
            logger.debug(f"[JSON解析] 方法2: 尝试修复常见问题...")
            
            # 修复1: 移除尾部逗号
            json_str_fixed = re.sub(r',\s*}', '}', json_str)
            json_str_fixed = re.sub(r',\s*]', ']', json_str_fixed)
            
            # 修复2: 修复单引号（但要注意字符串内的单引号）
            # 先尝试简单的替换（可能不完美，但能处理大部分情况）
            json_str_fixed = json_str_fixed.replace("'", '"')
            
            data = json.loads(json_str_fixed)
            logger.info(f"[JSON解析] ✅ 修复后 JSON 解析成功")
            
            # 验证类型
            if expected_type and not isinstance(data, expected_type):
                if expected_type == list and isinstance(data, dict):
                    data = [data]
                elif expected_type == dict and isinstance(data, list) and len(data) > 0:
                    data = data[0]
            
            return data
            
        except Exception as fix_e:
            logger.warning(f"[JSON解析] ❌ 修复后解析也失败: {str(fix_e)}")
    
    # 方法3: 尝试使用 ast.literal_eval（处理 Python 风格的单引号字典）
    try:
        logger.debug(f"[JSON解析] 方法3: 尝试 ast.literal_eval...")
        data = ast.literal_eval(json_str)
        logger.info(f"[JSON解析] ✅ ast.literal_eval 解析成功")
        
        # 验证类型
        if expected_type and not isinstance(data, expected_type):
            if expected_type == list and isinstance(data, dict):
                data = [data]
            elif expected_type == dict and isinstance(data, list) and len(data) > 0:
                data = data[0]
        
        return data
        
    except Exception as ast_e:
        logger.warning(f"[JSON解析] ❌ ast.literal_eval 解析失败: {str(ast_e)}")
    
    # 方法4: 尝试更激进的正则提取
    try:
        logger.debug(f"[JSON解析] 方法4: 尝试激进的正则提取...")
        
        # 提取 {...} 或 [...] 结构（更宽松的匹配）
        pattern = r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})|(\[[\s\S]*?\])'
        matches = re.findall(pattern, original_text, re.DOTALL)
        
        for match in matches:
            json_candidate = match[0] if match[0] else match[1]
            if json_candidate:
                try:
                    data = json.loads(json_candidate)
                    logger.info(f"[JSON解析] ✅ 激进正则提取后解析成功")
                    
                    # 验证类型
                    if expected_type and not isinstance(data, expected_type):
                        if expected_type == list and isinstance(data, dict):
                            data = [data]
                        elif expected_type == dict and isinstance(data, list) and len(data) > 0:
                            data = data[0]
                    
                    return data
                except:
                    continue
        
        logger.warning(f"[JSON解析] ❌ 激进正则提取也失败")
        
    except Exception as regex_e:
        logger.warning(f"[JSON解析] ❌ 激进正则提取异常: {str(regex_e)}")
    
    # 所有方法都失败
    logger.error(f"[JSON解析] ❌ 所有解析方法都失败")
    logger.error(f"[JSON解析] 原始文本（完整）:\n{original_text}")
    logger.error(f"[JSON解析] 清理后的文本（完整）:\n{json_str}")
    
    return None


def extract_json_object(text: str) -> Optional[dict]:
    """
    提取并解析 JSON 对象
    
    Args:
        text: 包含 JSON 的文本
    
    Returns:
        解析后的字典，如果解析失败返回 None
    """
    result = extract_and_parse_json(text, expected_type=dict)
    return result if isinstance(result, dict) else None


def extract_json_array(text: str) -> Optional[list]:
    """
    提取并解析 JSON 数组
    
    Args:
        text: 包含 JSON 的文本
    
    Returns:
        解析后的列表，如果解析失败返回 None
    """
    result = extract_and_parse_json(text, expected_type=list)
    return result if isinstance(result, list) else None





