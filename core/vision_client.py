#!/usr/bin/env python3
"""
视觉分析客户端 - VisionClient
使用公司内部API（支持Gemini 2.5 Flash）
"""

import os
from typing import List, Optional, Dict, Any
from pathlib import Path

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger_utils import get_logger
from llm_client import InternalAPIClient

logger = get_logger('vision_client')


class VisionClient:
    """
    视觉分析客户端
    使用公司内部API（支持Gemini 2.5 Flash、GPT-4O等视觉模型）
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化视觉客户端

        Args:
            api_key: 公司API Key，如果不提供则从环境变量INTERNAL_API_KEY读取
            base_url: API基础地址（可选，默认使用公司内部API地址）
        """
        try:
            # 使用公司内部API客户端（指定使用vision模型）
            self.client = InternalAPIClient(api_key=api_key, base_url=base_url, model_type='vision')
            self.model = self.client.model  # 现在会使用配置的vision模型

            logger.info(f"✅ VisionClient 初始化成功，使用公司内部API")
            logger.info(f"   模型: {self.model}")
            logger.info(f"   Base URL: {self.client.base_url}")
        except Exception as e:
            logger.error(f"❌ VisionClient 初始化失败: {str(e)}")
            raise

    def analyze_images(
        self,
        image_paths: List[str],
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        分析多张图片

        Args:
            image_paths: 图片文件路径列表
            prompt: 分析提示词
            system_prompt: 系统提示词（可选）
            model: 模型名称（可选，如果不提供则使用初始化时的模型）
            max_tokens: 最大生成 token 数
            temperature: 温度参数

        Returns:
            分析结果字典：
            {
                "success": bool,
                "response": str,  # 模型返回的文本
                "error": Optional[str],
                "usage": Optional[Dict]  # Token 使用情况
            }
        """
        try:
            # 使用提供的model或默认model（vision模型）
            actual_model = model or self.model

            logger.info(f"📤 发送视觉分析请求:")
            logger.info(f"   模型: {actual_model}")
            logger.info(f"   图片数量: {len(image_paths)}")
            logger.info(f"   Prompt 长度: {len(prompt)} 字符")

            # 调用公司内部API的视觉功能
            # 注意：需要传递model参数，确保使用vision模型
            response_text = self.client.call_with_vision(
                prompt=prompt,
                image_paths=image_paths,
                max_tokens=max_tokens,
                temperature=temperature
            )

            logger.info(f"✅ 视觉分析成功:")
            logger.info(f"   响应长度: {len(response_text)} 字符")

            return {
                "success": True,
                "response": response_text,
                "error": None,
                "usage": None  # 公司API暂未返回usage信息
            }

        except Exception as e:
            error_msg = f"视觉分析失败: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "response": "",
                "error": error_msg,
                "usage": None
            }

    def analyze_single_image(
        self,
        image_path: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        分析单张图片（便捷方法）

        Args:
            image_path: 图片文件路径
            prompt: 分析提示词
            system_prompt: 系统提示词（可选）
            model: 模型名称
            max_tokens: 最大生成 token 数
            temperature: 温度参数

        Returns:
            分析结果字典
        """
        return self.analyze_images(
            image_paths=[image_path],
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature
        )
