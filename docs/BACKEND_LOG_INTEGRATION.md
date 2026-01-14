# 后端日志集成到前端Debug弹窗

## 📅 更新日期
2025-12-29

## 🎯 问题分析

### 问题现象
前端Debug弹窗只显示前端日志（`console.log`等），没有显示后端日志（LLM调用、API调用等）。

### 根本原因
- 后端的`print`语句输出到控制台和日志文件（`search_system.log`）
- 前端的Debug弹窗只捕获浏览器`console.log`等输出
- **后端日志不会自动出现在前端Debug弹窗中**

## ✅ 解决方案

### 1. 添加日志API端点 (`web_app.py`)

新增 `/api/debug_logs` 端点，允许前端获取后端日志：

```python
@app.route('/api/debug_logs', methods=['GET'])
def get_debug_logs():
    """
    获取后端日志 - 用于前端Debug弹窗显示
    
    查询参数:
        - lines: 返回最后N行日志（默认500）
        - since: ISO格式时间戳，只返回此时间之后的日志
        - level: 日志级别过滤（DEBUG, INFO, WARNING, ERROR）
    """
```

**功能**:
- ✅ 读取 `search_system.log` 文件
- ✅ 支持时间段过滤（`since`参数）
- ✅ 支持日志级别过滤（`level`参数）
- ✅ 返回解析后的日志（包含时间戳、logger、级别、消息）

### 2. 搜索API返回日志 (`web_app.py`)

修改 `/api/search` 端点，在响应中包含最近的日志：

```python
return jsonify({
    "success": response.success,
    "query": response.query,
    "results": results_data,
    ...
    "debug_logs": search_logs[-100:] if search_logs else []  # 返回最后100行日志
})
```

**功能**:
- ✅ 每次搜索完成后，自动返回最近100行日志
- ✅ 包含LLM调用、API调用的完整输入输出
- ✅ 前端自动处理后端日志，无需额外请求

### 3. 前端日志轮询 (`templates/index.html`)

添加定期轮询机制，实时获取后端日志：

```javascript
// 定期获取后端日志（每2秒）
function startBackendLogPolling() {
    fetchBackendLogs();  // 首次立即获取
    backendLogInterval = setInterval(fetchBackendLogs, 2000);  // 每2秒获取一次
}
```

**功能**:
- ✅ 打开Debug弹窗时自动开始轮询
- ✅ 关闭Debug弹窗时停止轮询
- ✅ 使用增量获取（`since`参数），只获取新日志
- ✅ 自动去重，避免重复显示

### 4. 前端日志处理 (`templates/index.html`)

在搜索响应中处理后端日志：

```javascript
// 处理后端返回的日志（包含LLM和API调用的详细输出）
if (data.debug_logs && Array.isArray(data.debug_logs)) {
    data.debug_logs.forEach(logLine => {
        // 解析日志行并添加到debugLogs数组
    });
}
```

**功能**:
- ✅ 解析日志行格式（时间戳、logger、级别、消息）
- ✅ 转换为前端日志格式（包含ISO时间戳）
- ✅ 标记为后端日志（`source: 'backend'`）
- ✅ 自动去重

## 📊 日志显示

### 日志来源标识

- **[后端-xxx]**: 后端日志（来自`search_system.log`）
- **[前端]**: 前端日志（来自`console.log`等）

### 日志级别

- **error**: 错误（红色）
- **warning**: 警告（黄色）
- **info**: 信息（青色）
- **debug**: 调试（绿色）

### 日志内容

后端日志包含：
- ✅ LLM调用的完整输入输出（Prompt、响应、Token使用）
- ✅ Tavily API调用的完整请求响应（Payload、响应体）
- ✅ 结果评估的详细过程
- ✅ 错误信息和堆栈跟踪

## 🔧 使用方法

### 查看后端日志

1. 打开Debug弹窗（点击 "🐛 Debug日志" 按钮）
2. 执行搜索操作
3. 查看日志：
   - **自动获取**: 搜索完成后，后端日志自动显示
   - **实时轮询**: 打开弹窗后，每2秒自动获取新日志
   - **手动刷新**: 点击 "🔄 刷新后端日志" 按钮

### 日志状态显示

Debug弹窗顶部显示：
```
后端: 150 条 | 前端: 50 条 | 总计: 200 条
```

## 📝 API端点

### GET /api/debug_logs

**查询参数**:
- `lines`: 返回最后N行日志（默认500）
- `since`: ISO格式时间戳，只返回此时间之后的日志
- `level`: 日志级别过滤（DEBUG, INFO, WARNING, ERROR）

**响应格式**:
```json
{
    "success": true,
    "logs": [
        {
            "timestamp": "2025-12-29 15:00:54",
            "isoTimestamp": "2025-12-29T15:00:54Z",
            "logger": "search_engine",
            "level": "info",
            "message": "[🤖 LLM调用] 开始调用 deepseek"
        }
    ],
    "total_lines": 1000,
    "returned_lines": 500
}
```

## ✅ 验证清单

- [x] 后端日志API端点正常工作
- [x] 搜索API返回日志字段
- [x] 前端正确处理后端日志
- [x] 日志轮询机制正常工作
- [x] 日志去重功能正常
- [x] 日志显示包含来源标识
- [x] 时间段筛选正常工作
- [x] 日志导出包含后端日志

## 🐛 故障排查

### 问题：看不到后端日志

**检查**:
1. 确认日志文件存在：`search_system.log`
2. 检查后端日志API：访问 `http://localhost:5000/api/debug_logs`
3. 检查浏览器控制台：是否有API请求错误
4. 检查日志轮询：打开Debug弹窗后，是否每2秒请求一次

### 问题：日志重复显示

**原因**: 去重逻辑可能失效

**解决**: 检查 `isDuplicate` 判断逻辑，确保基于时间戳和消息内容去重

### 问题：日志太多导致页面卡顿

**解决**: 
- 日志数量限制已设置为5000条
- 可以清空日志或使用时间段筛选

---

**更新完成日期**: 2025-12-29  
**状态**: ✅ 已完成





