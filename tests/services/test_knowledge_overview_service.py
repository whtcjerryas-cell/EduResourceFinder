"""
Unit tests for KnowledgeOverviewService
"""

import pytest
import os
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from services.knowledge_overview_service import KnowledgeOverviewService
from utils.error_handling import ValidationError, NotFoundError


class TestKnowledgeOverviewService:
    """Test suite for KnowledgeOverviewService"""

    def test_init(self):
        """Test service initialization"""
        service = KnowledgeOverviewService()

        assert service.base_dir is not None
        assert service.evaluations_dir is not None
        assert service.knowledge_points_dir is not None

        # Check directory paths are correct
        assert 'evaluations' in service.evaluations_dir
        assert 'Knowledge Point' in service.knowledge_points_dir

    def test_validate_params_success(self):
        """Test parameter validation - success"""
        service = KnowledgeOverviewService()

        # Should not raise any exception
        service._validate_params("ID", "Kelas 1", "Matematika")

    def test_validate_params_failure_missing_country(self):
        """Test parameter validation - failure (missing country)"""
        service = KnowledgeOverviewService()

        with pytest.raises(ValidationError) as exc_info:
            service._validate_params("", "Kelas 1", "Matematika")

        assert "请提供国家、年级和学科参数" in str(exc_info.value)

    def test_validate_params_failure_missing_grade(self):
        """Test parameter validation - failure (missing grade)"""
        service = KnowledgeOverviewService()

        with pytest.raises(ValidationError) as exc_info:
            service._validate_params("ID", "", "Matematika")

        assert "请提供国家、年级和学科参数" in str(exc_info.value)

    def test_validate_params_failure_missing_subject(self):
        """Test parameter validation - failure (missing subject)"""
        service = KnowledgeOverviewService()

        with pytest.raises(ValidationError) as exc_info:
            service._validate_params("ID", "Kelas 1", "")

        assert "请提供国家、年级和学科参数" in str(exc_info.value)

    def test_match_grade_to_knowledge_file_kelas1(self):
        """Test grade to file matching - Kelas 1"""
        service = KnowledgeOverviewService()

        result = service._match_grade_to_knowledge_file("Kelas 1")
        assert result == "kelas1-2"

    def test_match_grade_to_knowledge_file_kelas2(self):
        """Test grade to file matching - Kelas 2"""
        service = KnowledgeOverviewService()

        result = service._match_grade_to_knowledge_file("Kelas 2")
        assert result == "kelas1-2"

    def test_match_grade_to_knowledge_file_kelas3(self):
        """Test grade to file matching - Kelas 3"""
        service = KnowledgeOverviewService()

        result = service._match_grade_to_knowledge_file("Kelas 3")
        assert result == "kelas3-4"

    def test_match_grade_to_knowledge_file_kelas4(self):
        """Test grade to file matching - Kelas 4"""
        service = KnowledgeOverviewService()

        result = service._match_grade_to_knowledge_file("Kelas 4")
        assert result == "kelas3-4"

    def test_match_grade_to_knowledge_file_kelas5(self):
        """Test grade to file matching - Kelas 5"""
        service = KnowledgeOverviewService()

        result = service._match_grade_to_knowledge_file("Kelas 5")
        assert result == "kelas5-6"

    def test_match_grade_to_knowledge_file_kelas6(self):
        """Test grade to file matching - Kelas 6"""
        service = KnowledgeOverviewService()

        result = service._match_grade_to_knowledge_file("Kelas 6")
        assert result == "kelas5-6"

    def test_match_grade_to_knowledge_file_numeric(self):
        """Test grade to file matching - numeric format"""
        service = KnowledgeOverviewService()

        assert service._match_grade_to_knowledge_file("1") == "kelas1-2"
        assert service._match_grade_to_knowledge_file("2") == "kelas1-2"
        assert service._match_grade_to_knowledge_file("3") == "kelas3-4"
        assert service._match_grade_to_knowledge_file("4") == "kelas3-4"
        assert service._match_grade_to_knowledge_file("5") == "kelas5-6"
        assert service._match_grade_to_knowledge_file("6") == "kelas5-6"

    def test_match_grade_to_knowledge_file_invalid(self):
        """Test grade to file matching - invalid grade"""
        service = KnowledgeOverviewService()

        result = service._match_grade_to_knowledge_file("Invalid")
        assert result == ""

    def test_match_grade_to_knowledge_file_out_of_range(self):
        """Test grade to file matching - out of range"""
        service = KnowledgeOverviewService()

        result = service._match_grade_to_knowledge_file("Kelas 10")
        assert result == ""

    @patch('builtins.open', new_callable=MagicMock)
    @patch('os.path.exists')
    @patch('json.load')
    def test_load_knowledge_points_success(self, mock_json_load, mock_exists, mock_open):
        """Test loading knowledge points - success"""
        service = KnowledgeOverviewService()

        # Mock file exists
        mock_exists.return_value = True

        # Mock JSON data
        mock_json_load.return_value = {
            'knowledge_points': [
                {'id': 'kp_1', 'topic_title_cn': 'Test Topic 1'},
                {'id': 'kp_2', 'topic_title_cn': 'Test Topic 2'}
            ]
        }

        result = service._load_knowledge_points("Kelas 1", "Matematika")

        assert len(result) == 2
        assert result[0]['id'] == 'kp_1'
        assert result[1]['id'] == 'kp_2'

    @patch('os.path.exists')
    def test_load_knowledge_points_file_not_found(self, mock_exists):
        """Test loading knowledge points - file not found"""
        service = KnowledgeOverviewService()

        # Mock file doesn't exist
        mock_exists.return_value = False

        with pytest.raises(NotFoundError) as exc_info:
            service._load_knowledge_points("Kelas 1", "Matematika")

        assert "知识点文件不存在" in str(exc_info.value)

    def test_load_knowledge_points_invalid_grade(self):
        """Test loading knowledge points - invalid grade"""
        service = KnowledgeOverviewService()

        with pytest.raises(ValidationError) as exc_info:
            service._load_knowledge_points("Invalid Grade", "Matematika")

        assert "无法匹配年级" in str(exc_info.value)

    def test_load_knowledge_points_unsupported_subject(self):
        """Test loading knowledge points - unsupported subject"""
        service = KnowledgeOverviewService()

        with pytest.raises(ValidationError) as exc_info:
            service._load_knowledge_points("Kelas 1", "Unsupported Subject")

        assert "暂不支持学科" in str(exc_info.value)

    def test_calculate_resource_richness_score_no_videos(self):
        """Test resource richness score calculation - no videos"""
        service = KnowledgeOverviewService()

        score = service._calculate_resource_richness_score(0, 0.0)

        # With 0 videos and 0 avg score:
        # video_score = 0 * 0.3 = 0
        # avg_score = 0 * 0.4 = 0
        # materials = 0 * 0.15 = 0
        # practice = 0 * 0.15 = 0
        # total = 0
        assert score == 0.0

    def test_calculate_resource_richness_score_with_videos(self):
        """Test resource richness score calculation - with videos"""
        service = KnowledgeOverviewService()

        score = service._calculate_resource_richness_score(5, 8.0)

        # video_score = min(5/5, 1.0) * 10 * 0.3 = 1.0 * 10 * 0.3 = 3.0
        # avg_score = 8.0 * 0.4 = 3.2
        # materials = 0 * 0.15 = 0
        # practice = 0 * 0.15 = 0
        # total = 6.2
        assert round(score, 2) == 6.2

    def test_calculate_resource_richness_score_max_videos(self):
        """Test resource richness score calculation - max videos"""
        service = KnowledgeOverviewService()

        # More than 5 videos should still cap at 5 for scoring
        score = service._calculate_resource_richness_score(10, 9.0)

        # video_score = min(10/5, 1.0) * 10 * 0.3 = 1.0 * 10 * 0.3 = 3.0
        # avg_score = 9.0 * 0.4 = 3.6
        # materials = 0 * 0.15 = 0
        # practice = 0 * 0.15 = 0
        # total = 6.6
        assert round(score, 2) == 6.6

    def test_extract_video_info(self):
        """Test extracting video info from evaluation data"""
        service = KnowledgeOverviewService()

        eval_data = {
            'video_url': 'https://youtube.com/watch?v=test',
            'video_metadata': {
                'title': 'Test Video'
            },
            'evaluation': {
                'overall_score': 8.5,
                'visual_quality': {
                    'combined_score': 8.0,
                    'details': 'Good visual'
                },
                'relevance': {
                    'score': 9.0,
                    'details': 'Highly relevant'
                },
                'pedagogy': {
                    'score': 8.5,
                    'details': 'Good pedagogy'
                },
                'metadata': {
                    'score': 8.0,
                    'details': 'Good metadata'
                }
            },
            'timestamp': '2025-01-10T12:00:00Z',
            'request_id': 'test_123'
        }

        result = service._extract_video_info(eval_data, 'kp_1')

        assert result['video_url'] == 'https://youtube.com/watch?v=test'
        assert result['video_title'] == 'Test Video'
        assert result['overall_score'] == 8.5
        assert result['kp_id'] == 'kp_1'
        assert result['evaluation_date'] == '2025-01-10T12:00:00Z'

    def test_match_videos_to_knowledge_points(self):
        """Test matching videos to knowledge points"""
        service = KnowledgeOverviewService()

        video_url_latest = {
            'https://youtube.com/watch?v=test1': {
                'kp_id': 'kp_1',
                'video_url': 'https://youtube.com/watch?v=test1',
                'video_title': 'Video 1'
            },
            'https://youtube.com/watch?v=test2': {
                'kp_id': 'kp_1',
                'video_url': 'https://youtube.com/watch?v=test2',
                'video_title': 'Video 2'
            },
            'https://youtube.com/watch?v=test3': {
                'kp_id': 'kp_2',
                'video_url': 'https://youtube.com/watch?v=test3',
                'video_title': 'Video 3'
            }
        }

        result = service._match_videos_to_knowledge_points(video_url_latest)

        assert len(result) == 2
        assert len(result['kp_1']) == 2
        assert len(result['kp_2']) == 1

        # Check that kp_id is removed from video info
        assert 'kp_id' not in result['kp_1'][0]

    def test_build_result_with_statistics(self):
        """Test building result with statistics"""
        service = KnowledgeOverviewService()

        knowledge_points = [
            {'id': 'kp_1', 'topic_title_cn': 'Topic 1', 'topic_title_id': 'Topik 1',
             'chapter_title': 'Chapter 1', 'learning_objective': 'Learn 1'},
            {'id': 'kp_2', 'topic_title_cn': 'Topic 2', 'topic_title_id': 'Topik 2',
             'chapter_title': 'Chapter 2', 'learning_objective': 'Learn 2'}
        ]

        knowledge_point_videos = {
            'kp_1': [
                {'overall_score': 8.0, 'video_title': 'Video 1'},
                {'overall_score': 9.0, 'video_title': 'Video 2'}
            ],
            'kp_2': []
        }

        result = service._build_result_with_statistics(knowledge_points, knowledge_point_videos)

        assert len(result) == 2

        # Check kp_1 with videos
        kp1 = next(r for r in result if r['id'] == 'kp_1')
        assert kp1['video_count'] == 2
        assert kp1['average_score'] == 8.5
        assert kp1['resource_richness_score'] > 0

        # Check kp_2 without videos
        kp2 = next(r for r in result if r['id'] == 'kp_2')
        assert kp2['video_count'] == 0
        assert kp2['average_score'] == 0.0
        assert kp2['resource_richness_score'] == 0.0

    def test_sort_results(self):
        """Test sorting results"""
        service = KnowledgeOverviewService()

        result_knowledge_points = [
            {'id': 'kp_1', 'resource_richness_score': 5.0,
             'videos': [{'overall_score': 7.0}, {'overall_score': 8.0}]},
            {'id': 'kp_2', 'resource_richness_score': 8.0,
             'videos': [{'overall_score': 6.0}, {'overall_score': 9.0}]},
            {'id': 'kp_3', 'resource_richness_score': 3.0,
             'videos': [{'overall_score': 5.0}]}
        ]

        result = service._sort_results(result_knowledge_points)

        # Check sorted by resource_richness_score (descending)
        assert result[0]['id'] == 'kp_2'
        assert result[1]['id'] == 'kp_1'
        assert result[2]['id'] == 'kp_3'

        # Check videos sorted by overall_score (descending)
        assert result[0]['videos'][0]['overall_score'] == 9.0
        assert result[0]['videos'][1]['overall_score'] == 6.0

    @patch.object(KnowledgeOverviewService, '_load_evaluations')
    @patch.object(KnowledgeOverviewService, '_load_knowledge_points')
    @patch.object(KnowledgeOverviewService, '_validate_params')
    def test_get_overview_success(self, mock_validate, mock_load_kp, mock_load_eval):
        """Test getting overview - success (integration test)"""
        service = KnowledgeOverviewService()

        # Mock validation
        mock_validate.return_value = None

        # Mock knowledge points
        mock_load_kp.return_value = [
            {'id': 'kp_1', 'topic_title_cn': 'Topic 1', 'topic_title_id': 'Topik 1',
             'chapter_title': 'Chapter 1', 'learning_objective': 'Learn 1'},
            {'id': 'kp_2', 'topic_title_cn': 'Topic 2', 'topic_title_id': 'Topik 2',
             'chapter_title': 'Chapter 2', 'learning_objective': 'Learn 2'}
        ]

        # Mock evaluations
        mock_load_eval.return_value = {
            'https://youtube.com/watch?v=test1': {
                'kp_id': 'kp_1',
                'video_url': 'https://youtube.com/watch?v=test1',
                'video_title': 'Video 1',
                'overall_score': 8.0,
                'evaluation_date': '2025-01-10T12:00:00Z'
            }
        }

        result, status_code = service.get_overview("ID", "Kelas 1", "Matematika")

        assert status_code == 200
        assert result['success'] is True
        assert result['total_knowledge_points'] == 2
        assert result['total_videos'] == 1
        assert len(result['knowledge_points']) == 2

    def test_get_overview_invalid_params(self):
        """Test getting overview - invalid params"""
        service = KnowledgeOverviewService()

        result, status_code = service.get_overview("", "Kelas 1", "Matematika")

        assert status_code == 400
        assert result['success'] is False
        assert "请提供国家、年级和学科参数" in result['message']

    def test_load_evaluations_empty_directory(self, tmp_path):
        """Test loading evaluations from empty directory"""
        service = KnowledgeOverviewService()

        # Create empty evaluations directory
        eval_dir = tmp_path / 'evaluations'
        eval_dir.mkdir()

        with patch.object(service, 'evaluations_dir', str(eval_dir)):
            result = service._load_evaluations("ID", "Kelas 1", "Matematika")

            assert result == {}

    def test_load_evaluations_with_files(self, tmp_path, sample_evaluation_data):
        """Test loading evaluations with files"""
        service = KnowledgeOverviewService()

        # Create evaluations directory
        eval_dir = tmp_path / 'evaluations'
        eval_dir.mkdir()

        # Create evaluation file
        eval_file = eval_dir / 'evaluation_test.json'
        with open(eval_file, 'w', encoding='utf-8') as f:
            json.dump(sample_evaluation_data, f, ensure_ascii=False)

        with patch.object(service, 'evaluations_dir', str(eval_dir)):
            result = service._load_evaluations("ID", "Kelas 1", "Matematika")

            assert len(result) == 1
            assert 'https://youtube.com/watch?v=test123' in result

    def test_load_evaluations_filters_by_params(self, tmp_path, sample_evaluation_data):
        """Test loading evaluations filters by search params"""
        service = KnowledgeOverviewService()

        # Create evaluations directory
        eval_dir = tmp_path / 'evaluations'
        eval_dir.mkdir()

        # Create evaluation files with different params
        for i, (country, grade, subject) in enumerate([
            ("ID", "Kelas 1", "Matematika"),
            ("ID", "Kelas 2", "Matematika"),
            ("MY", "Kelas 1", "Matematika")
        ]):
            eval_data = sample_evaluation_data.copy()
            eval_data['search_params'] = {
                'country': country,
                'grade': grade,
                'subject': subject
            }
            eval_file = eval_dir / f'evaluation_{i}.json'
            with open(eval_file, 'w', encoding='utf-8') as f:
                json.dump(eval_data, f, ensure_ascii=False)

        with patch.object(service, 'evaluations_dir', str(eval_dir)):
            result = service._load_evaluations("ID", "Kelas 1", "Matematika")

            # Should only return the first evaluation
            assert len(result) == 1

    def test_load_evaluations_deduplicates_by_url(self, tmp_path, sample_evaluation_data):
        """Test loading evaluations deduplicates videos by URL"""
        service = KnowledgeOverviewService()

        # Create evaluations directory
        eval_dir = tmp_path / 'evaluations'
        eval_dir.mkdir()

        # Create multiple evaluations for same video URL with different timestamps
        for i in range(3):
            eval_data = sample_evaluation_data.copy()
            eval_data['request_id'] = f'test_{i}'
            eval_data['timestamp'] = f'2025-01-10T1{i}:00:00Z'
            eval_file = eval_dir / f'evaluation_{i}.json'
            with open(eval_file, 'w', encoding='utf-8') as f:
                json.dump(eval_data, f, ensure_ascii=False)

        with patch.object(service, 'evaluations_dir', str(eval_dir)):
            result = service._load_evaluations("ID", "Kelas 1", "Matematika")

            # Should only return one evaluation (the latest)
            assert len(result) == 1
            # Should be the latest timestamp (12:00:00Z)
            video_info = list(result.values())[0]
            assert video_info['evaluation_date'] == '2025-01-10T12:00:00Z'
