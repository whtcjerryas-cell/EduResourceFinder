"""
MCP Tools for Agent-Native Education Resource Search

This module provides atomic tools for:
- Configuration management
- Pattern extraction (grades and subjects)
- Validation (grade matching, URL quality)
- Knowledge base management (learning and verification)

遵循 agent-native 原则：
- 工具是原子的，不编码业务逻辑
- 完整的CRUD操作
- Agent通过prompt决策如何使用工具
"""

from .config_tools import (
    read_country_config,
    list_available_countries
)

from .extraction_tools import (
    extract_grade_from_title,
    extract_subject_from_title
)

from .validation_tools import (
    validate_grade_match,
    validate_url_quality
)

from .knowledge_tools import (
    record_pattern_learning,
    list_learned_patterns,
    verify_pattern
)

from .agent_context_builder import (
    build_agent_system_prompt,
    build_scoring_context,
    build_tools_documentation
)

__all__ = [
    # Config tools
    'read_country_config',
    'list_available_countries',

    # Extraction tools
    'extract_grade_from_title',
    'extract_subject_from_title',

    # Validation tools
    'validate_grade_match',
    'validate_url_quality',

    # Knowledge tools
    'record_pattern_learning',
    'list_learned_patterns',
    'verify_pattern',

    # Context builder
    'build_agent_system_prompt',
    'build_scoring_context',
    'build_tools_documentation',
]
