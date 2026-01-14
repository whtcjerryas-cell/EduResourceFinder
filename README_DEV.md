# Indonesia 教育搜索系统 - 开发版本

## 📝 说明

这是一个**开发版本**，基于 `Indonesia` 项目的最新稳定版本（v5.0, commit: 3f1421d）。

### 与原项目的关系

- **源项目**: `/Users/shmiwanghao8/Desktop/education/Indonesia`
- **开发目录**: `/Users/shmiwanghao8/Desktop/education/Indonesia_dev_v5`
- **复制时间**: 2025-01-13
- **源版本**: v5.0 (3f1421d)

---

## 🚀 快速开始

### 1. 创建虚拟环境

```bash
python3.13 -m venv venv
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install --upgrade pip
pip install -r config/requirements.txt
```

### 3. 配置环境

```bash
cp .env.example .env
nano .env  # 填入必需的 API 密钥
```

### 4. 启动开发服务器

```bash
python3 web_app.py
```

---

## 📚 开发指南

### 代码结构

```
Indonesia_dev_v5/
├── core/           # 核心业务逻辑
├── routes/         # API 路由
├── services/       # 服务层
├── templates/      # Web 界面
├── static/         # 静态资源
├── config/         # 配置文件
├── data/           # 数据文件
├── web_app.py      # 应用入口
└── tests/          # 测试代码
```

### 开发工作流

1. **创建功能分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **编写代码和测试**
   ```bash
   # 开发新功能
   # 运行测试
   pytest tests/
   ```

3. **提交更改**
   ```bash
   git add .
   git commit -m "feat: 添加新功能描述"
   ```

4. **测试验证**
   ```bash
   # 手动测试
   python3 web_app.py

   # 或运行自动化测试
   pytest tests/ -v
   ```

---

## 🔧 常用命令

### 开发服务器

```bash
# 启动开发服务器
python3 web_app.py

# 指定端口
python3 web_app.py --port 8000

# 启用调试模式
FLASK_ENV=development python3 web_app.py
```

### 测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_search.py -v

# 查看测试覆盖率
pytest --cov=core tests/
```

### 数据库操作

```bash
# 初始化数据库
python3 -c "from core.database_manager import db; db.init_db()"

# 备份数据库
cp data/indo_edu_search.db data/indo_edu_search.db.backup

# 查看数据库
sqlite3 data/indo_edu_search.db ".tables"
```

---

## 📋 待办事项

### 当前开发任务

- [ ] 在此添加你的开发任务

### 已知问题

- [ ] 在此添加已知问题

---

## 🔍 调试技巧

### 查看日志

```bash
# 实时查看日志
tail -f logs/search_system.log

# 查看错误日志
grep ERROR logs/search_system.log

# 查看特定请求的日志
grep "request_id" logs/search_system.log
```

### 调试 API

```bash
# 测试健康检查
curl http://localhost:5000/api/health

# 测试搜索 API
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "query": "印尼数学教学",
    "country": "ID",
    "education_level": "SMP"
  }'
```

---

## 🚨 注意事项

1. **不要提交敏感信息**
   - `.env` 文件已在 `.gitignore` 中
   - 不要提交 API 密钥到版本控制

2. **数据库安全**
   - 定期备份数据库
   - 不要将生产数据库提交到仓库

3. **日志文件**
   - 日志文件已排除在版本控制外
   - 定期清理旧日志文件

4. **与原项目同步**
   - 如果需要同步原项目的更新，手动对比合并
   - 记录重要的修改和决策

---

## 📖 参考文档

- **部署指南**: `DEPLOYMENT.md`
- **API 文档**: `docs/api/`
- **架构文档**: `docs/architecture/`
- **配置说明**: `config/README.md`

---

## 🤝 贡献

在开发过程中，请：
1. 保持代码清晰易读
2. 添加必要的注释和文档
3. 编写测试用例
4. 遵循现有代码风格

---

## 📞 获取帮助

遇到问题时：
1. 查看日志文件
2. 阅读相关文档
3. 参考原项目 `Indonesia` 的实现

---

**最后更新**: 2025-01-13
**开发者**: [你的名字]
**状态**: 🟢 开发中
