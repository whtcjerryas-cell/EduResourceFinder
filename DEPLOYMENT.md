# Indonesia 教育搜索系统 - 部署指南

## 📦 系统要求

### 最低配置
- **操作系统**: Linux (Ubuntu 20.04+, CentOS 7+, Debian 10+)
- **Python**: 3.13+
- **内存**: 最低 2GB，推荐 4GB+
- **磁盘**: 最低 10GB 可用空间
- **网络**: 需要访问外网 API

### 依赖服务
- SQLite3 (Python 内置)
- ffmpeg (用于视频处理)

---

## 🚀 快速部署

### 1. 解压部署包

```bash
# 解压
tar -xzf indonesia_search_v5.0_YYYYMMDD_HHMMSS_XXXXXXX.tar.gz

# 进入目录
cd indonesia_search
```

### 2. 安装 Python 依赖

```bash
# 创建虚拟环境（推荐）
python3.13 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r config/requirements.txt
```

### 3. 安装系统依赖

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y ffmpeg python3.13-venv

# CentOS/RHEL
sudo yum install -y ffmpeg python3-venv
```

### 4. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
nano .env  # 或使用 vim
```

**必填配置项：**
```bash
# LLM API（至少配置一个）
OPENAI_API_KEY=sk-xxx           # OpenAI API Key
INTERNAL_API_KEY=xxx            # 内部 API Key

# 应用密钥（生成新密钥）
API_KEY_prod_abc123=service-a:user,admin

# 数据库路径
DATABASE_PATH=data/indo_edu_search.db
```

**生成安全密钥：**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 5. 初始化数据库

```bash
# 创建必要目录
mkdir -p data/{videos,audio,frames,subtitles,transcripts}
mkdir -p logs

# 初始化数据库（首次启动会自动创建）
python3 -c "from core.database_manager import db; db.init_db()"
```

### 6. 启动服务

#### 开发模式（测试）
```bash
python3 web_app.py
```

#### 生产模式（使用 Gunicorn）

**安装 Gunicorn：**
```bash
pip install gunicorn gevent
```

**启动服务：**
```bash
# 基础启动
gunicorn -w 4 -b 0.0.0.0:5000 web_app:app

# 推荐配置（使用 gevent worker）
gunicorn \
  --worker-class gevent \
  --workers 4 \
  --worker-connections 1000 \
  --timeout 300 \
  --bind 0.0.0.0:5000 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  --log-level info \
  web_app:app
```

#### 使用 Systemd（推荐）

创建服务文件 `/etc/systemd/system/indonesia-search.service`：

```ini
[Unit]
Description=Indonesia Education Search Service
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/indonesia_search
Environment="PATH=/path/to/indonesia_search/venv/bin"
ExecStart=/path/to/indonesia_search/venv/bin/gunicorn \
    --worker-class gevent \
    --workers 4 \
    --worker-connections 1000 \
    --timeout 300 \
    --bind 0.0.0.0:5000 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --log-level info \
    web_app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable indonesia-search
sudo systemctl start indonesia-search
sudo systemctl status indonesia-search
```

---

## 🔧 配置说明

### 环境变量详解

| 变量名 | 说明 | 默认值 | 是否必填 |
|--------|------|--------|----------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | - | 否（配置一个 LLM API 即可） |
| `INTERNAL_API_KEY` | 内部 API 密钥 | - | 否 |
| `API_KEY_*` | 应用认证密钥 | - | **是** |
| `DATABASE_PATH` | SQLite 数据库路径 | data/indo_edu_search.db | 否 |
| `LOG_LEVEL` | 日志级别 | INFO | 否 |
| `FLASK_PORT` | 服务端口 | 5000 | 否 |
| `DEBUG` | 调试模式 | False | 否 |

### API 密钥格式

应用认证密钥格式：`API_KEY_<random_string>=<service_name>:<permissions>`

示例：
```bash
API_KEY_prod_abc123=service-a:user,admin
#                    ↑ 服务名     ↑ 权限（多个用逗号分隔）
```

