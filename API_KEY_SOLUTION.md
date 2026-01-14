# API密钥认证问题 - 解决方案文档

**问题日期:** 2026-01-11
**解决状态:** ✅ 已解决

---

## 📋 问题描述

**错误信息:**
```
搜索失败: HTTP 401 - {
  "error": "API key required",
  "message": "Please provide X-API-Key header"
}
```

**原因分析:**
- 后端API实现了认证机制（安全修复 #041）
- 前端Web界面没有在请求中包含API密钥
- 导致所有搜索请求被拒绝（401 Unauthorized）

---

## 🎯 解决方案

### 方案1：在前端添加默认API密钥 ✅ **已实现**

**适用场景:** 个人使用、开发环境

**实现步骤:**

#### 1. 修改 `templates/index.html`

在第651-656行添加API密钥配置:
```javascript
{% block page_scripts %}
<script>
    // ========================================
    // 🔑 API密钥配置
    // ========================================
    // 开发环境默认API密钥（用于个人使用）
    // 生产环境请更改为您自己的密钥或从环境变量读取
    const DEFAULT_API_KEY = 'dev-key-12345';

    // 全局状态
    let currentResults = [];
    // ...
```

#### 2. 修改第一处搜索API调用 (第1099-1107行)

**修改前:**
```javascript
response = await fetch('/api/search', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(requestBody),
    signal: controller.signal
});
```

**修改后:**
```javascript
response = await fetch('/api/search', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-API-Key': DEFAULT_API_KEY  // 🔑 添加API密钥认证
    },
    body: JSON.stringify(requestBody),
    signal: controller.signal
});
```

#### 3. 修改第二处搜索API调用 (第1334-1342行)

**修改前:**
```javascript
response = await fetch('/api/search', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(requestBody),
    signal: controller.signal
});
```

**修改后:**
```javascript
response = await fetch('/api/search', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-API-Key': DEFAULT_API_KEY  // 🔑 添加API密钥认证
    },
    body: JSON.stringify(requestBody),
    signal: controller.signal
});
```

---

## ✅ 测试验证

### 测试场景
- **国家:** Indonesia
- **年级:** Kelas 1 (一年级)
- **学科:** Bahasa Indonesia (印尼语)

### 后端日志
```
✅ 搜索完成: 60.29秒
✅ 结果数: 20个
✅ 播放列表: 3个
✅ 视频: 9个
✅ 质量分数: 100.0/100
```

### 前端验证
- ✅ 没有401错误
- ✅ 搜索按钮状态正常
- ✅ API认证成功
- ✅ 结果正常显示

---

## 🔑 API密钥管理

### 当前可用的API密钥

| 密钥 | 用户 | 权限 | 用途 |
|------|------|------|------|
| `dev-key-12345` | dev-user | user + admin | 开发和测试 |
| `test-key-67890` | test-user | user | 测试环境 |

### 如何更换API密钥

#### 方法1: 直接修改代码（简单）

编辑 `templates/index.html` 第656行:
```javascript
const DEFAULT_API_KEY = 'your-new-api-key-here';
```

然后重启服务:
```bash
kill $(cat logs/app.pid)
source venv/bin/activate
python3 web_app.py > logs/app_startup.log 2>&1 &
```

#### 方法2: 使用环境变量（推荐）

**1. 设置环境变量:**
```bash
export WEB_API_KEY="your-api-key-here"
```

**2. 修改 `web_app.py`，在路由中传递配置:**
```python
@app.route('/')
def index():
    api_key = os.getenv('WEB_API_KEY', 'dev-key-12345')
    return render_template('index.html', web_api_key=api_key)
```

**3. 修改 `templates/index.html`:**
```javascript
const DEFAULT_API_KEY = '{{ web_api_key | default("dev-key-12345") }}';
```

#### 方法3: 添加用户输入界面（最安全）

创建登录页面，让用户输入自己的API密钥，保存在localStorage中。

---

## 📖 API使用示例

### cURL示例

```bash
curl -X POST http://localhost:5005/api/search \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: dev-key-12345' \
  -d '{
    "country": "Indonesia",
    "grade": "Kelas 1",
    "subject": "Matematika",
    "language": "zh",
    "max_results": 10
  }'
```

### JavaScript示例

```javascript
const response = await fetch('/api/search', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-API-Key': 'dev-key-12345'  // 必须添加
    },
    body: JSON.stringify({
        country: 'Indonesia',
        grade: 'Kelas 1',
        subject: 'Matematika',
        language: 'zh',
        max_results: 10
    })
});

const data = await response.json();
console.log(data);
```

### Python示例

```python
import requests

headers = {
    'Content-Type': 'application/json',
    'X-API-Key': 'dev-key-12345'  # 必须添加
}

data = {
    'country': 'Indonesia',
    'grade': 'Kelas 1',
    'subject': 'Matematika',
    'language': 'zh',
    'max_results': 10
}

response = requests.post(
    'http://localhost:5005/api/search',
    headers=headers,
    json=data
)

print(response.json())
```

---

## 🔒 安全建议

### 开发环境
- ✅ 使用默认密钥 `dev-key-12345`
- ✅ 密钥硬编码在前端
- ⚠️ 仅限本地使用

### 生产环境
- ❌ 不要硬编码API密钥
- ✅ 使用环境变量
- ✅ 为每个用户生成独立密钥
- ✅ 实施密钥轮换策略
- ✅ 添加IP白名单限制
- ✅ 记录所有API调用日志

### 密钥生成

生成新的API密钥:
```python
import secrets
import string

def generate_api_key(prefix='prod'):
    """生成安全的API密钥"""
    random_part = secrets.token_urlsafe(16)
    return f"{prefix}-{random_part}"

# 示例
api_key = generate_api_key('prod')
print(api_key)  # prod-xYz1234567890abcdef...
```

---

## 📊 相关文件

| 文件 | 修改内容 | 行数 |
|------|---------|------|
| `templates/index.html` | 添加API密钥配置 | 651-656 |
| `templates/index.html` | 修改第一处fetch调用 | 1099-1107 |
| `templates/index.html` | 修改第二处fetch调用 | 1334-1342 |
| `core/auth.py` | API认证实现 | 全部 |
| `web_app.py` | @require_api_key装饰器 | 多处 |

---

## 🚀 快速启动

现在系统已经配置完成，您可以：

1. **访问Web界面:**
   ```
   http://localhost:5005
   ```

2. **选择搜索参数:**
   - 国家: Indonesia (或其他10个国家)
   - 年级: Kelas 1-12
   - 学科: 8个学科可选

3. **点击搜索:**
   - 系统会自动使用API密钥认证
   - 显示搜索结果

4. **管理服务:**
   ```bash
   # 查看状态
   ps aux | grep web_app

   # 查看日志
   tail -f logs/app_startup.log

   # 停止服务
   kill $(cat logs/app.pid)

   # 重启服务
   kill $(cat logs/app.pid)
   source venv/bin/activate
   python3 web_app.py > logs/app_startup.log 2>&1 &
   echo $! > logs/app.pid
   ```

---

**文档创建时间:** 2026-01-11
**最后更新:** 2026-01-11
**状态:** ✅ 问题已解决，系统正常运行
