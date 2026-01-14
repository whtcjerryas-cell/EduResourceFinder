# 搜索系统优化快速开始指南

**版本**: 1.0
**更新时间**: 2026-01-05
**适合人群**: 产品经理、开发人员

---

## 🚀 5分钟快速上手

### 第一步：验证环境 (1分钟)

```bash
# 检查Python版本
python3 --version  # 需要 3.9+

# 检查项目目录
cd /Users/shmiwanghao8/Desktop/education/Indonesia
ls -la
```

### 第二步：启用优化功能 (1分钟)

```bash
# 设置环境变量（启用并行搜索）
export ENABLE_PARALLEL_SEARCH=true

# 或者添加到.env文件
echo "ENABLE_PARALLEL_SEARCH=true" >> .env
```

### 第三步：启动系统 (2分钟)

```bash
# 启动Flask应用
python3 web_app.py
```

**预期输出**:
```
* Serving Flask app 'web_app'
* Running on http://0.0.0.0:5001
* Debug mode: on
[INFO] 搜索缓存初始化完成: data/cache, TTL=3600秒
[INFO] 使用并行搜索模式
```

### 第四步：验证优化效果 (1分钟)

打开浏览器访问: http://localhost:5001

执行搜索请求，观察：
- ✅ 搜索速度更快（3秒 vs 9秒）
- ✅ 日志显示"并行搜索"
- ✅ 日志显示"缓存命中"（重复查询）

---

## 📊 性能对比

### 优化前 vs 优化后

| 场景 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 首次搜索 | 9秒 | 3秒 | **66%** ⚡ |
| 重复搜索 | 9秒 | ~10ms | **99.9%** ⚡⚡⚡ |
| 混合场景 | 9秒 | 2.1秒 | **77%** ⚡⚡ |

### 运行性能测试

```bash
python3 scripts/performance_test.py
```

**预期输出**:
```
📊 性能对比
  串行模式耗时: 9.15 秒
  并行模式耗时: 3.24 秒
  加速比: 2.82x
  性能提升: 64.6%
  ✅ 性能提升显著！
```

---

## 🔧 核心功能

### 1. 搜索结果缓存

**功能**: 自动缓存搜索结果，避免重复API调用

**使用方式**:
```python
from core.search_cache import get_search_cache

# 获取缓存实例
cache = get_search_cache()

# 查看缓存统计
stats = cache.get_stats()
print(f"命中率: {stats['hit_rate']:.1%}")
print(f"缓存文件数: {stats['cache_files_count']}")
```

**配置**:
- 默认TTL: 3600秒 (1小时)
- 缓存目录: `data/cache/`

**清空缓存**:
```bash
rm -rf data/cache/*.json
```

### 2. 并行搜索引擎

**功能**: 同时调用多个搜索引擎，减少等待时间

**使用方式**:
```bash
# 启用并行搜索（默认）
export ENABLE_PARALLEL_SEARCH=true

# 禁用并行搜索（回退到串行）
export ENABLE_PARALLEL_SEARCH=false
```

**并行引擎**:
- Tavily搜索
- Google搜索（如果启用）
- 百度搜索（如果启用）
- 本地定向搜索

### 3. 配置化管理

**功能**: 通过YAML配置文件管理系统行为

**配置文件**: `config/search.yaml`

**修改本地化关键词**:
```yaml
# config/search.yaml
search:
  localization:
    id: "Video pembelajaran"
    en: "Video lesson"
    th: "วิดีโอการสอน"  # 添加泰语
```

**添加教育平台**:
```yaml
# config/search.yaml
search:
  edtech_domains:
    - "youtube.com"
    - "ruangguru.com"
    - "new-platform.com"  # 添加新平台
```

**重启应用生效**:
```bash
# 停止服务 (Ctrl+C)
# 重新启动
python3 web_app.py
```

---

## 📈 监控和调试

### 查看缓存统计

```bash
# 方式1: Python命令
python3 -c "
from core.search_cache import get_search_cache
import json
cache = get_search_cache()
print(json.dumps(cache.get_stats(), indent=2, ensure_ascii=False))
"

# 方式2: 查看缓存文件
ls -lh data/cache/
```

**输出示例**:
```json
{
  "hits": 15,
  "misses": 10,
  "total_queries": 25,
  "hit_rate": 0.6,
  "cache_files_count": 10
}
```

### 查看实时日志

```bash
# 查看所有日志
tail -f search_system.log

# 过滤缓存日志
tail -f search_system.log | grep "缓存"

# 过滤并行搜索日志
tail -f search_system.log | grep "并行"
```

**关键日志标识**:
- `✅ 缓存命中`: 缓存成功
- `❌ 缓存未命中`: 缓存失败
- `⚡ 并行搜索启动`: 开始并行搜索
- `✅ 搜索完成`: 搜索任务完成

### EdTech域名检查

```bash
python3 -c "
from search_engine_v2 import SearchEngineV2
engine = SearchEngineV2()
urls = [
    'https://youtube.com/watch',
    'https://ruangguru.com/video',
    'https://example.com'
]
for url in urls:
    is_edtech = engine._is_edtech_domain(url)
    print(f'{url}: {\"✅ EdTech\" if is_edtech else \"❌ 普通\"}')
"
```

