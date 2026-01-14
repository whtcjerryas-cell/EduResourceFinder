# 自动化测试文档

## 📋 概述

本目录包含K12教育资源搜索系统的自动化测试套件，用于验证Stage 1和Stage 2的所有功能。

---

## 🧪 测试类型

### 1. 页面访问测试
验证所有新增页面能否正常访问并返回正确的内容。

**测试页面**:
- 首页 (`/`)
- 全球地图 (`/global_map`)
- 统计仪表板 (`/stats_dashboard`)
- 国家对比 (`/compare`)
- 知识点热力图 (`/knowledge_points`)
- 批量发现 (`/batch_discovery`)
- 健康检查 (`/health_status`)
- 报告中心 (`/report_center`)

### 2. API功能测试
验证所有新增API端点是否正常工作。

**测试API**:
- `GET /api/global_stats` - 全球统计数据
- `GET /api/knowledge_point_coverage` - 知识点覆盖率
- `POST /api/compare_countries` - 国家对比
- `GET /api/search_stats` - 搜索统计
- `POST /api/batch_discover_countries` - 批量发现
- `POST /api/health_check` - 健康检查
- `POST /api/generate_report` - 生成报告
- `GET /api/list_reports` - 报告列表

### 3. 核心模块测试
单元测试各个核心模块的功能。

**测试模块**:
- `core.analytics.DataAnalyzer` - 数据分析模块
- `core.health_checker.HealthChecker` - 健康检查器
- `core.report_generator.ReportGenerator` - 报告生成器
- `core.scheduler.TaskScheduler` - 任务调度器
- `core.resource_updater.ResourceUpdater` - 资源更新器

---

## 🚀 快速开始

### 前置要求

1. **确保服务器运行**:
   ```bash
   python3 web_app.py
   ```

2. **安装测试依赖**:
   ```bash
   pip install pytest requests
   ```

### 运行测试

#### 方式1: 快速测试脚本（推荐）

```bash
# 运行所有测试
python3 run_tests.py
```

输出示例：
```
🧪 K12教育资源搜索系统 - 自动化测试
🌐 测试地址: http://localhost:5001

📊 Stage 1: 可视化功能测试
✅ 首页访问 (0.52秒)
✅ 全球地图页面 (0.48秒)
✅ 统计仪表板页面 (0.51秒)
...

📊 测试结果统计
   总计: 20
   通过: 20 ✅
   失败: 0 ❌
   总耗时: 15.32秒

📈 成功率: 100.0%
```

#### 方式2: 使用Pytest

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_stage1_2_features.py

# 运行特定测试类
pytest tests/test_stage1_2_features.py::TestStage1Visualization

# 运行特定测试方法
pytest tests/test_stage1_2_features.py::TestStage1Visualization::test_global_map_page

# 显示详细输出
pytest -v

# 显示print输出
pytest -v -s
```

#### 方式3: 使用标记

```bash
# 只运行Stage 1测试
pytest -m stage1

# 只运行Stage 2测试
pytest -m stage2

# 只运行API测试
pytest -m api

# 只运行单元测试
pytest -m unit

# 排除慢速测试
pytest -m "not slow"
```

---

## 📊 测试覆盖范围

### Stage 1: 可视化功能 ✅

| 功能 | 测试覆盖 | 状态 |
|------|---------|------|
| 全球教育资源地图 | 页面访问、API | ✅ |
| 实时统计仪表板 | 页面访问、API | ✅ |
| 国家资源对比 | 页面访问、API | ✅ |
| 知识点热力图 | 页面访问、API | ✅ |

### Stage 2: 自动化功能 ✅

| 功能 | 测试覆盖 | 状态 |
|------|---------|------|
| 批量国家发现 | 页面访问、API、模块 | ✅ |
| 系统健康检查 | 页面访问、API、模块 | ✅ |
| 报告中心 | 页面访问、API、模块 | ✅ |
| 定时任务调度 | 模块测试 | ✅ |
| 资源更新 | 模块测试 | ✅ |

---

## 🔧 测试配置

### pytest.ini

测试配置文件 `pytest.ini` 包含：
- 测试文件匹配模式
- 输出格式设置
- 标记定义
- 超时设置

### 测试超时

- 默认超时: 60秒
- 健康检查: 60秒（可能需要较长时间）
- 报告生成: 60秒（可能需要较长时间）
- 其他测试: 10秒

---

## 📝 添加新测试

### 1. 添加页面测试

```python
@test_case("新功能页面")
def test_new_feature_page():
    response = requests.get(f"{BASE_URL}/new_feature", timeout=10)
    assert response.status_code == 200
    assert "预期内容" in response.text
```

### 2. 添加API测试

```python
@test_case("新功能API")
def test_new_feature_api():
    response = requests.post(
        f"{BASE_URL}/api/new_feature",
        json={'param': 'value'},
        timeout=10
    )
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
```

### 3. 添加模块测试

```python
@test_case("新模块")
def test_new_module():
    from core.new_module import NewClass
    obj = NewClass()
    result = obj.method()
    assert result is not None
```

---

## 🐛 调试测试

### 查看详细输出

```bash
# 显示print输出
pytest -v -s

# 显示更详细的错误信息
pytest --tb=long

# 只运行失败的测试
pytest --lf

# 遇到第一个失败就停止
pytest -x
```

### 调试单个测试

```python
# 在测试中添加断点
import pdb; pdb.set_trace()

# 或者使用print调试
print(f"Debug info: {variable}")
```

---

## 📈 持续集成

### GitHub Actions示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest requests

    - name: Start server
      run: python3 web_app.py &
      env:
        PORT: 5001

    - name: Run tests
      run: python3 run_tests.py
```

---

## ⚠️ 常见问题

### 问题1: 无法连接到服务器

**错误**: `ConnectionError: Failed to establish connection`

**解决方案**:
```bash
# 确保服务器正在运行
python3 web_app.py

# 检查端口占用
lsof -ti:5001
```

### 问题2: 测试超时

**错误**: `ReadTimeout: HTTPConnectionPool...`

**解决方案**:
- 增加测试超时时间
- 检查API性能
- 使用 `@pytest.mark.slow` 标记慢速测试

### 问题3: 模块导入失败

**错误**: `ModuleNotFoundError: No module named 'core.xxx'`

**解决方案**:
```bash
# 确保在项目根目录运行
cd /path/to/Indonesia
python3 run_tests.py

# 或者设置PYTHONPATH
export PYTHONPATH=/path/to/Indonesia:$PYTHONPATH
```

---

## 📚 相关文档

- [项目README](../README.md)
- [Stage 1 & 2总结](../STAGE1_2_SUMMARY.md)
- [API文档](../docs/API.md)

---

## 🎯 测试目标

- **覆盖率目标**: >80%
- **通过率目标**: 100%
- **响应时间目标**: <5秒（大部分API）

---

**最后更新**: 2026-01-05
**维护者**: Claude Code
