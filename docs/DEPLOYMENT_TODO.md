# Indonesia K12 Video Search System - 部署上线 TODO List

**项目**: Indonesia K12 Video Search System V3
**目标**: 将现有V3项目部署到生产环境，给老板演示
**项目路径**: `/Users/shmiwanghao8/Desktop/education/Indonesia`
**团队**: 产品经理（业务优化） + 2个后端开发（部署支持）
**工期**: 3-5人天
**最后更新**: 2026-01-05

---

## 📋 项目现状

### 已完成的功能
- ✅ 基础搜索功能（Google、Baidu、Tavily）
- ✅ AI驱动的查询生成
- ✅ 视频评估系统（多维度评分）
- ✅ 异步任务处理（WebSocket进度推送）
- ✅ 国家自动发现和配置
- ✅ 知识点管理
- ✅ Web界面（搜索、评估、历史记录）
- ✅ **配置化改造**（刚刚完成）

### 技术栈
- **后端**: Flask (Python)
- **数据库**: SQLite
- **前端**: HTML + JavaScript + Bootstrap
- **AI**: OpenAI API + Gemini API
- **部署**: 单体应用，直接运行

### API端点清单（17个）
1. `GET /` - 主页
2. `GET /knowledge_points` - 知识点页面
3. `GET /api/countries` - 获取国家列表
4. `GET /api/config/<country_code>` - 获取国家配置
5. `POST /api/discover_country` - 自动发现国家
6. `POST /api/search` - 搜索视频
7. `GET /api/history` - 获取搜索历史
8. `GET /api/history/<int:index>` - 获取历史详情
9. `POST /api/analyze_video` - 分析视频
10. `POST /api/batch_evaluate_videos` - 批量评估
11. `GET /api/knowledge_points` - 获取知识点
12. `GET /api/knowledge_point_overview` - 知识点概览
13. `GET /api/evaluation_history` - 评估历史
14. `GET /api/evaluation_detail/<request_id>` - 评估详情
15. `GET /api/debug_logs` - 调试日志
16. `POST /api/save_debug_log` - 保存日志
17. `POST /api/export_excel` - 导出Excel

---

## 🎯 职责分工

### 产品经理（你）负责
- ✅ 业务功能优化和测试
- ✅ 调整配置参数（评估权重、LLM参数等）
- ✅ 优化AI提示词和搜索策略
- ✅ 准备演示数据和场景

### 开发团队负责
- 🔧 部署脚本和文档
- 🔧 环境配置管理
- 🔧 日志和监控
- 🔧 代码Review（安全性和边界情况）
- 🔧 上线前的稳定性检查

**核心原则**: **开发团队不实现新功能**，只负责将现有功能**稳定、可靠**地部署到生产环境。

---

## 📊 部署任务清单（按优先级）

### P0 - 必须完成（阻塞上线）

#### 任务1: 环境配置和依赖管理 ⏱️ 0.5人天

**负责人**: 后端开发A
**优先级**: 🔴 P0
**预计工期**: 半天

**需求描述**:
```
确保项目可以在新环境中一键启动，所有依赖正确安装。
```

**检查项**:
- [ ] Python版本要求（建议Python 3.9+）
- [ ] 所有依赖包列在requirements文件中
- [ ] 环境变量配置完整
- [ ] API密钥配置安全

**交付物**:
- [ ] 更新 `requirements.txt` - 包含所有依赖包
- [ ] 更新 `.env.example` - 环境变量模板
- [ ] 创建 `/scripts/check_env.sh` - 环境检查脚本

**验收标准**:
- [ ] 在新机器上运行 `pip install -r requirements.txt` 成功
- [ ] 复制 `.env.example` 到 `.env` 并填入密钥后可以启动
- [ ] 环境检查脚本可以检测Python版本、依赖包、API密钥

---

#### 任务2: 部署脚本 ⏱️ 1人天

