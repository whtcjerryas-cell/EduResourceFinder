#!/usr/bin/env python3
"""
知识点概览服务 - 处理知识点概览相关业务逻辑
"""

import os
import json
import re
from typing import Dict, List, Tuple, Optional
from flask import jsonify
from utils.logger_utils import get_logger
from utils.error_handling import ValidationError, NotFoundError

logger = get_logger('knowledge_overview_service')


class KnowledgeOverviewService:
    """知识点概览服务类"""

    def __init__(self):
        """初始化服务"""
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.evaluations_dir = os.path.join(self.base_dir, 'data', 'evaluations')
        self.knowledge_points_dir = os.path.join(
            self.base_dir,
            'data', 'knowledge_points', 'Knowledge Point'
        )

    def get_overview(self, country: str, grade: str, subject: str) -> Tuple[dict, int]:
        """
        获取知识点概览数据

        Args:
            country: 国家代码（如 "ID"）
            grade: 年级（如 "Kelas 1", "1"）
            subject: 学科（如 "Matematika", "数学"）

        Returns:
            (响应字典, HTTP状态码)
        """
        try:
            # 1. 验证参数
            self._validate_params(country, grade, subject)

            logger.info(f"[📊 知识点概览] 收到请求: country={country}, grade={grade}, subject={subject}")

            # 2. 加载知识点数据
            knowledge_points = self._load_knowledge_points(grade, subject)

            # 3. 加载评估记录
            evaluations = self._load_evaluations(country, grade, subject)

            # 4. 匹配视频到知识点
            knowledge_point_videos = self._match_videos_to_knowledge_points(evaluations)

            # 5. 构建返回数据并计算统计
            result_knowledge_points = self._build_result_with_statistics(
                knowledge_points,
                knowledge_point_videos
            )

            # 6. 排序结果
            result_knowledge_points = self._sort_results(result_knowledge_points)

            logger.info(f"[📊 知识点概览] 返回 {len(result_knowledge_points)} 个知识点")

            return {
                "success": True,
                "knowledge_points": result_knowledge_points,
                "total_knowledge_points": len(result_knowledge_points),
                "total_videos": sum(kp['video_count'] for kp in result_knowledge_points)
            }, 200

        except (ValidationError, NotFoundError) as e:
            return {
                "success": False,
                "message": str(e),
                "knowledge_points": []
            }, e.status_code
        except Exception as e:
            logger.error(f"获取知识点概览失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": str(e),
                "knowledge_points": []
            }, 500

    def _validate_params(self, country: str, grade: str, subject: str) -> None:
        """
        验证参数

        Args:
            country: 国家代码
            grade: 年级
            subject: 学科

        Raises:
            ValidationError: 参数验证失败
        """
        if not country or not grade or not subject:
            raise ValidationError("请提供国家、年级和学科参数")

    def _load_knowledge_points(self, grade: str, subject: str) -> List[dict]:
        """
        加载知识点数据

        Args:
            grade: 年级
            subject: 学科

        Returns:
            知识点列表

        Raises:
            ValidationError: 无法匹配年级或学科
            NotFoundError: 知识点文件不存在
        """
        # 匹配年级到文件后缀
        grade_suffix = self._match_grade_to_knowledge_file(grade)
        if not grade_suffix:
            raise ValidationError(f"无法匹配年级: {grade}")

        # 确定文件名
        if 'matematika' in subject.lower() or '数学' in subject or 'math' in subject.lower():
            filename = f"5. Final Panduan Mata Pelajaran Matematika_{grade_suffix}.json"
        else:
            raise ValidationError(f"暂不支持学科: {subject}")

        # 加载文件
        filepath = os.path.join(self.knowledge_points_dir, filename)
        if not os.path.exists(filepath):
            raise NotFoundError(f"知识点文件不存在: {filename}")

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data.get('knowledge_points', [])

    def _match_grade_to_knowledge_file(self, grade: str) -> str:
        """
        匹配年级到知识点文件名后缀

        Args:
            grade: 年级字符串（如 "Kelas 1", "1", "Kelas 4"）

        Returns:
            文件名后缀（如 "kelas1-2", "kelas3-4"），如果无法匹配则返回空字符串
        """
        grade_lower = grade.lower().strip()

        # 提取数字
        numbers = re.findall(r'\d+', grade_lower)

        if numbers:
            grade_num = int(numbers[0])
            # 映射到文件名后缀
            if grade_num <= 2:
                return "kelas1-2"
            elif grade_num <= 4:
                return "kelas3-4"
            elif grade_num <= 6:
                return "kelas5-6"

        return ""

    def _load_evaluations(
        self,
        country: str,
        grade: str,
        subject: str
    ) -> Dict[str, dict]:
        """
        加载评估记录，每个视频URL只保留最新的一条（全局去重）

        Args:
            country: 国家代码
            grade: 年级
            subject: 学科

        Returns:
            {video_url: video_info} 字典
        """
        video_url_latest = {}

        if os.path.exists(self.evaluations_dir):
            for filename in os.listdir(self.evaluations_dir):
                if filename.startswith('evaluation_') and filename.endswith('.json'):
                    filepath = os.path.join(self.evaluations_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            eval_data = json.load(f)

                        # 检查是否匹配当前筛选条件
                        search_params = eval_data.get('search_params', {})
                        if (search_params.get('country') == country and
                            search_params.get('grade') == grade and
                            search_params.get('subject') == subject):

                            # 提取匹配的知识点
                            matched_kp = eval_data.get('matched_knowledge_point')
                            if not matched_kp:
                                evaluation = eval_data.get('evaluation', {})
                                matched_kp = evaluation.get('matched_knowledge_point')

                            if matched_kp:
                                kp_id = matched_kp.get('id')
                                video_url = eval_data.get('video_url', '')

                                if kp_id and video_url:
                                    video_info = self._extract_video_info(
                                        eval_data,
                                        kp_id
                                    )

                                    # 全局去重：每个视频URL只保留最新的一条评价记录
                                    if video_url in video_url_latest:
                                        existing_timestamp = video_url_latest[video_url].get('evaluation_date', '')
                                        if video_info['evaluation_date'] > existing_timestamp:
                                            video_url_latest[video_url] = video_info
                                    else:
                                        video_url_latest[video_url] = video_info
                    except Exception as e:
                        logger.warning(f"读取评估文件失败 {filename}: {str(e)}")
                        continue

        return video_url_latest

    def _extract_video_info(self, eval_data: dict, kp_id: str) -> dict:
        """
        从评估数据中提取视频信息

        Args:
            eval_data: 评估数据
            kp_id: 知识点ID

        Returns:
            视频信息字典
        """
        video_metadata = eval_data.get('video_metadata', {})
        evaluation = eval_data.get('evaluation', {})
        timestamp = eval_data.get('timestamp', '')

        return {
            "video_url": eval_data.get('video_url', ''),
            "video_title": video_metadata.get('title', '未知标题'),
            "overall_score": evaluation.get('overall_score', 0.0),
            "evaluation_date": timestamp,
            "request_id": eval_data.get('request_id', ''),
            "visual_quality": evaluation.get('visual_quality', {}).get('combined_score', 0.0),
            "relevance": evaluation.get('relevance', {}).get('score', 0.0),
            "pedagogy": evaluation.get('pedagogy', {}).get('score', 0.0),
            "metadata": evaluation.get('metadata', {}).get('score', 0.0),
            "visual_quality_details": evaluation.get('visual_quality', {}).get('details', ''),
            "relevance_details": evaluation.get('relevance', {}).get('details', ''),
            "pedagogy_details": evaluation.get('pedagogy', {}).get('details', ''),
            "metadata_details": evaluation.get('metadata', {}).get('details', ''),
            "kp_id": kp_id
        }

    def _match_videos_to_knowledge_points(self, video_url_latest: Dict[str, dict]) -> Dict[str, List[dict]]:
        """
        将去重后的视频信息按知识点分组

        Args:
            video_url_latest: {video_url: video_info} 字典

        Returns:
            {knowledge_point_id: [video_info, ...]} 字典
        """
        knowledge_point_videos = {}

        # 将去重后的视频信息按知识点分组
        for video_url, video_info in video_url_latest.items():
            kp_id = video_info.get('kp_id')
            if kp_id:
                if kp_id not in knowledge_point_videos:
                    knowledge_point_videos[kp_id] = []
                # 移除kp_id字段，避免在返回数据中重复
                video_info_clean = {k: v for k, v in video_info.items() if k != 'kp_id'}
                knowledge_point_videos[kp_id].append(video_info_clean)

        return knowledge_point_videos

    def _build_result_with_statistics(
        self,
        knowledge_points: List[dict],
        knowledge_point_videos: Dict[str, List[dict]]
    ) -> List[dict]:
        """
        构建返回数据并计算统计信息

        Args:
            knowledge_points: 知识点列表
            knowledge_point_videos: {kp_id: [videos]} 字典

        Returns:
            带统计信息的知识点列表
        """
        result_knowledge_points = []

        for kp in knowledge_points:
            kp_id = kp.get('id')
            videos = knowledge_point_videos.get(kp_id, [])

            # 计算平均分
            avg_score = 0.0
            if videos:
                scores = [v['overall_score'] for v in videos]
                avg_score = sum(scores) / len(scores)

            # 计算资源丰富程度分数
            resource_richness_score = self._calculate_resource_richness_score(
                len(videos),
                avg_score
            )

            result_knowledge_points.append({
                "id": kp_id,
                "topic_title_cn": kp.get('topic_title_cn', ''),
                "topic_title_id": kp.get('topic_title_id', ''),
                "chapter_title": kp.get('chapter_title', ''),
                "learning_objective": kp.get('learning_objective', ''),
                "videos": videos,
                "resource_richness_score": round(resource_richness_score, 2),
                "video_count": len(videos),
                "average_score": round(avg_score, 2),
                "learning_materials_count": 0,  # 远期功能
                "practice_questions_count": 0   # 远期功能
            })

        return result_knowledge_points

    def _calculate_resource_richness_score(
        self,
        video_count: int,
        avg_score: float
    ) -> float:
        """
        计算资源丰富程度分数

        公式：视频数量权重(30%) + 平均分权重(40%) + 学习资料数量权重(15%) + 练习题数量权重(15%)

        Args:
            video_count: 视频数量
            avg_score: 平均分

        Returns:
            资源丰富程度分数
        """
        # 视频数量分数：min(视频数量 / 5, 1.0) * 10（最多5个视频得满分）
        video_count_score = min(video_count / 5.0, 1.0) * 10

        # 平均分：直接使用（0-10分）
        avg_score_normalized = avg_score

        # 学习资料和练习题（远期功能，暂时为0）
        learning_materials_count = 0
        practice_questions_count = 0
        materials_score = min(learning_materials_count / 3.0, 1.0) * 10  # 最多3个资料得满分
        practice_score = min(practice_questions_count / 50.0, 1.0) * 10  # 最多50道题得满分

        # 资源丰富程度总分
        return (
            video_count_score * 0.3 +
            avg_score_normalized * 0.4 +
            materials_score * 0.15 +
            practice_score * 0.15
        )

    def _sort_results(self, result_knowledge_points: List[dict]) -> List[dict]:
        """
        排序结果

        Args:
            result_knowledge_points: 知识点列表

        Returns:
            排序后的知识点列表
        """
        # 按资源丰富程度分数排序（降序）
        result_knowledge_points.sort(
            key=lambda x: x['resource_richness_score'],
            reverse=True
        )

        # 对每个知识点的视频按分数从高到低排序
        for kp in result_knowledge_points:
            kp['videos'].sort(key=lambda x: x['overall_score'], reverse=True)

        return result_knowledge_points
