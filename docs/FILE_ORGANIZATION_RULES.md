# 文件组织规则

## 📋 规则概述

本文档定义了K12视频搜索系统的文件组织规则，确保项目结构清晰、易于维护。

**最后更新**: 2025-12-30  
**版本**: V3.2.0

---

## 📁 标准目录结构

```
Indonesia/
├── core/                          # 核心业务逻辑模块
│   ├── video_evaluator.py        # 视频评估器
│   ├── video_processor.py        # 视频处理器
│   ├── transcript_extractor.py   # 字幕提取器
│   ├── playlist_processor.py    # 播放列表处理器
│   └── vision_client.py          # 视觉分析客户端
│
├── templates/                     # 前端模板文件
│   ├── index.html                # 主页面
│   └── knowledge_points.html     # 知识点概览页面
│
├── data/                          # 数据文件目录
│   ├── config/                    # 配置文件
│   │   ├── countries_config.json # 国家配置（主配置）
│   │   └── search_history.json   # 搜索历史
│   ├── evaluations/               # 视频评估结果
│   │   └── evaluation_*.json     # 评估记录文件
│   ├── knowledge_points/         # 知识点数据
│   │   ├── syllabus_knowledge_points.json
│   │   └── Knowledge Point/      # 知识点JSON文件目录
│   ├── syllabus/                  # 教学大纲PDF文件
│   │   └── *.pdf
│   └── videos/                    # 视频文件（下载的视频）
│       ├── analyzed/              # 已分析的视频
│       └── *.mp4                  # 原始视频文件
│
├── docs/                          # 文档目录（所有.md文件）
│   ├── SOP_*.md                  # SOP文档
│   ├── README_*.md                # README文档
│   ├── ARCHITECTURE_*.md          # 架构文档
│   ├── DEBUG_*.md                 # 调试文档
│   ├── *_SUMMARY.md               # 总结文档
│   ├── *_UPDATE.md                # 更新文档
│   ├── *_GUIDE.md                 # 指南文档
│   └── *_解决方案.md              # 问题解决方案
│
├── logs/                          # 日志文件目录
│   ├── YYYY-MM-DD/                # 按日期组织的日志目录
│   │   └── debug_log_*.txt        # Debug日志文件
│   ├── search_system.log          # 主系统日志（运行时生成）
│   └── web_app_*.log              # Web应用日志
│
├── scripts/                        # 脚本文件目录
│   ├── test_*.py                  # 测试脚本
│   ├── extract_*.py               # 提取脚本
│   ├── generate_*.py              # 生成脚本
│   ├── debug_*.py                 # 调试脚本
│   ├── check_*.py                 # 检查脚本
│   ├── run_*.py                   # 运行脚本
│   ├── start_*.sh                 # 启动脚本
│   └── restart_*.sh                # 重启脚本
│
├── tests/                         # 测试文件目录
│   ├── test_*.html                # 测试HTML文件
│   ├── test_*.json                # 测试JSON数据
│   ├── test_*.csv                 # 测试CSV数据
│   └── *.txt                      # 测试文本文件
│
├── venv/                          # Python虚拟环境（不提交到Git）
│
├── .cursorrules                   # Cursor IDE规则文件
├── .env                           # 环境变量文件（不提交到Git）
├── .gitignore                     # Git忽略文件
│
├── web_app.py                     # Flask Web应用主入口（根目录）
├── search_engine_v2.py            # 搜索引擎核心（根目录）
├── discovery_agent.py             # 国家发现Agent（根目录）
├── search_strategy_agent.py       # 搜索策略Agent（根目录）
├── search_strategist.py           # 搜索策略模块（根目录）
├── result_evaluator.py            # 结果评估器（根目录）
├── config_manager.py              # 配置管理器（根目录）
├── json_utils.py                  # JSON工具函数（根目录）
├── logger_utils.py                # 日志工具（根目录）
│
├── requirements_*.txt             # Python依赖文件（根目录）
├── README.md                      # 项目主README（根目录）
└── search_system.log              # 主日志文件（运行时生成，根目录）
```

