# 日志问题排查指南

## 🔍 问题：日志文件中没有搜索信息

### 可能的原因

1. **Web 应用未重启**
   - 如果 Web 应用在添加日志功能之前就已经启动，需要重启才能生效
   - 日志系统在模块导入时初始化，已运行的进程不会自动加载新代码

2. **日志文件路径问题**
   - 日志文件位置：`/Users/shmiwanghao8/Desktop/education/Indonesia/search_system.log`
   - 确保有写入权限

3. **模块导入顺序问题**
   - 日志系统必须在导入其他模块之前初始化

## ✅ 解决方案

### 步骤 1: 重启 Web 应用

```bash
# 1. 找到正在运行的 Web 应用进程
ps aux | grep "python.*web_app\|flask"

# 2. 停止 Web 应用（使用 Ctrl+C 或 kill 命令）
# 如果使用 kill，替换 <PID> 为实际的进程ID
kill <PID>

# 3. 重新启动 Web 应用
python3 web_app.py
# 或
./start_web_app.sh
```

### 步骤 2: 验证日志功能

运行测试脚本：

```bash
python3 test_logging.py
```

然后检查日志文件：

```bash
tail -50 search_system.log
```

### 步骤 3: 执行一次搜索

在浏览器中执行一次搜索，然后立即检查日志：

```bash
# 实时查看日志（推荐）
tail -f search_system.log

# 或查看最新日志
tail -100 search_system.log
```

## 📋 日志文件位置确认

```bash
# 查看日志文件
ls -lh search_system.log

# 查看日志文件内容
cat search_system.log

# 实时监控日志
tail -f search_system.log
```

## 🔧 如果仍然没有日志

### 检查 1: 确认日志文件存在且可写

```bash
touch search_system.log
chmod 666 search_system.log
```

### 检查 2: 手动测试日志功能

```bash
python3 -c "
from logger_utils import get_logger
logger = get_logger('manual_test')
logger.info('手动测试日志')
print('请检查 search_system.log 文件')
"
```

### 检查 3: 检查 Web 应用启动日志

查看 Web 应用启动时的输出，应该看到：

```
📝 日志系统启动 - 日志文件: /Users/shmiwanghao8/Desktop/education/Indonesia/search_system.log
```

如果没有看到这条消息，说明日志系统没有正确初始化。

## 📝 日志内容说明

日志文件应该包含：

1. **搜索请求信息**
   - 国家、年级、学科
   - 搜索词生成过程

2. **混合搜索过程**
   - 搜索 A（通用搜索）的查询和结果
   - 搜索 B（本地定向搜索）的配置检查
   - 域名筛选和查询构建过程

3. **学科交叉验证过程**（如果使用国家发现功能）
   - LLM 输入输出
   - 解析过程
   - 遗漏学科补充

## 🎯 快速验证

运行以下命令，应该能看到日志输出：

```bash
# 1. 清空日志文件（可选）
> search_system.log

# 2. 在另一个终端实时查看日志
tail -f search_system.log

# 3. 在浏览器中执行一次搜索

# 4. 观察日志文件是否有新内容
```

## ⚠️ 注意事项

1. **日志文件会持续增长**：建议定期清理或查看
2. **日志包含敏感信息**：API 响应、查询词等，请妥善保管
3. **多进程问题**：如果使用多进程部署，每个进程会有独立的日志文件

## 🔄 如果问题仍然存在

请提供以下信息：

1. Web 应用启动时的完整输出
2. 执行搜索时的控制台输出
3. 日志文件的内容（如果有）
4. Python 版本：`python3 --version`