**负责人**: 后端开发B
**优先级**: 🔴 P0
**预计工期**: 1人天

**需求描述**:
```
编写一键部署脚本，支持快速部署和回滚。
```

**交付物**:
- [ ] `/scripts/deploy.sh` - 一键部署脚本
- [ ] `/scripts/stop.sh` - 停止服务脚本
- [ ] `/scripts/start.sh` - 启动服务脚本
- [ ] `/scripts/restart.sh` - 重启服务脚本
- [ ] `/docs/deployment.md` - 部署文档

**部署脚本功能**:
```bash
#!/bin/bash
# deploy.sh
- [ ] 检查环境（Python、依赖、配置文件）
- [ ] 检查端口占用（默认5001）
- [ ] 备份数据库（如果存在）
- [ ] 停止旧服务
- [ ] 启动新服务
- [ ] 健康检查（访问 /api/countries）
- [ ] 显示服务状态
```

**验收标准**:
- [ ] 一条命令可以完成部署：`./scripts/deploy.sh`
- [ ] 部署失败时给出明确的错误提示
- [ ] 部署文档清晰，任何开发都可以按文档部署
- [ ] 在测试环境验证至少3次

---

#### 任务3: 日志系统完善 ⏱️ 0.5人天

**负责人**: 后端开发A
**优先级**: 🔴 P0
**预计工期**: 半天

**需求描述**:
```
系统已有基础日志，需要确保所有关键操作都有日志记录。
```

**检查项**:
- [ ] 所有API请求都有日志
- [ ] 所有异常都有错误日志
- [ ] 日志包含request_id（已实现）
- [ ] 日志文件轮转配置

**交付物**:
- [ ] 更新 `/logger_utils.py` - 确保日志格式统一
- [ ] 配置日志轮转（按大小或时间）
- [ ] 添加 `/api/logs` 端点 - 查看日志（可选）

**验收标准**:
- [ ] 访问任何API端点，日志中都有记录
- [ ] 触发错误时，日志中有完整的堆栈信息
- [ ] 日志文件不会无限增长

---

#### 任务4: 错误处理和友好提示 ⏱️ 0.5人天

**负责人**: 后端开发A
**优先级**: 🔴 P0
**预计工期**: 半天

**需求描述**:
```
确保所有错误都被正确处理，用户看到友好的错误提示。
```

**检查项**:
- [ ] API调用失败时的错误提示
- [ ] AI API超时的处理
- [ ] 搜索引擎API失败的处理
- [ ] 数据库错误的处理
- [ ] 不暴露敏感信息（API密钥、密码）

**交付物**:
- [ ] 统一的错误响应格式：
  ```json
  {
    "success": false,
    "error": "错误信息",
    "error_code": "ERROR_CODE",
    "request_id": "uuid"
  }
  ```

**验收标准**:
- [ ] 故意断网，测试API失败时的错误提示
- [ ] 故意使用错误的API密钥，测试错误提示
- [ ] 错误日志中记录详细信息，但用户只看到友好提示

---

#### 任务5: 健康检查和状态监控 ⏱️ 0.5人天

**负责人**: 后端开发B
**优先级**: 🔴 P0
**预计工期**: 半天

**需求描述**:
```
提供健康检查端点，方便监控服务状态。
```

**交付物**:
- [ ] `GET /api/health` - 健康检查端点
- [ ] `GET /api/status` - 服务状态端点
- [ ] `GET /api/version` - 版本信息端点

**端点示例**:
```json
// GET /api/health
{
  "status": "healthy",
  "timestamp": "2026-01-05T15:30:00Z",
  "checks": {
    "database": "ok",
    "llm_api": "ok",
    "search_engine": "ok"
  }
}

// GET /api/status
{
  "uptime_seconds": 86400,
  "total_searches": 150,
  "total_evaluations": 80,
  "active_tasks": 3
}
```

