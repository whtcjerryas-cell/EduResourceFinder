#!/usr/bin/env python3
"""
配置路由 - 处理所有配置和国家相关的API请求
"""

import os
from flask import Blueprint, request, jsonify, send_file
from logger_utils import get_logger

logger = get_logger('config_routes')

# 创建蓝图
config_bp = Blueprint('config', __name__)


def init_config_bp(config_manager=None):
    """
    初始化配置路由蓝图

    Args:
        config_manager: 配置管理器实例

    Returns:
        配置好的蓝图
    """
    if config_manager is None:
        from config_manager import ConfigManager
        config_manager = ConfigManager()

    @config_bp.route('/api/countries', methods=['GET'])
    def get_countries():
        """获取所有已配置的国家列表"""
        try:
            countries = config_manager.get_all_countries()
            return jsonify({
                "success": True,
                "countries": countries
            })
        except Exception as e:
            logger.error(f"[国家列表] 获取失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": str(e),
                "countries": []
            }), 500

    @config_bp.route('/api/config/<country_code>', methods=['GET'])
    def get_config(country_code: str):
        """获取指定国家的配置"""
        try:
            country_config = config_manager.get_country_config(country_code)

            if not country_config:
                return jsonify({
                    "success": False,
                    "message": f"未找到国家配置: {country_code}"
                }), 404

            return jsonify({
                "success": True,
                "config": country_config.dict()
            })
        except Exception as e:
            logger.error(f"[国家配置] 获取失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    @config_bp.route('/api/config/education_levels', methods=['GET'])
    def get_education_levels():
        """获取所有教育层级"""
        try:
            # TODO: 实现教育层级获取逻辑
            return jsonify({
                "success": True,
                "education_levels": []
            })
        except Exception as e:
            logger.error(f"[教育层级] 获取失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    @config_bp.route('/api/config/subjects', methods=['GET'])
    def get_subjects():
        """获取所有学科"""
        try:
            country_code = request.args.get('country', '').upper()
            education_level = request.args.get('education_level', '')

            if not country_code:
                return jsonify({
                    "success": False,
                    "message": "请提供国家代码"
                }), 400

            country_config = config_manager.get_country_config(country_code)

            if not country_config:
                return jsonify({
                    "success": False,
                    "message": f"未找到国家配置: {country_code}"
                }), 404

            return jsonify({
                "success": True,
                "subjects": country_config.subjects
            })
        except Exception as e:
            logger.error(f"[学科列表] 获取失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    @config_bp.route('/api/available_subjects', methods=['GET'])
    def get_available_subjects():
        """获取可用学科列表（支持筛选）"""
        try:
            country_code = request.args.get('country', '').strip()
            grade = request.args.get('grade', '').strip()

            if not country_code or not grade:
                return jsonify({
                    "success": False,
                    "message": "请提供国家和年级"
                }), 400

            # 获取国家配置
            country_config = config_manager.get_country_config(country_code.upper())

            if not country_config:
                return jsonify({
                    "success": False,
                    "message": f"未找到国家配置: {country_code}"
                }), 404

            # 查找年级对应的学科
            grade_subject_mappings = country_config.grade_subject_mappings
            grade_key = grade.lower()

            if grade_key in grade_subject_mappings:
                available_subjects = grade_subject_mappings[grade_key].get('subjects', [])
            else:
                # 如果没有特定映射，返回所有学科
                available_subjects = [
                    {'local_name': s['local_name'], 'zh_name': s['zh_name']}
                    for s in country_config.subjects
                ]

            return jsonify({
                "success": True,
                "subjects": available_subjects,
                "country": country_code,
                "grade": grade
            })
        except Exception as e:
            logger.error(f"[可用学科] 获取失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    return config_bp