---

## 📝 文件分类规则

### 1. 核心代码文件（根目录）

**位置**: 项目根目录

**文件类型**:
- `web_app.py` - Flask应用主入口
- `*_engine*.py` - 搜索引擎相关
- `*_agent.py` - Agent相关
- `*_evaluator.py` - 评估器相关
- `*_manager.py` - 管理器相关
- `*_utils.py` - 工具函数（通用工具）

**规则**:
- ✅ 这些文件是项目的核心入口和主要模块
- ✅ 保持在根目录，便于导入和运行
- ❌ 不要移动到子目录

---

### 2. Core模块（core/目录）

**位置**: `core/`

**文件类型**:
- `video_*.py` - 视频处理相关
- `transcript_*.py` - 字幕提取相关
- `playlist_*.py` - 播放列表处理相关
- `vision_*.py` - 视觉分析相关

**规则**:
- ✅ 核心业务逻辑的独立模块
- ✅ 可以被根目录的模块导入
- ✅ 每个文件应该是一个独立的类或功能模块

---

### 3. 文档文件（docs/目录）

**位置**: `docs/`

**文件类型**: 所有 `.md` 文件

**命名规则**:
- `SOP_*.md` - SOP文档
- `README_*.md` - README文档
- `ARCHITECTURE_*.md` - 架构文档
- `DEBUG_*.md` - 调试文档
- `*_SUMMARY.md` - 总结文档
- `*_UPDATE.md` - 更新文档
- `*_GUIDE.md` - 指南文档
- `*_解决方案.md` - 问题解决方案
- `FILE_*.md` - 文件结构文档

**规则**:
- ✅ 所有文档文件必须放在 `docs/` 目录
- ✅ 根目录只保留 `README.md`（项目主README）
- ❌ 禁止在根目录创建其他 `.md` 文件

---

### 4. 配置文件（data/config/目录）

**位置**: `data/config/`

**文件类型**:
- `countries_config.json` - 国家配置（主配置文件）
- `search_history.json` - 搜索历史
- 其他配置JSON文件

**规则**:
- ✅ 所有配置文件放在 `data/config/` 目录
- ✅ 代码中引用时使用相对路径：`data/config/countries_config.json`
- ❌ 禁止在根目录放置配置文件

---

### 5. 数据文件（data/目录）

**位置**: `data/`

**子目录**:
- `data/config/` - 配置文件
- `data/evaluations/` - 评估结果（运行时生成）
- `data/knowledge_points/` - 知识点数据
- `data/syllabus/` - 教学大纲PDF
- `data/videos/` - 视频文件（运行时生成）

**规则**:
- ✅ 所有数据文件放在 `data/` 目录下
- ✅ 运行时生成的文件放在对应的子目录
- ✅ 按类型组织子目录

---

### 6. 脚本文件（scripts/目录）

**位置**: `scripts/`

**文件类型**:
- `test_*.py` - 测试脚本
- `extract_*.py` - 数据提取脚本
- `generate_*.py` - 代码生成脚本
- `debug_*.py` - 调试脚本
- `check_*.py` - 检查脚本
- `run_*.py` - 运行脚本
- `*.sh` - Shell脚本

**规则**:
- ✅ 所有脚本文件放在 `scripts/` 目录
- ✅ 测试脚本使用 `test_` 前缀
- ✅ Shell脚本放在 `scripts/` 目录
- ❌ 禁止在根目录放置脚本文件

---

### 7. 测试文件（tests/目录）

**位置**: `tests/`

**文件类型**:
- `test_*.html` - 测试HTML文件
- `test_*.json` - 测试JSON数据
- `test_*.csv` - 测试CSV数据
- `*.txt` - 测试文本文件

**规则**:
- ✅ 测试数据和测试HTML文件放在 `tests/` 目录
- ✅ 测试脚本放在 `scripts/` 目录
- ✅ 区分测试脚本（scripts/）和测试数据（tests/）

