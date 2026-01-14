"""
pytest configuration and fixtures for service tests
"""

import pytest
import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


@pytest.fixture
def sample_knowledge_points():
    """Sample knowledge points data for testing"""
    return [
        {
            "id": "kp_1",
            "topic_title_cn": "数字的认识",
            "topic_title_id": "Pengenalan Angka",
            "chapter_title": "第一章",
            "learning_objective": "认识1-10的数字"
        },
        {
            "id": "kp_2",
            "topic_title_cn": "加法运算",
            "topic_title_id": "Penjumlahan",
            "chapter_title": "第二章",
            "learning_objective": "学习基础加法"
        },
        {
            "id": "kp_3",
            "topic_title_cn": "减法运算",
            "topic_title_id": "Pengurangan",
            "chapter_title": "第二章",
            "learning_objective": "学习基础减法"
        }
    ]


@pytest.fixture
def sample_evaluation_data():
    """Sample evaluation data for testing"""
    return {
        "request_id": "test_123",
        "timestamp": "2025-01-10T12:00:00Z",
        "video_url": "https://youtube.com/watch?v=test123",
        "video_metadata": {
            "title": "Test Video",
            "description": "Test Description",
            "duration": 300
        },
        "evaluation": {
            "overall_score": 8.5,
            "visual_quality": {
                "combined_score": 8.0,
                "details": "Good visual quality"
            },
            "relevance": {
                "score": 9.0,
                "details": "Highly relevant"
            },
            "pedagogy": {
                "score": 8.5,
                "details": "Good pedagogical approach"
            },
            "metadata": {
                "score": 8.0,
                "details": "Good metadata"
            }
        },
        "matched_knowledge_point": {
            "id": "kp_1",
            "topic_title_cn": "数字的认识"
        },
        "search_params": {
            "country": "ID",
            "grade": "Kelas 1",
            "subject": "Matematika"
        }
    }


@pytest.fixture
def sample_video_urls():
    """Sample video URLs for testing"""
    return [
        {
            "url": "https://youtube.com/watch?v=test1",
            "title": "Math Video 1",
            "source": "direct"
        },
        {
            "url": "https://youtube.com/watch?v=test2",
            "title": "Math Video 2",
            "source": "direct"
        },
        {
            "url": "https://youtube.com/playlist?list=test123",
            "title": "Math Playlist",
            "source": "playlist"
        }
    ]


@pytest.fixture
def mock_video_crawler():
    """Mock video crawler"""
    crawler = Mock()
    crawler.process_video = Mock(return_value={
        'success': True,
        'metadata': {
            'title': 'Test Video',
            'description': 'Test Description',
            'duration': 300
        },
        'video_path': '/tmp/test_video.mp4',
        'frames_paths': ['/tmp/frame1.jpg'],
        'audio_path': '/tmp/audio.mp3',
        'transcript': 'This is a test transcript'
    })
    return crawler


@pytest.fixture
def mock_video_evaluator():
    """Mock video evaluator"""
    evaluator = Mock()
    evaluator.match_knowledge_point = Mock(return_value={
        'id': 'kp_1',
        'topic_title_cn': '数字的认识'
    })
    evaluator.evaluate_video_content = Mock(return_value={
        'overall_score': 8.5,
        'visual_quality': {
            'combined_score': 8.0,
            'details': 'Good visual quality'
        },
        'relevance': {
            'score': 9.0,
            'details': 'Highly relevant'
        },
        'pedagogy': {
            'score': 8.5,
            'details': 'Good pedagogical approach'
        },
        'metadata': {
            'score': 8.0,
            'details': 'Good metadata'
        },
        'token_usage': {
            'total_tokens': 1000
        }
    })
    return evaluator


@pytest.fixture
def mock_playlist_processor():
    """Mock playlist processor"""
    processor = Mock()
    processor.is_playlist_url = Mock(return_value=True)
    processor.extract_videos_from_playlist = Mock(return_value={
        'success': True,
        'videos': [
            {'url': 'https://youtube.com/watch?v=p1', 'title': 'Playlist Video 1'},
            {'url': 'https://youtube.com/watch?v=p2', 'title': 'Playlist Video 2'},
            {'url': 'https://youtube.com/watch?v=p3', 'title': 'Playlist Video 3'}
        ]
    })
    return processor


@pytest.fixture
def temp_knowledge_points_file(sample_knowledge_points):
    """Create a temporary knowledge points JSON file"""
    temp_dir = tempfile.mkdtemp()
    knowledge_dir = os.path.join(temp_dir, 'data', 'knowledge_points', 'Knowledge Point')
    os.makedirs(knowledge_dir, exist_ok=True)

    filename = "5. Final Panduan Mata Pelajaran Matematika_kelas1-2.json"
    filepath = os.path.join(knowledge_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump({'knowledge_points': sample_knowledge_points}, f, ensure_ascii=False, indent=2)

    yield temp_dir

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_evaluations_dir(sample_evaluation_data):
    """Create a temporary evaluations directory with sample evaluation files"""
    temp_dir = tempfile.mkdtemp()
    eval_dir = os.path.join(temp_dir, 'data', 'evaluations')
    os.makedirs(eval_dir, exist_ok=True)

    # Create multiple evaluation files
    for i in range(3):
        eval_data = sample_evaluation_data.copy()
        eval_data['request_id'] = f"test_{i}"
        eval_data['video_url'] = f"https://youtube.com/watch?v=test{i}"
        eval_data['timestamp'] = f"2025-01-10T1{i}:00:00Z"

        filepath = os.path.join(eval_dir, f"evaluation_test_{i}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(eval_data, f, ensure_ascii=False, indent=2)

    yield temp_dir

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
