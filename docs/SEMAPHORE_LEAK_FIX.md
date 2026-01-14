# Semaphore泄漏问题修复报告

## 问题描述

在网页上点击多个年级/学科搜索后，过几分钟网页会崩溃。日志中显示：
```
resource_tracker: There appear to be 1 leaked semaphore objects to clean up at shutdown
```

## 根本原因

### 1. 并发限制器中的Semaphore泄漏 ⚠️ **严重**

**问题位置**: `core/concurrency_limiter.py` 的 `release()` 方法

**问题分析**:
- `release()` 方法总是调用 `self.semaphore.release()`，即使 `request_id` 不在 `active_requests` 中
- 如果 `acquire()` 返回 `False`（超时），但代码路径错误地调用了 `release()`，会导致semaphore计数不匹配
- 如果 `acquire()` 成功，但后续发生异常，`release()` 会被调用，但如果 `request_id` 不在 `active_requests` 中，仍然会调用 `semaphore.release()`，导致计数不匹配

**修复前代码**:
```python
def release(self):
    """释放执行许可"""
    with self.active_lock:
        request_id = threading.get_ident()
        if request_id in self.active_requests:
            self.active_requests.remove(request_id)
            self.stats["completed_requests"] += 1

    self.semaphore.release()  # ❌ 总是释放，即使没有成功获取
    logger.debug(f"释放许可: 当前并发={len(self.active_requests)}/{self.max_concurrent}")
```

### 2. web_app.py中的并发限制器使用问题

**问题位置**: `web_app.py` 的 `/api/search` 端点

**问题分析**:
- 如果 `acquire()` 返回 `False`（超时），代码会直接返回，但 `finally` 块仍然会执行 `release()`
- 这会导致semaphore泄漏，因为释放了从未获取的许可

**修复前代码**:
```python
if concurrency_limiter is not None:
    if not concurrency_limiter.acquire(timeout=5.0):
        return jsonify({...}), 503

try:
    # ... 搜索逻辑 ...
finally:
    # ❌ 总是释放，即使acquire失败
    if concurrency_limiter is not None:
        concurrency_limiter.release()
```

## 修复方案

### 1. 修复 `concurrency_limiter.py`

**修复后代码**:
```python
def release(self):
    """释放执行许可"""
    with self.active_lock:
        request_id = threading.get_ident()
        if request_id in self.active_requests:
            self.active_requests.remove(request_id)
            self.stats["completed_requests"] += 1
            # ✅ 只有在成功获取许可的情况下才释放semaphore
            self.semaphore.release()
            logger.debug(f"释放许可: 当前并发={len(self.active_requests)}/{self.max_concurrent}")
        else:
            # ✅ 如果request_id不在active_requests中，说明没有成功获取许可，不应该释放semaphore
            logger.warning(f"尝试释放未获取的许可: request_id={request_id}, 当前活跃请求={list(self.active_requests)}")
```

**关键改进**:
- ✅ 只有当 `request_id` 在 `active_requests` 中时才释放semaphore
- ✅ 添加警告日志，帮助调试未匹配的释放操作

### 2. 修复 `web_app.py`

**修复后代码**:
```python
# 并发限制检查
acquired_limiter = False  # ✅ 跟踪是否成功获取许可
if concurrency_limiter is not None:
    if concurrency_limiter.acquire(timeout=5.0):
        acquired_limiter = True  # ✅ 标记已获取
    else:
        logger.warning(f"搜索请求被限流: 超过最大并发数")
        return jsonify({...}), 503

try:
    # ... 搜索逻辑 ...
finally:
    # ✅ 只有在成功获取许可的情况下才释放
    if concurrency_limiter is not None and acquired_limiter:
        try:
            concurrency_limiter.release()
        except Exception as e:
            logger.error(f"释放并发限制器失败: {str(e)}")
```

**关键改进**:
- ✅ 使用 `acquired_limiter` 标志跟踪是否成功获取许可
- ✅ 只有在成功获取时才释放
- ✅ 添加异常处理，防止释放过程中的错误导致崩溃

## 修复文件清单

1. ✅ `core/concurrency_limiter.py` - 修复 `release()` 方法
2. ✅ `web_app.py` - 修复 `/api/search` 端点的并发限制器使用

## 验证方法

### 1. 重启服务器

```bash
# 停止现有服务器
pkill -f "web_app.py"

# 启动服务器
python3 web_app.py
```

### 2. 执行多次搜索测试

使用测试脚本模拟多次搜索：
```bash
python3 scripts/test_multiple_searches.py
```

### 3. 检查日志

检查是否还有semaphore泄漏警告：
```bash
tail -f web_app.log | grep -E "semaphore|leaked|释放许可|获取许可"
```

**预期结果**:
- ✅ 不应该再出现 `resource_tracker: There appear to be X leaked semaphore objects` 警告
- ✅ 如果出现 `尝试释放未获取的许可` 警告，说明有代码路径问题，需要进一步调查

### 4. 手动测试

在网页上连续点击多个年级/学科进行搜索，观察：
- ✅ 服务器是否稳定运行
- ✅ 是否出现崩溃
- ✅ 日志中是否有错误

## 预期效果

修复后，系统应该能够：
- ✅ 正确处理并发搜索请求
- ✅ 正确释放semaphore资源
- ✅ 避免semaphore泄漏导致的崩溃
- ✅ 稳定运行长时间

## 注意事项

1. **需要重启服务器**: 修复后需要重启服务器才能生效
2. **监控日志**: 建议持续监控日志，确保没有新的semaphore泄漏
3. **并发限制**: 当前最大并发数为10（可通过环境变量 `MAX_CONCURRENT_SEARCHES` 配置）

## 相关文件

- `core/concurrency_limiter.py` - 并发限制器实现
- `web_app.py` - Flask应用主文件
- `scripts/test_multiple_searches.py` - 测试脚本

## 修复日期

2026-01-06

