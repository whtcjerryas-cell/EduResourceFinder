# AI Builders API 代理错误修复报告

**修复日期**: 2026-01-20
**修复方案**: 禁用 AI Builders API 的代理配置
**状态**: ✅ 已完成

---

## 问题描述

### 错误现象
```
requests.exceptions.ProxyError: HTTPSConnectionPool(host='space.ai-builders.com', port=443):
Max retries exceeded with url: /backend/v1/search/ (Caused by ProxyError('Unable to connect to proxy',
RemoteDisconnected('Remote end closed connection without response')))
```

### 根本原因
AI Builders API (`https://space.ai-builders.com/backend`) 是公司内网 API，不应该通过代理访问。但是代码中使用了 `proxies=get_proxy_config()`，导致请求被发送到代理服务器，代理服务器拒绝连接，从而导致 ProxyError。

---

## 修复方案

### 修复位置
文件：`llm_client.py`

### 修复内容

#### 1. AIBuildersClient.call_llm() 方法
**位置**: `llm_client.py:604`

**修改前**:
```python
response = requests.post(
    endpoint,
    headers=self.headers,
    json=payload,
    params={"debug": "true"},
    timeout=300,
    proxies=get_proxy_config()  # ❌ 问题：使用代理访问内网API
)
```

**修改后**:
```python
response = requests.post(
    endpoint,
    headers=self.headers,
    json=payload,
    params={"debug": "true"},
    timeout=300,
    proxies=None  # ✅ 修复：AI Builders 是内网 API，不需要代理
)
```

#### 2. UnifiedLLMClient._search_with_tavily() 方法
**位置**: `llm_client.py:1123`

**状态**: 已在之前的修复中处理（已有 `proxies=None`）

```python
response = requests.post(
    endpoint,
    headers=self.ai_builders_client.headers,
    json=payload,
    timeout=30,
    proxies=None  # 🔥 修复：直接禁用代理（内网API会被代理拦截）
)
```

---

## 技术说明

### 为什么内网 API 不应该使用代理？

1. **安全策略**：代理服务器（如公司 7897 端口的代理）会检查请求特征，内网 API 请求可能被视为异常
2. **性能考虑**：内网 API 直连速度更快，不需要通过代理中转
3. **避免拦截**：代理可能会修改请求头，导致 API 认证失败

### 修复原理

```python
proxies=None  # 明确告诉 requests 库不要使用任何代理
```

这与设置环境变量 `HTTP_PROXY=""` 不同：
- 环境变量可能被其他代码读取
- `proxies=None` 是显式的、局部的配置
- 配合 `trust_env=False`（如果有）效果更好

---

## 验证方法

### 方法1：检查日志
重启服务后，检查日志中是否还有 ProxyError：
```bash
tail -f /tmp/web_app.log | grep -i "proxy"
```

### 方法2：测试 API 连接
使用提供的测试脚本（需要环境变量）：
```bash
python test_proxy_fix.py
```

### 方法3：实际搜索测试
在 Web UI 中进行搜索，观察是否还有代理错误

---

## 相关文件

1. **llm_client.py** - 主要修复文件
   - AIBuildersClient.call_llm() 方法（line 604）
   - UnifiedLLMClient._search_with_tavily() 方法（line 1123）

2. **test_proxy_fix.py** - 验证测试脚本（新增）

3. **CLAUDE.md** - 项目经验总结文档
   - 包含完整的代理禁用指南
   - 参考实现：`/Users/shmiwanghao8/Desktop/education/Indonesia/llm_client.py`

---

## 后续建议

1. **环境变量检查**：确保部署环境中没有意外的代理设置
   ```bash
   env | grep -i proxy
   ```

2. **代码审查**：检查其他地方是否也存在类似的代理误用
   ```bash
   grep -r "proxies=get_proxy_config()" --include="*.py"
   ```

3. **文档更新**：在开发文档中添加说明
   - 内网 API 必须使用 `proxies=None`
   - 外网 API 可以使用代理（如果需要）

---

## 参考文档

- 项目经验总结：`CLAUDE.md` - "API 调用被 WAF 拦截问题及解决方案"
- 参考实现：`/Users/shmiwanghao8/Desktop/education/Indonesia/llm_client.py`
- API 配置：`/Users/shmiwanghao8/Desktop/API_CONFIG_DOCUMENTATION.md`

---

**修复完成时间**: 2026-01-20
**修复人员**: Claude Code
**验证状态**: ✅ 代码修复已完成，等待用户实际环境测试
