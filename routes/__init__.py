#!/usr/bin/env python3
"""
路由模块 - 将 web_app.py 中的路由按功能拆分为独立的蓝图模块

使用方法：
    from routes import BLUEPRINT_CONFIG
    for name, config in BLUEPRINT_CONFIG.items():
        init_func = config['init_func']
        url_prefix = config['url_prefix']
        bp = init_func()  # 初始化蓝图
        app.register_blueprint(bp, url_prefix=url_prefix)
"""

from flask import Blueprint

# 导入所有蓝图初始化函数
from .search_routes import init_search_bp
from .config_routes import init_config_bp
from .export_routes import init_export_bp
from .page_routes import init_page_bp
from .evaluation_routes import init_evaluation_bp
from .monitoring_routes import init_monitoring_bp
from .report_routes import init_report_bp
# 新增蓝图
from .video_analysis_routes import init_video_analysis_bp
from .knowledge_routes import init_knowledge_bp
from .university_routes import init_university_bp
from .vocational_routes import init_vocational_bp
from .country_routes import init_country_bp
from .history_routes import init_history_bp
from .admin_routes import init_admin_bp

__all__ = [
    'init_search_bp',
    'init_config_bp',
    'init_export_bp',
    'init_page_bp',
    'init_evaluation_bp',
    'init_monitoring_bp',
    'init_report_bp',
    'init_video_analysis_bp',
    'init_knowledge_bp',
    'init_university_bp',
    'init_vocational_bp',
    'init_country_bp',
    'init_history_bp',
    'init_admin_bp',
]

# 蓝图初始化配置
BLUEPRINT_CONFIG = {
    'page_bp': {
        'init_func': init_page_bp,
        'url_prefix': '',  # 页面路由不需要前缀
    },
    'search_bp': {
        'init_func': init_search_bp,
        'url_prefix': '/api',
    },
    'config_bp': {
        'init_func': init_config_bp,
        'url_prefix': '/api',
    },
    'evaluation_bp': {
        'init_func': init_evaluation_bp,
        'url_prefix': '/api',
    },
    'monitoring_bp': {
        'init_func': init_monitoring_bp,
        'url_prefix': '/api',
    },
    'export_bp': {
        'init_func': init_export_bp,
        'url_prefix': '/api',
    },
    'report_bp': {
        'init_func': init_report_bp,
        'url_prefix': '/api',
    },
    # 新增蓝图配置
    'video_analysis_bp': {
        'init_func': init_video_analysis_bp,
        'url_prefix': '/api',
    },
    'knowledge_bp': {
        'init_func': init_knowledge_bp,
        'url_prefix': '/api',
    },
    'university_bp': {
        'init_func': init_university_bp,
        'url_prefix': '/api',
    },
    'vocational_bp': {
        'init_func': init_vocational_bp,
        'url_prefix': '/api',
    },
    'country_bp': {
        'init_func': init_country_bp,
        'url_prefix': '/api',
    },
    'history_bp': {
        'init_func': init_history_bp,
        'url_prefix': '/api',
    },
    'admin_bp': {
        'init_func': init_admin_bp,
        'url_prefix': '/api',
    },
}
