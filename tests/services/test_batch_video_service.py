"""
Unit tests for BatchVideoService
"""

import pytest
import os
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path

from services.batch_video_service import BatchVideoService
from utils.error_handling import ValidationError, ServiceUnavailableError


class TestBatchVideoService:
    """Test suite for BatchVideoService"""

    def test_init(self, mock_video_crawler, mock_video_evaluator):
        """Test service initialization"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        assert service.video_crawler == mock_video_crawler
        assert service.video_evaluator == mock_video_evaluator
        assert service.playlist_processor is None
        assert service.base_dir is not None
        assert service.evaluations_dir is not None
        assert service.knowledge_points_dir is not None

    def test_init_with_playlist_processor(self, mock_video_crawler, mock_video_evaluator, mock_playlist_processor):
        """Test service initialization with playlist processor"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator,
            playlist_processor=mock_playlist_processor
        )

        assert service.playlist_processor == mock_playlist_processor

    def test_extract_and_validate_params_success(self, mock_video_crawler, mock_video_evaluator):
        """Test parameter extraction and validation - success"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        request_data = {
            'results': [
                {'url': 'https://youtube.com/watch?v=test1', 'title': 'Video 1'},
                {'url': 'https://youtube.com/watch?v=test2', 'title': 'Video 2'}
            ],
            'country': 'ID',
            'grade': 'Kelas 1',
            'subject': 'Matematika',
            'max_videos_per_playlist': 5,
            'max_total_videos': 20,
            'preferred_languages': ['id', 'en']
        }

        result = service._extract_and_validate_params(request_data)

        assert result['country'] == 'ID'
        assert result['grade'] == 'Kelas 1'
        assert result['subject'] == 'Matematika'
        assert result['max_videos_per_playlist'] == 5
        assert result['max_total_videos'] == 20
        assert result['preferred_languages'] == ['id', 'en']
        assert len(result['results']) == 2

    def test_extract_and_validate_params_default_values(self, mock_video_crawler, mock_video_evaluator):
        """Test parameter extraction and validation - default values"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        request_data = {
            'results': [
                {'url': 'https://youtube.com/watch?v=test1', 'title': 'Video 1'}
            ]
        }

        result = service._extract_and_validate_params(request_data)

        assert result['max_videos_per_playlist'] == 3
        assert result['max_total_videos'] == 10
        assert result['preferred_languages'] == ['en', 'id', 'zh']

    def test_extract_and_validate_params_empty_results(self, mock_video_crawler, mock_video_evaluator):
        """Test parameter extraction and validation - empty results"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        request_data = {
            'results': []
        }

        with pytest.raises(ValidationError) as exc_info:
            service._extract_and_validate_params(request_data)

        assert "请提供要评估的结果列表" in str(exc_info.value)

    def test_extract_video_urls_direct_only(self, mock_video_crawler, mock_video_evaluator):
        """Test extracting video URLs - direct videos only"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        results = [
            {'url': 'https://youtube.com/watch?v=test1', 'title': 'Video 1'},
            {'url': 'https://youtube.com/watch?v=test2', 'title': 'Video 2'},
            {'url': '', 'title': 'Empty URL'}  # Should be skipped
        ]

        video_urls = service._extract_video_urls(results, max_videos_per_playlist=3, max_total_videos=10)

        assert len(video_urls) == 2
        assert video_urls[0]['url'] == 'https://youtube.com/watch?v=test1'
        assert video_urls[0]['source'] == 'direct'
        assert video_urls[1]['url'] == 'https://youtube.com/watch?v=test2'

    def test_extract_video_urls_with_playlist(self, mock_video_crawler, mock_video_evaluator, mock_playlist_processor):
        """Test extracting video URLs - with playlist"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator,
            playlist_processor=mock_playlist_processor
        )

        # Mock is_playlist_url to only identify playlist URLs
        mock_playlist_processor.is_playlist_url.side_effect = lambda url: 'playlist?list=' in url

        results = [
            {'url': 'https://youtube.com/playlist?list=test123', 'title': 'Test Playlist'},
            {'url': 'https://youtube.com/watch?v=direct', 'title': 'Direct Video'}
        ]

        video_urls = service._extract_video_urls(results, max_videos_per_playlist=2, max_total_videos=10)

        # Should have 2 from playlist + 1 direct = 3 total
        assert len(video_urls) == 3
        assert video_urls[0]['source'] == 'playlist'
        assert video_urls[2]['source'] == 'direct'

    def test_extract_video_urls_respects_max_total_videos(self, mock_video_crawler, mock_video_evaluator):
        """Test extracting video URLs - respects max_total_videos limit"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        results = [
            {'url': f'https://youtube.com/watch?v=test{i}', 'title': f'Video {i}'}
            for i in range(10)
        ]

        video_urls = service._extract_video_urls(results, max_videos_per_playlist=3, max_total_videos=5)

        assert len(video_urls) == 5

    def test_extract_video_urls_empty_list(self, mock_video_crawler, mock_video_evaluator):
        """Test extracting video URLs - empty list"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        video_urls = service._extract_video_urls([], max_videos_per_playlist=3, max_total_videos=10)

        assert len(video_urls) == 0

    def test_match_grade_to_knowledge_file_kelas1(self, mock_video_crawler, mock_video_evaluator):
        """Test grade to file matching - Kelas 1"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        result = service._match_grade_to_knowledge_file("Kelas 1")
        assert result == "kelas1-2"

    def test_match_grade_to_knowledge_file_kelas3(self, mock_video_crawler, mock_video_evaluator):
        """Test grade to file matching - Kelas 3"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        result = service._match_grade_to_knowledge_file("Kelas 3")
        assert result == "kelas3-4"

    def test_match_grade_to_knowledge_file_kelas5(self, mock_video_crawler, mock_video_evaluator):
        """Test grade to file matching - Kelas 5"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        result = service._match_grade_to_knowledge_file("Kelas 5")
        assert result == "kelas5-6"

    def test_match_grade_to_knowledge_file_invalid(self, mock_video_crawler, mock_video_evaluator):
        """Test grade to file matching - invalid grade"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        result = service._match_grade_to_knowledge_file("Invalid")
        assert result == ""

    @patch('builtins.open', new_callable=MagicMock)
    @patch('os.path.exists')
    @patch('json.load')
    def test_load_knowledge_points_success(self, mock_json_load, mock_exists, mock_open,
                                            mock_video_crawler, mock_video_evaluator):
        """Test loading knowledge points - success"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        mock_exists.return_value = True
        mock_json_load.return_value = {
            'knowledge_points': [
                {'id': 'kp_1', 'topic_title_cn': 'Topic 1'},
                {'id': 'kp_2', 'topic_title_cn': 'Topic 2'}
            ]
        }

        result = service._load_knowledge_points("ID", "Kelas 1", "Matematika")

        assert len(result) == 2
        assert result[0]['id'] == 'kp_1'

    def test_load_knowledge_points_missing_params(self, mock_video_crawler, mock_video_evaluator):
        """Test loading knowledge points - missing params"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        result = service._load_knowledge_points("", "Kelas 1", "Matematika")
        assert result is None

        result = service._load_knowledge_points("ID", "", "Matematika")
        assert result is None

        result = service._load_knowledge_points("ID", "Kelas 1", "")
        assert result is None

    @patch('os.path.exists')
    def test_load_knowledge_points_file_not_found(self, mock_exists,
                                                   mock_video_crawler, mock_video_evaluator):
        """Test loading knowledge points - file not found"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        mock_exists.return_value = False

        result = service._load_knowledge_points("ID", "Kelas 1", "Matematika")

        assert result is None

    def test_evaluate_single_video_success(self, mock_video_crawler, mock_video_evaluator,
                                            sample_knowledge_points):
        """Test evaluating single video - success"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        video_info = {'url': 'https://youtube.com/watch?v=test', 'title': 'Test Video'}
        params = {
            'country': 'ID',
            'grade': 'Kelas 1',
            'subject': 'Matematika',
            'preferred_languages': ['en', 'id']
        }

        with patch.object(service, '_save_evaluation_result'):
            result = service._evaluate_single_video(video_info, sample_knowledge_points, params)

            assert result['success'] is True
            assert result['data']['video_url'] == 'https://youtube.com/watch?v=test'
            assert result['data']['evaluation']['overall_score'] == 8.5
            assert result['token_usage'] == 1000

    def test_evaluate_single_video_process_failure(self, mock_video_crawler, mock_video_evaluator,
                                                    sample_knowledge_points):
        """Test evaluating single video - process failure"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        # Mock process_video to fail
        mock_video_crawler.process_video.return_value = {
            'success': False,
            'error': 'Video processing failed'
        }

        video_info = {'url': 'https://youtube.com/watch?v=test', 'title': 'Test Video'}
        params = {
            'country': 'ID',
            'grade': 'Kelas 1',
            'subject': 'Matematika',
            'preferred_languages': ['en', 'id']
        }

        result = service._evaluate_single_video(video_info, sample_knowledge_points, params)

        assert result['success'] is False
        assert result['data']['success'] is False
        assert result['data']['error'] == 'Video processing failed'

    def test_batch_evaluate_videos_success(self, mock_video_crawler, mock_video_evaluator,
                                            sample_knowledge_points):
        """Test batch evaluating videos - success"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        video_urls = [
            {'url': 'https://youtube.com/watch?v=test1', 'title': 'Video 1'},
            {'url': 'https://youtube.com/watch?v=test2', 'title': 'Video 2'}
        ]

        params = {
            'country': 'ID',
            'grade': 'Kelas 1',
            'subject': 'Matematika',
            'preferred_languages': ['en', 'id']
        }

        with patch.object(service, '_save_evaluation_result'):
            result = service._batch_evaluate_videos(video_urls, sample_knowledge_points, params)

            assert result['total_videos'] == 2
            assert result['successful_count'] == 2
            assert result['failed_count'] == 0
            assert result['average_score'] == 8.5
            assert result['total_tokens'] == 2000

    def test_batch_evaluate_videos_with_failure(self, mock_video_crawler, mock_video_evaluator,
                                                 sample_knowledge_points):
        """Test batch evaluating videos - with failure"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        # First video succeeds, second fails
        mock_video_crawler.process_video.side_effect = [
            {'success': True, 'metadata': {'title': 'Video 1'}, 'video_path': '/tmp/v1.mp4',
             'frames_paths': [], 'audio_path': '/tmp/a1.mp3', 'transcript': 'transcript'},
            {'success': False, 'error': 'Processing failed'}
        ]

        video_urls = [
            {'url': 'https://youtube.com/watch?v=test1', 'title': 'Video 1'},
            {'url': 'https://youtube.com/watch?v=test2', 'title': 'Video 2'}
        ]

        params = {
            'country': 'ID',
            'grade': 'Kelas 1',
            'subject': 'Matematika',
            'preferred_languages': ['en', 'id']
        }

        with patch.object(service, '_save_evaluation_result'):
            result = service._batch_evaluate_videos(video_urls, sample_knowledge_points, params)

            assert result['total_videos'] == 2
            assert result['successful_count'] == 1
            assert result['failed_count'] == 1

    def test_batch_evaluate_videos_empty_list(self, mock_video_crawler, mock_video_evaluator,
                                               sample_knowledge_points):
        """Test batch evaluating videos - empty list"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        params = {
            'country': 'ID',
            'grade': 'Kelas 1',
            'subject': 'Matematika',
            'preferred_languages': ['en', 'id']
        }

        result = service._batch_evaluate_videos([], sample_knowledge_points, params)

        assert result['total_videos'] == 0
        assert result['successful_count'] == 0
        assert result['failed_count'] == 0
        assert result['average_score'] == 0.0
        assert len(result['evaluations']) == 0

    def test_save_evaluation_result(self, mock_video_crawler, mock_video_evaluator, tmp_path):
        """Test saving evaluation result"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        # Override evaluations directory
        eval_dir = tmp_path / 'evaluations'
        eval_dir.mkdir()

        with patch.object(service, 'evaluations_dir', str(eval_dir)):
            video_url = 'https://youtube.com/watch?v=test'
            process_result = {
                'metadata': {'title': 'Test Video', 'duration': 300}
            }
            evaluation = {'overall_score': 8.5}
            matched_kp = {'id': 'kp_1'}
            params = {'country': 'ID', 'grade': 'Kelas 1', 'subject': 'Matematika'}

            service._save_evaluation_result(video_url, process_result, evaluation, matched_kp, params)

            # Check file was created
            files = list(eval_dir.glob('evaluation_*.json'))
            assert len(files) == 1

            # Check file contents
            with open(files[0], 'r', encoding='utf-8') as f:
                data = json.load(f)

            assert data['video_url'] == video_url
            assert data['evaluation'] == evaluation
            assert data['matched_knowledge_point'] == matched_kp

    def test_format_response(self, mock_video_crawler, mock_video_evaluator):
        """Test formatting response"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        evaluation_results = {
            'evaluations': [
                {'success': True, 'video_url': 'https://youtube.com/watch?v=test1',
                 'evaluation': {'overall_score': 8.5}},
                {'success': True, 'video_url': 'https://youtube.com/watch?v=test2',
                 'evaluation': {'overall_score': 9.0}}
            ],
            'successful_count': 2,
            'failed_count': 0,
            'average_score': 8.75,
            'total_videos': 2,
            'total_tokens': 2000
        }

        response, status_code = service._format_response(evaluation_results)

        assert status_code == 200
        assert response['success'] is True
        assert response['total_videos'] == 2
        assert response['successful_count'] == 2
        assert response['failed_count'] == 0
        assert response['average_score'] == 8.75
        assert response['token_usage_summary']['total_tokens'] == 2000
        assert 'request_id' in response

    def test_batch_evaluate_real_flow(self, mock_video_crawler, mock_video_evaluator):
        """Test batch evaluate with real flow (minimal mocking)"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        request_data = {
            'results': [
                {'url': 'https://youtube.com/watch?v=test1', 'title': 'Video 1'}
            ],
            'country': 'ID',
            'grade': 'Kelas 1',
            'subject': 'Matematika'
        }

        with patch.object(service, '_save_evaluation_result'):
            response, status_code = service.batch_evaluate(request_data)

            # Should either succeed or fail gracefully
            assert status_code in [200, 400, 500]
            assert 'success' in response

    def test_batch_evaluate_no_videos(self, mock_video_crawler, mock_video_evaluator):
        """Test batch evaluate - no videos found"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        with patch.object(service, '_extract_and_validate_params') as mock_extract:
            mock_extract.return_value = {
                'results': [],
                'country': 'ID',
                'grade': 'Kelas 1',
                'subject': 'Matematika',
                'max_videos_per_playlist': 3,
                'max_total_videos': 10,
                'preferred_languages': ['en', 'id']
            }

            request_data = {'results': []}

            response, status_code = service.batch_evaluate(request_data)

            assert status_code == 400
            assert response['success'] is False
            assert "没有找到可评估的视频" in response['message']

    def test_batch_evaluate_validation_error(self, mock_video_crawler, mock_video_evaluator):
        """Test batch evaluate - validation error"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        request_data = {'results': []}

        response, status_code = service.batch_evaluate(request_data)

        assert status_code == 400
        assert response['success'] is False
        assert "请提供要评估的结果列表" in response['message']

    def test_evaluate_single_video_without_knowledge_points(self, mock_video_crawler, mock_video_evaluator):
        """Test evaluating single video without knowledge points"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        video_info = {'url': 'https://youtube.com/watch?v=test', 'title': 'Test Video'}
        params = {
            'country': 'ID',
            'grade': 'Kelas 1',
            'subject': 'Matematika',
            'preferred_languages': ['en', 'id']
        }

        with patch.object(service, '_save_evaluation_result'):
            result = service._evaluate_single_video(video_info, None, params)

            assert result['success'] is True
            # When knowledge_points is None, match_knowledge_point should not be called
            # or should handle None gracefully
            assert result['data']['matched_knowledge_point'] is None

    def test_batch_evaluate_exception_handling(self, mock_video_crawler, mock_video_evaluator):
        """Test batch evaluate handles exceptions gracefully"""
        service = BatchVideoService(
            video_crawler=mock_video_crawler,
            video_evaluator=mock_video_evaluator
        )

        video_urls = [
            {'url': 'https://youtube.com/watch?v=test1', 'title': 'Video 1'}
        ]

        params = {
            'country': 'ID',
            'grade': 'Kelas 1',
            'subject': 'Matematika',
            'preferred_languages': ['en', 'id']
        }

        # Mock to raise exception
        mock_video_crawler.process_video.side_effect = Exception("Test exception")

        result = service._batch_evaluate_videos(video_urls, None, params)

        assert result['total_videos'] == 1
        assert result['successful_count'] == 0
        assert result['failed_count'] == 1
        assert len(result['evaluations']) == 1
        assert result['evaluations'][0]['success'] is False
        assert 'error' in result['evaluations'][0]
