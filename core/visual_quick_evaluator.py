#!/usr/bin/env python3
from utils.json_parser import JSONParser
"""
视觉快速评估器 - VisualQuickEvaluator
基于网页截图的快速教育资源评估系统

评估维度：
1. 语言检测 - 独立评估
2. 标题与内容一致性 - 综合评估
3. 内容质量 - 综合评估
4. 年级难度匹配 - 综合评估
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
import re
from typing import Dict, List, Optional, Any
from utils.logger_utils import get_logger

logger = get_logger('visual_quick_evaluator')


class VisualQuickEvaluator:
    """
    视觉快速评估器

    使用视觉大模型分析视频页面截图，快速评估资源质量
    """

    def __init__(self, vision_client=None):
        """
        初始化评估器

        Args:
            vision_client: VisionClient实例（可选，如果不提供则延迟初始化）
        """
        self.vision_client = vision_client
        self._init_vision_client()

    def _init_vision_client(self):
        """延迟初始化视觉客户端"""
        if self.vision_client is None:
            try:
                from core.vision_client import VisionClient
                self.vision_client = VisionClient()
                logger.info("✅ VisionClient 初始化成功")
            except Exception as e:
                logger.error(f"❌ VisionClient 初始化失败: {str(e)}")
                self.vision_client = None

    # ========================================================================
    # 提示词模板
    # ========================================================================

    LANGUAGE_DETECTION_PROMPT = """你是一个语言检测专家。

任务：检测视频页面的主要语言

目标语言：{target_language}（如：ar=阿拉伯语, en=英语, zh=中文, id=印尼语）
页面截图：已提供

检测要点：
1. 视频标题的文字语言
2. 描述文字的语言
3. 页面UI元素的语言
4. 缩略图/封面上是否有文字

输出格式（JSON）：
{{
  "detected_language": "语言代码（ar/en/zh/id等）",
  "is_match": true/false,
  "confidence": 0.0-1.0
}}

注意：
- 只输出JSON，不要有其他内容
- is_match: 检测到的语言是否与目标语言一致
- confidence: 检测置信度（0-1之间）
"""

    COMPREHENSIVE_EVALUATION_PROMPT = """你是一个教育资源评估专家。

任务：从3个维度评估视频页面价值

视频标题：{title}
目标年级：{grade}
目标学科：{subject}
页面截图：已提供

请评估以下3个维度：

**维度1：标题与内容一致性（防标题党）**
- 标题承诺的内容是否在页面中可见
- 封面图是否与标题相关
- 描述文字是否与标题匹配
- 视频缩略图是否展示标题内容

**维度2：内容质量**
- 来源可信度（官方平台、认证频道、个人创作者）
- 页面专业性（封面设计、排版、描述完整度）
- 互动质量（观看量、点赞、评论数等，如果可见）

**维度3：年级难度匹配**
- 视频标题的术语难度
- 描述中的知识点深度
- 封面/缩略图展示的内容层次
- 如果有章节列表，查看章节标题的难度

输出格式（JSON）：
{{
  "title_consistency": {{
    "score": 0.0-1.0,
    "is_consistent": true/false,
    "reason": "判断理由（中文，30字内）"
  }},
  "content_quality": {{
    "score": 0.0-10.0,
    "source_type": "official/verified/personal/low_quality",
    "reason": "判断理由（中文，30字内）"
  }},
  "grade_match": {{
    "score": 0.0-1.0,
    "is_appropriate": true/false,
    "estimated_grade": "推测的实际年级（如：高中一年级）",
    "reason": "判断理由（中文，30字内）"
  }}
}}

