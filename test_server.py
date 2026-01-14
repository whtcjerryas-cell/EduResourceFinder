#!/usr/bin/env python3
"""
简单的测试服务器 - 用于Playwright测试规则搜索引擎
"""

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
CORS(app)

# 尝试导入规则搜索引擎
try:
    from core.rule_based_search import RuleBasedSearchEngine
    HAS_ENGINE = True
    print("✅ 规则搜索引擎加载成功")
except ImportError as e:
    HAS_ENGINE = False
    print(f"⚠️  规则搜索引擎加载失败: {e}")

@app.route('/')
def index():
    """主页"""
    return '''
    <h1>规则搜索引擎测试服务器</h1>
    <p><a href="/rule_search_demo.html">规则搜索演示页面</a></p>
    <p><a href="/api/search/rule-based/config">查看配置API</a></p>
    '''

@app.route('/rule_search_demo.html')
def demo_page():
    """演示页面"""
    try:
        return render_template('rule_search_demo.html')
    except:
        return """
        <h1>演示页面未找到</h1>
        <p>请确保 templates/rule_search_demo.html 文件存在</p>
        """

@app.route('/api/search', methods=['POST'])
def search_unified():
    """统一搜索API - 支持AI和规则搜索"""

    if not HAS_ENGINE:
        return jsonify({
            "success": False,
            "message": "搜索引擎未加载",
            "results": []
        }), 500

    try:
        data = request.get_json()
        search_mode = data.get('search_mode', 'rule_based')

        if search_mode == 'ai':
            # AI搜索模式 - 当前开发中
            return jsonify({
                "success": False,
                "message": "⚠️ AI搜索功能正在开发中，请使用规则搜索",
                "results": [],
                "dev_note": "AI搜索计划于2026年Q2上线",
                "localized_info": {
                    "supported": True,
                    "under_development": True
                }
            }), 501  # 501 Not Implemented
        else:
            # 规则搜索模式 - 重定向到规则搜索endpoint
            return search_rule_based()

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"搜索失败: {str(e)}",
            "results": []
        }), 500


@app.route('/api/search/rule-based', methods=['POST'])
def search_rule_based():
    """规则搜索API"""

    if not HAS_ENGINE:
        return jsonify({
            "success": False,
            "message": "规则搜索引擎未加载",
            "results": []
        }), 500

    try:
        data = request.get_json()
        country = data.get('country', 'ID')
        grade = data.get('grade', '1')
        subject = data.get('subject', 'math')
        max_results = data.get('max_results', 20)

        print(f"搜索请求: country={country}, grade={grade}, subject={subject}")

        engine = RuleBasedSearchEngine()
        result = engine.search(
            country=country,
            grade=grade,
            subject=subject,
            max_results=max_results
        )

        # 格式化结果
        formatted_results = []
        for item in result['results']:
            formatted_results.append({
                "url": item['url'],
                "title": item.get('title', 'N/A'),
                "snippet": item.get('snippet', ''),
                "score": item['score'],
                "score_reason": item.get('score_reason', ''),
                "source": "rule_based_search",
                "type": "video"
            })

        response = {
            "success": True,
            "message": f"找到 {len(formatted_results)} 个结果",
            "results": formatted_results,
            "localized_info": result['localized_info'],
            "search_metadata": result['search_metadata']
        }

        print(f"返回 {len(formatted_results)} 个结果")
        return jsonify(response), 200

    except Exception as e:
        print(f"搜索失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"搜索失败: {str(e)}",
            "results": []
        }), 500

@app.route('/api/search/rule-based/config', methods=['GET'])
def get_config():
    """获取配置"""

    if not HAS_ENGINE:
        return jsonify({
            "success": False,
            "message": "规则搜索引擎未加载"
        }), 500

    try:
        engine = RuleBasedSearchEngine()
        supported_countries = list(engine.config.keys())

        return jsonify({
            "success": True,
            "supported_countries": supported_countries,
            "has_default": 'DEFAULT' in engine.config
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

if __name__ == '__main__':
    PORT = 5007
    print("=" * 60)
    print("🚀 规则搜索引擎测试服务器")
    print("=" * 60)
    print("访问地址:")
    print(f"  - 主页: http://localhost:{PORT}/")
    print(f"  - 演示: http://localhost:{PORT}/rule_search_demo.html")
    print(f"  - API: http://localhost:{PORT}/api/search/rule-based")
    print("=" * 60)

    app.run(host='0.0.0.0', port=PORT, debug=True)
