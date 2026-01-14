#!/usr/bin/env python3
"""
导出路由 - 处理所有导出相关的API请求
"""

import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from logger_utils import get_logger

logger = get_logger('export_routes')

# 创建蓝图
export_bp = Blueprint('export', __name__)


def init_export_bp():
    """
    初始化导出路由蓝图

    Returns:
        配置好的蓝图
    """

    @export_bp.route('/api/export_excel', methods=['POST'])
    def export_excel():
        """导出Excel"""
        try:
            from services.export_handler import ExportHandler

            data = request.get_json()
            results = data.get('results') or data.get('selected_results', [])
            search_params = data.get('search_params', {})

            logger.info(f"[Excel导出] 收到数据: results={len(results)}个")

            # 使用导出处理器
            export_handler = ExportHandler()
            output, filename = export_handler.export_search_results_to_excel(
                results=results,
                search_params=search_params
            )

            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )

        except ImportError as e:
            logger.error(f"[Excel导出] 缺少依赖库: {str(e)}")
            return jsonify({
                "success": False,
                "message": "缺少必要的库，请安装: pip install pandas openpyxl"
            }), 500
        except Exception as e:
            logger.error(f"[Excel导出] 处理失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"导出失败: {str(e)}"
            }), 500

    @export_bp.route('/api/export_batch_excel', methods=['POST'])
    def export_batch_excel():
        """批量导出Excel"""
        request_id = str(uuid.uuid4())[:8]

        try:
            from services.export_service import ExportService

            data = request.get_json()
            batch_results = data.get('results', [])
            batch_name = data.get('batch_name', f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

            logger.info(f"[批量导出] 收到数据: results={len(batch_results)}个")

            # 使用导出服务
            export_service = ExportService()
            result = export_service.export_batch_results(
                batch_results=batch_results,
                batch_name=batch_name
            )

            if result['success']:
                return send_file(
                    result['file_path'],
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name=result['filename']
                )
            else:
                return jsonify(result), 500

        except Exception as e:
            logger.error(f"[批量导出] 处理失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"批量导出失败: {str(e)}"
            }), 500

    @export_bp.route('/api/export_search_log/<search_id>', methods=['GET'])
    def export_search_log(search_id):
        """导出搜索日志"""
        try:
            from core.search_log_collector import get_log_collector
            from core.excel_exporter import ExcelExporter

            log_collector = get_log_collector()
            search_log = log_collector.get_log_by_id(search_id)

            if not search_log:
                return jsonify({
                    "success": False,
                    "error": f"未找到搜索日志: {search_id}"
                }), 404

            exporter = ExcelExporter()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"search_log_{search_id}_{timestamp}.xlsx"

            # 确保输出目录存在
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, filename)

            success = exporter.export_search_log(search_log, output_path)

            if success:
                return send_file(
                    output_path,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name=filename
                )
            else:
                return jsonify({
                    "success": False,
                    "error": "导出失败"
                }), 500

        except Exception as e:
            logger.error(f"[日志导出] 处理失败: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    return export_bp
