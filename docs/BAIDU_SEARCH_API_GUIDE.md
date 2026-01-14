# 百度搜索API集成指南

## 概述

本文档介绍如何申请和使用百度搜索API，系统已集成以下3种百度搜索API：

1. **百度搜索**：基础搜索API
   - 文档：https://cloud.baidu.com/doc/qianfan/s/2mh4su4uy
   - 每天100次免费调用

2. **百度智能搜索生成**：智能搜索+内容生成
   - 文档：https://cloud.baidu.com/doc/qianfan/s/Omh4su4s0
   - 每天100次免费调用

3. **智能搜索生成高性能版**：高性能版本
   - 文档：https://cloud.baidu.com/doc/qianfan/s/Kmiy99ziv
   - 每天100次免费调用

## 申请流程

### 1. 注册百度智能云账号

- 访问 [百度智能云官网](https://cloud.baidu.com/)
- 点击"注册"按钮，填写相关信息
- 验证手机号或邮箱

### 2. 实名认证

- 登录后，进入"控制台" > "账号管理" > "实名认证"
- 按照提示上传身份证照片或进行人脸识别
- 实名认证是申请API的必要条件

### 3. 开通千帆服务

- 进入"控制台" > "千帆应用开发平台"
- 创建应用，获取API Key和Secret Key
- 开通搜索相关服务

### 4. 获取API密钥

- 在应用详情页面查看 `API Key` 和 `Secret Key`
- 妥善保管密钥，不要泄露

## 配置

### 环境变量配置

在 `.env` 文件中添加：

```bash
# 百度搜索API（必需）
BAIDU_API_KEY=your_baidu_api_key
BAIDU_SECRET_KEY=your_baidu_secret_key

# 选择使用的API类型（可选，默认：baidu）
# 可选值：baidu（百度搜索）、smart（智能搜索生成）、high_performance（高性能版）
BAIDU_SEARCH_API_TYPE=baidu
```

### API类型说明

- **baidu**（默认）：百度搜索API
  - 文档：https://cloud.baidu.com/doc/qianfan/s/2mh4su4uy
  - 每天100次免费调用
  
- **smart**：百度智能搜索生成API
  - 文档：https://cloud.baidu.com/doc/qianfan/s/Omh4su4s0
  - 每天100次免费调用
  - 包含智能生成功能
  
- **high_performance**：智能搜索生成高性能版API
  - 文档：https://cloud.baidu.com/doc/qianfan/s/Kmiy99ziv
  - 每天100次免费调用
  - 性能更高，响应更快

## 使用方法

### 在代码中使用

```python
from search_strategist import SearchHunter

# 使用百度搜索引擎
hunter = SearchHunter(search_engine="baidu")

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

# 使用百度搜索引擎
strategist = SearchStrategist(llm_client, search_engine="baidu")

# 执行搜索
playlists = strategist.search_for_playlists(syllabus_data)
```

## API调用流程

1. **获取access_token**：
   - 使用API Key和Secret Key获取access_token
   - Token有效期通常为30天
   - 调用：`https://aip.baidubce.com/oauth/2.0/token`

2. **调用搜索API**：
   - 使用access_token调用相应的搜索API
   - 传递查询词和参数
   - **注意**：实际API endpoint请参考官方文档：
     - 百度搜索：https://cloud.baidu.com/doc/qianfan/s/2mh4su4uy
     - 智能搜索生成：https://cloud.baidu.com/doc/qianfan/s/Omh4su4s0
     - 高性能版：https://cloud.baidu.com/doc/qianfan/s/Kmiy99ziv

3. **解析结果**：
   - 解析API返回的JSON数据
   - 提取标题、URL、摘要等信息

## 重要提示

⚠️ **API Endpoint可能需要调整**：
- 当前实现使用的是通用的百度API调用方式
- 实际endpoint可能因文档版本而异
- 建议根据官方文档调整endpoint URL
- 如果API调用失败，请检查endpoint是否正确

## API限制

- **每天免费配额**：每个API每天100次免费调用
- **超出配额**：需要付费使用
- **结果数量限制**：每次最多返回10个结果

## 错误处理

### 常见错误码

- **400**：客户端请求参数错误
- **500**：服务端执行错误
- **501**：调用模型服务超时
- **502**：模型流式输出超时

### 错误处理机制

系统会自动处理以下情况：
- API调用失败时返回空结果
- Token过期时自动重新获取
- 网络错误时记录详细日志

## 申请流程（通用步骤）

### 方式1：百度智能云

1. **注册账号**
   - 访问 [百度智能云官网](https://cloud.baidu.com/)
   - 点击"注册"按钮，填写相关信息
   - 验证手机号或邮箱

2. **实名认证**
   - 登录后，进入"控制台" > "账号管理" > "实名认证"
   - 按照提示上传身份证照片或进行人脸识别
   - 实名认证是申请API的必要条件

3. **查找搜索相关服务**
   - 进入"控制台" > "产品与服务"
   - 搜索"搜索"、"网站搜索"或"站内搜索"
   - 查看是否有相关的API服务

4. **创建应用**
   - 找到相关服务后，点击"创建应用"
   - 填写应用名称、应用描述等信息
   - 选择套餐（通常有免费版和付费版）

5. **获取API密钥**
   - 应用创建成功后，在应用详情页面查看
   - 记录 `API Key` 和 `Secret Key`（如果有）
   - 妥善保管密钥，不要泄露

### 方式2：百度开放平台

1. **访问开放平台**
   - 访问 [百度开放平台](https://developer.baidu.com/)
   - 注册或登录百度账号

2. **查找API服务**
   - 浏览API列表，查找搜索相关服务
   - 查看API文档和使用说明

3. **申请API权限**
   - 点击"申请"或"开通"按钮
   - 填写申请信息
   - 等待审核（可能需要1-3个工作日）

4. **获取API密钥**
   - 审核通过后，获取API Key
   - 查看API调用文档

## 可能的替代方案

如果百度不提供公开的搜索API，可以考虑以下替代方案：

### 1. 百度站内搜索

- **用途**：搜索特定网站的内容
- **申请**：在百度站内搜索平台申请
- **限制**：只能搜索已提交的网站内容

### 2. 其他中文搜索引擎API

- **搜狗搜索API**：可能需要企业认证
- **360搜索API**：查看360开放平台
- **神马搜索API**：查看阿里云相关服务

### 3. 爬虫方案（需谨慎）

- 使用爬虫抓取搜索结果
- ⚠️ **注意**：可能违反robots.txt和服务条款
- 建议：优先使用官方API

## 集成到系统

如果成功申请到百度搜索API，可以按照以下方式集成：

### 1. 环境变量配置

在 `.env` 文件中添加：

```bash
# 百度搜索API（如果申请成功）
BAIDU_API_KEY=your_baidu_api_key
BAIDU_SECRET_KEY=your_baidu_secret_key  # 如果有
```

### 2. 代码集成

参考Google搜索的集成方式，在 `SearchHunter` 类中添加 `_search_baidu()` 方法：

```python
def _search_baidu(self, query: str, max_results: int) -> List[SearchResult]:
    """
    使用百度搜索API搜索
    
    Args:
        query: 搜索查询词
        max_results: 最大返回结果数
    
    Returns:
        搜索结果列表
    """
    api_key = os.getenv("BAIDU_API_KEY")
    secret_key = os.getenv("BAIDU_SECRET_KEY")
    
    if not api_key:
        print(f"    [⚠️ 警告] BAIDU_API_KEY 未设置")
        return self._mock_search(query, max_results)
    
    # TODO: 根据百度API文档实现具体调用逻辑
    # 参考Google搜索的实现方式
    pass
```

### 3. 更新SearchHunter

在 `SearchHunter.__init__()` 中添加百度搜索支持：

```python
if search_engine == "baidu":
    self.baidu_api_key = os.getenv("BAIDU_API_KEY")
    if not self.baidu_api_key:
        print(f"    [⚠️ 警告] BAIDU_API_KEY 未设置，百度搜索将不可用")
```

在 `SearchHunter.search()` 中添加：

```python
elif self.search_engine == "baidu":
    return self._search_baidu(query, max_results)
```

## 官方资源

- **百度智能云**：https://cloud.baidu.com/
- **百度开放平台**：https://developer.baidu.com/
- **百度站内搜索**：https://zn.baidu.com/（如果可用）

## 注意事项

1. **API限制**：
   - 查看API的调用频率限制
   - 了解免费配额和付费标准
   - 注意每日/每月调用次数限制

2. **服务条款**：
   - 仔细阅读API服务条款
   - 确保使用符合规定
   - 注意数据使用限制

3. **审核时间**：
   - API申请可能需要审核
   - 审核时间通常1-3个工作日
   - 企业认证可能需要更长时间

4. **技术支持**：
   - 查看官方文档和示例代码
   - 联系百度技术支持获取帮助
   - 加入开发者社区交流

## 建议

1. **先确认需求**：
   - 明确需要搜索什么内容
   - 确定是否需要通用搜索还是站内搜索
   - 评估API费用和限制

2. **查看最新文档**：
   - 百度API服务可能会变化
   - 建议查看最新的官方文档
   - 联系百度客服确认当前可用的服务

3. **测试集成**：
   - 申请成功后，先进行小规模测试
   - 验证API调用是否正常
   - 检查结果格式是否符合预期

## 更新日志

- **2025-01-XX**: 创建文档，提供百度搜索API申请指南

---

**重要提示**：由于百度API服务可能会变化，本文档仅供参考。建议以百度官方最新文档为准。如果发现信息有误，请及时更新文档。

