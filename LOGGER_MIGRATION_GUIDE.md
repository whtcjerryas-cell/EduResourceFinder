# Logger 迁移规范

## 日志级别定义

### ERROR（错误）
**用途**: API 调用失败、文件读取错误、异常情况
**示例**:
- API 调用失败、超时
- 文件不存在或无法读取
- 初始化失败

**替换规则**:
```python
# 替换前
print(f"[❌ 错误] 公司内部API调用失败: {error_msg}")

# 替换后
logger.error(f"公司内部API调用失败: {error_msg}")
```

---

### WARNING（警告）
**用途**: 降级到备用 API、额度不足、可恢复的问题
**示例**:
- 降级到备用 API
- API 返回空内容
- 客户端初始化失败（有备用方案）

**替换规则**:
```python
# 替换前
print(f"[⚠️ 警告] Gemini-2.5-Pro 返回空内容，自动切换到 DeepSeek...")

# 替换后
logger.warning(f"Gemini-2.5-Pro 返回空内容，自动切换到 DeepSeek...")
```

---

### INFO（信息）
**用途**: 正常操作（搜索、API 调用开始/成功）
**示例**:
- API 调用开始
- 搜索执行
- 客户端初始化成功
- 操作成功完成

**替换规则**:
```python
# 替换前
print(f"[✅] 公司内部API客户端初始化成功")

# 替换后
logger.info("公司内部API客户端初始化成功")
```

---

### DEBUG（调试）
**用途**: 详细参数、响应内容、调试信息
**示例**:
- 详细的请求参数
- 响应内容前 N 个字符
- 内部处理逻辑

**替换规则**:
```python
# 替换前
print(f"[📤 输入] Model: {model_name}")
print(f"[📤 输入] Max Tokens: {max_tokens}")

# 替换后
logger.debug(f"Model: {model_name}, Max Tokens: {max_tokens}")
```

---

## 批量替换脚本

### 第 1 步: 替换 ERROR 日志
```bash
# 替换 [❌ 错误] 为 logger.error
sed -i 's/print(f"\[❌ 错误\]/logger.error(f"/g' llm_client.py
```

### 第 2 步: 替换 WARNING 日志
```bash
# 替换 [⚠️ 警告] 为 logger.warning
sed -i 's/print(f"\[⚠️ 警告\]/logger.warning(f"/g' llm_client.py
# 替换 [⚠️] 为 logger.warning（无"警告"文本）
sed -i 's/print(f"\[⚠️\]/logger.warning(f"/g' llm_client.py
```

### 第 3 步: 替换 INFO 日志
```bash
# 替换 [✅] 为 logger.info
sed -i 's/print("\[✅\]/logger.info("/g' llm_client.py
# 替换成功的 API 调用
sed -i 's/print(f"\[✅/logger.info(f"/g' llm_client.py
```

### 第 4 步: 替换 DEBUG 日志
```bash
# 替换 [📤 输入] 为 logger.debug
sed -i 's/print(f"\[📤 输入\]/logger.debug(f"/g' llm_client.py
# 替换 [📥 响应] 为 logger.debug
sed -i 's/print(f"\[📥 响应\]/logger.debug(f"/g' llm_client.py'
```

---

## 特殊情况处理

### 1. 多行 print 语句
```python
# 替换前
print(f"[❌ 错误] 公司内部API调用失败: {error_msg}")
print(f"[❌ 错误] 异常类型: {type(e).__name__}")
print(f"[❌ 错误] 异常堆栈:\n{traceback.format_exc()}")

# 替换后
logger.error(f"公司内部API调用失败: {error_msg}\n"
             f"异常类型: {type(e).__name__}\n"
             f"异常堆栈:\n{traceback.format_exc()}")
```

### 2. 分隔线
```python
# 替换前
print(f"\n{'='*80}")
print(f"[🏢 公司内部API] 开始调用 {model_name}")
print(f"{'='*80}")

# 替换后
logger.info(f"{'='*80}\n"
            f"公司内部API 开始调用 {model_name}\n"
            f"{'='*80}")
```

### 3. 表情符号
- 移除装饰性表情符号（❌, ⚠️, ✅, 📤, 📥, 🔍等）
- 保留有意义的文本信息

---

## Logger 配置

确保在 `logger_utils.py` 中配置了正确的日志格式：

```python
import logging
import sys

def get_logger(name: str) -> logging.Logger:
    """获取配置好的 logger"""
    logger = logging.getLogger(name)

    if not logger.handlers:
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # 文件处理器（可选）
        file_handler = logging.FileHandler('app.log')
        file_handler.setLevel(logging.DEBUG)

        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        logger.setLevel(logging.DEBUG)

    return logger
```

---

## 验证检查清单

- [ ] 所有 ERROR 级别的日志已迁移
- [ ] 所有 WARNING 级别的日志已迁移
- [ ] 关键 INFO 级别的日志已迁移
- [ ] 关键 DEBUG 级别的日志已迁移
- [ ] 移除了不必要的表情符号
- [ ] 日志格式统一
- [ ] 测试验证日志输出正常

---

**创建日期**: 2026-01-21
**状态**: 规范定义完成，待执行迁移
