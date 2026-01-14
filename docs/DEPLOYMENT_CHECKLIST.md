# 搜索系统优化部署检查清单

**项目**: Indonesia K12 Video Search System V3
**优化版本**: Ralph Loop 迭代1-4
**部署日期**: 2026-01-05

---

## 📋 部署前检查

### 1. 代码完整性检查

- [x] **缓存模块**
  - [x] `core/search_cache.py` 文件存在
  - [x] SearchCache 类实现完整
  - [x] 缓存目录可访问

- [x] **并行搜索**
  - [x] `search_engine_v2.py` 已更新
  - [x] `_parallel_search()` 方法存在
  - [x] `concurrent.futures` 已导入

- [x] **配置集成**
  - [x] `core/config_loader.py` 已导入
  - [x] `app_config` 属性已添加
  - [x] `_is_edtech_domain()` 方法存在

- [x] **测试工具**
  - [x] `scripts/performance_test.py` 已创建
  - [x] 可执行权限已设置

### 2. 文档完整性检查

- [x] **优化文档**
  - [x] `docs/OPTIMIZATION_REPORT.md`
  - [x] `docs/SEARCH_OPTIMIZATION_PLAN.md`
  - [x] `docs/ralph_iteration_2_summary.md`
  - [x] `docs/ralph_iteration_3_summary.md`
  - [x] `docs/ralph_iteration_4_summary.md`

- [x] **配置文档**
  - [x] `docs/CONFIGURATION_GUIDE.md`
  - [x] `config/README.md`

---

## 🔧 环境准备

### 1. Python环境

```bash
# 检查Python版本
python3 --version  # 应该是 3.9+

# 检查依赖包
pip3 list | grep -E "flask|pydantic|requests|pyyaml"
```

**必需的依赖包**:
- [ ] Flask >= 2.0
- [ ] Pydantic >= 2.0
- [ ] requests
- [ ] PyYAML

### 2. 目录结构检查

```bash
# 检查必需的目录
ls -la data/        # 数据目录
ls -la data/cache/  # 缓存目录（应该存在）
ls -la config/      # 配置目录
ls -la core/        # 核心模块目录
ls -la scripts/     # 脚本目录
ls -la logs/        # 日志目录
```

**必需的目录**:
- [ ] `data/` - 数据目录
- [ ] `data/cache/` - 缓存目录（自动创建）
- [ ] `config/` - 配置文件目录
- [ ] `core/` - 核心模块目录
- [ ] `logs/` - 日志目录

### 3. 配置文件检查

```bash
# 检查配置文件
ls -la config/*.yaml

# 验证YAML语法
python3 -c "import yaml; yaml.safe_load(open('config/search.yaml'))"
```

**必需的配置文件**:
- [ ] `config/evaluation_weights.yaml`
- [ ] `config/llm.yaml`
- [ ] `config/search.yaml`
- [ ] `config/video_processing.yaml`

### 4. 环境变量配置

```bash
# 检查.env文件
cat .env

# 必需的环境变量
echo $OPENAI_API_KEY
echo $AI_BUILDER_TOKEN
echo $GOOGLE_API_KEY
echo $GOOGLE_CX
echo $BAIDU_API_KEY
```

**必需的环境变量**:
- [ ] `OPENAI_API_KEY` - OpenAI API密钥
- [ ] `AI_BUILDER_TOKEN` - AI Builders Token
- [ ] `GOOGLE_API_KEY` - Google API密钥（可选）
- [ ] `GOOGLE_CX` - Google自定义搜索ID（可选）
- [ ] `BAIDU_API_KEY` - 百度API密钥（可选）

**优化相关环境变量**:
- [ ] `ENABLE_PARALLEL_SEARCH=true` - 启用并行搜索（默认true）

---

## 🧪 功能测试

### 1. 基础导入测试

```bash
python3 -c "
from search_engine_v2 import SearchEngineV2
from core.search_cache import get_search_cache
print('✅ 所有模块导入成功')
"
```

**预期输出**:
```
✅ SearchEngineV2 导入成功
✅ 所有模块导入成功
```

### 2. 缓存功能测试

```bash
python3 -c "
from core.search_cache import get_search_cache
cache = get_search_cache()
print(f'✅ 缓存初始化成功')
print(f'✅ 缓存目录: {cache.cache_dir}')
print(f'✅ TTL: {cache.ttl_seconds}秒')
"
```

