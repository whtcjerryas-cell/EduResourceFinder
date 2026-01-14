# K12 视频搜索系统 V3 - AI 驱动的国家自动接入系统

## 🎯 核心特性

V3 版本实现了**"AI 驱动的国家自动接入系统"**，不再需要手动配置国家信息。通过 UI 交互，AI 会自动调研并配置新国家。

### 主要功能

1. **AI 自动调研国家信息** (`CountryDiscoveryAgent`)
   - 使用 Tavily 搜索 + LLM 提取国家 K12 教育体系信息
   - 自动提取年级表达（使用当地语言）
   - 自动提取学科名称（使用当地语言）
   - 自动识别 EdTech 域名白名单
   - 自动识别主要语言代码

2. **动态 UI 交互**
   - **[+]** 按钮：添加新国家（弹出输入框，AI 自动调研）
   - **[⟳]** 按钮：刷新当前国家配置（重新调研并更新）
   - **级联下拉框**：年级和学科选项从配置中动态读取
   - **Loading 状态**：显示调研和搜索进度

3. **"全部 (All)" 搜索逻辑**
   - 支持选择"全部年级"或"全部学科"
   - 后端自动批量搜索所有组合
   - 智能去重和结果合并
   - 速率限制保护（避免 API 过载）

## 📁 文件结构

```
.
├── discovery_agent.py          # AI 驱动的国家发现 Agent
├── config_manager.py          # 国家配置管理器
├── web_app.py                 # Flask Web 应用（已更新）
├── templates/
│   └── index.html             # 前端界面（已更新）
├── countries_config.json      # 国家配置存储文件（自动生成）
├── search_engine_v2.py        # 搜索引擎（复用）
└── search_strategist.py       # 搜索策略（复用）
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements_web.txt
```

### 2. 设置环境变量

```bash
export AI_BUILDER_TOKEN="your_token_here"
```

或创建 `.env` 文件：
```
AI_BUILDER_TOKEN=your_token_here
```

### 3. 启动 Web 应用

```bash
python web_app.py
```

访问：http://localhost:5000

## 📖 使用指南

### 添加新国家

1. 点击国家下拉框旁边的 **[+]** 按钮
2. 在弹出的对话框中输入国家名称（英文），例如：
   - `Philippines`
   - `Japan`
   - `Thailand`
3. 点击"开始调研"按钮
4. AI 会自动：
   - 使用 Tavily 搜索该国的 K12 教育体系信息
   - 使用 LLM 提取结构化数据（年级、学科、域名等）
   - 保存到 `countries_config.json`
   - 自动选中新添加的国家

### 刷新国家配置

1. 选择要刷新的国家
2. 点击 **[⟳]** 按钮
3. 确认后，AI 会重新调研并更新该国家的配置

### 使用级联下拉框

1. **选择国家**：从国家下拉框中选择一个国家
2. **选择年级**：年级下拉框会自动加载该国家的年级列表（使用当地语言）
   - 可以选择"全部 (All)"进行批量搜索
3. **选择学科**：学科下拉框会自动加载该国家的学科列表（使用当地语言）
   - 可以选择"全部 (All)"进行批量搜索

### 批量搜索

当选择"全部 (All)"时：
- 后端会自动循环搜索所有年级/学科组合
- 结果会自动去重和合并
- 显示合并后的统计信息

**注意**：批量搜索可能需要较长时间，请耐心等待。

## 🔧 API 端点

### 1. 国家发现 API

**POST** `/api/discover_country`

请求体：
```json
{
  "country_name": "Philippines"
}
```

响应：
```json
{
  "success": true,
  "message": "成功调研国家: Philippines",
  "profile": {
    "country_code": "PH",
    "country_name": "Philippines",
    "language_code": "en",
    "grades": ["Kindergarten", "Grade 1", ..., "Grade 12"],
    "subjects": ["Math", "Science", "Filipino", ...],
    "domains": ["deped.gov.ph", ...],
    "notes": "..."
  }
}
```

### 2. 获取国家配置 API

**GET** `/api/config/<country_code>`

响应：
```json
{
  "success": true,
  "config": {
    "country_code": "PH",
    "country_name": "Philippines",
    "language_code": "en",
    "grades": [...],
    "subjects": [...],
    "domains": [...],
    "notes": "..."
  }
}
```

### 3. 获取所有国家列表

**GET** `/api/countries`

