# 教育视频搜索系统 V2

## 概述

新版搜索系统基于国家、年级、学期进行搜索，使用 AI 生成本地语言的搜索词，提供 Web 界面和历史记录功能。

## 主要特性

1. **智能搜索词生成**：使用 AI 根据国家、年级、学期、学科自动生成本地语言的搜索词
2. **Web 界面**：友好的 Web 界面，支持选择国家、年级、学科等条件
3. **历史记录**：自动保存搜索历史，可以快速查看之前的搜索结果
4. **完整日志**：所有搜索过程都有详细的日志输出

## 安装

```bash
# 安装依赖
pip install -r requirements_web.txt
```

## 使用方法

### 1. 启动 Web 应用

```bash
python web_app.py
```

应用将在 `http://localhost:5000` 启动

### 2. 使用 Web 界面

1. 打开浏览器访问 `http://localhost:5000`
2. 选择国家、输入年级、学期（可选）、学科
3. 点击"开始搜索"
4. 查看搜索结果
5. 在右侧查看搜索历史

### 3. API 使用

#### 搜索 API

```bash
POST /api/search
Content-Type: application/json

{
    "country": "ID",
    "grade": "1",
    "semester": "1",
    "subject": "Matematika"
}
```

#### 获取历史记录

```bash
GET /api/history
```

#### 获取特定历史记录

```bash
GET /api/history/<index>
```

## 架构说明

### 文件结构

```
.
├── search_engine_v2.py    # 新版搜索引擎核心
├── web_app.py             # Flask Web 应用
├── templates/
│   └── index.html        # 前端界面
├── search_history.json    # 历史记录（自动生成）
└── requirements_web.txt   # 依赖项
```

### 核心组件

1. **SearchEngineV2**：主搜索引擎类
2. **QueryGenerator**：使用 AI 生成搜索词
3. **ResultEvaluator**：评估和筛选搜索结果
4. **AIBuildersClient**：AI Builders API 客户端

## 搜索策略

1. **AI 生成搜索词**：根据国家、年级、学期、学科，使用 AI 生成本地语言的搜索词
2. **Tavily 搜索**：使用 Tavily API 执行实际搜索
3. **规则匹配**：使用硬规则筛选高质量资源（播放列表、频道、EdTech 网站等）
4. **结果展示**：在 Web 界面展示搜索结果

## 支持的国家和语言

- **印尼 (ID)**：印尼语 (id)
- **中国 (CN)**：中文 (zh)
- **美国 (US)**：英语 (en)
- **马来西亚 (MY)**：马来语 (ms)
- **新加坡 (SG)**：英语 (en)
- **印度 (IN)**：英语 (en)

## 日志输出

所有搜索过程都会在控制台输出详细日志，包括：
- AI 搜索词生成过程
- Tavily 搜索执行过程
- 结果评估过程
- 统计信息

## 注意事项

1. 需要设置 `AI_BUILDER_TOKEN` 环境变量
2. 历史记录保存在 `search_history.json` 文件中
3. 历史记录最多保留最近 100 条