注意：
- 只输出JSON，不要有其他内容
- 各维度独立评分，不要互相影响
- score范围：title_consistency和grade_match是0-1，content_quality是0-10
- source_type可选值：official（官方）、verified（认证频道）、personal（个人）、low_quality（低质量）
"""

    # ========================================================================
    # 评估方法
    # ========================================================================

    def evaluate_language(
        self,
        screenshot_path: str,
        target_language: str
    ) -> Optional[Dict[str, Any]]:
        """
        评估视频页面语言是否匹配

        Args:
            screenshot_path: 截图文件路径
            target_language: 目标语言代码（ar/en/zh/id等）

        Returns:
            {
                "detected_language": "ar",
                "is_match": true,
                "confidence": 0.95
            }
            失败返回None
        """
        if not self.vision_client:
            logger.warning("VisionClient未初始化，无法进行语言检测")
            return None

        try:
            # 构建提示词
            prompt = self.LANGUAGE_DETECTION_PROMPT.format(
                target_language=target_language
            )

            logger.info(f"🔍 开始语言检测: 目标语言={target_language}")

            # 调用视觉分析
            result = self.vision_client.analyze_single_image(
                image_path=screenshot_path,
                prompt=prompt,
                max_tokens=300,
                temperature=0.3
            )

            if not result.get('success'):
                logger.warning(f"语言检测失败: {result.get('error')}")
                return None

            # 解析JSON响应
            response_text = result.get('response', '')
            parsed = JSONParser.extract_json_from_response(response_text)

            if parsed:
                logger.info(f"✅ 语言检测成功: {parsed}")
                return parsed
            else:
                logger.warning(f"语言检测JSON解析失败: {response_text[:200]}")
                return None

        except Exception as e:
            logger.error(f"❌ 语言检测异常: {str(e)}")
            return None

    def evaluate_comprehensive(
        self,
        screenshot_path: str,
        title: str,
        target_grade: str,
        subject: str
    ) -> Optional[Dict[str, Any]]:
        """
        综合评估（标题+质量+年级）

        Args:
            screenshot_path: 截图文件路径
            title: 视频标题
            target_grade: 目标年级
            subject: 学科

        Returns:
            {
                "title_consistency": {...},
                "content_quality": {...},
                "grade_match": {...}
            }
            失败返回None
        """
        if not self.vision_client:
            logger.warning("VisionClient未初始化，无法进行综合评估")
            return None

        try:
            # 构建提示词
            prompt = self.COMPREHENSIVE_EVALUATION_PROMPT.format(
                title=title[:200],  # 限制标题长度
                grade=target_grade,
                subject=subject
            )

            logger.info(f"🔍 开始综合评估: 标题={title[:50]}..., 年级={target_grade}")

            # 调用视觉分析
            result = self.vision_client.analyze_single_image(
                image_path=screenshot_path,
                prompt=prompt,
                max_tokens=800,
                temperature=0.3
            )

            if not result.get('success'):
                logger.warning(f"综合评估失败: {result.get('error')}")
                return None

            # 解析JSON响应
            response_text = result.get('response', '')
            parsed = JSONParser.extract_json_from_response(response_text)

            if parsed:
                logger.info(f"✅ 综合评估成功")
                return parsed
            else:
                logger.warning(f"综合评估JSON解析失败: {response_text[:200]}")
                return None

        except Exception as e:
            logger.error(f"❌ 综合评估异常: {str(e)}")
            return None

    def evaluate_full(
        self,
        screenshot_path: str,
        title: str,
        target_grade: str,
        subject: str,
        target_language: str
    ) -> Optional[Dict[str, Any]]:
        """
        完整评估（语言+综合）

        Args:
            screenshot_path: 截图文件路径
            title: 视频标题
            target_grade: 目标年级
            subject: 学科
            target_language: 目标语言

        Returns:
            {
                "overall_score": 7.5,
                "should_download": true,
                "breakdown": {
                    "title_consistency": {...},
                    "language_match": {...},
                    "content_quality": {...},
                    "grade_match": {...}
                },
                "recommendation": "推荐下载：..."
            }
            失败返回None
        """
        try:
            # 第1步：语言检测
            language_result = self.evaluate_language(
                screenshot_path=screenshot_path,
                target_language=target_language
            )

            if not language_result:
                logger.warning("语言检测失败，使用默认值")
                language_result = {
                    "detected_language": "unknown",
                    "is_match": True,  # 默认认为匹配
                    "confidence": 0.0
                }

            # 第2步：综合评估
            comprehensive_result = self.evaluate_comprehensive(
                screenshot_path=screenshot_path,
                title=title,
                target_grade=target_grade,
                subject=subject
            )

            if not comprehensive_result:
                logger.warning("综合评估失败，无法完成评估")
                return None

            # 第3步：计算总分
            overall_result = self._calculate_overall_score(
                language_result=language_result,
                comprehensive_result=comprehensive_result
            )

            return overall_result

        except Exception as e:
            logger.error(f"❌ 完整评估异常: {str(e)}")
            return None

    # ========================================================================
    # 评分计算
    # ========================================================================

    def _calculate_overall_score(
        self,
        language_result: Dict[str, Any],
        comprehensive_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算总分

        评分权重：
        - 标题一致性：25%
        - 语言匹配：20%
        - 内容质量：40%
        - 年级匹配：15%

        下载推荐阈值：7.0分
        """
        try:
            # 提取各维度分数
            title_score = comprehensive_result.get('title_consistency', {}).get('score', 0.5)
            quality_score = comprehensive_result.get('content_quality', {}).get('score', 5.0)
            grade_score = comprehensive_result.get('grade_match', {}).get('score', 0.5)

            # 语言分数（is_match为True则1.0，否则0.0，考虑置信度）
            language_confidence = language_result.get('confidence', 0.5)
            if language_result.get('is_match', False):
                language_score = 1.0 * language_confidence
            else:
                language_score = 0.0

            # 计算总分（0-10）
            # 注意：quality_score已经是0-10，其他是0-1
            overall_score = (
                title_score * 0.25 * 10 +  # 转换到0-10
                language_score * 0.20 * 10 +
                quality_score * 0.40 +
                grade_score * 0.15 * 10
            )

            overall_score = round(overall_score, 1)

            # 判断是否推荐下载
            should_download = overall_score >= 7.0

            # 生成推荐理由
            recommendation = self._generate_recommendation(
                overall_score=overall_score,
                language_result=language_result,
                comprehensive_result=comprehensive_result
            )

            return {
                "overall_score": overall_score,
                "should_download": should_download,
                "breakdown": {
                    "title_consistency": {
                        "score": title_score,
                        "weight": 0.25,
                        "reason": comprehensive_result.get('title_consistency', {}).get('reason', '')
                    },
                    "language_match": {
                        "score": language_score,
                        "weight": 0.20,
                        "detected_language": language_result.get('detected_language', 'unknown'),
                        "is_match": language_result.get('is_match', False)
                    },
                    "content_quality": {
                        "score": quality_score,
                        "weight": 0.40,
                        "source_type": comprehensive_result.get('content_quality', {}).get('source_type', 'unknown'),
                        "reason": comprehensive_result.get('content_quality', {}).get('reason', '')
                    },
                    "grade_match": {
                        "score": grade_score,
                        "weight": 0.15,
                        "is_appropriate": comprehensive_result.get('grade_match', {}).get('is_appropriate', False),
                        "reason": comprehensive_result.get('grade_match', {}).get('reason', '')
                    }
                },
                "recommendation": recommendation
            }

        except Exception as e:
            logger.error(f"❌ 计算总分失败: {str(e)}")
            return None

    def _generate_recommendation(
        self,
        overall_score: float,
        language_result: Dict[str, Any],
        comprehensive_result: Dict[str, Any]
    ) -> str:
        """
        生成推荐理由
        """
        if overall_score >= 8.0:
            base = "强烈推荐"
        elif overall_score >= 7.0:
            base = "推荐下载"
        elif overall_score >= 5.0:
            base = "可考虑"
        else:
            base = "不推荐"

        # 收集关键信息
        highlights = []

        # 语言匹配
        if language_result.get('is_match'):
            highlights.append("语言正确")
        else:
            highlights.append("语言可能不匹配")

        # 内容质量
        source_type = comprehensive_result.get('content_quality', {}).get('source_type', '')
        if source_type == 'official':
            highlights.append("官方来源")
        elif source_type == 'verified':
            highlights.append("认证频道")
        elif source_type == 'low_quality':
            highlights.append("质量较低")

        # 标题一致性
        if comprehensive_result.get('title_consistency', {}).get('is_consistent'):
            highlights.append("内容相关")
        else:
            highlights.append("内容可能不相关")

        # 年级匹配
        if comprehensive_result.get('grade_match', {}).get('is_appropriate'):
            highlights.append("难度适合")
        else:
            highlights.append("难度可能不适合")

        return f"{base}：{'、'.join(highlights)}"

    # ========================================================================
    # JSON解析工具
    # ========================================================================

