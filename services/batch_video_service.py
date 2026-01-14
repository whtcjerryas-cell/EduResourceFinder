#!/usr/bin/env python3
"""
批量视频评估服务 - 处理批量视频评估相关业务逻辑
"""

import os
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
from flask import jsonify
from logger_utils import get_logger
from utils.error_handling import ValidationError, ServiceUnavailableError

logger = get_logger('batch_video_service')


class BatchVideoService:
    """批量视频评估服务类"""

    def __init__(self, video_crawler, video_evaluator, playlist_processor=None):
        """
        初始化服务

        Args:
            video_crawler: 视频爬虫实例
            video_evaluator: 视频评估器实例
            playlist_processor: 播放列表处理器实例（可选）
        """
        self.video_crawler = video_crawler
        self.video_evaluator = video_evaluator
        self.playlist_processor = playlist_processor
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.evaluations_dir = os.path.join(self.base_dir, 'data', 'evaluations')
        self.knowledge_points_dir = os.path.join(
            self.base_dir,
            'data', 'knowledge_points', 'Knowledge Point'
        )

    def batch_evaluate(self, request_data: dict) -> Tuple[dict, int]:
        """
        批量评估视频

        Args:
            request_data: 请求数据字典
                - results: 搜索结果列表
                - country: 国家代码
                - grade: 年级
                - subject: 学科
                - max_videos_per_playlist: 每个播放列表最大视频数
                - max_total_videos: 总视频数上限
                - preferred_languages: 首选语言列表

        Returns:
            (响应字典, HTTP状态码)
        """
        try:
            # 1. 验证和提取参数
            params = self._extract_and_validate_params(request_data)

            # 2. 提取视频URL列表（处理播放列表）
            video_urls = self._extract_video_urls(
                params['results'],
                params['max_videos_per_playlist'],
                params['max_total_videos']
            )

            if not video_urls:
                return {
                    "success": False,
                    "message": "没有找到可评估的视频"
                }, 400

            # 3. 加载知识点列表
            knowledge_points = self._load_knowledge_points(
                params['country'],
                params['grade'],
                params['subject']
            )

            # 4. 批量评估视频
            evaluation_results = self._batch_evaluate_videos(
                video_urls,
                knowledge_points,
                params
            )

            # 5. 格式化响应
            return self._format_response(evaluation_results)

        except (ValidationError, ServiceUnavailableError) as e:
            return {
                "success": False,
                "message": str(e)
            }, e.status_code
        except Exception as e:
            logger.error(f"批量评估失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": str(e)
            }, 500

    def _extract_and_validate_params(self, request_data: dict) -> dict:
        """
        提取和验证请求参数

        Args:
            request_data: 请求数据

        Returns:
            参数字典

        Raises:
            ValidationError: 参数验证失败
        """
        results = request_data.get('results', [])

        if not results:
            raise ValidationError("请提供要评估的结果列表")

        return {
            'results': results,
            'country': request_data.get('country', ''),
            'grade': request_data.get('grade', ''),
            'subject': request_data.get('subject', ''),
            'max_videos_per_playlist': request_data.get('max_videos_per_playlist', 3),
            'max_total_videos': request_data.get('max_total_videos', 10),
            'preferred_languages': request_data.get('preferred_languages', ['en', 'id', 'zh'])
        }

    def _extract_video_urls(
        self,
        results: List[dict],
        max_videos_per_playlist: int,
        max_total_videos: int
    ) -> List[dict]:
        """
        提取视频URL列表（处理播放列表）

        Args:
            results: 搜索结果列表
            max_videos_per_playlist: 每个播放列表最大视频数
            max_total_videos: 总视频数上限

        Returns:
            视频信息列表
        """
        video_urls = []

        for result in results:
            url = result.get('url', '')
            if not url:
                continue

            if self.playlist_processor and self.playlist_processor.is_playlist_url(url):
                # 提取播放列表中的视频
                playlist_result = self.playlist_processor.extract_videos_from_playlist(
                    url,
                    max_videos=max_videos_per_playlist
                )
                if playlist_result.get('success'):
                    for video in playlist_result.get('videos', [])[:max_videos_per_playlist]:
                        video_urls.append({
                            "url": video.get('url', ''),
                            "title": video.get('title', ''),
                            "source": "playlist",
                            "playlist_url": url
                        })
            else:
                video_urls.append({
                    "url": url,
                    "title": result.get('title', ''),
                    "source": "direct"
                })

            if len(video_urls) >= max_total_videos:
                break

        return video_urls

    def _load_knowledge_points(
        self,
        country: str,
        grade: str,
        subject: str
    ) -> Optional[List[dict]]:
        """
        加载知识点列表

        Args:
            country: 国家代码
            grade: 年级
            subject: 学科

        Returns:
            知识点列表，如果无法加载则返回None
        """
        if not (country and grade and subject):
            return None

        grade_suffix = self._match_grade_to_knowledge_file(grade)
        if not grade_suffix:
            return None

        if 'matematika' in subject.lower() or '数学' in subject or 'math' in subject.lower():
            filename = f"5. Final Panduan Mata Pelajaran Matematika_{grade_suffix}.json"
            filepath = os.path.join(self.knowledge_points_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    kp_data = json.load(f)
                return kp_data.get('knowledge_points', [])

        return None

    def _match_grade_to_knowledge_file(self, grade: str) -> str:
        """
        匹配年级到知识点文件名后缀

        Args:
            grade: 年级字符串（如 "Kelas 1", "1", "Kelas 4"）

        Returns:
            文件名后缀（如 "kelas1-2", "kelas3-4"），如果无法匹配则返回空字符串
        """
        import re
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

    def _batch_evaluate_videos(
        self,
        video_urls: List[dict],
        knowledge_points: Optional[List[dict]],
        params: dict
    ) -> dict:
        """
        批量评估视频

        Args:
            video_urls: 视频URL列表
            knowledge_points: 知识点列表
            params: 参数字典

        Returns:
            评估结果字典
        """
        evaluations = []
        successful_count = 0
        failed_count = 0
        total_tokens = 0

        for video_info in video_urls:
            try:
                result = self._evaluate_single_video(
                    video_info,
                    knowledge_points,
                    params
                )

                if result['success']:
                    successful_count += 1
                    total_tokens += result.get('token_usage', 0)
                else:
                    failed_count += 1

                evaluations.append(result['data'])

            except Exception as e:
                failed_count += 1
                logger.error(f"评估视频失败 {video_info.get('url', '')}: {str(e)}")
                evaluations.append({
                    "success": False,
                    "video_url": video_info.get('url', ''),
                    "error": str(e)
                })

        # 计算平均分
        scores = [
            e['evaluation']['overall_score']
            for e in evaluations
            if e.get('success') and e.get('evaluation')
        ]
        average_score = sum(scores) / len(scores) if scores else 0.0

        return {
            'evaluations': evaluations,
            'successful_count': successful_count,
            'failed_count': failed_count,
            'average_score': average_score,
            'total_videos': len(video_urls),
            'total_tokens': total_tokens
        }

    def _evaluate_single_video(
        self,
        video_info: dict,
        knowledge_points: Optional[List[dict]],
        params: dict
    ) -> dict:
        """
        评估单个视频

        Args:
            video_info: 视频信息
            knowledge_points: 知识点列表
            params: 参数字典

        Returns:
            {success: bool, data: dict, token_usage: int}
        """
        video_url = video_info['url']
        output_dir = './data/videos/analyzed'

        # 处理视频
        process_result = self.video_crawler.process_video(
            video_url=video_url,
            output_dir=output_dir,
            video_quality="480p",
            num_frames=6,
            extract_transcript=True,
            preferred_languages=params['preferred_languages']
        )

        if not process_result.get('success'):
            return {
                'success': False,
                'data': {
                    "success": False,
                    "video_url": video_url,
                    "error": process_result.get('error', '视频处理失败')
                },
                'token_usage': 0
            }

        # 匹配知识点
        matched_knowledge_point = None
        if knowledge_points:
            matched_knowledge_point = self.video_evaluator.match_knowledge_point(
                video_title=process_result['metadata'].get('title', ''),
                video_description=process_result['metadata'].get('description', ''),
                transcript=process_result.get('transcript'),
                knowledge_points=knowledge_points
            )

        # 评估视频
        evaluation = self.video_evaluator.evaluate_video_content(
            video_metadata=process_result['metadata'],
            video_path=process_result.get('video_path'),
            frames_paths=process_result.get('frames_paths', []),
            audio_path=process_result.get('audio_path'),
            transcript=process_result.get('transcript'),
            knowledge_point=matched_knowledge_point,
            knowledge_points=knowledge_points
        )

        # 收集Token使用情况
        token_usage = evaluation.get('token_usage', {}).get('total_tokens', 0)

        # 保存评估结果
        self._save_evaluation_result(
            video_url,
            process_result,
            evaluation,
            matched_knowledge_point,
            params
        )

        return {
            'success': True,
            'data': {
                "success": True,
                "video_url": video_url,
                "video_title": process_result['metadata'].get('title', ''),
                "evaluation": evaluation,
                "matched_knowledge_point": matched_knowledge_point
            },
            'token_usage': token_usage
        }

    def _save_evaluation_result(
        self,
        video_url: str,
        process_result: dict,
        evaluation: dict,
        matched_knowledge_point: Optional[dict],
        params: dict
    ) -> None:
        """
        保存评估结果到文件

        Args:
            video_url: 视频URL
            process_result: 视频处理结果
            evaluation: 评估结果
            matched_knowledge_point: 匹配的知识点
            params: 参数字典
        """
        os.makedirs(self.evaluations_dir, exist_ok=True)

        eval_request_id = str(uuid.uuid4())[:8]
        eval_data = {
            "request_id": eval_request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "video_url": video_url,
            "video_metadata": process_result['metadata'],
            "evaluation": evaluation,
            "matched_knowledge_point": matched_knowledge_point,
            "search_params": {
                "country": params['country'],
                "grade": params['grade'],
                "subject": params['subject']
            }
        }

        eval_file = os.path.join(self.evaluations_dir, f"evaluation_{eval_request_id}.json")
        with open(eval_file, 'w', encoding='utf-8') as f:
            json.dump(eval_data, f, ensure_ascii=False, indent=2)

    def _format_response(self, evaluation_results: dict) -> Tuple[dict, int]:
        """
        格式化响应

        Args:
            evaluation_results: 评估结果字典

        Returns:
            (响应字典, HTTP状态码)
        """
        return {
            "success": True,
            "request_id": str(uuid.uuid4())[:8],
            "total_videos": evaluation_results['total_videos'],
            "successful_count": evaluation_results['successful_count'],
            "failed_count": evaluation_results['failed_count'],
            "average_score": round(evaluation_results['average_score'], 2),
            "evaluations": evaluation_results['evaluations'],
            "token_usage_summary": {
                "total_tokens": evaluation_results['total_tokens']
            }
        }, 200
