# 测试脚本使用说明

## 📋 概述

本项目包含3个自动化测试脚本，用于验证所有修改和功能是否正常。

---

## 🎯 测试脚本列表

### 1. `tests/test_sidebar_optimization.py`

**用途**: 测试侧边栏优化功能

**测试内容**:
- ✅ 主页访问
- ✅ 搜索历史页面访问
- ✅ 知识点概览页面
- ✅ 评估报告页面
- ✅ 核心API端点

**运行方式**:
```bash
python3 tests/test_sidebar_optimization.py
```

**预期输出**:
```
✅ 检测到服务器运行在 http://localhost:5001
🚀 快速测试：检查页面和API可访问性

页面访问测试:
  ✅ 主页
  ✅ 搜索历史
  ✅ 知识点概览
  ✅ 评估报告

API端点测试:
  ✅ 国家列表
  ✅ 搜索历史

总计: 6 | ✅ 通过: 6 | ❌ 失败: 0
通过率: 100.0%

🎉 所有测试通过！
```

---

### 2. `tests/test_all_pages.py`

**用途**: 全面测试所有页面和功能

**测试内容**:
- ✅ 核心页面（4个）
- ✅ Stage 1 数据可视化页面（3个）
- ✅ Stage 2 智能自动化页面（3个）
- ✅ 核心API（2个）
- ✅ 性能监控API（3个）
- ✅ 配置API（动态测试）

**运行方式**:
```bash
python3 tests/test_all_pages.py
```

**预期输出**:
```
======================================================================
🚀 K12教育资源搜索系统 - 全面功能测试
======================================================================

📝 测试1: 核心页面
✅ 主页
✅ 搜索历史
✅ 知识点概览
✅ 评估报告

📊 测试2: 数据可视化页面 (Stage 1)
✅ 全球资源地图
✅ 实时统计仪表板
✅ 国家资源对比

🤖 测试3: 智能自动化页面 (Stage 2)
✅ 批量国家发现
✅ 系统健康检查
✅ 报告中心

🔌 测试4: 核心API端点
✅ API: 获取国家列表
✅ API: 获取搜索历史

⚙️  测试5: 配置相关API
✅ API: 获取CN配置

📈 测试6: 性能监控API
✅ API: 性能统计
✅ API: 缓存统计
✅ API: 系统指标

======================================================================
测试总结
======================================================================

📊 测试统计:
   总测试数: 16
   ✅ 通过: 16
   ❌ 失败: 0
   通过率: 100.0%

🎉 恭喜！所有测试通过！
```

---

### 3. `run_tests.sh`

**用途**: 一键运行所有测试的便捷脚本

**运行方式**:
```bash
# 方式1: 使用bash
bash run_tests.sh

# 方式2: 直接运行（已添加执行权限）
./run_tests.sh
```

**功能**:
- 自动检查服务器状态
- 依次运行所有测试脚本
- 汇总测试结果

---

## 🚀 快速开始

### 步骤1: 启动服务器

```bash
python3 web_app.py
```

**注意**: 服务器必须在5001端口运行，测试才能执行。

### 步骤2: 运行测试

**选择一种方式**:

```bash
# 方式A: 快速测试（推荐）
python3 tests/test_sidebar_optimization.py

# 方式B: 完整测试
python3 tests/test_all_pages.py

# 方式C: 一键运行所有测试
./run_tests.sh
```

### 步骤3: 查看结果

测试脚本会自动显示：
- ✅ 通过的测试项
- ❌ 失败的测试项
- 📊 通过率统计
- 🎉 测试总结

---

## 📊 测试覆盖范围

### 页面测试（10个）

| # | 页面名称 | 路由 | 功能 |
|---|---------|------|------|
| 1 | 主页 | `/` | 搜索功能 + 180px侧边栏 |
| 2 | 搜索历史 | `/search_history` | **新增**独立历史页面 |
| 3 | 知识点概览 | `/knowledge_points` | 知识点管理 |
| 4 | 评估报告 | `/evaluation_reports` | 视频评估 |
| 5 | 全球资源地图 | `/global_map` | 交互式地图 |
| 6 | 实时统计仪表板 | `/stats_dashboard` | 系统统计 |
| 7 | 国家资源对比 | `/compare` | 多国对比 |
| 8 | 批量国家发现 | `/batch_discovery` | 批量接入 |
| 9 | 系统健康检查 | `/health_status` | 自动化测试 |
| 10 | 报告中心 | `/report_center` | 报告生成 |

### API测试（6+）