---

### 8. 日志文件（logs/目录）

**位置**: `logs/`

**文件类型**:
- `YYYY-MM-DD/debug_log_*.txt` - 按日期组织的Debug日志
- `search_system.log` - 主系统日志（运行时生成）
- `web_app_*.log` - Web应用日志

**规则**:
- ✅ Debug日志按日期组织：`logs/YYYY-MM-DD/`
- ✅ 主日志文件可以在根目录（运行时生成）
- ✅ 历史日志文件放在 `logs/` 目录

---

### 9. 前端模板（templates/目录）

**位置**: `templates/`

**文件类型**:
- `*.html` - HTML模板文件

**规则**:
- ✅ 所有HTML模板文件放在 `templates/` 目录
- ✅ Flask会自动识别此目录
- ❌ 禁止在根目录放置HTML文件

---

### 10. 依赖文件（根目录）

**位置**: 项目根目录

**文件类型**:
- `requirements_*.txt` - Python依赖文件
- `.env` - 环境变量文件（不提交到Git）
- `.gitignore` - Git忽略文件
- `.cursorrules` - Cursor IDE规则文件

**规则**:
- ✅ 依赖文件保持在根目录
- ✅ 环境配置文件不提交到Git

---

## 🔄 文件移动规则

### 创建新文件时的检查清单

创建新文件前，请检查以下问题：

1. **文件类型是什么？**
   - `.md` → `docs/`
   - `.py` (脚本) → `scripts/`
   - `.py` (核心模块) → `core/` 或根目录
   - `.json` (配置) → `data/config/`
   - `.json` (数据) → `data/` 对应子目录
   - `.html` → `templates/` 或 `tests/`
   - `.sh` → `scripts/`

2. **文件用途是什么？**
   - 测试脚本 → `scripts/test_*.py`
   - 工具脚本 → `scripts/`
   - 核心业务逻辑 → `core/` 或根目录
   - 文档 → `docs/`

3. **文件是否已存在？**
   - 检查是否有重复文件
   - 检查是否有旧版本需要清理

---

## 📋 文件命名规范

### Python文件
- **核心模块**: `snake_case.py`（如 `search_engine_v2.py`）
- **测试脚本**: `test_*.py`（如 `test_api.py`）
- **工具脚本**: `动词_名词.py`（如 `extract_syllabus.py`）

### 文档文件
- **SOP文档**: `SOP_*.md`（如 `SOP_COMPLETE_V3.2.md`）
- **README文档**: `README_*.md`（如 `README_V3.md`）
- **总结文档**: `*_SUMMARY.md`（如 `OPTIMIZATION_SUMMARY.md`）

### 配置文件
- **主配置**: `countries_config.json`
- **历史记录**: `search_history.json`
- **评估结果**: `evaluation_*.json`

---

## ✅ 文件组织检查清单

创建或移动文件后，请检查：

- [ ] 文件是否放在正确的目录？
- [ ] 文件命名是否符合规范？
- [ ] 是否有重复文件？
- [ ] 代码中的路径引用是否正确？
- [ ] 是否需要更新 `.gitignore`？
- [ ] 是否需要更新文档？

---

## 🚫 禁止事项

1. ❌ **禁止在根目录创建文档文件**（除了 `README.md`）
2. ❌ **禁止在根目录创建测试脚本**
3. ❌ **禁止在根目录创建配置文件**
4. ❌ **禁止在根目录创建HTML文件**
5. ❌ **禁止创建重复文件**（先检查是否已存在）
6. ❌ **禁止使用中文文件名**（除了文档中的解决方案文件）

---

## 📚 参考文档

- **文件结构说明**: `docs/FILE_STRUCTURE.md`
- **SOP文档**: `docs/SOP_COMPLETE_V3.2.md`
- **项目README**: `README.md`

---

**最后更新**: 2025-12-30  
**维护者**: AI Assistant





