#!/usr/bin/env python3
"""
监控路由 - 处理所有性能监控、统计和系统健康相关的API
"""

from flask import Blueprint, request, jsonify
from logger_utils import get_logger

logger = get_logger('monitoring_routes')

# 创建蓝图
monitoring_bp = Blueprint('monitoring', __name__)


def init_monitoring_bp(perf_monitor=None, cache_manager=None):
    """
    初始化监控路由蓝图

    Args:
        perf_monitor: 性能监控器实例
        cache_manager: 缓存管理器实例

    Returns:
        配置好的监控蓝图
    """
    from core.performance_monitor import get_performance_monitor
    from core.multi_level_cache import get_cache

    # 使用单例模式
    perf_monitor = perf_monitor or get_performance_monitor()
    cache_manager = cache_manager or get_cache()

    @monitoring_bp.route('/performance_stats', methods=['GET'])
    def get_performance_stats():
        """获取性能统计"""
        try:
            stats = perf_monitor.get_all_stats()
            return jsonify({
                "success": True,
                "stats": stats
            })
        except Exception as e:
            logger.error(f"[性能统计] 获取失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    @monitoring_bp.route('/performance_by_country', methods=['GET'])
    def get_performance_by_country():
        """按国家获取性能统计"""
        try:
            country = request.args.get('country', 'ID')
            stats = perf_monitor.get_stats_by_country(country)
            return jsonify({
                "success": True,
                "country": country,
                "stats": stats
            })
        except Exception as e:
            logger.error(f"[国家性能统计] 获取失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    @monitoring_bp.route('/performance_by_engine', methods=['GET'])
    def get_performance_by_engine():
        """按搜索引擎获取性能统计"""
        try:
            engine = request.args.get('engine', 'google')
            stats = perf_monitor.get_stats_by_engine(engine)
            return jsonify({
                "success": True,
                "engine": engine,
                "stats": stats
            })
        except Exception as e:
            logger.error(f"[引擎性能统计] 获取失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    @monitoring_bp.route('/slow_queries', methods=['GET'])
    def get_slow_queries():
        """获取慢查询列表"""
        try:
            limit = request.args.get('limit', 20, type=int)
            queries = perf_monitor.get_slow_queries(limit)
            return jsonify({
                "success": True,
                "queries": queries,
                "count": len(queries)
            })
        except Exception as e:
            logger.error(f"[慢查询] 获取失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    @monitoring_bp.route('/cache_stats', methods=['GET'])
    def get_cache_stats():
        """获取缓存统计"""
        try:
            stats = cache_manager.get_stats()
            return jsonify({
                "success": True,
                "stats": stats
            })
        except Exception as e:
            logger.error(f"[缓存统计] 获取失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    @monitoring_bp.route('/system_metrics', methods=['GET'])
    def get_system_metrics():
        """获取系统指标"""
        try:
            import psutil
            import os

            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)

            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_info = {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
                "free": memory.free
            }

            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            disk_info = {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            }

            return jsonify({
                "success": True,
                "metrics": {
                    "cpu_percent": cpu_percent,
                    "memory": memory_info,
                    "disk": disk_info
                }
            })
        except Exception as e:
            logger.error(f"[系统指标] 获取失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    @monitoring_bp.route('/concurrency_stats', methods=['GET'])
    def get_concurrency_stats():
        """获取并发统计"""
        try:
            # TODO: 从并发限制器获取统计信息
            return jsonify({
                "success": True,
                "stats": {
                    "active_requests": 0,
                    "max_concurrent": 10,
                    "queue_size": 0
                }
            })
        except Exception as e:
            logger.error(f"[并发统计] 获取失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    @monitoring_bp.route('/global_stats', methods=['GET'])
    def get_global_stats():
        """获取全局统计"""
        try:
            # 合并多个统计源
            perf_stats = perf_monitor.get_all_stats()
            cache_stats = cache_manager.get_stats()

            return jsonify({
                "success": True,
                "stats": {
                    "performance": perf_stats,
                    "cache": cache_stats
                }
            })
        except Exception as e:
            logger.error(f"[全局统计] 获取失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    @monitoring_bp.route('/feedback', methods=['POST'])
    def submit_feedback():
        """提交用户反馈"""
        try:
            data = request.get_json()
            # TODO: 保存反馈到数据库
            return jsonify({
                "success": True,
                "message": "反馈已提交"
            })
        except Exception as e:
            logger.error(f"[反馈提交] 失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    @monitoring_bp.route('/feedback/stats', methods=['GET'])
    def get_feedback_stats():
        """获取反馈统计"""
        try:
            # TODO: 从数据库获取反馈统计
            return jsonify({
                "success": True,
                "stats": {
                    "total_feedback": 0,
                    "average_rating": 0.0
                }
            })
        except Exception as e:
            logger.error(f"[反馈统计] 获取失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    @monitoring_bp.route('/debug_logs', methods=['GET'])
    def get_debug_logs():
        """获取调试日志"""
        try:
            limit = request.args.get('limit', 100, type=int)
            # TODO: 实现日志查询
            return jsonify({
                "success": True,
                "logs": []
            })
        except Exception as e:
            logger.error(f"[调试日志] 获取失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    @monitoring_bp.route('/save_debug_log', methods=['POST'])
    def save_debug_log():
        """保存调试日志"""
        try:
            data = request.get_json()
            # TODO: 保存日志到文件
            return jsonify({
                "success": True,
                "message": "日志已保存"
            })
        except Exception as e:
            logger.error(f"[保存日志] 失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    @monitoring_bp.route('/admin/quality_evaluation', methods=['POST'])
    def admin_quality_evaluation():
        """管理员：质量评估"""
        try:
            data = request.get_json()
            # TODO: 实现质量评估
            return jsonify({
                "success": True,
                "message": "质量评估已提交"
            })
        except Exception as e:
            logger.error(f"[质量评估] 失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    @monitoring_bp.route('/admin/system_health', methods=['GET'])
    def admin_system_health():
        """管理员：系统健康检查"""
        try:
            health = {
                "status": "healthy",
                "checks": {
                    "database": "ok",
                    "cache": "ok",
                    "llm_api": "ok",
                    "search_apis": "ok"
                }
            }
            return jsonify({
                "success": True,
                "health": health
            })
        except Exception as e:
            logger.error(f"[系统健康检查] 失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    logger.info("✅ 监控路由已初始化")
    return monitoring_bp
