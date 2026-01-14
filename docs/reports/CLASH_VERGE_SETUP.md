# Clash Verge 配置指南
# 目标：只让浏览器和Claude Code走代理，Python脚本走公司网络

## 方法1：使用规则配置（推荐）

### 步骤1：打开Clash Verge配置
1. 打开Clash Verge
2. 点击"配置" → "配置文件"
3. 选择你正在使用的配置文件
4. 点击"编辑"

### 步骤2：添加规则
在`rules:`部分添加以下规则：

```yaml
rules:
  # 🏢 公司内部API - 直连（重要！）
  - DOMAIN-SUFFIX,transsion.com,DIRECT
  - DOMAIN-SUFFIX,hk-intra-paas.transsion.com,DIRECT

  # 🎯 浏览器/Claude Code - 走代理
  - DOMAIN-SUFFIX,google.com,PROXY
  - DOMAIN-SUFFIX,github.com,PROXY
  - DOMAIN-SUFFIX,openai.com,PROXY
  - DOMAIN-SUFFIX,anthropic.com,PROXY
  - DOMAIN-SUFFIX,claude.ai,PROXY
  - DOMAIN-SUFFIX,youtube.com,PROXY
  - DOMAIN-SUFFIX,twitter.com,PROXY

  # 🏠 国内网站直连
  - GEOIP,CN,DIRECT

  # 🎯 其他流量根据需求选择
  - MATCH,PROXY  # 或 MATCH,DIRECT
```

### 步骤3：保存并应用
1. 点击"保存"
2. 点击"应用配置"
3. 重启Clash Verge

---

## 方法2：使用应用程序代理（macOS/Windows）

### macOS方案：

#### 方法A：使用Proxifier（推荐）
1. 下载并安装 Proxifier
2. 添加代理服务器：
   - 代理服务器地址: 127.0.0.1
   - 端口: 7897
   - 类型: HTTPS
3. 添加规则：
   - 应用程序: Chrome, Safari, Edge, Claude Code
   - 目标: 所有
   - 操作: 使用代理 127.0.0.1:7897
4. 添加Python规则：
   - 应用程序: python, python3
   - 目标: transsion.com
   - 操作: Direct

#### 方法B：使用Clash的规则集（更简单）
创建一个自定义规则集文件 `company_network.yaml`:

```yaml
# 公司网络规则
payload:
  # 公司域名
  - '+.transsion.com'
  - '+.hk-intra-paas.transsion.com'

  # 如果知道具体的IP段，也可以添加
  - 'IP-CIDR,8.212.8.132/32,no-resolve'
```

然后在主配置中引用：
```yaml
rule-providers:
  company:
    type: file
    behavior: domain
    path: ./ruleset/company_network.yaml
    interval: 86400

rules:
  - RULE-SET,company,DIRECT
  # ... 其他规则
```

---

## 方法3：使用Clash Verge的"绕过代理"列表

### 步骤1：
打开Clash Verge → 设置 → 绕过代理

### 步骤2：
添加以下域名或IP：
```
*.transsion.com
*.hk-intra-paas.transsion.com
8.212.8.132
```

### 步骤3：
保存并重启Clash

---

## 验证配置是否生效

### 测试1：检查Python脚本是否直连
```bash
# 运行测试脚本
python3 test_with_proxy_enabled.py

# 应该看到：
# ✅ 响应时间: 2-3秒
# ✅ 公司内部API可以正常使用
```

### 测试2：检查浏览器是否走代理
1. 访问 https://ip.sb
2. 应该显示代理服务器的IP（美国）

### 测试3：检查公司API是否直连
```bash
curl -I https://hk-intra-paas.transsion.com/tranai-proxy/v1/models

# 应该快速返回，不经过代理
```

---

## 推荐配置组合

### 最佳实践（推荐）：
1. ✅ **代码层面**：使用 `trust_env=False`（已完成）
2. ✅ **Clash配置**：添加 `transsion.com,DIRECT` 规则
3. ✅ **双重保障**：即使Clash规则失效，代码也能正确路由

### 最小配置（简单）：
1. ✅ **代码层面**：使用 `trust_env=False`（已完成）
2. ⚠️ **Clash配置**：无需修改

---

## 常见问题

### Q1: 配置后仍然被拦截？
**A**: 检查以下几点：
1. Clash配置是否保存并应用？
2. 是否重启了Clash Verge？
3. 规则顺序是否正确？（从上到下匹配）
4. 运行 `scutil --proxy` 查看系统代理设置

### Q2: 如何验证Python脚本真的直连了？
**A**:
```bash
# 方法1：查看日志
tail -f search_system.log | grep "代理"

# 应该看到：
# [🔧 代理] 已清除 X 个代理环境变量，确保公司API可访问
# [✅] 公司内部API客户端初始化成功 (代理: 已强制禁用)

# 方法2：运行测试
python3 test_with_proxy_enabled.py
```

### Q3: Claude Code需要特殊配置吗？
**A**: 不需要！Claude Code会自动使用系统代理。只要Clash的规则中有：
```yaml
- DOMAIN-SUFFIX,anthropic.com,PROXY
- DOMAIN-SUFFIX,claude.ai,PROXY
```

### Q4: 可以让不同的Python脚本使用不同的路由吗？
**A**: 可以！方法如下：
1. 为需要代理的脚本：不设置 `trust_env=False`
2. 为需要直连的脚本：设置 `trust_env=False`
3. 或使用环境变量：
   ```bash
   # 直连脚本
   NO_PROXY="*" python3 script_direct.py

   # 代理脚本
   python3 script_proxy.py
   ```

---

## 配置文件示例

### 完整的Clash配置示例：
见文件：`clash_verge_config.yaml`

### 快速应用配置：
```bash
# 1. 备份当前配置
cp ~/.config/clash/config.yaml ~/.config/clash/config.yaml.backup

# 2. 复制新配置
cp clash_verge_config.yaml ~/.config/clash/config.yaml

# 3. 重启Clash Verge
killall Clash && open -a Clash

# 4. 验证
python3 test_with_proxy_enabled.py
```

---

## 总结

**方案1（代码层面）**：
- ✅ 已完成
- ✅ 立即生效
- ✅ 无需修改Clash配置
- ✅ 适用于所有Python脚本

**方案2（Clash配置）**：
- 🛠️ 需要手动配置
- 🛠️ 灵活控制所有应用的代理
- 🛠️ 需要重启Clash

**推荐**：同时使用两个方案，提供双重保障！