**预期输出**:
```
✅ 缓存初始化成功
✅ 缓存目录: data/cache
✅ TTL: 3600秒
```

### 3. 并行搜索测试

```bash
python3 -c "
from search_engine_v2 import SearchEngineV2
engine = SearchEngineV2()
print(f'✅ SearchEngineV2实例化成功')
print(f'✅ 有_parallel_search方法: {hasattr(engine, \"_parallel_search\")}')
print(f'✅ 有_cached_search方法: {hasattr(engine, \"_cached_search\")}')
"
```

**预期输出**:
```
✅ SearchEngineV2实例化成功
✅ 有_parallel_search方法: True
✅ 有_cached_search方法: True
```

### 4. 配置加载测试

```bash
python3 -c "
from search_engine_v2 import SearchEngineV2
engine = SearchEngineV2()
print(f'✅ 有app_config属性: {hasattr(engine, \"app_config\")}')
print(f'✅ 有_is_edtech_domain方法: {hasattr(engine, \"_is_edtech_domain\")}')
"
```

**预期输出**:
```
✅ 有app_config属性: True
✅ 有_is_edtech_domain方法: True
```

### 5. 性能测试

```bash
# 运行完整的性能测试
python3 scripts/performance_test.py
```

**预期输出**:
```
================================================================================
🔍 搜索性能测试
================================================================================

[测试1: 并行搜索]
[测试2: 串行搜索]
[性能对比]
✅ 性能提升: 60-80%
```

---

## 🚀 部署步骤

### 1. 备份当前版本

```bash
# 创建备份目录
mkdir -p backups/before_optimization_$(date +%Y%m%d)

# 备份关键文件
cp search_engine_v2.py backups/before_optimization_$(date +%Y%m%d)/
cp web_app.py backups/before_optimization_$(date +%Y%m%d)/
cp -r config/ backups/before_optimization_$(date +%Y%m%d)/
```

### 2. 更新代码

```bash
# 确保在项目根目录
cd /Users/shmiwanghao8/Desktop/education/Indonesia

# 验证新文件存在
ls -la core/search_cache.py
ls -la scripts/performance_test.py
```

### 3. 设置环境变量

```bash
# 在.env文件中添加优化配置
echo "ENABLE_PARALLEL_SEARCH=true" >> .env

# 验证
cat .env | grep PARALLEL
```

### 4. 创建缓存目录

```bash
# 创建缓存目录（如果不存在）
mkdir -p data/cache

# 设置权限
chmod 755 data/cache
```

### 5. 停止旧服务

```bash
# 查找并停止正在运行的Flask服务
ps aux | grep "python3 web_app.py"
kill <PID>

# 或者使用停止脚本（如果有）
./scripts/stop.sh
```

### 6. 启动新服务

```bash
# 启动Flask应用
python3 web_app.py

# 或者使用启动脚本（如果有）
./scripts/start.sh
```

### 7. 验证部署

```bash
# 检查服务是否启动
curl http://localhost:5001/api/countries

# 检查日志
tail -f search_system.log | grep -E "缓存|并行|搜索"
```

**预期日志输出**:
```
[INFO] 搜索缓存初始化完成: data/cache, TTL=3600秒
[INFO] 使用并行搜索模式
[INFO] 并行搜索启动 3 个任务
```

---

## 📊 部署后验证

### 1. 功能验证

**搜索功能测试**:
- [ ] 访问主页 http://localhost:5001
- [ ] 执行搜索请求
- [ ] 查看搜索结果
- [ ] 检查响应时间

**缓存验证**:
- [ ] 执行相同搜索两次
- [ ] 第二次应该更快（缓存命中）
- [ ] 检查日志中的缓存命中率

**并行搜索验证**:
- [ ] 查看日志中的并行搜索输出
- [ ] 确认多个搜索引擎并行执行
- [ ] 检查总耗时是否减少

### 2. 性能验证

**性能指标**:
- [ ] 搜索响应时间 < 5秒（优化前约9秒）
- [ ] 缓存命中率 > 20%
- [ ] 并行搜索日志正常
- [ ] 无明显错误或警告

