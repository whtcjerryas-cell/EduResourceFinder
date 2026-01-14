# Indonesia 搜索系统 - 快速使用指南

**版本**: V3.2.0
**更新日期**: 2026-01-05
**适用对象**: 开发者、测试人员、研究人员

---

## 目录

1. [快速开始](#快速开始)
2. [Web 界面使用](#web-界面使用)
3. [API 使用指南](#api-使用指南)
4. [支持的国家](#支持的国家)
5. [常见问题](#常见问题)
6. [性能优化技巧](#性能优化技巧)
7. [故障排查](#故障排查)

---

## 快速开始

### 1. 启动系统

```bash
# 进入项目目录
cd ~/Desktop/education/Indonesia

# 激活虚拟环境
source venv/bin/activate

# 启动 Web 服务
python3 web_app.py
```

系统将在 http://localhost:5001 启动

### 2. 访问界面

打开浏览器访问：http://localhost:5001

### 3. 开始搜索

1. 选择国家
2. 选择年级
3. 选择学科
4. 点击"搜索"按钮

---

## Web 界面使用

### 主页功能

#### 搜索表单

**必填字段**：
- 🌍 **国家**：从下拉菜单选择（支持 10 个国家）
- 📚 **年级**：根据国家自动显示对应年级
- 📖 **学科**：根据国家自动显示对应学科

**可选字段**：
- 📅 **学期**：某些国家支持学期选择
- 🌐 **语言**：可以指定搜索语言

#### 按钮功能

- **🔍 搜索**：执行搜索请求
- **🐛 Debug 日志**：查看实时日志
- **📊 查看历史**：查看搜索历史记录
- **📥 导出结果**：导出搜索结果为 Excel

### 知识点页面

访问：http://localhost:5001/knowledge_points

功能：
- 📊 查看所有知识点统计
- 📈 可视化图表展示
- 🔍 按国家/年级/学科筛选
- 📋 知识点详情查看

---

## API 使用指南

### 基础搜索

**端点**: `POST /api/search`

#### 最简单的请求

```json
{
  "country": "Indonesia",
  "grade": "Kelas 10",
  "subject": "Matematika"
}
```

#### 完整参数请求

```json
{
  "country": "China",
  "grade": "高中一",
  "subject": "数学",
  "semester": "上学期",
  "language": "zh"
}
```

### 响应格式

```json
{
  "success": true,
  "message": "搜索成功",
  "query": "Matematika Kelas 10",
  "results": [
    {
      "title": "资源标题",
      "url": "https://example.com/resource",
      "snippet": "资源描述...",
      "score": 7.5,
      "source": "Google搜索",
      "recommendation_reason": "默认推荐"
    }
  ],
  "debug_logs": ["日志条目..."]
}
```

### 其他常用 API

#### 1. 获取国家列表

```bash
GET /api/countries
```

响应：
```json
{
  "success": true,
  "countries": [
    {"country_code": "ID", "country_name": "Indonesia"},
    {"country_code": "CN", "country_name": "China"}
  ]
}
```

#### 2. 获取国家配置

```bash
GET /api/config/ID
```

响应包含：
- 年级列表
- 学科列表
- 支持的域名
- 语言配置

#### 3. 获取搜索历史

```bash
GET /api/history
```

#### 4. 获取知识点

```bash
GET /api/knowledge_points?country=Indonesia&grade=Kelas%2010&subject=Matematika
```

#### 5. 查看调试日志

```bash
GET /api/debug_logs
```

---

## 支持的国家

### 已验证国家（7个）

| 国家 | 代码 | 语言 | 年级示例 | 学科示例 |
|------|------|------|----------|----------|
| 🇮🇩 印尼 | ID | 印尼语 | Kelas 10 | Matematika |
| 🇨🇳 中国 | CN | 中文 | 高中一 | 数学 |
| 🇮🇳 印度 | IN | 英语 | Class 10 | Mathematics |
| 🇵🇭 菲律宾 | PH | 英语 | Grade 10 | Mathematics |
| 🇷🇺 俄罗斯 | RU | 俄语 | 10 класс | Математика |
| 🇪🇬 埃及 | EG | 英语 | Grade 10 | Science |
| 🇿🇦 南非 | ZA | 英语 | Grade 10 | Mathematics |

### 配置的国家（10个）

还包括：
- 🇸🇦 沙特阿拉伯 (SA)
- 🇮🇶 伊拉克 (IQ)
- 🇳🇬 尼日利亚 (NG)

---

## 常见问题

### Q1: 搜索速度慢怎么办？

**A**: 几种解决方案：

1. **使用缓存**：重复搜索会非常快（< 10ms）
2. **并发搜索**：批量搜索时使用并发请求
3. **检查网络**：某些国家（如俄罗斯）可能网络延迟较高

```python
# 并发搜索示例
from concurrent.futures import ThreadPoolExecutor

def search(country, grade, subject):
    # 执行搜索
    pass

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(search, *args) for args in search_list]
```

### Q2: 如何添加新国家？

**A**: 两种方法：

**方法 1: Web 界面**
1. 点击"🌍 添加国家"按钮
2. 输入国家名称（英文）
3. 系统自动调研并添加

**方法 2: API**

```bash
POST /api/discover_country
{
  "country_name": "Japan"
}
```

### Q3: 搜索结果不相关怎么办？

**A**: 优化搜索建议：

1. **使用更具体的年级和学科**
2. **检查学科名称是否正确**（使用本地化名称）
3. **查看 Debug 日志**了解搜索过程
4. **尝试不同的学期**（如果支持）

### Q4: 如何导出搜索结果？

**A**: 多种导出方式：

1. **Web 界面**：点击"📥 导出结果"按钮
2. **API 调用**：

```bash
POST /api/export_excel
{
  "results": [...]
}
```

3. **手动处理**：从 API 响应中提取数据

### Q5: API 返回错误怎么办？

**A**: 常见错误处理：

| 错误代码 | 说明 | 解决方案 |
|---------|------|----------|
| 400 | 参数缺失 | 检查必填参数 |
| 404 | 路径无效 | 检查 API 路径 |
| 500 | 服务器错误 | 查看 Debug 日志 |

---

## 性能优化技巧

### 1. 利用缓存

```python
# 第一次搜索：慢（~5-10秒）
result1 = search(country="Indonesia", grade="Kelas 10", subject="Matematika")

# 第二次搜索：快（< 10ms）
result2 = search(country="Indonesia", grade="Kelas 10", subject="Matematika")
```

### 2. 并发批量搜索

```python
import requests
from concurrent.futures import ThreadPoolExecutor

def perform_search(payload):
    response = requests.post(
        "http://localhost:5001/api/search",
        json=payload,
        timeout=120
    )
    return response.json()

# 批量搜索
searches = [
    {"country": "Indonesia", "grade": "Kelas 10", "subject": "Matematika"},
    {"country": "China", "grade": "高中一", "subject": "数学"},
    {"country": "India", "grade": "Class 10", "subject": "Mathematics"}
]

with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(perform_search, searches))

# 性能：5个并发请求只需 1.61s（串行需要 8.90s）
```

### 3. 选择合适的搜索引擎

系统会自动选择，但你可以在配置中优化：

- **中文内容**：优先使用百度 API
- **国际内容**：优先使用 Google API
- **备用**：Tavily API

### 4. 减少不必要的参数

```python
# 好：简单快速
{"country": "Indonesia", "grade": "Kelas 10", "subject": "Matematika"}

# 如果不需要，不要添加可选参数
```

---

## 故障排查

### 问题 1: 服务无法启动

**症状**: 端口被占用

```bash
# 检查端口占用
lsof -i :5001

# 终止进程
kill <PID>

# 或使用脚本重启
bash scripts/restart_web_app.sh
```

### 问题 2: 搜索无结果

**可能原因**：
1. 网络问题
2. API 密钥失效
3. 搜索引擎限制

**解决方案**：
```bash
# 检查 API 密钥
cat .env

# 查看 Debug 日志
curl http://localhost:5001/api/debug_logs

# 重启服务
python3 web_app.py
```

### 问题 3: 性能突然下降

**检查项**：
1. 查看日志文件大小：`search_system.log`
2. 检查缓存是否生效
3. 测试网络连接
4. 查看搜索引擎 API 状态

### 问题 4: 某个国家搜索特别慢

**已知情况**：
- 俄罗斯搜索：~16-17s（正常）
- 埃及搜索：~8-9s（正常）

**优化方案**：
1. 使用并发搜索
2. 利用缓存
3. 考虑调整搜索引擎优先级

---

## 高级用法

### 1. 批量搜索所有组合

```python
countries = ["Indonesia", "China", "India"]
grades = ["Kelas 10", "高中一", "Class 10"]
subjects = ["Matematika", "数学", "Mathematics"]

# 生成所有组合
from itertools import product
combinations = product(countries, grades, subjects)

# 并发执行
with ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(lambda x: search(*x), combinations)
```

### 2. 搜索结果分析

```python
results = response.json()

# 按评分筛选
high_quality = [r for r in results['results'] if r['score'] > 7.0]

# 按来源分组
by_source = {}
for r in results['results']:
    source = r['source']
    if source not in by_source:
        by_source[source] = []
    by_source[source].append(r)
```

### 3. 自定义评分

```python
# 根据需要调整结果排序
sorted_results = sorted(
    results['results'],
    key=lambda x: (
        x['score'],
        'edu' in x['url'],  # 优先教育网站
        len(x['snippet'])   # 优先详细描述
    ),
    reverse=True
)
```

---

## 实用脚本

### 测试脚本

```python
#!/usr/bin/env python3
import requests

BASE_URL = "http://localhost:5001"

def test_search():
    payload = {
        "country": "Indonesia",
        "grade": "Kelas 10",
        "subject": "Matematika"
    }

    response = requests.post(f"{BASE_URL}/api/search", json=payload)
    data = response.json()

    if data['success']:
        print(f"✅ 搜索成功！找到 {len(data['results'])} 个结果")
        for i, result in enumerate(data['results'][:3], 1):
            print(f"{i}. {result['title']}")
    else:
        print(f"❌ 搜索失败: {data['message']}")

if __name__ == "__main__":
    test_search()
```

### 批量测试脚本

```python
#!/usr/bin/env python3
import requests
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://localhost:5001"

TESTS = [
    {"country": "Indonesia", "grade": "Kelas 10", "subject": "Matematika"},
    {"country": "China", "grade": "高中一", "subject": "数学"},
    {"country": "India", "grade": "Class 10", "subject": "Mathematics"}
]

def test_search(payload):
    response = requests.post(f"{BASE_URL}/api/search", json=payload)
    return payload['country'], response.json()

with ThreadPoolExecutor(max_workers=3) as executor:
    results = executor.map(test_search, TESTS)

    for country, data in results:
        status = "✅" if data['success'] else "❌"
        print(f"{status} {country}: {len(data.get('results', []))} results")
```

---

## 联系和支持

### 文档

- 项目 README: `~/Desktop/education/Indonesia/README.md`
- 综合测试报告: `COMPREHENSIVE_TEST_REPORT.md`
- 技术文档: `docs/TECHNICAL_DOCUMENTATION_V3.md`

### 日志

- 系统日志: `search_system.log`
- Debug 日志: http://localhost:5001/api/debug_logs

### 测试报告

- 迭代 1: `TEST_REPORT_2026-01-05.md`
- 迭代 2: `TEST_REPORT_ITERATION_2.md`
- 综合报告: `COMPREHENSIVE_TEST_REPORT.md`

---

**更新日期**: 2026-01-05
**版本**: V3.2.0
**测试状态**: ✅ 所有功能正常

**祝您使用愉快！** 🎉
