# 调试指南 - 国家下拉框显示"加载中"问题

## 🔍 问题排查步骤

### 步骤 1: 检查浏览器控制台

1. 打开网页后，按 `F12` 打开开发者工具
2. 切换到 **Console（控制台）** 标签
3. 查看是否有以下日志：
   - `[DEBUG] 页面加载完成，开始初始化...`
   - `[DEBUG] 开始加载国家列表...`
   - `[DEBUG] API 响应状态: 200`
   - `[DEBUG] 国家列表加载成功，共 X 个国家`

**如果没有看到这些日志**：
- 说明 JavaScript 代码没有执行
- 可能原因：script 标签未正确闭合、语法错误

**如果看到错误信息**：
- 记录错误信息，告诉我具体是什么错误

### 步骤 2: 检查网络请求

1. 在开发者工具中切换到 **Network（网络）** 标签
2. 刷新页面
3. 查找 `/api/countries` 请求
4. 点击该请求，查看：
   - **Status（状态）**: 应该是 `200`
   - **Response（响应）**: 应该包含 `{"success": true, "countries": [...]}`

**如果请求失败**：
- 检查后端是否正在运行
- 检查后端日志是否有错误

### 步骤 3: 检查后端日志

在后端终端中查看是否有以下输出：
```
[DEBUG] 获取国家列表: 找到 X 个国家
```

**如果没有看到**：
- 说明请求没有到达后端
- 检查路由是否正确

### 步骤 4: 手动测试 API

在终端运行：
```bash
python test_api.py
```

或者使用 curl：
```bash
curl http://localhost:5000/api/countries
```

应该返回：
```json
{
  "success": true,
  "countries": [
    {"country_code": "ID", "country_name": "Indonesia"}
  ]
}
```

### 步骤 5: 检查配置文件

确认 `countries_config.json` 文件存在且格式正确：
```bash
cat countries_config.json
```

应该看到类似内容：
```json
{
  "ID": {
    "country_code": "ID",
    "country_name": "Indonesia",
    ...
  }
}
```

## 🛠️ 常见问题及解决方案

### 问题 1: 控制台显示 "Uncaught SyntaxError"

**原因**: JavaScript 语法错误

**解决**: 
1. 检查浏览器控制台的错误信息
2. 查看错误指向的行号
3. 修复语法错误

### 问题 2: 控制台显示 "Failed to fetch"

**原因**: 网络请求失败

**解决**:
1. 确认后端服务正在运行
2. 检查 URL 是否正确（应该是 `/api/countries`）
3. 检查 CORS 设置

### 问题 3: API 返回 500 错误

**原因**: 后端处理错误

**解决**:
1. 查看后端终端日志
2. 检查 `config_manager.py` 是否能正常读取配置文件
3. 运行测试：`python -c "from config_manager import ConfigManager; cm = ConfigManager(); print(cm.get_all_countries())"`

### 问题 4: 按钮点击没反应

**原因**: 事件监听器未绑定

**解决**:
1. 检查控制台是否有 `[DEBUG] 绑定按钮事件...` 日志
2. 如果没有，说明初始化函数没有执行
3. 检查 `DOMContentLoaded` 或 `window.onload` 是否触发

## 📝 调试代码

在浏览器控制台中运行以下代码来手动测试：

```javascript
// 测试 1: 检查元素是否存在
console.log('国家下拉框:', document.getElementById('country'));
console.log('添加按钮:', document.getElementById('addCountryBtn'));

// 测试 2: 手动调用 API
fetch('/api/countries')
  .then(r => r.json())
  .then(data => console.log('API 响应:', data))
  .catch(e => console.error('API 错误:', e));

// 测试 3: 手动绑定按钮事件
document.getElementById('addCountryBtn').addEventListener('click', () => {
  console.log('按钮被点击了！');
  alert('按钮工作正常！');
});
```

## 🎯 快速修复

如果以上步骤都没有解决问题，尝试：

1. **硬刷新页面**（清除缓存）:
   - Windows/Linux: `Ctrl + Shift + R`
   - Mac: `Cmd + Shift + R`

2. **重启后端服务**:
   ```bash
   # 停止当前服务（Ctrl+C）
   # 重新启动
   python web_app.py
   ```

3. **检查文件编码**:
   确保 `templates/index.html` 是 UTF-8 编码

4. **检查 Python 版本**:
   确保使用 Python 3.6+

## 📞 如果问题仍然存在

请提供以下信息：
1. 浏览器控制台的完整错误信息（截图或复制文本）
2. Network 标签中 `/api/countries` 请求的详细信息
3. 后端终端的完整日志输出
4. 浏览器类型和版本（Chrome/Firefox/Safari 等）

