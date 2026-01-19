#!/usr/bin/env python3
"""
视频内容评估器 - VideoEvaluator
智能评分系统：Rule-Based + AI-Based
"""

import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

from logger_utils import get_logger
from search_strategist import AIBuildersClient
from json_utils import extract_and_parse_json, extract_json_object
from core.config_loader import get_config

logger = get_logger('video_evaluator')

# 尝试导入 VisionClient，如果不可用则使用文本模拟
try:
    from core.vision_client import VisionClient
    HAS_VISION_CLIENT = True
except ImportError as e:
    HAS_VISION_CLIENT = False
    import sys
    from pathlib import Path
    # 添加项目根目录到路径后重试
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    try:
        from core.vision_client import VisionClient
        HAS_VISION_CLIENT = True
    except ImportError:
        HAS_VISION_CLIENT = False
        logger.warning(f"VisionClient 不可用，将使用文本模拟视觉分析。错误: {str(e)}")


class VideoEvaluator:
    """
    视频内容评估器
    结合规则评分和AI评分，提供多维度评估
    """
    
    def __init__(self, api_token: Optional[str] = None, vision_api_key: Optional[str] = None):
        """
        初始化评估器

        Args:
            api_token: AI Builders API 令牌
            vision_api_key: 视觉API密钥（公司内部API），如果不提供则从环境变量INTERNAL_API_KEY读取
        """
        self.client = AIBuildersClient(api_token)

        # 加载配置
        self.config = get_config()

        # 初始化视觉客户端（使用公司内部API）
        self.vision_client = None
        if HAS_VISION_CLIENT:
            try:
                self.vision_client = VisionClient(api_key=vision_api_key)
                logger.info("✅ VisionClient 初始化成功，将使用公司内部API进行视觉分析")
            except Exception as e:
                logger.warning(f"⚠️  VisionClient 初始化失败: {str(e)}，将使用文本模拟")
                self.vision_client = None
        else:
            logger.warning("⚠️  VisionClient 不可用，将使用文本模拟视觉分析")
    
    def match_knowledge_point(
        self,
        video_title: str,
        video_description: Optional[str],
        transcript: Optional[str],
        knowledge_points: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        自动匹配最相关的知识点
        
        Args:
            video_title: 视频标题
            video_description: 视频描述（可选）
            transcript: 字幕/转录文本（可选，前1000字符）
            knowledge_points: 知识点列表
        
        Returns:
            匹配的知识点字典，如果没有匹配则返回None
        """
        if not knowledge_points:
            logger.warning("    [⚠️ 警告] 知识点列表为空，无法匹配")
            return None
        
        logger.info(f"    [🔍 知识点匹配] 开始从 {len(knowledge_points)} 个知识点中匹配...")
        
        # 构建知识点摘要（用于LLM匹配）
        knowledge_points_summary = []
        for i, kp in enumerate(knowledge_points, 1):
            summary = {
                "id": kp.get('id', f'KP{i}'),
                "topic_title_cn": kp.get('topic_title_cn', ''),
                "topic_title_id": kp.get('topic_title_id', ''),
                "chapter_title": kp.get('chapter_title', ''),
                "learning_objective": kp.get('learning_objective', '')[:200] + '...' if len(kp.get('learning_objective', '')) > 200 else kp.get('learning_objective', '')
            }
            knowledge_points_summary.append(summary)
        
        # 准备视频信息（用于匹配）
        video_info = f"标题: {video_title}"
        if video_description:
            video_info += f"\n描述: {video_description[:300]}"
        if transcript:
            video_info += f"\n内容摘要: {transcript[:500]}"
        
        system_prompt = """你是一个教育内容匹配专家。你的任务是根据视频内容，从给定的知识点列表中选择最相关的一个知识点。

**匹配标准**：
1. 视频内容是否直接讲解该知识点？
2. 视频标题和描述是否与该知识点相关？
3. 视频内容是否覆盖了该知识点的学习目标？

请返回最匹配的知识点ID，如果没有明显匹配的，返回null。"""
        
        user_prompt = f"""请根据以下视频信息，从知识点列表中选择最相关的一个知识点。

**视频信息**：
{video_info}

**知识点列表**：
{json.dumps(knowledge_points_summary, ensure_ascii=False, indent=2)}

**要求**：
1. 仔细分析视频内容与每个知识点的相关性
2. 选择最匹配的知识点（如果都不匹配，返回null）
3. 只返回知识点的ID，格式：{{"matched_knowledge_point_id": "MAT-3-4-BIL-01"}} 或 {{"matched_knowledge_point_id": null}}

请以JSON格式返回："""
        
        try:
            response = self.client.call_llm(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model="deepseek",  # 使用 deepseek 模型（不是 deepseek-chat）
                temperature=0.3,
                max_tokens=500
            )
            
            # 解析响应
            result = extract_and_parse_json(response)
            matched_id = result.get('matched_knowledge_point_id') if result else None
            
            if not matched_id:
                logger.warning("    [⚠️ 警告] LLM未找到匹配的知识点")
                return None
            
            # 查找匹配的知识点
            matched_kp = next((kp for kp in knowledge_points if kp.get('id') == matched_id), None)
            
            if matched_kp:
                logger.info(f"    [✅ 匹配成功] 知识点: {matched_kp.get('topic_title_cn', matched_kp.get('topic_title_id', 'N/A'))}")
                return matched_kp
            else:
                logger.warning(f"    [⚠️ 警告] 未找到ID为 {matched_id} 的知识点")
                return None
                
        except Exception as e:
            logger.error(f"    [❌ 匹配失败] {str(e)}")
            import traceback
            traceback.print_exc()
            # 如果匹配失败，返回第一个知识点作为默认值
            if knowledge_points:
                logger.info(f"    [📌 使用默认] 返回第一个知识点: {knowledge_points[0].get('topic_title_cn', 'N/A')}")
                return knowledge_points[0]
            return None
    
    def evaluate_video_content(
        self,
        video_metadata: Dict[str, Any],
        video_path: Optional[str] = None,
        frames_paths: Optional[List[str]] = None,
        audio_path: Optional[str] = None,
        transcript: Optional[str] = None,
        knowledge_point: Optional[Dict[str, Any]] = None,
        knowledge_points: Optional[List[Dict[str, Any]]] = None,  # 新增：知识点列表（用于自动匹配）
        log_collector=None  # 新增：搜索日志收集器（可选），用于记录模型调用
    ) -> Dict[str, Any]:
        """
        评估视频内容
        
        Args:
            video_metadata: 视频元数据（必须包含 max_resolution_height）
            video_path: 视频文件路径（可选）
            frames_paths: 关键帧路径列表（可选）
            audio_path: 音频文件路径（可选）
            transcript: 字幕/转录文本（可选）
            knowledge_point: 知识点信息（可选，包含 learning_objective）
            knowledge_points: 知识点列表（可选，如果提供且knowledge_point为空，将自动匹配）
        
        Returns:
            评估结果字典：
            {
                "overall_score": float,  # 总分（0-10）
                "visual_quality": {
                    "tech_score": float,  # 硬指标（分辨率）
                    "design_score": float,  # 软指标（Vision AI）
                    "combined_score": float,  # 加权合并
                    "details": str
                },
                "relevance": {
                    "score": float,
                    "details": str
                },
                "pedagogy": {
                    "score": float,
                    "details": str
                },
                "metadata": {
                    "score": float,
                    "details": str
                },
                "breakdown": {
                    "visual_weight": 0.2,
                    "relevance_weight": 0.4,
                    "pedagogy_weight": 0.3,
                    "metadata_weight": 0.1
                }
            }
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"🎬 开始评估视频内容")
        logger.info(f"{'='*80}")

        # 设置日志收集器（用于记录模型调用）
        self.log_collector = log_collector

        # 自动匹配知识点（如果提供了知识点列表但没有指定知识点）
        matched_knowledge_point = knowledge_point  # 初始化
        if not knowledge_point and knowledge_points:
            logger.info(f"\n[🔍 自动匹配知识点] 从 {len(knowledge_points)} 个知识点中匹配...")
            video_title = video_metadata.get('title', '')
            video_description = video_metadata.get('description', '')
            transcript_preview = transcript[:1000] if transcript else None
            
            matched_kp = self.match_knowledge_point(
                video_title=video_title,
                video_description=video_description,
                transcript=transcript_preview,
                knowledge_points=knowledge_points
            )
            
            if matched_kp:
                knowledge_point = matched_kp
                matched_knowledge_point = matched_kp
                logger.info(f"[✅ 匹配成功] 知识点: {matched_kp.get('topic_title_cn', matched_kp.get('topic_title_id', 'N/A'))}")
            else:
                # 如果匹配失败，使用第一个知识点作为默认值（至少可以进行相关度评估）
                if knowledge_points and len(knowledge_points) > 0:
                    knowledge_point = knowledge_points[0]
                    matched_knowledge_point = knowledge_points[0]
                    logger.warning(f"[⚠️ 匹配失败] 使用第一个知识点作为默认值: {knowledge_points[0].get('topic_title_cn', knowledge_points[0].get('topic_title_id', 'N/A'))}")
                else:
                    logger.warning(f"[⚠️ 匹配失败] 知识点列表为空，将使用通用评估")
        elif knowledge_point:
            matched_knowledge_point = knowledge_point
        
        # 记录最终使用的知识点（用于调试）
        if knowledge_point:
            logger.info(f"[📚 知识点] 将使用知识点进行评估: {knowledge_point.get('topic_title_cn', knowledge_point.get('topic_title_id', 'N/A'))}")
        else:
            logger.warning(f"[📚 知识点] 无知识点信息，相关度评估将使用默认分数")
            if knowledge_points:
                logger.warning(f"[📚 知识点] 知识点列表存在 ({len(knowledge_points)} 个)，但匹配失败")
            else:
                logger.warning(f"[📚 知识点] 知识点列表为空，无法进行相关度评估")
        
        result = {
            "overall_score": 0.0,
            "visual_quality": {
                "tech_score": 0.0,
                "design_score": 0.0,
                "combined_score": 0.0,
                "details": ""
            },
            "relevance": {
                "score": 0.0,
                "details": ""
            },
            "pedagogy": {
                "score": 0.0,
                "details": ""
            },
            "metadata": {
                "score": 0.0,
                "details": ""
            },
            "breakdown": self.config.get_overall_weights(),
            "matched_knowledge_point": matched_knowledge_point  # 保存匹配的知识点信息
        }
        
        try:
            # 获取权重配置
            weights = self.config.get_overall_weights()
            visual_weight_pct = weights['visual_quality'] * 100
            relevance_weight_pct = weights['relevance'] * 100
            pedagogy_weight_pct = weights['pedagogy'] * 100
            metadata_weight_pct = weights['metadata'] * 100

            # ==================== 并行执行4个评估维度 ====================
            import concurrent.futures

            logger.info(f"\n[🚀 开始并行评估] 将同时执行4个评估维度...")

            # 定义评估任务
            def evaluate_visual():
                logger.info(f"[📊 启动] 视觉质量评估 (权重: {visual_weight_pct:.0f}%)")
                result = self._evaluate_visual_quality(
                    video_metadata=video_metadata,
                    frames_paths=frames_paths
                )
                logger.info(f"    [✅ 完成] 技术分: {result['tech_score']:.1f}, "
                           f"设计分: {result['design_score']:.1f}, "
                           f"综合分: {result['combined_score']:.1f}")
                return ('visual', result)

            def evaluate_relevance():
                logger.info(f"[📊 启动] 内容相关度评估 (权重: {relevance_weight_pct:.0f}%)")
                result = self._evaluate_relevance(
                    transcript=transcript,
                    knowledge_point=knowledge_point,
                    video_metadata=video_metadata
                )
                logger.info(f"    [✅ 完成] 相关度分数: {result['score']:.1f}")
                return ('relevance', result)

            def evaluate_pedagogy():
                logger.info(f"[📊 启动] 教学质量评估 (权重: {pedagogy_weight_pct:.0f}%)")
                result = self._evaluate_pedagogy(
                    transcript=transcript,
                    video_metadata=video_metadata
                )
                logger.info(f"    [✅ 完成] 教学质量分数: {result['score']:.1f}")
                return ('pedagogy', result)

            def evaluate_metadata():
                logger.info(f"[📊 启动] 热度/元数据评估 (权重: {metadata_weight_pct:.0f}%)")
                result = self._evaluate_metadata(video_metadata)
                logger.info(f"    [✅ 完成] 热度分数: {result['score']:.1f}")
                return ('metadata', result)

            # 使用线程池并行执行4个评估任务
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                # 提交所有任务
                future_to_dim = {
                    executor.submit(evaluate_visual): 'visual',
                    executor.submit(evaluate_relevance): 'relevance',
                    executor.submit(evaluate_pedagogy): 'pedagogy',
                    executor.submit(evaluate_metadata): 'metadata'
                }

                # 收集结果
                evaluation_results = {}
                for future in concurrent.futures.as_completed(future_to_dim):
                    dim = future_to_dim[future]
                    try:
                        dim_name, result = future.result()
                        evaluation_results[dim_name] = result
                        result[dim] = result  # 同时保存到主result字典
                    except Exception as e:
                        logger.error(f"    [❌ 失败] {dim} 评估出错: {str(e)}")
                        # 使用默认值
                        if dim == 'visual':
                            evaluation_results[dim] = {
                                'tech_score': 0.0,
                                'design_score': 0.0,
                                'combined_score': 0.0
                            }
                        elif dim == 'relevance':
                            evaluation_results[dim] = {'score': 0.0}
                        elif dim == 'pedagogy':
                            evaluation_results[dim] = {'score': 0.0}
                        elif dim == 'metadata':
                            evaluation_results[dim] = {'score': 0.0}

            logger.info(f"[🎉 完成] 所有4个评估维度并行执行完毕！\n")
            
            # 计算总分（加权平均）
            weights = result["breakdown"]
            overall_score = (
                visual_result["combined_score"] * weights["visual_weight"] +
                relevance_result["score"] * weights["relevance_weight"] +
                pedagogy_result["score"] * weights["pedagogy_weight"] +
                metadata_result["score"] * weights["metadata_weight"]
            )
            result["overall_score"] = round(overall_score, 2)
            
            logger.info(f"\n{'='*80}")
            logger.info(f"🎉 评估完成")
            logger.info(f"{'='*80}")
            logger.info(f"总分: {result['overall_score']:.2f}/10")
            logger.info(f"  视觉质量: {visual_result['combined_score']:.2f} (权重{visual_weight_pct:.0f}%)")
            logger.info(f"  内容相关度: {relevance_result['score']:.2f} (权重{relevance_weight_pct:.0f}%)")
            logger.info(f"  教学质量: {pedagogy_result['score']:.2f} (权重{pedagogy_weight_pct:.0f}%)")
            logger.info(f"  热度/元数据: {metadata_result['score']:.2f} (权重{metadata_weight_pct:.0f}%)")
            logger.info(f"{'='*80}\n")
            
        except Exception as e:
            logger.error(f"❌ 评估失败: {str(e)}", exc_info=True)
            result["error"] = str(e)
        
        # 收集Token使用情况（如果可用）
        token_usage_summary = {}
        
        # 视觉分析的Token（如果可用）
        if "visual_quality" in result and "token_usage" in result["visual_quality"]:
            token_usage_summary["visual_analysis"] = result["visual_quality"]["token_usage"]
        
        # 将Token汇总添加到结果中
        if token_usage_summary:
            result["token_usage"] = token_usage_summary
        
        # 将匹配的知识点添加到结果中（如果存在）
        if knowledge_point:
            result["matched_knowledge_point"] = knowledge_point
        
        return result
    
    def _evaluate_visual_quality(
        self,
        video_metadata: Dict[str, Any],
        frames_paths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        评估视觉质量
        
        1. 硬指标（Tech Score）：基于 max_resolution_height
        2. 软指标（Design Score）：Vision AI 分析关键帧
        
        Returns:
            {
                "tech_score": float,
                "design_score": float,
                "combined_score": float,
                "details": str
            }
        """
        result = {
            "tech_score": 0.0,
            "design_score": 0.0,
            "combined_score": 0.0,
            "details": ""
        }
        
        # 1. 硬指标评分（基于 max_resolution_height）
        max_resolution_height = video_metadata.get('max_resolution_height', 0)
        logger.info(f"    [📺 硬指标] 最大分辨率高度: {max_resolution_height}p")
        
        if max_resolution_height >= 1080:
            tech_score = 10.0
            tech_detail = f"支持1080p及以上 ({max_resolution_height}p)"
        elif max_resolution_height >= 720:
            tech_score = 8.0
            tech_detail = f"支持720p ({max_resolution_height}p)"
        elif max_resolution_height >= 480:
            tech_score = 5.0
            tech_detail = f"支持480p ({max_resolution_height}p)"
        else:
            tech_score = 2.0
            tech_detail = f"分辨率较低 ({max_resolution_height}p)"
        
        result["tech_score"] = tech_score
        logger.info(f"    [✅ 硬指标] 分数: {tech_score:.1f}/10 - {tech_detail}")
        
        # 2. 软指标评分（Vision AI 分析）
        design_score = 0.0
        design_detail = ""
        
        if frames_paths and len(frames_paths) > 0:
            logger.info(f"    [👁️ 软指标] 开始Vision AI分析，关键帧数量: {len(frames_paths)}")
            try:
                design_result = self._analyze_frame_design(frames_paths)
                design_score = design_result.get("score", 0.0)
                design_detail = design_result.get("details", "")
                logger.info(f"    [✅ 软指标] Vision AI分数: {design_score:.1f}/10")
            except Exception as e:
                logger.warning(f"    [⚠️ 警告] Vision AI分析失败: {str(e)}")
                design_score = 5.0  # 默认中等分数
                design_detail = "Vision AI分析失败，使用默认分数"
        else:
            logger.warning(f"    [⚠️ 警告] 无关键帧数据，跳过Vision AI分析")
            design_score = 5.0  # 默认中等分数
            design_detail = "无关键帧数据，使用默认分数"
        
        result["design_score"] = design_score
        result["details"] = f"硬指标: {tech_detail}; 软指标: {design_detail}"
        
        # 合并分数（硬指标60%，软指标40%）
        combined_score = tech_score * 0.6 + design_score * 0.4
        result["combined_score"] = round(combined_score, 2)
        
        logger.info(f"    [📊 合并] 硬指标({tech_score:.1f}) × 60% + 软指标({design_score:.1f}) × 40% = {combined_score:.2f}")
        
        return result
    
    def _analyze_frame_design(self, frames_paths: List[str]) -> Dict[str, Any]:
        """
        使用Vision AI分析关键帧的设计质量
        
        Args:
            frames_paths: 关键帧文件路径列表
        
        Returns:
            {
                "score": float,
                "details": str
            }
        """
        logger.info(f"        [🔍 Vision AI] 分析 {len(frames_paths)} 张关键帧...")
        
        # 构建Prompt
        system_prompt = """你是一个教育视频质量评估专家，专门评估教学可视化的设计质量。

**重要说明**：
我将提供视频的截图。请注意，这些截图来自低分辨率版本，**请忽略压缩噪点和像素模糊**。
请专注于评估**教学可视化的设计质量**：

1. **板书/PPT排版**：是否拥挤？是否清晰易读？
2. **字体大小**：在移动端是否易读？
3. **视觉辅助**：是否使用了图表、动画等辅助理解？
4. **教师位置**：老师是否一直遮挡板书？
5. **色彩对比**：文字与背景对比度是否足够？
6. **内容组织**：信息层次是否清晰？

请给出0-10分的评分，并提供简短的评估理由。"""
        
        user_prompt = f"""请分析以下教学视频的关键帧（共{len(frames_paths)}张），评估其教学可视化设计质量。

**评估要求**：
1. 忽略低分辨率造成的像素模糊
2. 专注于评估教学设计的质量
3. 给出0-10分的评分
4. 提供简短的评估理由

请以JSON格式返回：
{{
    "score": 7.5,
    "details": "板书清晰，但配色单调，缺少图表辅助"
}}"""
        
        # 如果 VisionClient 可用，使用真正的视觉分析
        if self.vision_client:
            try:
                logger.info(f"        [👁️ 使用视觉API] 发送 {len(frames_paths)} 张图片进行分析...")
                
                # 限制图片数量（避免请求过大）
                frames_to_analyze = frames_paths[:6]  # 最多分析6张
                
                # 记录开始时间
                import time
                start_time = time.time()

                # 调用视觉API
                result = self.vision_client.analyze_images(
                    image_paths=frames_to_analyze,
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    model="gemini-2.5-pro",  # 使用高质量多模态模型（性价比高）
                    max_tokens=500,
                    temperature=0.3
                )

                # 计算执行时间
                execution_time = time.time() - start_time

                if result["success"]:
                    response_text = result["response"]

                    # ✅ 新增：记录视觉模型调用到日志收集器
                    if self.log_collector:
                        try:
                            # 构建输入信息摘要
                            input_summary = f"分析了 {len(frames_to_analyze)} 张视频截图"
                            if frames_paths:
                                input_summary += f"\n图片路径: {frames_paths[0]}"
                                if len(frames_paths) > 1:
                                    input_summary += f" 等{len(frames_to_analyze)}张"

                            # 截取输出结果（限制长度）
                            output_summary = response_text[:500] + "..." if len(response_text) > 500 else response_text

                            # 记录LLM调用
                            self.log_collector.record_llm_call(
                                model_name="gemini-2.5-pro (Vision)",
                                function="视频视觉评估",
                                provider="Internal API",
                                prompt=user_prompt[:200] + "..." if len(user_prompt) > 200 else user_prompt,
                                input_data=input_summary,
                                output_data=output_summary,
                                execution_time=execution_time,
                                tokens_used=None,  # Vision API暂未返回token数
                                cost=None
                            )
                            logger.info("        [📝 日志] 视觉模型调用已记录到搜索日志")
                        except Exception as log_err:
                            logger.warning(f"        [⚠️ 警告] 记录视觉模型调用失败: {log_err}")

                    # 保存 token 使用情况（如果可用）
                    usage = result.get("usage")
                    if usage:
                        # 将 usage 存储到结果中，供外部访问
                        logger.info(f"        [📊 Token] 视觉API: {usage.get('total_tokens', 'N/A')} tokens")
                    
                    # 解析响应
                    data = extract_json_object(response_text)
                    if data:
                        score = float(data.get("score", 5.0))
                        details = data.get("details", "")
                        logger.info(f"        [✅ Vision AI] 分析成功，分数: {score:.1f}/10")
                        result_dict = {
                            "score": max(0, min(10, score)),  # 限制在0-10范围
                            "details": details
                        }
                        # 添加 usage 信息
                        if usage:
                            result_dict["token_usage"] = usage
                        return result_dict
                    else:
                        logger.warning(f"        [⚠️ 警告] 无法解析Vision AI响应")
                        logger.debug(f"        响应内容: {response_text[:200]}")
                        return {
                            "score": 5.0,
                            "details": "Vision AI响应解析失败"
                        }
                else:
                    error_msg = result.get("error", "未知错误")
                    logger.error(f"        [❌ 错误] Vision API调用失败: {error_msg}")
                    # 降级到文本模拟
                    logger.info(f"        [⚠️ 降级] 使用文本模拟分析")
                    return self._analyze_frame_design_fallback(frames_paths)
            
            except Exception as e:
                logger.error(f"        [❌ 错误] Vision AI分析异常: {str(e)}")
                import traceback
                traceback.print_exc()
                # 降级到文本模拟
                logger.info(f"        [⚠️ 降级] 使用文本模拟分析")
                return self._analyze_frame_design_fallback(frames_paths)
        
        # 如果没有 VisionClient，使用文本模拟（降级方案）
        return self._analyze_frame_design_fallback(frames_paths)
    
    def _analyze_frame_design_fallback(self, frames_paths: List[str]) -> Dict[str, Any]:
        """
        文本模拟视觉分析（降级方案）
        
        Args:
            frames_paths: 关键帧文件路径列表
        
        Returns:
            {
                "score": float,
                "details": str
            }
        """
        logger.info(f"        [📝 文本模拟] 使用文本描述模拟视觉分析...")
        
        system_prompt = """你是一个教育视频质量评估专家，专门评估教学可视化的设计质量。

**重要说明**：
我将提供视频的截图路径。请注意，这些截图来自低分辨率版本，**请忽略压缩噪点和像素模糊**。
请专注于评估**教学可视化的设计质量**：

1. **板书/PPT排版**：是否拥挤？是否清晰易读？
2. **字体大小**：在移动端是否易读？
3. **视觉辅助**：是否使用了图表、动画等辅助理解？
4. **教师位置**：老师是否一直遮挡板书？
5. **色彩对比**：文字与背景对比度是否足够？
6. **内容组织**：信息层次是否清晰？

请给出0-10分的评分，并提供简短的评估理由。"""
        
        user_prompt = f"""请分析以下教学视频的关键帧（共{len(frames_paths)}张），评估其教学可视化设计质量。

**关键帧路径**：
{chr(10).join(f"- {path}" for path in frames_paths[:6])}

**评估要求**：
1. 忽略低分辨率造成的像素模糊
2. 专注于评估教学设计的质量
3. 给出0-10分的评分
4. 提供简短的评估理由

请以JSON格式返回：
{{
    "score": 7.5,
    "details": "板书清晰，但配色单调，缺少图表辅助"
}}"""
        
        try:
            # 调用LLM（文本模拟）
            response = self.client.call_llm(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=500,
                temperature=0.3,
                model="deepseek"
            )
            
            # 解析响应
            data = extract_json_object(response)
            if data:
                score = float(data.get("score", 5.0))
                details = data.get("details", "")
                return {
                    "score": max(0, min(10, score)),  # 限制在0-10范围
                    "details": details
                }
            else:
                logger.warning(f"        [⚠️ 警告] 无法解析Vision AI响应")
                return {
                    "score": 5.0,
                    "details": "Vision AI响应解析失败"
                }
        
        except Exception as e:
            logger.error(f"        [❌ 错误] Vision AI分析失败: {str(e)}")
            return {
                "score": 5.0,
                "details": f"Vision AI分析失败: {str(e)}"
            }
    
    def _evaluate_relevance(
        self,
        transcript: Optional[str],
        knowledge_point: Optional[Dict[str, Any]],
        video_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        评估内容相关度
        
        Args:
            transcript: 字幕/转录文本
            knowledge_point: 知识点信息（包含 learning_objective）
            video_metadata: 视频元数据
        
        Returns:
            {
                "score": float,
                "details": str
            }
        """
        result = {
            "score": 0.0,
            "details": ""
        }
        
        if not transcript:
            logger.warning(f"    [⚠️ 警告] 无字幕/转录文本，无法评估相关度")
            result["score"] = 0.0
            result["details"] = "无字幕/转录文本"
            return result
        
        if not knowledge_point:
            logger.warning(f"    [⚠️ 警告] 无知识点信息，无法评估相关度")
            result["score"] = 5.0  # 默认中等分数
            result["details"] = "无知识点信息，使用默认分数"
            return result
        
        learning_objective = knowledge_point.get('learning_objective', '')
        topic_title = knowledge_point.get('topic_title_id', '') or knowledge_point.get('topic_title_cn', '')
        
        logger.info(f"    [📚 知识点] 主题: {topic_title}")
        logger.info(f"    [📚 知识点] 学习目标: {learning_objective[:100]}...")
        logger.info(f"    [📝 字幕] 长度: {len(transcript)} 字符")
        
        system_prompt = """你是一个JSON输出机器。你的唯一任务是返回JSON格式的评估结果。

**严格规则**：
1. 只能返回JSON对象，格式：{"score": 数字, "details": "字符串"}
2. 禁止返回任何其他文本、解释、Markdown、代码块标记
3. 禁止在JSON前后添加任何文字
4. 如果违反规则，输出将被视为无效

**评估标准**：
1. 视频内容是否直接讲解目标知识点？
2. 是否覆盖了学习目标中提到的所有关键概念？
3. 是否有无关内容或偏离主题？
4. 内容深度是否适合目标年级？

**输出格式示例**：
{"score": 8.5, "details": "评估理由"}"""
        
        user_prompt = f"""{{"score": 8.5, "details": "评估理由"}}

评估视频内容与学习目标的匹配度。

学习目标：{learning_objective}
知识点主题：{topic_title}
视频字幕（前2000字符）：{transcript[:2000]}

**重要**：只返回JSON对象，不要添加任何解释文字。格式：{{"score": 数字, "details": "字符串"}}"""
        
        try:
            response = self.client.call_llm(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=300,  # 减少token限制，强制简洁
                temperature=0.1,  # 进一步降低温度，提高确定性
                model="grok-4-fast"  # 使用Grok模型，结构化输出更可靠
            )
            
            # 记录原始响应（用于调试）
            logger.debug(f"    [📝 原始响应] 长度: {len(response)} 字符")
            logger.debug(f"    [📝 原始响应] 前500字符: {response[:500]}")
            
            data = extract_json_object(response)
            if data:
                score = float(data.get("score", 5.0))
                details = data.get("details", "")
                result["score"] = max(0, min(10, score))
                result["details"] = details
            else:
                logger.warning(f"    [⚠️ 警告] 无法解析相关度评估响应")
                result["score"] = 5.0
                result["details"] = "相关度评估响应解析失败"
        
        except Exception as e:
            logger.error(f"    [❌ 错误] 相关度评估失败: {str(e)}")
            result["score"] = 5.0
            result["details"] = f"相关度评估失败: {str(e)}"
        
        return result
    
    def _evaluate_pedagogy(
        self,
        transcript: Optional[str],
        video_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        评估教学质量
        
        Args:
            transcript: 字幕/转录文本
            video_metadata: 视频元数据
        
        Returns:
            {
                "score": float,
                "details": str
            }
        """
        result = {
            "score": 0.0,
            "details": ""
        }
        
        if not transcript:
            logger.warning(f"    [⚠️ 警告] 无字幕/转录文本，无法评估教学质量")
            result["score"] = 0.0
            result["details"] = "无字幕/转录文本"
            return result
        
        logger.info(f"    [📝 字幕] 长度: {len(transcript)} 字符")
        
        system_prompt = """你是一个JSON输出机器。你的唯一任务是返回JSON格式的评估结果。

**严格规则**：
1. 只能返回JSON对象，格式：{"score": 数字, "details": "字符串"}
2. 禁止返回任何其他文本、解释、Markdown、代码块标记
3. 禁止在JSON前后添加任何文字
4. 如果违反规则，输出将被视为无效

**评估维度**：
1. 讲解逻辑：是否有清晰的引入->概念->例子->总结结构？
2. 语速：是否适合目标学生？
3. 引导性提问：是否有适当的提问？
4. 重点强调：是否突出了关键概念？
5. 互动性：是否有适当的互动元素？

**输出格式示例**：
{"score": 7.5, "details": "评估理由"}"""
        
        user_prompt = f"""{{"score": 7.5, "details": "评估理由"}}

评估教学视频的教学质量。

视频字幕（前2000字符）：{transcript[:2000]}

**重要**：只返回JSON对象，不要添加任何解释文字。格式：{{"score": 数字, "details": "字符串"}}"""
        
        try:
            response = self.client.call_llm(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=300,  # 减少token限制，强制简洁
                temperature=0.1,  # 进一步降低温度，提高确定性
                model="grok-4-fast"  # 使用Grok模型，结构化输出更可靠
            )
            
            # 记录原始响应（用于调试）
            logger.debug(f"    [📝 原始响应] 长度: {len(response)} 字符")
            logger.debug(f"    [📝 原始响应] 前500字符: {response[:500]}")
            
            data = extract_json_object(response)
            if data:
                score = float(data.get("score", 5.0))
                details_raw = data.get("details", "")
                
                # 处理details可能是对象的情况（LLM返回结构化数据）
                if isinstance(details_raw, dict):
                    # 将对象转换为格式化的字符串
                    details_parts = []
                    for key, value in details_raw.items():
                        details_parts.append(f"{key}: {value}")
                    details = " | ".join(details_parts)
                elif isinstance(details_raw, str):
                    details = details_raw
                else:
                    details = str(details_raw) if details_raw else "无详细评估"
                
                result["score"] = max(0, min(10, score))
                result["details"] = details
                logger.info(f"    [✅ 解析成功] 分数: {score:.1f}, details类型: {type(details_raw).__name__}")
            else:
                logger.warning(f"    [⚠️ 警告] 无法解析教学质量评估响应")
                logger.warning(f"    [⚠️ 原始响应] {response[:1000]}")
                result["score"] = 5.0
                result["details"] = f"教学质量评估响应解析失败。原始响应: {response[:200]}..."
        
        except Exception as e:
            logger.error(f"    [❌ 错误] 教学质量评估失败: {str(e)}")
            result["score"] = 5.0
            result["details"] = f"教学质量评估失败: {str(e)}"
        
        return result
    
    def _evaluate_metadata(self, video_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估热度/元数据
        
        基于 view_count 和 like_count 计算归一化分数
        
        Returns:
            {
                "score": float,
                "details": str
            }
        """
        result = {
            "score": 0.0,
            "details": ""
        }
        
        view_count = video_metadata.get('view_count', 0)
        like_count = video_metadata.get('like_count', 0)
        
        logger.info(f"    [📊 元数据] 观看次数: {view_count:,}, 点赞数: {like_count:,}")
        
        # 归一化评分（基于经验阈值）
        # 观看次数评分（0-5分）
        if view_count >= 1000000:
            view_score = 5.0
        elif view_count >= 500000:
            view_score = 4.0
        elif view_count >= 100000:
            view_score = 3.0
        elif view_count >= 10000:
            view_score = 2.0
        elif view_count >= 1000:
            view_score = 1.0
        else:
            view_score = 0.5
        
        # 点赞率评分（0-5分）
        # 先初始化 like_ratio，避免未定义错误
        like_ratio = 0.0
        like_score = 0.0
        
        if view_count > 0:
            like_ratio = like_count / view_count
            if like_ratio >= 0.05:  # 5%以上点赞率
                like_score = 5.0
            elif like_ratio >= 0.03:  # 3%以上
                like_score = 4.0
            elif like_ratio >= 0.02:  # 2%以上
                like_score = 3.0
            elif like_ratio >= 0.01:  # 1%以上
                like_score = 2.0
            else:
                like_score = 1.0
        # else: view_count <= 0 时，like_ratio 和 like_score 保持初始值 0.0
        
        # 合并分数（观看次数60%，点赞率40%）
        metadata_score = view_score * 0.6 + like_score * 0.4
        result["score"] = round(metadata_score, 2)
        result["details"] = f"观看次数: {view_count:,} (得分{view_score:.1f}), 点赞率: {like_ratio*100:.2f}% (得分{like_score:.1f})"
        
        logger.info(f"    [📊 计算] 观看次数得分: {view_score:.1f}, 点赞率得分: {like_score:.1f}")
        logger.info(f"    [📊 合并] {view_score:.1f} × 60% + {like_score:.1f} × 40% = {metadata_score:.2f}")
        
        return result

