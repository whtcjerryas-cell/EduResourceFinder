# 搜索多个条件崩溃问题修复（重新应用）

## 问题描述

用户报告：搜索多个条件导致崩溃的问题又出现了。

## 排查结果

### ✅ 已确认的修复点

1. **并发限制器（core/concurrency_limiter.py）**
   - ✅ Semaphore泄漏修复：只在成功获取时释放
   - ✅ 默认并发数：2（已降低）
   - ✅ 诊断测试：通过

2. **后端搜索API（web_app.py）**
   - ✅ acquired_limiter标志：正确使用
   - ✅ 超时保护：ThreadPoolExecutor + 150秒
   - ✅ 内存清理：gc.collect()正确调用

3. **前端批量搜索（templates/index.html）**
   - ✅ isSearchCompleted标志：正确设置
   - ✅ Promise.all()：等待所有任务完成
   - ✅ MAX_CONCURRENT：2（与后端匹配）

### ⚠️ 发现的问题

1. **多个web_app进程**
   - 发现2个进程同时运行
   - 可能导致端口冲突和资源竞争
   - **已解决**：停止所有进程

## 修复措施

### 1. 停止所有进程
```bash
pkill -f "python.*web_app.py"
```

### 2. 验证关键修复点

#### core/concurrency_limiter.py
```python
def release(self):
    with self.active_lock:
        request_id = threading.get_ident()
        if request_id in self.active_requests:
            self.active_requests.remove(request_id)
            self.stats["completed_requests"] += 1
            # ✅ 只有在成功获取许可的情况下才释放semaphore
            self.semaphore.release()
```

#### web_app.py
```python
acquired_limiter = False
if concurrency_limiter is not None:
    if concurrency_limiter.acquire(timeout=5.0):
        acquired_limiter = True
    else:
        return jsonify({"success": False, "message": "服务器繁忙"}), 503

try:
    # 执行搜索
finally:
    # ✅ 只有在成功获取许可的情况下才释放
    if concurrency_limiter is not None and acquired_limiter:
        concurrency_limiter.release()
```

#### templates/index.html
```javascript
// ✅ 等待所有任务完成
await Promise.all(allPromises);

// ✅ 设置标志阻止进度更新
isSearchCompleted = true;
```

## 重启服务器

### 启动命令
```bash
cd /Users/shmiwanghao8/Desktop/education/Indonesia
source venv/bin/activate
python web_app.py
```

### 验证步骤

1. **检查进程**
   ```bash
   ps aux | grep -E "python.*web_app" | grep -v grep
   ```
   - 应该只有1个进程

2. **检查端口**
   ```bash
   lsof -i :5000
   lsof -i :5001
   ```
   - 应该只有1个进程占用端口

3. **测试单个搜索**
   - 选择1个国家、1个年级、1个学科
   - 点击搜索
   - 应该正常返回结果

4. **测试批量搜索**
   - 选择1个国家、2个年级、1个学科（2个组合）
   - 点击搜索
   - 应该正常完成，不崩溃

## 预防措施

### 1. 确保只有一个进程运行

创建启动脚本 `start_web_app_safe.sh`：
```bash
#!/bin/bash
cd /Users/shmiwanghao8/Desktop/education/Indonesia

# 停止所有现有进程
pkill -f "python.*web_app.py"
sleep 2

# 检查是否还有进程
if ps aux | grep -E "python.*web_app" | grep -v grep; then
    echo "❌ 仍有进程在运行，请手动停止"
    exit 1
fi

# 启动新进程
source venv/bin/activate
python web_app.py
```

### 2. 监控内存使用

定期检查内存使用：
```bash
ps aux | grep -E "python.*web_app" | awk '{print $6/1024 " MB"}'
```

### 3. 查看日志

定期查看错误日志：
```bash
tail -f search_system.log | grep -E "ERROR|Exception|崩溃|crash|内存|memory|semaphore|泄漏"
```

## 如果问题再次出现

### 排查步骤

1. **检查进程数**
   ```bash
   ps aux | grep -E "python.*web_app" | grep -v grep | wc -l
   ```
   - 应该只有1个

2. **检查并发限制器状态**
   ```bash
   python3 scripts/diagnose_crash.py
   ```

3. **查看最新日志**
   ```bash
   tail -100 search_system.log | grep -E "ERROR|Exception|崩溃|crash"
   ```

4. **检查内存使用**
   ```bash
   ps aux | grep -E "python.*web_app" | awk '{print $6/1024 " MB"}'
   ```

### 快速修复

如果问题再次出现，执行：
```bash
# 1. 停止所有进程
pkill -f "python.*web_app.py"

# 2. 等待2秒
sleep 2

# 3. 验证进程已停止
ps aux | grep -E "python.*web_app" | grep -v grep || echo "✅ 所有进程已停止"

# 4. 重新启动
cd /Users/shmiwanghao8/Desktop/education/Indonesia
source venv/bin/activate
python web_app.py
```

## 修复日期

2026-01-08
