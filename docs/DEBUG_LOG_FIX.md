# Debug日志功能修复和增强

## 📅 更新日期
2025-12-29

## 🐛 问题修复

### 问题1：后端日志获取失败

**现象**: Debug弹窗显示 "获取后端日志失败: {}"

**原因分析**:
1. 错误对象序列化问题：`error` 对象可能没有正确的 `message` 属性
2. HTTP响应状态码未检查：即使API返回错误，前端也可能没有正确处理

**解决方案**:
1. ✅ 改进错误处理：检查HTTP状态码，提供更详细的错误信息
2. ✅ 改进错误消息提取：支持多种错误类型（Error对象、字符串、对象）
3. ✅ 添加API响应检查：检查 `data.success` 字段，显示API返回的错误消息

### 问题2：导出日志保存位置

**需求**: 导出日志时保存到 `logs/当前日期/` 目录下

**解决方案**:
1. ✅ 添加 `/api/save_debug_log` API端点
2. ✅ 自动创建日期目录（`logs/YYYY-MM-DD/`）
3. ✅ 保存文件到指定目录
4. ✅ 同时提供浏览器下载（双重保障）

### 问题3：时间段选择器默认值

**需求**: 时间段选择器默认选择过去30分钟

**解决方案**:
1. ✅ 添加 `setDefaultTimeRange()` 函数
2. ✅ 页面加载时自动设置默认值
3. ✅ 打开Debug弹窗时，如果时间段为空，自动设置默认值

---

## ✅ 实现的功能

### 1. 改进的错误处理

```javascript
// 检查HTTP状态码
if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
}

// 改进的错误消息提取
let errorMsg = '未知错误';
if (error instanceof Error) {
    errorMsg = error.message || error.toString();
} else if (typeof error === 'string') {
    errorMsg = error;
} else if (error && typeof error === 'object') {
    errorMsg = JSON.stringify(error);
}
```

### 2. 日志保存API (`web_app.py`)

```python
@app.route('/api/save_debug_log', methods=['POST'])
def save_debug_log():
    """
    保存Debug日志到服务器指定目录
    
    请求体:
        - log_text: 日志文本内容
        - filename: 文件名
        - date_dir: 日期目录（格式：YYYY-MM-DD）
    """
```

**功能**:
- ✅ 自动创建日期目录（`logs/YYYY-MM-DD/`）
- ✅ 保存日志文件到指定目录
- ✅ 返回文件路径和保存状态

### 3. 默认时间段设置

```javascript
function setDefaultTimeRange() {
    const now = new Date();
    const thirtyMinutesAgo = new Date(now.getTime() - 30 * 60 * 1000);
    
    // 格式化为 datetime-local 需要的格式
    startTimeInput.value = formatDateTimeLocal(thirtyMinutesAgo);
    endTimeInput.value = formatDateTimeLocal(now);
}
```

**触发时机**:
- ✅ 页面加载时（`DOMContentLoaded`）
- ✅ 打开Debug弹窗时（如果时间段为空）

---

## 📁 文件保存位置

### 导出全部日志
- **保存位置**: `logs/YYYY-MM-DD/debug_log_YYYY-MM-DDTHH-mm-ss.txt`
- **示例**: `logs/2025-12-29/debug_log_2025-12-29T18-30-27.txt`

### 按时间段导出
- **保存位置**: `logs/YYYY-MM-DD/debug_log_START_to_END_exported_TIMESTAMP.txt`
- **示例**: `logs/2025-12-29/debug_log_2025-12-29_18-00-00_to_2025-12-29_18-30-00_exported_2025-12-29T18-30-27.txt`

---

## 🔧 使用方法

### 查看后端日志

1. 打开Debug弹窗（点击 "🐛 Debug日志" 按钮）
2. 时间段选择器自动设置为过去30分钟
3. 日志自动轮询（每2秒）
4. 如果看到错误，检查：
   - 日志文件是否存在：`search_system.log`
   - API端点是否正常：`http://localhost:5000/api/debug_logs`
   - 浏览器控制台是否有详细错误信息

### 导出日志

1. **导出全部日志**:
   - 点击 "导出全部日志" 按钮
   - 文件保存到 `logs/当前日期/` 目录
   - 同时提供浏览器下载

2. **按时间段导出**:
   - 时间段选择器默认选择过去30分钟（可手动调整）
   - 点击 "按时间段导出" 按钮
   - 文件保存到 `logs/当前日期/` 目录
   - 同时提供浏览器下载

---

## ✅ 验证清单

- [x] 错误处理改进（显示详细错误信息）
- [x] HTTP状态码检查
- [x] API响应检查（`data.success`）
- [x] 日志保存API端点
- [x] 自动创建日期目录
- [x] 默认时间段设置（过去30分钟）
- [x] 页面加载时设置默认值
- [x] Debug弹窗打开时设置默认值

---

## 🐛 故障排查

### 问题：仍然看到 "获取后端日志失败: {}"

**检查步骤**:
1. 检查日志文件是否存在：`ls -la search_system.log`
2. 检查API端点：`curl http://localhost:5000/api/debug_logs?lines=5`
3. 检查浏览器控制台：查看详细错误信息
4. 检查网络请求：打开浏览器开发者工具 → Network → 查看 `/api/debug_logs` 请求

### 问题：日志文件未保存到指定目录

**检查步骤**:
1. 检查目录权限：`ls -la logs/`
2. 检查API响应：查看浏览器控制台的API响应
3. 检查服务器日志：查看 `search_system.log` 中的保存日志记录

---

**更新完成日期**: 2025-12-29  
**状态**: ✅ 已完成





