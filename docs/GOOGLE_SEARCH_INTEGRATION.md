# Google Custom Search API 集成指南

## 概述

系统已集成Google Custom Search API，作为搜索引擎选项之一。Google搜索提供高质量、稳定的搜索结果，特别适合教育内容搜索。

## 配置

### 1. 获取API密钥

1. 访问 [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. 创建新的API密钥
3. 启用 "Custom Search API"
4. 记录API密钥

### 2. 获取搜索引擎ID (CX)

1. 访问 [Google Programmable Search Engine](https://programmablesearchengine.google.com/controlpanel/create)
2. 创建新的搜索引擎（或使用现有的）
3. 记录搜索引擎ID (CX)

### 3. 配置环境变量

在 `.env` 文件中添加：

```bash
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CX=your_google_cx  # 必需，从Google Programmable Search Engine获取
```

**重要**: 
- `GOOGLE_CX` 必须配置，不能硬编码在代码中
- 每个搜索引擎ID对应一个特定的搜索范围，建议为不同项目使用不同的CX
- **安全考虑**: 虽然CX不像API密钥那么敏感，但硬编码在代码中会带来以下问题：
  - 不够灵活：更换CX需要修改代码
  - 版本控制风险：CX会出现在Git历史中
  - 多环境管理困难：不同环境可能需要不同的CX
  - 最佳实践：所有配置都应该通过环境变量管理

## 使用方法

### 在代码中使用

```python
from search_strategist import SearchHunter, AIBuildersClient

# 初始化Google搜索器
hunter = SearchHunter(search_engine="google")

# 执行搜索
results = hunter.search("playlist matematika kelas 1", max_results=10)

for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"摘要: {result.snippet}")
```

### 在SearchStrategist中使用

```python
from search_strategist import SearchStrategist, AIBuildersClient

llm_client = AIBuildersClient()

# 使用Google搜索引擎
strategist = SearchStrategist(llm_client, search_engine="google")

# 执行搜索
playlists = strategist.search_for_playlists(syllabus_data)
```

## API限制

### Google Custom Search API限制

- **每次请求最多返回10个结果**
- **每天免费配额**: 100次搜索请求
- **超出配额**: 需要付费（$5/1000次搜索）

### 分页支持

如果需要更多结果，可以：
1. 多次调用（每次最多10个结果）
2. 使用 `start` 参数进行分页

**注意**: 当前实现限制每次最多10个结果，如需更多结果需要修改代码支持分页。

## 支持的搜索引擎

系统支持以下搜索引擎：

1. **ai-builders** (默认)
   - 使用Tavily搜索API
   - 优点：与LLM使用同一套认证
   - 自动降级：失败时自动切换到DuckDuckGo

2. **google**
   - 使用Google Custom Search API
   - 优点：结果质量高、稳定
   - 需要：API密钥和CX

3. **duckduckgo**
   - 使用DuckDuckGo搜索
   - 优点：免费、无需API密钥
   - 需要：安装 `duckduckgo-search` 库

4. **serpapi**
   - 使用SerpAPI
   - 优点：稳定、结果质量高
   - 需要：SerpAPI账户和API密钥

## 测试

运行测试脚本验证Google搜索功能：

```bash
python scripts/test_google_search.py
```

测试脚本会：
1. 检查环境变量配置
2. 测试多个搜索查询
3. 显示搜索结果

## API响应格式

Google Custom Search API返回的JSON格式：

```json
{
  "items": [
    {
      "title": "结果标题",
      "link": "https://example.com",
      "snippet": "结果摘要",
      "htmlSnippet": "HTML格式的摘要"
    }
  ],
  "searchInformation": {
    "totalResults": "1000",
    "searchTime": 0.5
  }
}
```

## 错误处理

### 常见错误

1. **403 Forbidden**
   - 原因：API密钥无效或未启用Custom Search API
   - 解决：检查API密钥和API启用状态

2. **400 Bad Request**
   - 原因：参数错误（如CX无效）
   - 解决：检查CX值是否正确

3. **429 Too Many Requests**
   - 原因：超出每日配额
   - 解决：等待配额重置或升级到付费计划

### 降级机制

如果Google搜索失败，系统会：
1. 记录错误信息
2. 返回空结果（不会自动降级到其他搜索引擎）
3. 上层代码可以处理空结果或切换到其他搜索引擎

## 性能对比

| 搜索引擎 | 响应时间 | 结果质量 | 配额限制 | 成本 |
|---------|---------|---------|---------|------|
| Google | ~0.5-1s | ⭐⭐⭐⭐⭐ | 100次/天（免费） | $5/1000次 |
| Tavily | ~2-5s | ⭐⭐⭐⭐ | 无限制 | 免费 |
| DuckDuckGo | ~1-2s | ⭐⭐⭐ | 无限制 | 免费 |
| SerpAPI | ~1-2s | ⭐⭐⭐⭐⭐ | 100次/月（免费） | $50/月起 |

## 最佳实践

1. **优先使用Google搜索**（如果配额充足）
   - 结果质量最高
   - 响应速度快

2. **配额管理**
   - 监控每日使用量
   - 重要搜索使用Google，其他使用Tavily或DuckDuckGo

3. **错误处理**
   - 实现重试机制
   - 失败时切换到备用搜索引擎

4. **结果缓存**
   - 对于相同查询，可以缓存结果
   - 减少API调用次数

## 更新日志

### V3.4.0 (2025-01-XX)

- ✅ 集成Google Custom Search API
- ✅ 支持通过环境变量配置API密钥和CX
- ✅ 添加测试脚本
- ✅ 更新文档

---

**最后更新**: 2025-01-XX

