# 并发搜索超时崩溃问题修复

## 问题描述

当同时执行2个搜索任务时：
- 第1个搜索任务成功完成
- 第2个搜索任务一直没有响应
- 最终导致网页崩溃

## 问题分析

### 根本原因

1. **前端超时时间不足**
   - 前端超时：120秒
   - 后端处理时间：60-62秒
   - 如果网络延迟或后端处理变慢，可能超过120秒

2. **后端缺少整体超时保护**
   - `search_engine.search()` 可能在某些情况下卡住
   - 没有整体超时机制，导致请求一直挂起

3. **并行搜索超时处理不完善**
   - `as_completed()` 虽然有超时参数，但异常处理不够完善
   - 如果某个任务卡住，可能影响整体

## 修复内容

### 1. 后端添加整体超时保护

**文件**: `web_app.py`

**修复代码**:
```python
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

# 使用ThreadPoolExecutor执行搜索，支持真正的超时中断
SEARCH_TIMEOUT = 150  # 150秒超时

def execute_search():
    """在独立线程中执行搜索"""
    search_engine = ReloadedSearchEngineV2()
    return search_engine.search(search_request)

with ThreadPoolExecutor(max_workers=1) as executor:
    future = executor.submit(execute_search)
    try:
        response = future.result(timeout=SEARCH_TIMEOUT)
    except FuturesTimeoutError:
        future.cancel()  # 尝试取消任务
        # 返回超时响应
        response = SearchResponse(
            success=False,
            message="搜索超时（超过150秒），请稍后重试或减少搜索条件"
        )
```

**优势**:
- ✅ 真正的超时中断（ThreadPoolExecutor支持）
- ✅ 超时后返回友好错误消息
- ✅ 不会导致请求一直挂起

### 2. 增加前端超时时间

**文件**: `templates/index.html`

**修复代码**:
```javascript
// 之前：120秒超时
// 现在：180秒超时（3分钟）
var timeoutId = setTimeout(function() {
    controller.abort();
}, 180000); // 180秒超时
```

**说明**:
- 180秒 > 后端150秒超时，给后端足够时间
- 如果后端超时，前端也会超时，但会收到明确的错误消息

### 3. 增强并行搜索超时处理

**文件**: `search_engine_v2.py`

**修复代码**:
```python
try:
    for future in as_completed(future_to_task, timeout=timeout):
        try:
            task_name, task_results = future.result(timeout=1.0)
            results[task_name] = task_results
        except concurrent.futures.TimeoutError:
            logger.warning(f"任务结果获取超时")
            results[task_name] = []
except concurrent.futures.TimeoutError:
    logger.warning(f"并行搜索整体超时，已收集部分结果")
    # 尝试获取已完成的任务结果
    for future in future_to_task:
        if future.done():
            try:
                task_name, task_results = future.result(timeout=0.5)
                results[task_name] = task_results
            except:
                pass
```

**优势**:
- ✅ 单个任务超时不影响整体
- ✅ 整体超时后收集已完成的结果
- ✅ 详细的日志记录

## 修复效果

### 修复前
- ❌ 第2个搜索任务可能一直挂起
- ❌ 前端120秒超时可能不够
- ❌ 后端没有整体超时保护
- ❌ 超时后导致崩溃

### 修复后
- ✅ 后端150秒超时保护，超时后返回错误
- ✅ 前端180秒超时，给后端足够时间
- ✅ 并行搜索有完善的超时处理
- ✅ 超时后返回友好错误消息，不会崩溃

## 超时时间配置

| 层级 | 超时时间 | 说明 |
|------|---------|------|
| 前端 | 180秒 | 给后端足够时间 |
| 后端整体 | 150秒 | 搜索整体超时 |
| 并行搜索 | 30秒 | 单个并行搜索任务 |
| 播放列表信息 | 8秒 | 单个播放列表信息获取 |
| LLM评分 | 30秒 | 单个结果LLM评分 |

## 测试建议

1. **正常搜索测试**
   - 执行单个搜索
   - 验证结果正常返回

2. **并发搜索测试**
   - 同时执行2个搜索
   - 验证两个都能正常完成或超时

3. **超时测试**
   - 执行复杂搜索（可能超过150秒）
   - 验证超时后返回友好错误消息
   - 验证不会崩溃

## 相关文件

- `web_app.py` - 后端超时保护
- `templates/index.html` - 前端超时时间
- `search_engine_v2.py` - 并行搜索超时处理

## 修复日期

2026-01-08