**验收标准**:
- [ ] `/api/health` 可以快速返回服务状态
- [ ] 数据库文件损坏时返回 "unhealthy"
- [ ] 可以用curl快速检查服务状态

---

### P1 - 强烈建议（提升可靠性）

#### 任务6: 代码Review ⏱️ 1人天

**负责人**: 后端开发A + 后端开发B
**优先级**: 🟡 P1
**预计工期**: 1人天

**Review重点**:

1. **安全性** 🔴
   - [ ] 检查是否有SQL注入风险
   - [ ] 检查是否泄露API密钥
   - [ ] 检查用户输入验证

2. **边界情况** 🟡
   - [ ] 空值处理（None、空字符串、空列表）
   - [ ] 异常捕获
   - [ ] 超时处理

3. **性能** 🟡
   - [ ] 大量数据时的性能
   - [ ] 并发请求处理

**Review流程**:
```
1. 开发阅读代码，记录问题
2. 与产品经理讨论优先级
3. 产品经理决定是否修改
4. 关键问题必须修复
5. 一般问题可以记录到待办
```

**输出**:
- Review报告（列出发现的问题）
- 优先级分类（P0必须修复 / P1建议修复 / P2可以优化）

---

#### 任务7: 数据库备份和恢复 ⏱️ 0.5人天

**负责人**: 后端开发B
**优先级**: 🟡 P1
**预计工期**: 半天

**需求描述**:
```
提供数据库备份和恢复脚本，防止数据丢失。
```

**交付物**:
- [ ] `/scripts/backup_db.sh` - 备份数据库
- [ ] `/scripts/restore_db.sh` - 恢复数据库
- [ ] 定时备份配置（可选）

**验收标准**:
- [ ] 备份脚本可以成功备份SQLite数据库
- [ ] 恢复脚本可以从备份恢复数据库
- [ ] 备份文件包含时间戳

---

#### 任务8: 性能测试和优化 ⏱️ 0.5人天

**负责人**: 后端开发A
**优先级**: 🟡 P1
**预计工期**: 半天

**测试项目**:
- [ ] 搜索API响应时间
- [ ] 批量评估API响应时间
- [ ] 并发处理能力
- [ ] 内存使用情况

**交付物**:
- [ ] 性能测试报告
- [ ] 如果发现性能问题，提供优化建议

**验收标准**:
- [ ] 搜索API响应时间 < 10秒
- [ ] 可以支持5个并发用户
- [ ] 内存使用 < 1GB

---

### P2 - 可选优化（有时间再做）

#### 任务9: 自动化测试 ⏱️ 1人天

**负责人**: 后端开发B
**优先级**: 🟢 P2
**预计工期**: 1人天

**测试内容**:
- [ ] 核心API的集成测试
- [ ] 关键功能的端到端测试

**交付物**:
- [ ] `/tests/test_api.py` - API测试脚本
- [ ] `/tests/run_tests.sh` - 运行测试

---

#### 任务10: Docker容器化（可选）⏱️ 1人天

**负责人**: 后端开发B
**优先级**: 🟢 P2
**预计工期**: 1人天

**交付物**:
- [ ] `Dockerfile`
- [ ] `docker-compose.yml`
- [ ] Docker部署文档

**说明**: 如果部署环境支持Docker，容器化可以简化部署。

---

## 📅 时间规划建议

### 快速模式（3人天）
适合时间紧张的场景

- **Day 1上午**: 任务1（环境配置）
- **Day 1下午**: 任务2（部署脚本）
- **Day 2上午**: 任务3（日志）+ 任务4（错误处理）
- **Day 2下午**: 任务5（健康检查）
- **Day 3**: 任务6（Review）+ 测试

### 标准模式（5人天）
适合追求高质量的场景

- **Day 1**: 任务1 + 任务2
- **Day 2**: 任务3 + 任务4 + 任务5
- **Day 3**: 任务6（Review）+ 任务7（备份）
- **Day 4**: 任务8（性能测试）
- **Day 5**: 全面测试 + 准备上线