---

## 📊 验证部署

### 1. 健康检查

```bash
# 检查服务状态
curl http://localhost:5000/api/health

# 预期响应
{
  "status": "ok",
  "version": "5.0",
  "timestamp": "2025-01-13T12:00:00Z"
}
```

### 2. 测试搜索 API

```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: prod_abc123" \
  -d '{
    "query": "印尼数学教学",
    "country": "ID",
    "education_level": "SMP"
  }'
```

### 3. 查看日志

```bash
# 查看应用日志
tail -f logs/search_system.log

# 查看 Gunicorn 日志（如果使用）
tail -f logs/error.log
tail -f logs/access.log
```

---

## 🔒 安全配置

### 1. 文件权限

```bash
# 设置合适的文件权限
chmod 750 .
chmod 640 .env
chmod -R 755 core routes services templates static
chmod 644 core/*.py routes/*.py
```

### 2. 防火墙配置

```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 5000/tcp
sudo ufw reload

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

### 3. Nginx 反向代理（推荐）

配置文件 `/etc/nginx/sites-available/indonesia-search`：

```nginx
upstream indonesia_backend {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://indonesia_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }

    # 静态文件直接服务
    location /static {
        alias /path/to/indonesia_search/static;
        expires 30d;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/indonesia-search /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 📈 性能优化

### 1. Gunicorn 配置优化

根据服务器规格调整 worker 数量：

```bash
# 公式：(2 x CPU核心数) + 1
# 例如 4 核 CPU：workers = 9

gunicorn \
  --worker-class gevent \
  --workers 9 \
  --worker-connections 1000 \
  --timeout 300 \
  --bind 0.0.0.0:5000 \
  web_app:app
```

### 2. 数据库优化

```bash
# SQLite 优化（在 .env 中添加）
SQLITE_PRAGMA=journal_mode=WAL,synchronous=NORMAL
```

### 3. 缓存配置

```bash
# 启用缓存
ENABLE_CACHE=true
```

---

## 🐛 故障排查

### 问题 1：服务无法启动

```bash
# 检查端口占用
sudo lsof -i :5000

# 检查日志
tail -100 logs/search_system.log
```

### 问题 2：API 请求失败

```bash
# 验证 API 密钥
curl -v -X POST http://localhost:5000/api/search \
  -H "X-API-Key: your-api-key"

# 检查 .env 配置
cat .env | grep -v "^#" | grep -v "^$"
```

### 问题 3：数据库错误

```bash
# 检查数据库文件权限
ls -la data/indo_edu_search.db

# 重新初始化数据库
rm data/indo_edu_search.db
python3 -c "from core.database_manager import db; db.init_db()"
```

---

## 🔄 更新部署

### 1. 备份当前版本

```bash
# 备份数据库
cp data/indo_edu_search.db data/indo_edu_search.db.backup

# 备份配置
cp .env .env.backup
```

### 2. 部署新版本

```bash
# 停止服务
sudo systemctl stop indonesia-search

# 解压新版本
tar -xzf indonesia_search_vX.X.tar.gz

# 恢复配置
cp .env.backup indonesia_search/.env

# 更新依赖
cd indonesia_search
source venv/bin/activate
pip install -r config/requirements.txt

# 启动服务
sudo systemctl start indonesia-search
```

### 3. 验证更新

```bash
# 检查服务状态
sudo systemctl status indonesia-search

# 查看日志
sudo journalctl -u indonesia-search -f
```

---

## 📞 支持

- **技术文档**: 查看 `docs/` 目录
- **问题反馈**: 提交 Issue
- **版本信息**: 查看 `VERSION.txt`

---

## 📝 版本历史

- **v5.0** - 批量搜索性能优化 + 全教育层级支持
- **v3.4.0** - 企业级功能完善与 Bug 修复
- **v3.0** - 配置化改造完成

---

**打包时间**: 详见 `VERSION.txt`
**Git Commit**: 详见 `VERSION.txt`
