# 百度搜索API集成说明

## 概述

系统已集成百度搜索API，支持3种搜索服务，适用于国内项目。

## 支持的API

1. **百度搜索**
   - 文档：https://cloud.baidu.com/doc/qianfan/s/2mh4su4uy
   - 每天100次免费调用
   - 基础搜索功能

2. **百度智能搜索生成**
   - 文档：https://cloud.baidu.com/doc/qianfan/s/Omh4su4s0
   - 每天100次免费调用
   - 搜索 + 智能内容生成

3. **智能搜索生成高性能版**
   - 文档：https://cloud.baidu.com/doc/qianfan/s/Kmiy99ziv
   - 每天100次免费调用
   - 高性能版本，响应更快

## 配置

### 环境变量

在 `.env` 文件中添加：

```bash
# 百度搜索API（必需）
BAIDU_API_KEY=your_baidu_api_key
BAIDU_SECRET_KEY=your_baidu_secret_key

# 选择API类型（可选，默认：baidu）
# 可选值：baidu, smart, high_performance
BAIDU_SEARCH_API_TYPE=baidu
```

### 获取API密钥

1. 访问 [百度智能云](https://cloud.baidu.com/)
2. 注册并实名认证
3. 进入"千帆应用开发平台"
4. 创建应用，获取API Key和Secret Key

## 使用方法

### 在SearchHunter中使用

```python
from search_strategist import SearchHunter

# 使用百度搜索引擎
hunter = SearchHunter(search_engine="baidu")

# 执行搜索
results = hunter.search("playlist matematika kelas 1", max_results=10)
```

### 在SearchStrategist中使用

```python
from search_strategist import SearchStrategist, AIBuildersClient

llm_client = AIBuildersClient()
strategist = SearchStrategist(llm_client, search_engine="baidu")
```

### 直接使用百度搜索客户端

```python
from baidu_search_client import BaiduSearchClient

client = BaiduSearchClient()

# 使用百度搜索
results = client.search_baidu("Python编程", max_results=10)

# 使用智能搜索生成
result = client.search_smart("Python编程", max_results=10)

# 使用高性能版
result = client.search_high_performance("Python编程", max_results=10)
```

## API调用说明

### 1. Access Token获取

百度API需要先获取access_token：

```python
# 自动获取（在BaiduSearchClient初始化时）
client = BaiduSearchClient()  # 会自动获取token
```

### 2. API调用

```python
# 百度搜索
results = client.search_baidu(query="搜索词", max_results=10)

# 智能搜索生成（返回搜索结果+生成内容）
result = client.search_smart(query="搜索词", max_results=10)

# 高性能版（返回搜索结果+生成内容）
result = client.search_high_performance(query="搜索词", max_results=10)
```

## 响应格式

### 百度搜索响应

```json
{
  "data": {
    "results": [
      {
        "title": "结果标题",
        "url": "https://example.com",
        "snippet": "结果摘要"
      }
    ]
  }
}
```

### 智能搜索/高性能版响应

```json
{
  "data": {
    "results": [...],
    "generated_content": "生成的内容"
  }
}
```

## 错误处理

### 常见错误

1. **Token获取失败**
   - 检查API Key和Secret Key是否正确
   - 确认网络连接正常

2. **API调用失败**
   - 检查access_token是否有效
   - 确认API endpoint是否正确
   - 查看错误码和错误信息

3. **配额超限**
   - 每天100次免费调用
   - 超出后需要付费

## 测试

运行测试脚本：

```bash
python scripts/test_baidu_search.py
```

## 注意事项

1. **API Endpoint**：
   - 当前实现使用通用百度API调用方式
   - 实际endpoint可能需要根据文档调整
   - 如果调用失败，请检查endpoint URL

2. **Token管理**：
   - access_token有效期通常为30天
   - 系统会在初始化时自动获取
   - Token过期需要重新获取

3. **调用限制**：
   - 每个API每天100次免费调用
   - 超出后需要付费
   - 建议监控调用次数

4. **结果格式**：
   - 不同API的响应格式可能不同
   - 代码已处理多种可能的格式
   - 如果遇到新格式，可能需要调整解析逻辑

## 更新日志

- **2025-01-XX**: 集成百度搜索API，支持3种搜索服务

---

**参考文档**：
- 百度搜索：https://cloud.baidu.com/doc/qianfan/s/2mh4su4uy
- 智能搜索生成：https://cloud.baidu.com/doc/qianfan/s/Omh4su4s0
- 高性能版：https://cloud.baidu.com/doc/qianfan/s/Kmiy99ziv