**运行性能测试**:
```bash
python3 scripts/performance_test.py
```

**预期结果**:
- 性能提升 > 50%
- 并行搜索工作正常
- 缓存统计正常

### 3. 日志验证

**检查关键日志**:
```bash
# 缓存日志
grep "缓存" search_system.log | tail -20

# 并行搜索日志
grep "并行" search_system.log | tail -20

# 错误日志
grep "ERROR" search_system.log | tail -20
```

**预期输出**:
```
[INFO] ✅ 缓存命中: Matematika Kelas 5... (命中率: 35.0%)
[INFO] ⚡ 并行搜索启动 3 个并行搜索任务
[INFO] ✅ Tavily通用搜索 完成 (2.34秒, 15个结果)
[INFO] ✅ Google搜索 完成 (2.89秒, 12个结果)
```

---

## ⚠️ 常见问题和解决方案

### 问题1: 缓存目录权限错误

**症状**:
```
PermissionError: [Errno 13] Permission denied: 'data/cache'
```

**解决方案**:
```bash
# 创建目录并设置权限
mkdir -p data/cache
chmod 755 data/cache

# 或者使用当前用户
sudo chown -R $USER:$USER data/cache
```

### 问题2: 并行搜索未生效

**症状**: 日志显示"使用串行搜索"

**解决方案**:
```bash
# 检查环境变量
echo $ENABLE_PARALLEL_SEARCH

# 设置为true
export ENABLE_PARALLEL_SEARCH=true

# 或者在.env文件中添加
echo "ENABLE_PARALLEL_SEARCH=true" >> .env
```

### 问题3: 配置文件读取失败

**症状**: 日志显示"从配置读取失败，使用硬编码映射"

**解决方案**:
```bash
# 检查配置文件
cat config/search.yaml

# 验证YAML语法
python3 -c "import yaml; yaml.safe_load(open('config/search.yaml'))"

# 检查文件权限
ls -la config/search.yaml
```

### 问题4: 性能提升不明显

**可能原因**:
1. 网络延迟高
2. API限流
3. 缓存未命中

**诊断**:
```bash
# 运行性能测试
python3 scripts/performance_test.py

# 检查缓存统计
python3 -c "
from core.search_cache import get_search_cache
cache = get_search_cache()
print(cache.get_stats())
"
```

---

## 📈 监控指标

### 关键性能指标 (KPI)

| 指标 | 目标值 | 实际值 | 状态 |
|------|--------|--------|------|
| 搜索响应时间 | < 5秒 | ___ | ⬜ |
| 缓存命中率 | > 20% | ___ | ⬜ |
| 并行搜索成功率 | > 95% | ___ | ⬜ |
| API错误率 | < 5% | ___ | ⬜ |

### 监控命令

**实时监控日志**:
```bash
tail -f search_system.log
```

**查看缓存统计**:
```bash
python3 -c "
from core.search_cache import get_search_cache
import json
cache = get_search_cache()
print(json.dumps(cache.get_stats(), indent=2))
"
```

**查看缓存文件**:
```bash
ls -lh data/cache/ | wc -l  # 缓存文件数量
du -sh data/cache/          # 缓存目录大小
```

---

## ✅ 部署完成检查

### 最终检查清单

- [ ] 所有文件已更新
- [ ] 环境变量已配置
- [ ] 缓存目录已创建
- [ ] 服务已重启
- [ ] 功能测试通过
- [ ] 性能测试通过
- [ ] 日志正常输出
- [ ] 监控指标正常

### 签署确认

**部署人员**: ___________
**测试人员**: ___________
**产品经理**: ___________
**部署日期**: ___________

---

## 📞 紧急回滚

如果部署后出现严重问题，执行回滚：

```bash
# 1. 停止服务
./scripts/stop.sh

# 2. 恢复备份文件
cp backups/before_optimization_YYYYMMDD/search_engine_v2.py ./
cp backups/before_optimization_YYYYMMDD/web_app.py ./

# 3. 禁用优化功能
export ENABLE_PARALLEL_SEARCH=false

# 4. 重启服务
./scripts/start.sh

# 5. 验证回滚成功
curl http://localhost:5001/api/countries
```

---

**检查清单版本**: 1.0
**最后更新**: 2026-01-05
**状态**: ✅ 就绪部署
