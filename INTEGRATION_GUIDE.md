# 规则搜索引擎集成指南

## 📋 当前系统架构

### 已有组件
- ✅ **Flask Web应用** (`web_app.py`)
- ✅ **搜索API** (`/api/search`)
- ✅ **前端界面** (`templates/index.html`)
- ✅ **AI搜索引擎** (`search_engine_v2.py`)

### 新增组件
- ✅ **规则搜索引擎** (`core/rule_based_search.py`) - **已测试通过**
- ✅ **配置文件** (`config/country_search_config.yaml`)

---

## 🎯 集成方案

### 方案1：添加新API endpoint（推荐）✅

**优点**：
- 不影响现有AI搜索功能
- 可以A/B测试两种搜索方式
- 前端可以选择使用哪种搜索

**实现步骤**：

#### 1. 在 `web_app.py` 添加新的API endpoint

```python
@app.route('/api/search/rule-based', methods=['POST'])
@require_api_key
def search_rule_based():
    """规则搜索引擎API - 基于YAML配置的本地化搜索"""

    request_id = str(uuid.uuid4())[:8]
    set_request_id(request_id)

    try:
        logger.info(f"[规则搜索] 开始处理搜索请求 [ID: {request_id}]")

        data = request.get_json()

        # 输入验证
        from core.input_validators import validate_search_request
        is_valid, error_msg, validated_data = validate_search_request(data)

        if not is_valid:
            return jsonify({
                "success": False,
                "message": f"输入验证失败: {error_msg}",
                "results": []
            }), 400

        country = validated_data.country
        grade = validated_data.grade
        subject = validated_data.subject

        logger.info(f"[规则搜索] 国家={country}, 年级={grade}, 学科={subject}")

        # 使用规则搜索引擎
        from core.rule_based_search import RuleBasedSearchEngine

        engine = RuleBasedSearchEngine()
        result = engine.search(
            country=country,
            grade=grade,
            subject=subject,
            max_results=20
        )

        # 转换为前端格式
        formatted_results = []
        for item in result['results']:
            formatted_results.append({
                "url": item['url'],
                "title": item.get('title', 'N/A'),
                "snippet": item.get('snippet', ''),
                "score": item['score'],
                "score_reason": item.get('score_reason', ''),
                "source": "rule_based_search"
            })

        response = {
            "success": True,
            "message": f"找到 {len(formatted_results)} 个结果",
            "results": formatted_results,
            "localized_info": result['localized_info'],
            "search_metadata": result['search_metadata']
        }

        logger.info(f"[规则搜索] 返回 {len(formatted_results)} 个结果 [ID: {request_id}]")

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"[规则搜索] 搜索失败: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"搜索失败: {str(e)}",
            "results": []
        }), 500
```

#### 2. 前端调用（添加到 `templates/index.html`）

```javascript
// 规则搜索函数
async function searchWithRuleBased(country, grade, subject) {
    const response = await fetch('/api/search/rule-based', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': 'your-api-key'
        },
        body: JSON.stringify({
            country: country,
            grade: grade,
            subject: subject
        })
    });

    const data = await response.json();

    if (data.success) {
        displayResults(data.results);
        displayMetadata(data.localized_info, data.search_metadata);
    } else {
        showError(data.message);
    }
}

// 显示本地化信息
function displayMetadata(localizedInfo, metadata) {
    console.log('本地化信息:', localizedInfo);
    console.log('使用的查询:', metadata.queries_used);

    // 在页面上显示
    document.getElementById('localized-grade').textContent = localizedInfo.grade;
    document.getElementById('localized-subject').textContent = localizedInfo.subject;
    document.getElementById('queries-used').textContent = metadata.queries_used.join(', ');
}
```

---

### 方案2：修改现有 `/api/search`（高级）

**优点**：
- 统一的搜索接口
- 可以根据配置自动选择搜索方式

**实现**：

在现有的 `/api/search` endpoint中添加搜索模式选择：

```python
# 在搜索API中添加模式选择
search_mode = data.get('search_mode', 'ai')  # 'ai' 或 'rule_based'

if search_mode == 'rule_based':
    # 使用规则搜索引擎
    from core.rule_based_search import RuleBasedSearchEngine
    engine = RuleBasedSearchEngine()
    result = engine.search(country, grade, subject)
    # ... 转换结果格式
else:
    # 使用现有AI搜索引擎
    search_request = SearchRequest(...)
    result = search_engine_v2.search(search_request)
    # ... 现有逻辑
```

---

## 🚀 快速开始

### Step 1: 添加API endpoint

在 `web_app.py` 的第1130行（`/api/batch_evaluate_videos` 之前）添加上面的新endpoint代码。

