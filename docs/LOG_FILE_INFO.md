# 日志文件说明

## 📝 日志文件位置

**日志文件路径**: `search_system.log`

**完整路径**: `/Users/shmiwanghao8/Desktop/education/Indonesia/search_system.log`

## 🔍 如何查看日志

### 方法 1: 使用命令行查看
```bash
# 查看最新日志（最后50行）
tail -50 search_system.log

# 实时查看日志（类似 tail -f）
tail -f search_system.log

# 查看所有日志
cat search_system.log

# 搜索特定内容
grep "学科交叉验证" search_system.log
grep "搜索B-本地" search_system.log
```

### 方法 2: 使用文本编辑器
直接用任何文本编辑器打开 `search_system.log` 文件即可。

### 方法 3: 使用 less 查看（支持搜索）
```bash
less search_system.log
# 在 less 中：
# - 按 / 搜索
# - 按 n 下一个匹配
# - 按 q 退出
```

## 📊 日志内容

日志文件包含以下信息：

1. **学科交叉验证日志**
   - LLM 输入（System Prompt 和 User Prompt）
   - LLM 输出（完整响应）
   - 解析过程的每一步
   - 遗漏学科详情
   - 去重和补充过程

2. **混合搜索日志**
   - 搜索 A（通用搜索）的查询和结果
   - 搜索 B（本地定向搜索）的配置检查
   - 域名筛选过程
   - 查询词构建过程
   - Tavily API 请求和响应详情
   - 结果合并和去重过程

3. **Tavily API 调用日志**
   - 请求参数（查询词、域名限制等）
   - 响应状态和结果数量
   - 每个结果的 URL 和匹配情况

## 🔄 日志轮转

日志文件使用轮转机制：
- **最大文件大小**: 10MB
- **备份文件数量**: 5个
- **备份文件命名**: `search_system.log.1`, `search_system.log.2`, 等

当日志文件达到 10MB 时，会自动创建新的日志文件，旧文件会被重命名。

## 📋 日志格式

```
2025-12-29 14:45:28 - discovery_agent - INFO - [🔍 验证] 开始学科交叉验证...
2025-12-29 14:45:28 - discovery_agent - INFO - [📋 输入] 国家: Indonesia
2025-12-29 14:45:28 - search_engine - INFO - [🔍 搜索A-通用] 查询: "playlist matematika kelas 3 SD"
```

格式说明：
- `时间戳` - `模块名` - `日志级别` - `消息内容`

## 🎯 调试建议

### 查找学科交叉验证问题
```bash
grep "学科交叉验证" search_system.log
grep "LLM 输出" search_system.log
grep "解析完成" search_system.log
```

### 查找本地化资源搜索问题
```bash
grep "搜索B-本地" search_system.log
grep "视频托管平台" search_system.log
grep "匹配目标域名" search_system.log
```

### 查看完整的搜索流程
```bash
grep "步骤" search_system.log
```

## ⚙️ 日志级别

- **DEBUG**: 详细调试信息（只写入文件，不在控制台显示）
- **INFO**: 一般信息（控制台和文件都显示）
- **WARNING**: 警告信息
- **ERROR**: 错误信息
- **CRITICAL**: 严重错误

## 📝 注意事项

1. 日志文件会持续增长，建议定期清理或查看
2. 日志文件包含敏感信息（如 API 响应），请妥善保管
3. 如果日志文件不存在，会在第一次运行时自动创建
4. 所有 `print()` 语句的输出都会自动写入日志文件

## 🔧 自定义日志文件位置

如果需要更改日志文件位置，可以修改 `logger_utils.py` 中的 `LOG_FILE` 变量：

```python
LOG_FILE = os.path.join(LOG_DIR, 'your_custom_log_file.log')
```

或者在使用时指定：

```python
from logger_utils import get_logger
logger = get_logger('module_name', log_file='/path/to/custom.log')
```

