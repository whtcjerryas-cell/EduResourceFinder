"""
规则搜索引擎集成补丁

使用方法：
1. 备份现有 web_app.py: cp web_app.py web_app_backup_before_rule_based_search.py
2. 运行此脚本: python3 integrate_rule_based_search.py
3. 重启服务器: python3 web_app.py
"""

import re

# 要添加的代码
NEW_ENDPOINT_CODE = '''
# ============================================================================
# 规则搜索引擎 API (基于YAML配置的本地化搜索)
# ============================================================================

@app.route('/api/search/rule-based', methods=['POST'])
@require_api_key
def search_rule_based():
    """规则搜索引擎API - 使用YAML配置的本地化搜索

    优点：
    - 快速响应（无需AI调用）
    - 结果一致（基于规则）
    - 零成本（无API费用）
    - 支持本地化（多国配置）

    API请求格式:
    {
        "country": "ID",      # 国家代码
        "grade": "1",         # 年级
        "subject": "math",    # 学科
        "max_results": 20     # 可选，返回结果数
    }

    API响应格式:
    {
        "success": true,
        "results": [...],
        "localized_info": {...},
        "search_metadata": {...}
    }
    """

    request_id = str(uuid.uuid4())[:8]
    set_request_id(request_id)

    # 并发限制检查
    acquired_limiter = False
    if concurrency_limiter is not None:
        if concurrency_limiter.acquire(timeout=5.0):
            acquired_limiter = True
        else:
            logger.warning(f"[规则搜索] 搜索请求被限流: 超过最大并发数")
            return jsonify({
                "success": False,
                "message": "服务器繁忙，请稍后重试",
                "results": []
            }), 503

    try:
        logger.info(f"[规则搜索] 开始处理搜索请求 [ID: {request_id}]")
        logger.debug(f"[规则搜索] 请求数据: {json.dumps(request.get_json(), ensure_ascii=False)}")

        data = request.get_json()

        # ======================================================================
        # 输入验证
        # ======================================================================
        from core.input_validators import validate_search_request

        is_valid, error_msg, validated_data = validate_search_request(data)
        if not is_valid:
            logger.warning(f"[规则搜索] 输入验证失败: {error_msg}")
            return jsonify({
                "success": False,
                "message": f"输入验证失败: {error_msg}",
                "results": []
            }), 400

        # 使用验证后的安全数据
        country = validated_data.country
        grade = validated_data.grade
        subject = validated_data.subject
        max_results = data.get('max_results', 20)

        logger.info(f"[规则搜索] 国家={country}, 年级={grade}, 学科={subject}, 最大结果={max_results}")

        # ======================================================================
        # 执行规则搜索
        # ======================================================================
        from core.rule_based_search import RuleBasedSearchEngine

        logger.debug(f"[规则搜索] 初始化规则搜索引擎...")
        engine = RuleBasedSearchEngine()

        logger.info(f"[规则搜索] 执行搜索 [ID: {request_id}]")
        result = engine.search(
            country=country,
            grade=grade,
            subject=subject,
            max_results=max_results
        )

        # ======================================================================
        # 格式化结果
        # ======================================================================
        formatted_results = []
        for item in result['results']:
            formatted_results.append({
                "url": item['url'],
                "title": item.get('title', 'N/A'),
                "snippet": item.get('snippet', ''),
                "score": item['score'],
                "score_reason": item.get('score_reason', ''),
                "source": "rule_based_search",
                "type": "video"  # 默认类型，可以根据实际调整
            })

        # ======================================================================
        # 构建响应
        # ======================================================================
        response_data = {
            "success": True,
            "message": f"找到 {len(formatted_results)} 个结果",
            "results": formatted_results,
            "localized_info": result['localized_info'],
            "search_metadata": result['search_metadata'],
            "request_id": request_id
        }

        logger.info(
            f"[规则搜索] 搜索成功 [ID: {request_id}] "
            f"返回={len(formatted_results)}个结果, "
            f"最高分={result['search_metadata']['top_score']:.1f}, "
            f"支持={result['localized_info']['supported']}"
        )

        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"[规则搜索] 搜索失败 [ID: {request_id}]: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"搜索失败: {str(e)}",
            "results": [],
            "request_id": request_id
        }), 500

    finally:
        # 释放并发限制器
        if acquired_limiter and concurrency_limiter is not None:
            concurrency_limiter.release()
            logger.debug(f"[规则搜索] 释放并发限制器 [ID: {request_id}]")


# ============================================================================
# 规则搜索配置查询API
# ============================================================================

@app.route('/api/search/rule-based/config', methods=['GET'])
def get_rule_based_config():
    """获取规则搜索配置信息

    返回当前支持的国家和配置
    """
    try:
        from core.rule_based_search import RuleBasedSearchEngine

        engine = RuleBasedSearchEngine()

        # 获取支持的国家
        supported_countries = list(engine.config.keys())

        # 获取每个国家的详细信息
        country_details = {}
        for country_code in supported_countries:
            if country_code == 'DEFAULT':
                continue

            country_config = engine.config[country_code]
            grades_subjects = []

            for grade_key, grade_data in country_config.items():
                if grade_key.startswith('grade_'):
                    grade_num = grade_key.replace('grade_', '')
                    subjects = list(grade_data.keys())
                    grades_subjects.append({
                        'grade': grade_num,
                        'subjects': subjects
                    })

            country_details[country_code] = {
                'grades_subjects': grades_subjects
            }

        return jsonify({
            "success": True,
            "supported_countries": supported_countries,
            "country_details": country_details,
            "has_default": 'DEFAULT' in engine.config
        }), 200

    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


'''

