# 教育视频搜索系统 V2 架构说明

## 架构概览

新版系统完全重构了搜索架构，从基于知识点的搜索改为基于国家/年级/学期的搜索，并提供了完整的 Web 界面。

## 主要改进

### 1. 搜索策略改变

**旧版（V1）**：
- 基于知识点搜索
- 按章节分组搜索
- 搜索词固定格式

**新版（V2）**：
- 基于国家/年级/学期搜索
- 使用 AI 生成本地语言搜索词
- 更灵活、更准确的搜索

### 2. Web 界面

- 友好的用户界面
- 实时搜索和结果展示
- 搜索历史记录
- 响应式设计

### 3. 历史记录功能

- 自动保存搜索历史
- 快速查看历史结果
- 最多保留 100 条记录

## 文件结构

```
.
├── search_engine_v2.py      # 新版搜索引擎核心
│   ├── SearchEngineV2      # 主搜索引擎类
│   ├── QueryGenerator      # AI 搜索词生成器
│   ├── ResultEvaluator     # 结果评估器
│   └── AIBuildersClient    # API 客户端
│
├── web_app.py              # Flask Web 应用
│   ├── /                   # 主页
│   ├── /api/search         # 搜索 API
│   ├── /api/history        # 历史记录 API
│   └── /api/history/<id>   # 特定历史记录
│
├── templates/
│   └── index.html          # 前端界面
│
├── search_history.json      # 历史记录存储（自动生成）
│
└── requirements_web.txt    # 依赖项
```

## 工作流程

```
用户输入（国家/年级/学期/学科）
    ↓
AI 生成搜索词（使用本地语言）
    ↓
Tavily 搜索执行
    ↓
规则匹配评估
    ↓
结果展示 + 历史记录保存
```

## 核心组件详解

### 1. SearchEngineV2

主搜索引擎类，协调整个搜索流程。

**主要方法**：
- `search(request: SearchRequest) -> SearchResponse`：执行搜索

### 2. QueryGenerator

使用 AI 生成本地语言的搜索词。

**特点**：
- 根据国家自动选择语言
- 使用教育系统常用术语
- 优先包含"playlist"等关键词

### 3. ResultEvaluator

使用规则匹配筛选高质量资源。

**规则**：
1. YouTube 播放列表（100% 确定）
2. YouTube 频道页面
3. EdTech 网站
4. 系列视频（标题包含 Part/Series 等）

### 4. Web 应用

Flask 应用，提供 RESTful API 和 Web 界面。

**API 端点**：
- `POST /api/search`：执行搜索
- `GET /api/history`：获取历史记录
- `GET /api/history/<index>`：获取特定历史记录

## 数据模型

### SearchRequest
```python
{
    "country": "ID",        # 国家代码
    "grade": "1",          # 年级
    "semester": "1",       # 学期（可选）
    "subject": "Matematika", # 学科
    "language": "id"       # 语言（可选，自动检测）
}
```

### SearchResponse
```python
{
    "success": true,
    "query": "搜索词",
    "results": [...],      # 搜索结果列表
    "total_count": 10,     # 总结果数
    "playlist_count": 5,   # 播放列表数
    "video_count": 3,      # 视频数
    "message": "搜索成功",
    "timestamp": "2024-01-01T00:00:00"
}
```

## 日志输出

所有搜索过程都会输出详细日志：

```
================================================================================
🔍 开始搜索
================================================================================
国家: ID
年级: 1
学期: 1
学科: Matematika
================================================================================

[步骤 1] 生成搜索词...
    [🤖 AI 生成] 正在为 ID/1/Matematika 生成搜索词...
    [✅ AI 生成] 搜索词: "playlist matematika kelas 1 semester 1"

[步骤 2] 执行搜索...
    [🔍 搜索] 查询: "playlist matematika kelas 1 semester 1"
    [✅ 搜索] 找到 20 个结果

[步骤 3] 评估结果...
    [📋 评估] 正在评估 20 个搜索结果...
    [✅ 评估] 找到 5 个高质量资源

[步骤 4] 统计结果...
    [📊 统计] 播放列表: 2 个
    [📊 统计] 视频: 2 个
    [📊 统计] 总计: 5 个
```

## 使用示例

### 命令行测试

```python
from search_engine_v2 import SearchEngineV2, SearchRequest

engine = SearchEngineV2()
request = SearchRequest(
    country="ID",
    grade="1",
    semester="1",
    subject="Matematika"
)
result = engine.search(request)
print(f"找到 {result.total_count} 个结果")
```

### Web 界面使用

1. 启动应用：`python web_app.py`
2. 访问 `http://localhost:5000`
3. 选择国家、输入年级、学期、学科
4. 点击"开始搜索"
5. 查看结果和历史记录

## 注意事项

1. **环境变量**：需要设置 `AI_BUILDER_TOKEN`
2. **依赖安装**：`pip install -r requirements_web.txt`
3. **历史记录**：保存在 `search_history.json`，最多 100 条
4. **日志输出**：所有搜索过程都会在控制台输出详细日志

## 未来改进方向

1. 添加更多国家支持
2. 支持批量搜索
3. 添加结果导出功能
4. 添加搜索结果评分和排序
5. 支持用户自定义搜索规则