---

## ✅ 上线前检查清单

### 环境检查
- [ ] Python版本正确（3.9+）
- [ ] 所有依赖包已安装
- [ ] 环境变量已配置（.env文件）
- [ ] API密钥有效（OpenAI、Gemini等）
- [ ] 端口5001未被占用

### 功能检查
- [ ] 主页可以正常访问
- [ ] 搜索功能正常工作
- [ ] 评估功能正常工作
- [ ] 国家发现功能正常
- [ ] 知识点功能正常
- [ ] 历史记录功能正常

### 性能检查
- [ ] 搜索响应时间可接受（< 10秒）
- [ ] 可以支持多个用户同时使用
- [ ] 内存使用正常（< 1GB）
- [ ] 磁盘空间充足（> 5GB）

### 日志检查
- [ ] 所有API都有日志记录
- [ ] 错误日志包含完整信息
- [ ] 日志文件不会无限增长

### 安全检查
- [ ] 不泄露API密钥
- [ ] 不暴露数据库路径
- [ ] 错误提示不包含敏感信息

### 运维检查
- [ ] 部署脚本测试通过
- [ ] 停止/启动/重启脚本正常
- [ ] 健康检查端点正常
- [ ] 数据库备份脚本正常

### 文档检查
- [ ] 部署文档完整
- [ ] 环境配置说明清晰
- [ ] API文档清晰（如果有的话）
- [ ] 常见问题FAQ

---

## 📝 部署文档模板

### 1. 环境要求

```bash
# 操作系统
- macOS / Linux

# Python版本
- Python 3.9 或更高

# 依赖包
见 requirements.txt
```

### 2. 部署步骤

```bash
# 1. 克隆代码
git clone <repository_url>
cd Indonesia

# 2. 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
vim .env  # 填入API密钥

# 5. 启动服务
python3 web_app.py

# 6. 访问应用
# 浏览器打开: http://localhost:5001
```

### 3. 配置说明

```bash
# 必须配置的环境变量
OPENAI_API_KEY=sk-xxx              # OpenAI API密钥
GEMINI_API_KEY=xxx                 # Gemini API密钥（可选）
INTERNAL_API_KEY=xxx               # 公司内部API密钥（可选）

# 可选配置
HTTP_PROXY=http://127.0.0.1:7897   # 代理设置（可选）
LOG_LEVEL=INFO                     # 日志级别
```

### 4. 常见问题

**Q1: 启动时报错 "ModuleNotFoundError"**
```bash
A: 重新安装依赖:
   pip install -r requirements.txt
```

**Q2: API调用失败**
```bash
A: 检查.env文件中的API密钥是否正确配置
   检查网络连接和代理设置
```

**Q3: 数据库错误**
```bash
A: 检查data目录是否存在
   确保程序有写入权限
```

**Q4: 端口被占用**
```bash
A: 修改web_app.py中的端口:
   app.run(debug=True, host='0.0.0.0', port=5002)
```

---

## 🚀 一键部署命令

```bash
# 完整部署流程
cd /Users/shmiwanghao8/Desktop/education/Indonesia
./scripts/deploy.sh
```

---

## 📞 联系方式

- **产品经理**: [你的联系方式]
- **开发A**: [联系方式]
- **开发B**: [联系方式]

---

## 📚 相关文档

- [配置文件说明](/Users/shmiwanghao8/Desktop/education/Indonesia/config/README.md)
- [配置化使用指南](/Users/shmiwanghao8/Desktop/education/Indonesia/docs/CONFIGURATION_GUIDE.md)
- [系统README](/Users/shmiwanghao8/Desktop/education/Indonesia/README.md)

---

**最后更新**: 2026-01-05
**维护者**: 产品经理 + 开发团队
**项目状态**: ✅ 功能完整，待部署
