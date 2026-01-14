# 配置文件说明

**Indonesia K12 Video Search System**

本目录包含所有系统配置文件。通过修改这些配置文件，你可以快速调整系统行为，无需修改代码。

---

## 📁 配置文件列表

### 核心配置文件

| 文件 | 说明 | 重要性 |
|------|------|--------|
| `evaluation_weights.yaml` | 视频评估权重和阈值 | ⭐⭐⭐⭐⭐ |
| `llm.yaml` | 大语言模型配置 | ⭐⭐⭐⭐⭐ |
| `search.yaml` | 搜索引擎配置 | ⭐⭐⭐⭐ |
| `video_processing.yaml` | 视频处理配置 | ⭐⭐⭐⭐ |
| `prompts/ai_search_strategy.yaml` | AI提示词配置 | ⭐⭐⭐⭐⭐ |

### 环境配置

| 文件 | 说明 |
|------|------|
| `.env.example` | 环境变量配置模板 |

---

## 🎯 快速开始

### 1. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量，填入API密钥
vim .env
```

### 2. 测试配置加载

```bash
# 测试配置加载器是否正常工作
python core/config_loader.py
```

### 3. 修改配置

```bash
# 例如：调整评估权重
vim config/evaluation_weights.yaml

# 修改后重启服务即可生效
```

---

## 📖 详细说明

### evaluation_weights.yaml

**作用**: 控制视频评估的权重分配

**常用调整**:
- `overall_weights`: 综合评分权重（视觉、相关度、教学法、元数据）
- `video_quality.resolution`: 分辨率评分阈值
- `metadata.view_count`: 观看次数评分阈值
- `metadata.like_ratio`: 点赞率评分阈值

**示例**:
```yaml
# 提高相关性权重
overall_weights:
  relevance: 0.5  # 从0.4提高到0.5
  visual_quality: 0.15
  pedagogy: 0.25
  metadata: 0.1
```

---

### llm.yaml

**作用**: 配置所有大语言模型相关参数

**常用调整**:
- `models`: 切换不同的AI模型
- `params`: 调整LLM生成参数（temperature, max_tokens）
- `model_fallback_order`: 模型降级顺序

**示例**:
```yaml
# 切换到Gemini模型
models:
  internal_api: "gemini-2.5-pro"  # 从gpt-4o切换

# 提高创造性
params:
  default:
    temperature: 0.7  # 从0.3提高到0.7
```

---

### search.yaml

**作用**: 配置搜索引擎和搜索策略

**常用调整**:
- `engines`: 搜索引擎API密钥和端点
- `strategy.max_attempts_per_chapter`: 每个章节的搜索尝试次数
- `localization`: 不同语言的搜索关键词

**示例**:
```yaml
# 增加搜索尝试次数
strategy:
  max_attempts_per_chapter: 10  # 从5改为10
```

---

### video_processing.yaml

**作用**: 配置视频下载、处理、转写

**常用调整**:
- `download.default_quality`: 默认下载视频质量
- `frames.default_count`: 提取关键帧数量
- `transcription.whisper_model`: Whisper模型大小

**示例**:
```yaml
# 提高视频质量
download:
  default_quality: "720p"  # 从480p改为720p

# 提取更多帧
frames:
  default_count: 10  # 从6改为10
```

---

### prompts/ai_search_strategy.yaml

**作用**: 所有AI搜索相关的提示词

**常用调整**:
- `search_query_generation.system_prompt`: 搜索查询生成提示词
- `knowledge_point_matching.system_prompt`: 知识点匹配提示词
- 各种评估提示词

**示例**:
```yaml
# 优化搜索查询生成提示词
search_query_generation:
  system_prompt: |
    你是一个专业的教育搜索引擎优化助手。

    ## 新增要求
    - 优先寻找印尼本地教育平台的视频
    - 避免包含广告的搜索结果
    ...
```

---

## 🔧 配置热重载

当前配置在服务启动时加载。修改配置后：

1. **简单方法**: 重启服务
   ```bash
   # 停止服务
   pkill -f "python.*web_app"

   # 启动服务
   python web_app.py
   ```

2. **高级方法**: 未来可以添加配置热重载功能（无需重启）

---

## 📝 最佳实践

### 1. 修改配置前备份

```bash
# 备份当前配置
cp config/evaluation_weights.yaml config/evaluation_weights.yaml.backup
```

### 2. 小步迭代

- 每次只调整1-2个参数
- 测试效果后再继续调整
- 保留工作良好的配置

### 3. 记录实验结果

```yaml
# 在配置文件中添加注释
# 实验1: 提高相关性权重到0.5 - 2026-01-05
# 结果: 相关视频排序更准确，推荐！
relevance: 0.5
```

### 4. 版本控制

```bash
# 提交重要的配置更改
git add config/
git commit -m "调整评估权重：提高相关性权重"
```

---

## ⚠️ 注意事项

### 1. 配置格式

- YAML格式要求严格
- 缩进必须使用空格（不能使用Tab）
- 字符串建议用引号包裹
- 注释使用 `#` 符号

### 2. 权重总和

确保权重总和为1.0：

```yaml
# ✅ 正确
overall_weights:
  visual_quality: 0.2
  relevance: 0.4
  pedagogy: 0.3
  metadata: 0.1
  # 总和: 0.2+0.4+0.3+0.1 = 1.0 ✅

# ❌ 错误
overall_weights:
  visual_quality: 0.3
  relevance: 0.3
  pedagogy: 0.3
  metadata: 0.3
  # 总和: 0.3+0.3+0.3+0.3 = 1.2 ❌
```

### 3. API密钥安全

- 永远不要把API密钥提交到Git
- 使用环境变量存储敏感信息
- `.env` 文件应该添加到 `.gitignore`

---

## 🆘 常见问题

### Q1: 修改配置后没有生效？

**A**:
1. 检查配置文件格式是否正确
2. 确认是否重启了服务
3. 查看日志是否有错误信息

### Q2: 如何知道当前使用的是哪个配置？

**A**:
```python
from core.config_loader import get_config

config = get_config()
print(config.get_config_info())
```

### Q3: 配置文件可以分环境吗（开发/生产）？

**A**: 可以！创建多个配置文件：
```bash
config/
├── evaluation_weights.dev.yaml    # 开发环境
├── evaluation_weights.prod.yaml   # 生产环境
└── evaluation_weights.yaml         # 默认配置
```

然后在代码中根据环境变量选择：
```python
import os
env = os.getenv('FLASK_ENV', 'development')
config_file = f'evaluation_weights.{env}.yaml'
```

### Q4: 如何恢复默认配置？

**A**:
```bash
# 从Git恢复默认配置
git checkout config/

# 或从备份恢复
cp config/evaluation_weights.yaml.backup config/evaluation_weights.yaml
```

---

## 📚 相关文档

- [配置化使用指南](CONFIGURATION_GUIDE.md) - 如何在代码中使用配置
- [系统文档](../README.md) - 系统总体说明

---

**最后更新**: 2026-01-05
**维护者**: 产品经理 + AI
