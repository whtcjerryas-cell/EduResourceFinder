#!/usr/bin/env python3
"""
页面路由 - 处理所有HTML页面路由
包括主页、知识库页面、报告页面等静态页面
"""

from flask import Blueprint, render_template, send_from_directory
from utils.logger_utils import get_logger

logger = get_logger('page_routes')

# 创建蓝图
page_bp = Blueprint('pages', __name__)


def init_page_bp():
    """
    初始化页面路由蓝图

    Returns:
        配置好的页面蓝图
    """

    @page_bp.route('/')
    def index():
        """主页"""
        try:
            return render_template('index.html')
        except Exception as e:
            logger.error(f"[主页] 渲染失败: {str(e)}")
            return f"主页加载失败: {str(e)}", 500

    @page_bp.route('/favicon.ico')
    def favicon():
        """网站图标"""
        try:
            return send_from_directory('static', 'favicon.ico')
        except Exception as e:
            logger.warning(f"[图标] 加载失败: {str(e)}")
            return '', 404

    @page_bp.route('/app')
    def app_page():
        """应用主页面"""
        try:
            return render_template('app.html')
        except Exception as e:
            logger.error(f"[应用页面] 渲染失败: {str(e)}")
            return f"应用页面加载失败: {str(e)}", 500

    @page_bp.route('/knowledge_points')
    def knowledge_points_page():
        """知识点页面"""
        try:
            return render_template('knowledge_points.html')
        except Exception as e:
            logger.error(f"[知识点页面] 渲染失败: {str(e)}")
            return f"知识点页面加载失败: {str(e)}", 500

    @page_bp.route('/evaluation_reports')
    def evaluation_reports_page():
        """评估报告页面"""
        try:
            return render_template('evaluation_reports.html')
        except Exception as e:
            logger.error(f"[评估报告页面] 渲染失败: {str(e)}")
            return f"评估报告页面加载失败: {str(e)}", 500

    @page_bp.route('/search_history')
    def search_history_page():
        """搜索历史页面"""
        try:
            return render_template('search_history.html')
        except Exception as e:
            logger.error(f"[搜索历史页面] 渲染失败: {str(e)}")
            return f"搜索历史页面加载失败: {str(e)}", 500

    @page_bp.route('/test_base_new')
    def test_base_new():
        """测试基础新页面"""
        try:
            return render_template('test_base_new.html')
        except Exception as e:
            logger.error(f"[测试页面] 渲染失败: {str(e)}")
            return f"测试页面加载失败: {str(e)}", 500

    @page_bp.route('/test_search')
    def test_search():
        """搜索测试页面"""
        try:
            return render_template('test_search.html')
        except Exception as e:
            logger.error(f"[搜索测试页面] 渲染失败: {str(e)}")
            return f"搜索测试页面加载失败: {str(e)}", 500

    @page_bp.route('/report_center')
    def report_center():
        """报告中心页面"""
        try:
            return render_template('report_center.html')
        except Exception as e:
            logger.error(f"[报告中心页面] 渲染失败: {str(e)}")
            return f"报告中心页面加载失败: {str(e)}", 500

    logger.info("✅ 页面路由已初始化")
    return page_bp
