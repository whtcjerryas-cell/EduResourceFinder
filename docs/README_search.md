# 印尼 K12 视频课程库搜索 Agent

## 功能说明

这是一个智能搜索系统，用于为印尼 K12 教育知识点自动搜索相关的视频播放列表（Playlist）。

**核心策略**：通过核心章节找到完整的播放列表，而不是寻找单个碎片化视频。

## 安装依赖

```bash
pip install -r requirements_search.txt
```

## 环境变量配置

需要设置以下环境变量：

```bash
export AI_BUILDER_TOKEN="your_ai_builder_token"
```

可选（如果使用其他搜索引擎）：
```bash
export SERPAPI_KEY="your_serpapi_key"  # 仅在使用 SerpAPI 时需要
```

## 搜索引擎选择

系统支持三种搜索引擎：

1. **ai-builders**（默认，推荐）：使用 AI Builders 的搜索 API
   - 优点：与 LLM 评估使用同一套认证，无需额外配置
   - 自动降级：如果 API 不可用，会自动降级到 DuckDuckGo

2. **duckduckgo**：使用 DuckDuckGo 搜索
   - 优点：免费，无需 API 密钥
   - 需要安装：`pip install duckduckgo-search`

3. **serpapi**：使用 SerpAPI
   - 优点：更稳定，结果质量高
   - 需要：SerpAPI 账户和 API 密钥

在代码中可以通过修改 `search_engine` 参数来选择搜索引擎。

## 使用方法

### 基本用法

```bash
python search_strategist.py
```

默认会处理 1-2 年级的知识点文件。

### 指定文件

```bash
python search_strategist.py "path/to/knowledge_points.json"
```

## 工作流程

1. **策略制定 (Query Generator)**
   - 遍历每个章节（Chapter），而不是每个知识点（Topic）
   - 为每个章节生成搜索查询词

2. **智能搜索循环 (Agentic Loop)**
   - 对每个查询执行最多 3 次的"搜索-评估-修正"循环：
     - **搜索 (Hunter)**：调用搜索引擎获取前 10 个结果
     - **评估 (Inspector)**：使用 LLM 判断结果质量
     - **修正**：根据反馈优化搜索词

3. **全局去重**
   - 确保最终输出的 CSV 中 URL 不重复

## 输出格式

结果会保存为 CSV 文件，包含以下字段：

- `grade_level`: 年级
- `subject`: 学科
- `chapter_title`: 章节标题
- `playlist_url`: 播放列表 URL
- `search_query`: 使用的搜索词
- `attempt_number`: 第几次尝试成功

## 日志说明

系统会输出详细的日志信息，包括：

- `[🔍 策略]`: 查询生成
- `[🤖 尝试]`: 搜索尝试
- `[🕵️ 评估]`: 结果评估
- `[🔄 修正]`: 查询优化
- `[✅ 成功]`: 找到播放列表
- `[❌ 失败]`: 搜索失败

## AI Builders 搜索 API

系统会尝试以下端点来访问 AI Builders 搜索 API：

1. `/v1/search`
2. `/api/search`
3. `/search`

如果这些端点都不可用，系统会尝试通过 LLM 工具调用的方式执行搜索。

如果 AI Builders 搜索失败，系统会自动降级到 DuckDuckGo 搜索（如果已安装）。

## 注意事项

1. 搜索过程可能需要较长时间，请耐心等待
2. 建议在网络稳定的环境下运行
3. 如果使用 DuckDuckGo 搜索，可能会遇到速率限制
4. 建议先在小规模数据上测试
5. AI Builders 搜索 API 的具体端点格式可能因版本而异，如果遇到问题请检查 API 文档