---

## 🎯 常见使用场景

### 场景1: 测试搜索性能

```bash
# 1. 清空缓存
rm -rf data/cache/*.json

# 2. 执行搜索（首次，慢）
curl -X POST http://localhost:5001/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "country": "ID",
    "grade": "Kelas 5",
    "subject": "Matematika"
  }'

# 3. 执行相同搜索（缓存命中，快）
# （重复上面的命令）
```

### 场景2: 对比串行vs并行

```bash
# 测试并行模式
export ENABLE_PARALLEL_SEARCH=true
python3 scripts/performance_test.py

# 测试串行模式
export ENABLE_PARALLEL_SEARCH=false
python3 scripts/performance_test.py
```

### 场景3: 添加新语言支持

```bash
# 1. 编辑配置文件
vim config/search.yaml

# 2. 添加新语言
# 在 localization 下添加:
#   th: "วิดีโอการสอน"

# 3. 重启应用
python3 web_app.py

# 4. 验证配置
tail -f search_system.log | grep "本地化"
```

### 场景4: 监控缓存效果

```bash
# 运行一段时间后
python3 -c "
from core.search_cache import get_search_cache
cache = get_search_cache()
stats = cache.get_stats()
print(f'总查询: {stats[\"total_queries\"]}')
print(f'缓存命中: {stats[\"hits\"]}')
print(f'命中率: {stats[\"hit_rate\"]:.1%}')
"
```

---

## ⚠️ 故障排除

### 问题1: 搜索没有变快

**可能原因**:
1. 并行搜索未启用
2. 缓存未命中
3. 网络延迟高

**解决步骤**:
```bash
# 1. 检查环境变量
echo $ENABLE_PARALLEL_SEARCH  # 应该是 true

# 2. 检查缓存
ls -la data/cache/  # 应该有 .json 文件

# 3. 查看日志
tail -50 search_system.log | grep -E "并行|缓存"

# 4. 运行性能测试
python3 scripts/performance_test.py
```

### 问题2: 缓存不工作

**症状**: 重复查询仍然很慢

**诊断**:
```bash
# 检查缓存目录权限
ls -la data/cache/

# 检查日志中的缓存错误
grep "缓存.*失败" search_system.log
```

**解决**:
```bash
# 修复权限
chmod 755 data/cache/

# 清空并重建缓存
rm -rf data/cache/*
mkdir -p data/cache
```

### 问题3: 配置未生效

**症状**: 修改了配置但行为没变

**诊断**:
```bash
# 检查配置文件语法
python3 -c "import yaml; yaml.safe_load(open('config/search.yaml'))"

# 检查日志中的配置加载
grep "配置读取" search_system.log
```

**解决**:
```bash
# 重启应用
# (Ctrl+C 停止，然后重新启动)
python3 web_app.py
```

---

## 📚 进阶使用

### 自定义缓存TTL

```python
# 修改 core/search_cache.py
cache = SearchCache(
    cache_dir="data/cache",
    ttl_seconds=7200  # 2小时
)
```

### 添加新的搜索引擎

在 `search_engine_v2.py` 的并行搜索任务列表中添加：
```python
search_tasks.append({
    'name': '新搜索引擎',
    'func': new_search_function,
    'engine_name': 'NewEngine',
    'max_results': 15
})
```

### 批量性能测试

```bash
# 创建测试脚本
cat > test_batch.sh <<'EOF'
#!/bin/bash
for i in {1..10}; do
  echo "测试 $i"
  python3 scripts/performance_test.py >> performance_results.log 2>&1
  sleep 5
done
EOF

chmod +x test_batch.sh
./test_batch.sh
```

---

## 🎓 学习资源

### 官方文档

- [完整优化报告](./OPTIMIZATION_REPORT.md)
- [部署检查清单](./DEPLOYMENT_CHECKLIST.md)
- [迭代2总结：缓存系统](./ralph_iteration_2_summary.md)
- [迭代3总结：并行搜索](./ralph_iteration_3_summary.md)
- [迭代4总结：配置化](./ralph_iteration_4_summary.md)
- [配置化使用指南](./CONFIGURATION_GUIDE.md)

### 代码示例

- 缓存使用: `core/search_cache.py`
- 并行搜索: `search_engine_v2.py` (第688-755行)
- 配置加载: `core/config_loader.py`
- 性能测试: `scripts/performance_test.py`

---

## ✅ 快速检查清单

部署前快速检查：

- [ ] Python 3.9+ 已安装
- [ ] 所有依赖包已安装
- [ ] `.env` 文件已配置
- [ ] `ENABLE_PARALLEL_SEARCH=true` 已设置
- [ ] `data/cache/` 目录可写
- [ ] 配置文件存在且语法正确
- [ ] 可以启动服务 (`python3 web_app.py`)
- [ ] 可以访问 http://localhost:5001
- [ ] 性能测试通过

**全部通过？恭喜，优化系统已就绪！** 🎉

---

**文档版本**: 1.0
**最后更新**: 2026-01-05
**维护者**: 产品经理 + AI辅助