| # | API名称 | 路由 | 功能 |
|---|---------|------|------|
| 1 | 国家列表 | `/api/countries` | 获取所有国家 |
| 2 | 搜索历史 | `/api/history` | 获取历史记录 |
| 3 | 国家配置 | `/api/config/{code}` | 获取配置信息 |
| 4 | 性能统计 | `/api/performance_stats` | 性能指标 |
| 5 | 缓存统计 | `/api/cache_stats` | 缓存数据 |
| 6 | 系统指标 | `/api/system_metrics` | 系统资源 |

---

## ✅ 成功标准

### 测试通过的标志

1. **所有HTTP状态码为200**
   - 所有页面可以正常访问
   - 所有API可以正常调用

2. **JSON响应正确**
   - `success: true`
   - 数据结构符合预期

3. **通过率100%**
   - 0个失败项
   - 所有功能正常工作

### 当前测试结果

```
✅ 测试时间: 2026-01-06 09:14:41
✅ 总测试数: 16
✅ 通过: 16
✅ 失败: 0
✅ 通过率: 100.0%
```

---

## 🐛 故障排查

### 问题1: 服务器未运行

**错误信息**:
```
❌ 错误: 服务器未运行或无法访问
```

**解决方案**:
```bash
# 启动服务器
python3 web_app.py

# 等待服务器启动完成（看到 "Running on http://0.0.0.0:5001"）
# 然后在另一个终端运行测试
python3 tests/test_all_pages.py
```

### 问题2: 端口被占用

**错误信息**:
```
Address already in use
Port 5001 is in use by another program.
```

**解决方案**:
```bash
# 查找并终止占用端口的进程
lsof -ti:5001 | xargs kill -9

# 重新启动服务器
python3 web_app.py
```

### 问题3: 页面返回404

**错误信息**:
```
❌ 搜索历史 (状态码: 404)
```

**原因**: 服务器未重启，新路由未加载

**解决方案**:
```bash
# 重启服务器
lsof -ti:5001 | xargs kill -9
python3 web_app.py
```

### 问题4: API返回非200状态码

**错误信息**:
```
❌ API: 获取国家列表 (状态码: 500)
```

**可能原因**:
- 数据库/配置文件损坏
- 模块导入错误
- 权限问题

**解决方案**:
1. 检查服务器日志
2. 确认所有依赖已安装
3. 检查文件权限

---

## 📈 测试最佳实践

### 1. 定期运行测试

**建议频率**:
- 代码修改后：立即运行
- 每天开始工作前：运行一次
- 发布前：完整测试

### 2. 持续集成

可以将测试集成到CI/CD流程：

```yaml
# .github/workflows/test.yml 示例
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start server
        run: python3 web_app.py &
      - name: Run tests
        run: python3 tests/test_all_pages.py
```

### 3. 测试覆盖率

当前测试覆盖：
- ✅ 页面可访问性：100%
- ✅ API响应正确性：100%
- ⚠️ UI交互：需要手动测试
- ⚠️ 跨浏览器：需要手动测试

### 4. 扩展测试

如需添加新测试：

```python
# 在 tests/test_all_pages.py 中添加

def test_new_feature():
    """测试新功能"""
    try:
        response = requests.get("http://localhost:5001/new_feature")
        if response.status_code == 200:
            print("✅ 新功能测试通过")
            return True
        else:
            print(f"❌ 新功能测试失败 - HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 新功能测试失败 - {str(e)}")
        return False
```

---

## 📚 相关文档

- [侧边栏优化总结](../SIDEBAR_OPTIMIZATION_SUMMARY.md) - 详细的优化说明
- [测试报告](./TEST_REPORT.md) - 完整的测试报告
- [UI/UX优化文档](../UI_UX_FINAL_SUMMARY.md) - 第一阶段优化
- [Stage 1 & 2 功能说明](../scalable-zooming-yeti.md) - 实施计划

---

## 🎓 测试学习资源

### Python测试

- [pytest官方文档](https://docs.pytest.org/)
- [requests库文档](https://requests.readthedocs.io/)

### Web测试

- [Selenium文档](https://www.selenium.dev/documentation/)
- [RESTful API测试最佳实践](https://restfulapi.net/testing-restful-api/)

### 持续集成

- [GitHub Actions](https://docs.github.com/en/actions)
- [Travis CI](https://docs.travis-ci.com/)

---

**最后更新**: 2026-01-06
**维护者**: AI开发团队
**版本**: 1.0.0

---

## 📞 支持

如果遇到问题或需要帮助：

1. 查看本文档的"故障排查"部分
2. 查看 [TEST_REPORT.md](./TEST_REPORT.md) 了解详细测试结果
3. 检查服务器日志文件：`search_system.log`

**Happy Testing! 🎉**