def integrate():
    """集成规则搜索引擎到web_app.py"""

    print("=" * 70)
    print("🔧 规则搜索引擎集成工具")
    print("=" * 70)

    # 读取web_app.py
    print("\n📖 读取 web_app.py...")
    with open('web_app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已经集成
    if '/api/search/rule-based' in content:
        print("⚠️  检测到规则搜索API已存在，跳过集成")
        return

    # 找到插入位置（在 /api/batch_evaluate_videos 之前）
    marker = "@app.route('/api/batch_evaluate_videos'"
    if marker not in content:
        print(f"❌ 未找到插入位置: {marker}")
        print("请手动添加规则搜索endpoint")
        return

    # 插入新代码
    print("📝 插入规则搜索API...")
    content = content.replace(marker, NEW_ENDPOINT_CODE + "\n" + marker)

    # 备份原文件
    print("💾 备份原文件到 web_app_backup_before_rule_based_search.py...")
    with open('web_app_backup_before_rule_based_search.py', 'w', encoding='utf-8') as f:
        # 重新读取原文件内容
        with open('web_app.py', 'r', encoding='utf-8') as original:
            f.write(original.read())

    # 写入修改后的内容
    print("💾 写入修改后的 web_app.py...")
    with open('web_app.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("\n" + "=" * 70)
    print("✅ 集成完成！")
    print("=" * 70)
    print("\n📋 新增API endpoints:")
    print("   1. POST /api/search/rule-based - 规则搜索")
    print("   2. GET  /api/search/rule-based/config - 查询配置")
    print("\n🧪 测试命令:")
    print("   curl -X POST http://localhost:5000/api/search/rule-based \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -H 'X-API-Key: dev-key-123' \\")
    print("     -d '{\"country\": \"ID\", \"grade\": \"1\", \"subject\": \"math\"}'")
    print("\n🚀 启动服务器:")
    print("   python3 web_app.py")
    print("\n📖 查看集成指南:")
    print("   cat INTEGRATION_GUIDE.md")
    print()


if __name__ == "__main__":
    try:
        integrate()
    except FileNotFoundError:
        print("❌ 错误: 找不到 web_app.py")
        print("请在项目根目录运行此脚本")
    except Exception as e:
        print(f"❌ 集成失败: {e}")
        import traceback
        traceback.print_exc()