响应：
```json
{
  "success": true,
  "countries": [
    {"country_code": "ID", "country_name": "Indonesia"},
    {"country_code": "PH", "country_name": "Philippines"},
    ...
  ]
}
```

### 4. 搜索 API（支持批量搜索）

**POST** `/api/search`

请求体：
```json
{
  "country": "PH",
  "grade": "ALL",  // 或具体年级如 "Grade 1"
  "subject": "ALL",  // 或具体学科如 "Math"
  "semester": null
}
```

## 🎨 UI 特性

### 新增按钮

- **[+]** 按钮：添加新国家
- **[⟳]** 按钮：刷新当前国家配置

### 模态框

- 添加国家时弹出模态框
- 显示调研进度和状态
- 支持取消操作

### Loading 状态

- 调研时显示 Loading 动画
- 批量搜索时显示进度提示
- 搜索时显示 Loading 状态

## 📝 配置文件格式

`countries_config.json` 格式：

```json
{
  "ID": {
    "country_code": "ID",
    "country_name": "Indonesia",
    "language_code": "id",
    "grades": ["Kelas 1", "Kelas 2", ..., "Kelas 12"],
    "subjects": ["Matematika", "IPA", "IPS", ...],
    "domains": ["ruangguru.com", "zenius.net"],
    "notes": "印尼 K12 教育体系"
  },
  "PH": {
    "country_code": "PH",
    "country_name": "Philippines",
    "language_code": "en",
    "grades": ["Kindergarten", "Grade 1", ..., "Grade 12"],
    "subjects": ["Math", "Science", "Filipino", ...],
    "domains": ["deped.gov.ph"],
    "notes": "菲律宾 K12 教育体系"
  }
}
```

## 🔍 Discovery Agent 工作原理

1. **搜索阶段**：
   - 使用 Tavily 搜索该国的 K12 教育体系信息
   - 执行多个搜索查询以收集全面信息

2. **提取阶段**：
   - 使用 LLM（Gemini 2.5 Pro）分析搜索结果
   - 提取结构化信息（年级、学科、域名等）
   - **关键**：确保提取的是**当地语言**的学科名

3. **存储阶段**：
   - 将提取的信息保存到 `countries_config.json`
   - 自动生成国家代码（ISO 3166-1 alpha-2）

## ⚠️ 注意事项

1. **API 速率限制**：
   - 批量搜索时，每 3 个请求后等待 1 秒
   - 避免瞬间发送大量请求

2. **调研时间**：
   - 国家调研可能需要 30-60 秒
   - 请耐心等待，不要重复点击

3. **配置准确性**：
   - AI 提取的信息可能不完全准确
   - 建议调研后检查配置，必要时手动调整

4. **语言要求**：
   - 输入国家名称时使用英文
   - 例如：`Philippines` 而不是 `菲律宾`

## 🐛 故障排除

### 问题：国家调研失败

**可能原因**：
- API Token 未设置或无效
- 网络连接问题
- 国家名称输入错误

**解决方案**：
1. 检查 `AI_BUILDER_TOKEN` 环境变量
2. 检查网络连接
3. 确保使用英文国家名称

### 问题：下拉框显示"配置不存在"

**可能原因**：
- 国家配置未创建
- 配置文件损坏

**解决方案**：
1. 点击 **[+]** 按钮添加国家
2. 或点击 **[⟳]** 按钮刷新配置

### 问题：批量搜索超时

**可能原因**：
- 搜索任务过多
- API 速率限制

**解决方案**：
1. 减少搜索范围（不要同时选择"全部年级"和"全部学科"）
2. 等待一段时间后重试

## 📚 相关文档

- `SOP_V2_COMPLETE.md` - V2 版本系统文档
- `ARCHITECTURE_V2.md` - 系统架构文档
- `README_WEB_APP.md` - Web 应用使用说明

## 🎉 更新日志

### V3.0.0 (2024-01-XX)

- ✨ 新增 AI 驱动的国家自动接入系统
- ✨ 新增动态 UI 交互（添加/刷新国家按钮）
- ✨ 新增级联下拉框（年级和学科动态加载）
- ✨ 新增"全部 (All)"批量搜索功能
- 🔧 重构配置管理系统
- 📝 新增 Discovery Agent 和 Config Manager

---

**开发者提示**：如需扩展功能，请参考 `discovery_agent.py` 和 `config_manager.py` 的实现。