### Step 2: 测试API

```bash
# 启动服务器
python3 web_app.py

# 测试API（使用curl）
curl -X POST http://localhost:5000/api/search/rule-based \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "country": "ID",
    "grade": "1",
    "subject": "math"
  }'
```

### Step 3: 前端集成

在 `templates/index.html` 添加：
1. 规则搜索按钮
2. 规则搜索函数
3. 结果显示区域

---

## 📊 API响应格式

### 成功响应
```json
{
  "success": true,
  "message": "找到 10 个结果",
  "results": [
    {
      "url": "https://ruangguru.com/math1",
      "title": "Matematika SD Kelas 1",
      "snippet": "Belajar matematika...",
      "score": 9.5,
      "score_reason": "Trusted domain: ruangguru.com (9.5)",
      "source": "rule_based_search"
    }
  ],
  "localized_info": {
    "country": "ID",
    "grade": "SD Kelas 1",
    "subject": "Matematika",
    "curriculum": "Kurikulum Merdeka",
    "supported": true
  },
  "search_metadata": {
    "queries_used": [
      "Matematika SD Kelas 1 Kurikulum Merdeka",
      "Matematika SD Kelas 1 SD"
    ],
    "total_found": 10,
    "top_score": 9.5,
    "search_method": "rule_based"
  }
}
```

### 错误响应
```json
{
  "success": false,
  "message": "国家代码无效",
  "results": []
}
```

---

## 🎨 前端界面建议

### 添加搜索模式选择器

```html
<div class="search-mode-selector">
    <label>
        <input type="radio" name="search_mode" value="ai" checked>
        AI搜索（智能但慢）
    </label>
    <label>
        <input type="radio" name="search_mode" value="rule_based">
        规则搜索（快速且准确）
    </label>
</div>
```

### 显示本地化信息

```html
<div class="localized-info" id="localized-info">
    <h3>📍 搜索信息</h3>
    <p>年级: <span id="localized-grade">-</span></p>
    <p>学科: <span id="localized-subject">-</span></p>
    <p>课程: <span id="localized-curriculum">-</span></p>
    <p>使用查询: <span id="queries-used">-</span></p>
</div>
```

---

## 📝 集成检查清单

### 后端集成
- [ ] 添加 `/api/search/rule-based` endpoint
- [ ] 测试API端点（curl或Postman）
- [ ] 验证输入验证正常工作
- [ ] 验证错误处理正常工作
- [ ] 检查日志输出

### 前端集成
- [ ] 添加搜索模式选择器
- [ ] 实现规则搜索函数
- [ ] 添加结果显示
- [ ] 添加本地化信息显示
- [ ] 测试用户交互

### 测试
- [ ] 测试印尼搜索
- [ ] 测试DEFAULT配置（沙特、美国等）
- [ ] 测试错误情况（无效国家、年级）
- [ ] 测试并发请求
- [ ] 性能测试（响应时间）

---

## 💡 使用建议

### 何时使用规则搜索？
- ✅ 已配置的国家（印尼等）
- ✅ 需要快速响应
- ✅ 需要一致的结果
- ✅ 需要节省API成本

### 何时使用AI搜索？
- ✅ 未配置的国家
- ✅ 需要智能理解
- ✅ 复杂查询
- ✅ 探索性搜索

### 混合策略
```python
# 优先使用规则搜索，fallback到AI
if country in configured_countries:
    use_rule_based_search()
else:
    use_ai_search()
```

---

## 🔧 常见问题

### Q1: 测试通过了，为什么不能直接用？
A: 测试验证的是**代码逻辑**，但集成到系统需要：
1. **API接口** - 前后端通信
2. **数据格式转换** - 统一返回格式
3. **前端UI** - 展示结果
4. **错误处理** - 用户体验

### Q2: 需要多久完成集成？
A: **1-2小时**
- 添加API endpoint: 30分钟
- 测试API: 15分钟
- 前端集成: 30-45分钟

### Q3: 会影响现有功能吗？
A: **不会** - 添加新endpoint，不修改现有代码

### Q4: 需要安装依赖吗？
A: **不需要** - 规则搜索引擎的依赖已满足：
- ✅ PyYAML
- ✅ logging
- ✅ dataclasses

---

## 📞 下一步

### 选项1：自动集成
我可以帮您：
1. 修改 `web_app.py` 添加新endpoint
2. 修改 `templates/index.html` 添加前端代码
3. 测试完整流程

### 选项2：手动集成
按照本文档逐步集成，遇到问题随时询问。

### 选项3：创建独立应用
创建一个新的Flask应用专门用于规则搜索，与现有系统并行运行。

---

*准备好开始集成了吗？告诉我您的选择！* 🚀
