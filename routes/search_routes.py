#!/usr/bin/env python3
"""
搜索路由 - 处理所有搜索相关的API请求
"""

import uuid
from flask import Blueprint, request, jsonify
from utils.logger_utils import get_logger

logger = get_logger('search_routes')

# 创建蓝图
search_bp = Blueprint('search', __name__)


def init_search_bp(concurrency_limiter=None):
    """
    初始化搜索路由蓝图

    Args:
        concurrency_limiter: 并发限制器（可选）

    Returns:
        配置好的蓝图
    """
    from services.search_handler import SearchHandler
    search_handler = SearchHandler(concurrency_limiter=concurrency_limiter)

    @search_bp.route('/api/search', methods=['POST'])
    def search():
        """搜索API"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "success": False,
                    "message": "请求数据为空",
                    "results": []
                }), 400

            # 使用搜索处理器
            result_data, status_code = search_handler.handle_search_request(
                request_data=data,
                concurrency_limiter=concurrency_limiter
            )

            return jsonify(result_data), status_code

        except Exception as e:
            logger.error(f"[搜索请求] 处理失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"搜索失败: {str(e)}",
                "results": []
            }), 500

    @search_bp.route('/api/history', methods=['GET'])
    def get_search_history():
        """获取搜索历史"""
        try:
            # TODO: 实现搜索历史功能
            return jsonify({
                "success": True,
                "history": [],
                "total": 0
            })
        except Exception as e:
            logger.error(f"[搜索历史] 获取失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    @search_bp.route('/api/search_suggestions', methods=['GET'])
    def get_search_suggestions():
        """获取搜索建议"""
        try:
            query = request.args.get('q', '').strip()
            country = request.args.get('country', '').strip()

            # TODO: 实现搜索建议功能
            return jsonify({
                "success": True,
                "suggestions": []
            })
        except Exception as e:
            logger.error(f"[搜索建议] 获取失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    return search_bp
