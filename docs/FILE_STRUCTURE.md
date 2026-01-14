# 文件结构说明

## 📁 目录结构

```
Indonesia/
├── core/                          # 核心代码（主要业务逻辑）
│   ├── web_app.py                # Web应用主入口
│   ├── search_engine_v2.py       # 搜索引擎核心
│   ├── discovery_agent.py        # 国家发现Agent
│   ├── result_evaluator.py       # 结果评估器
│   ├── search_strategist.py      # 搜索策略
│   ├── config_manager.py         # 配置管理器
│   └── logger_utils.py           # 日志工具
│
├── templates/                     # 前端模板
│   └── index.html                # 主页面
│
├── data/                          # 数据文件
│   ├── config/                    # 配置文件
│   │   ├── countries_config.json # 国家配置
│   │   └── search_history.json   # 搜索历史
│   ├── knowledge_points/          # 知识点数据
│   │   ├── syllabus_knowledge_points.json
│   │   └── Knowledge Point/      # 知识点JSON文件
│   └── syllabus/                  # 教学大纲PDF
│       └── *.pdf
│
├── docs/                          # 文档
│   ├── ARCHITECTURE_V2.md
│   ├── DEBUG_GUIDE.md
│   ├── DEBUG_LOG_ENHANCEMENT.md
│   ├── FRONTEND_FEATURES_GUIDE.md
│   ├── FRONTEND_UPDATE_SUMMARY.md
│   ├── LOCAL_SEARCH_FIX_SUMMARY.md
│   ├── LOGGING_ENHANCEMENT.md
│   ├── LOG_FILE_INFO.md
│   ├── LOG_TROUBLESHOOTING.md
│   ├── OPTIMIZATION_SUMMARY.md
│   ├── OPTIMIZATION_V3.md
│   ├── README_*.md
│   ├── RESTART_WEB_APP.md
│   ├── SOP_*.md
│   ├── TECHNICAL_DOCUMENTATION_V3.md
│   ├── TEST_RESULTS.md
│   ├── UPGRADE_SUMMARY.md
│   ├── 日志问题解决方案.md
│   └── 端口占用解决方案.md
│
├── logs/                          # 日志文件
│   ├── search_system.log         # 主日志文件（运行时生成）
│   ├── batch_extraction_log.txt
│   ├── extraction_log.txt
│   ├── failed_check_response_iter_1.txt
│   ├── search_output.log
│   ├── test_output.log
│   ├── test_output_detailed.log
│   ├── web_app_console.log
│   └── web_app.log
│
├── scripts/                        # 脚本文件
│   ├── check_logging.py
│   ├── create_demo_data.py
│   ├── debug_verification.py
│   ├── extract_syllabus_knowledge.py
│   ├── extract_syllabus_structured.py
│   ├── generate_web_view.py
│   ├── restart_web_app.sh
│   ├── run_search_and_view.py
│   ├── run_test_with_html.py
│   ├── start_web_app.sh
│   ├── test_api.py
│   ├── test_logging.py
│   ├── test_local_search.py
│   ├── test_small_search.py
│   └── test_tavily_search.py
│
├── tests/                          # 测试文件
│   ├── test_frontend.html
│   ├── test_knowledge_points.json
│   ├── test_playlists.csv
│   ├── test_playlists.html
│   └── serach_v3.txt
│
├── requirements_v3.txt            # Python依赖
├── .env                            # 环境变量（不提交到Git）
└── README.md                       # 项目说明（待创建）
```

## 📝 文件分类说明

### Core（核心代码）
- **web_app.py**: Flask Web应用主入口，提供API接口
- **search_engine_v2.py**: 搜索引擎核心逻辑，包含LLM调用和Tavily搜索
- **discovery_agent.py**: 国家发现Agent，自动调研国家教育体系
- **result_evaluator.py**: 结果评估器，使用LLM对搜索结果评分
- **search_strategist.py**: 搜索策略模块
- **config_manager.py**: 配置管理器，读写国家配置
- **logger_utils.py**: 日志工具，统一管理日志输出

### Templates（前端模板）
- **index.html**: 主页面，包含搜索界面、历史记录、Debug弹窗

### Data（数据文件）
- **config/**: 配置文件目录
  - `countries_config.json`: 国家配置（年级、学科、域名等）
  - `search_history.json`: 搜索历史记录
- **knowledge_points/**: 知识点数据
  - `syllabus_knowledge_points.json`: 教学大纲知识点
  - `Knowledge Point/`: 知识点JSON文件目录
- **syllabus/**: 教学大纲PDF文件

### Docs（文档）
- 所有 `.md` 文档文件，包括：
  - 架构文档（ARCHITECTURE_*.md）
  - SOP文档（SOP_*.md）
  - 技术文档（TECHNICAL_*.md）
  - 更新日志（*_SUMMARY.md, *_UPDATE.md）
  - 问题解决方案（*_解决方案.md）

### Logs（日志文件）
- **search_system.log**: 主日志文件（运行时生成，包含所有详细日志）
- 其他历史日志文件

### Scripts（脚本）
- 测试脚本（test_*.py）
- 工具脚本（extract_*.py, generate_*.py）
- 启动脚本（*.sh）

### Tests（测试）
- 测试HTML文件
- 测试数据JSON文件

## 🔧 路径更新

以下文件路径已更新：

1. **config_manager.py**
   - `countries_config.json` → `data/config/countries_config.json`

2. **web_app.py**
   - `search_history.json` → `data/config/search_history.json`

## 📋 注意事项

1. **日志文件位置**: `search_system.log` 仍在项目根目录（运行时生成）
2. **配置文件**: 已移动到 `data/config/` 目录
3. **数据文件**: 已移动到 `data/` 目录
4. **文档文件**: 已移动到 `docs/` 目录
5. **脚本文件**: 已移动到 `scripts/` 目录

## ✅ 验证

运行以下命令验证文件结构：

```bash
# 检查配置文件
ls -la data/config/

# 检查文档
ls -la docs/ | head -10

# 检查日志
ls -la logs/ | head -10

# 检查脚本
ls -la scripts/ | head -10
```

---

**更新日期**: 2025-12-29  
**状态**: ✅ 文件结构已整理完成





