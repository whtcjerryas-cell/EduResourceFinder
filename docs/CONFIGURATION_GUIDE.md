# 配置化使用指南

**日期**: 2026-01-05
**目的**: 将硬编码配置迁移到配置文件

---

## 📋 已创建的配置文件

### 1. 评估权重配置 ✅
**文件**: `config/evaluation_weights.yaml`
**作用**: 控制视频评估的权重和阈值
**重要性**: ⭐⭐⭐⭐⭐ (最关键)

### 2. LLM配置 ✅
**文件**: `config/llm.yaml`
**作用**: 配置所有大语言模型参数
**重要性**: ⭐⭐⭐⭐⭐

### 3. 搜索引擎配置 ✅
**文件**: `config/search.yaml`
**作用**: 配置搜索引擎API和策略
**重要性**: ⭐⭐⭐⭐

### 4. 视频处理配置 ✅
**文件**: `config/video_processing.yaml`
**作用**: 配置视频下载、处理、转写
**重要性**: ⭐⭐⭐⭐

### 5. AI提示词配置 ✅
**文件**: `config/prompts/ai_search_strategy.yaml`
**作用**: 所有AI搜索相关的提示词
**重要性**: ⭐⭐⭐⭐⭐

### 6. 环境变量示例 ✅
**文件**: `.env.example`
**作用**: 环境变量配置模板
**重要性**: ⭐⭐⭐⭐

### 7. 配置加载器 ✅
**文件**: `core/config_loader.py`
**作用**: 加载和管理所有配置
**重要性**: ⭐⭐⭐⭐⭐

---

## 🔧 如何使用配置

### 步骤1: 在代码中导入配置加载器

```python
# 在文件顶部添加导入
from core.config_loader import get_config
```

### 步骤2: 获取配置加载器实例

```python
# 获取配置加载器
config = get_config()
```

### 步骤3: 使用配置（示例）

#### 示例1: 使用评估权重

**修改前** (硬编码):
```python
# core/video_evaluator.py (第288-291行)

overall_score = (
    visual_score * 0.2 +      # 硬编码
    relevance_score * 0.4 +    # 硬编码
    pedagogy_score * 0.3 +     # 硬编码
    metadata_score * 0.1       # 硬编码
)
```

**修改后** (使用配置):
```python
# core/video_evaluator.py

from core.config_loader import get_config

config = get_config()
weights = config.get_overall_weights()

overall_score = (
    visual_score * weights['visual_quality'] +
    relevance_score * weights['relevance'] +
    pedagogy_score * weights['pedagogy'] +
    metadata_score * weights['metadata']
)
```

#### 示例2: 使用LLM模型配置

**修改前** (硬编码):
```python
# llm_client.py (第77行)
self.model = "gpt-4o"  # 硬编码
```

**修改后** (使用配置):
```python
# llm_client.py

from core.config_loader import get_config

config = get_config()
models = config.get_llm_models()

self.model = models.get('internal_api', 'gpt-4o')
```

#### 示例3: 使用LLM参数配置

**修改前** (硬编码):
```python
# llm_client.py (第99行)
max_tokens=2000,
temperature=0.3  # 硬编码
```

**修改后** (使用配置):
```python
# llm_client.py

from core.config_loader import get_config

config = get_config()
params = config.get_llm_params('default')

max_tokens=params['max_tokens'],
temperature=params['temperature']
```

#### 示例4: 使用提示词配置

**修改前** (硬编码):
```python
# search_strategist.py (第115-123行)
system_prompt = """你是一个教育系统分析专家...
很长的提示词...
"""  # 硬编码
```

**修改后** (使用配置):
```python
# search_strategist.py

from core.config_loader import get_config

config = get_config()
system_prompt = config.get_system_prompt('search_query_generation')
```

#### 示例5: 使用搜索配置

**修改前** (硬编码):
```python
# search_strategist.py (第707行)
"gl": "id"  # 硬编码
```

**修改后** (使用配置):
```python
# search_strategist.py

from core.config_loader import get_config

config = get_config()
search_config = config.get_search_config()

"gl": search_config.get('engines', {}).get('google', {}).get('default_region', 'id')
```

---

## 🚀 快速开始

### 1. 测试配置加载器

```bash
cd /Users/shmiwanghao8/Desktop/education/Indonesia
python core/config_loader.py
```

**预期输出**:
```
==================================================
配置加载器测试
==================================================

1. 评估权重配置:
   视觉质量: 0.2
   相关性: 0.4
   教学法: 0.3
   元数据: 0.1

2. LLM模型配置:
   内部API模型: gpt-4o
   视觉分析模型: gpt-4o
   转写模型: base

3. 搜索策略配置:
   最大尝试次数: 5
   重试延迟: 1秒

4. 本地化关键词:
   印尼语: Video pembelajaran
   英语: Video lesson
   中文: 教学视频

==================================================
配置加载器测试完成！
==================================================
```

### 2. 修改配置并查看效果

```bash
# 1. 编辑配置文件
vim config/evaluation_weights.yaml

# 2. 修改相关性权重
# 从 0.4 改为 0.5
relevance: 0.5

# 3. 相应降低其他权重
visual_quality: 0.15
pedagogy: 0.25
metadata: 0.1

# 4. 保存并重启服务
# 配置会自动生效！
```

---

## 📝 配置化迁移清单

### P0 优先级（必须立即迁移）

- [ ] **评估权重** (`core/video_evaluator.py:288-291`)
  - 综合评分权重
  - 视觉质量权重
  - 元数据权重
  - **预期影响**: 可以快速调整评分策略

- [ ] **LLM模型** (`llm_client.py:77`)
  - 内部API模型
  - Gemini模型
  - 视觉模型
  - **预期影响**: 可以快速切换AI模型

- [ ] **LLM参数** (`llm_client.py:99`)
  - temperature
  - max_tokens
  - **预期影响**: 可以控制AI生成行为

- [ ] **提示词** (多个文件)
  - 搜索查询生成提示词
  - 知识点匹配提示词
  - 评估提示词
  - **预期影响**: 可以优化AI策略

### P1 优先级（尽快迁移）

- [ ] **搜索引擎配置** (`search_strategist.py`)
  - Google搜索区域
  - Baidu模型选择
  - **预期影响**: 可以调整搜索行为

- [ ] **视频处理配置** (`core/video_processor.py`)
  - 默认视频质量
  - 帧提取数量
  - **预期影响**: 可以控制视频处理质量

### P2 优先级（有空再迁移）

- [ ] **重试逻辑参数**
- [ ] **超时设置**
- [ ] **文件路径配置**

---

## 🎯 实施计划

### Day 1 (2小时)

**你做**:
1. ✅ 测试配置加载器（5分钟）
2. ✅ 修改评估权重使用配置（30分钟）
3. ✅ 修改LLM模型使用配置（30分钟）
4. ✅ 测试配置修改是否生效（15分钟）
5. ✅ 调整一次评估权重，验证效果（20分钟）

**开发做**:
1. ✅ 代码Review（30分钟）
2. ✅ 提出改进建议（如需要）

### Day 2 (2小时)

**你做**:
1. ✅ 迁移所有LLM参数使用配置（1小时）
2. ✅ 迁移提示词使用配置（1小时）

**开发做**:
1. ✅ 代码Review（1小时）

### Day 3-7 (持续)

**你做**:
- ✅ 根据实验效果调整配置
- ✅ 优化提示词
- ✅ 调整评分权重
- ✅ 切换不同的AI模型

**开发做**:
- ✅ 继续代码Review
- ✅ 完善其他基础设施

---

## ✅ 验收标准

配置化完成后，你应该能够：

### 1. 快速调整评分策略
```bash
# 只需修改配置文件，无需改代码
vim config/evaluation_weights.yaml
# 重启服务
python web_app.py
```

### 2. 切换AI模型
```bash
# 修改配置
vim config/llm.yaml
# models:
#   internal_api: "gemini-2.5-pro"  # 从gpt-4o切换

# 重启服务
python web_app.py
```

### 3. 优化提示词
```bash
# 修改提示词
vim config/prompts/ai_search_strategy.yaml

# 重启服务
python web_app.py
```

### 4. 调整搜索行为
```bash
# 修改搜索配置
vim config/search.yaml
# strategy:
#   max_attempts_per_chapter: 10  # 从5改为10

# 重启服务
python web_app.py
```

---

## 🎉 核心优势

### 之前（硬编码）
```
调整评分 → 修改代码 → 重启服务 → 测试 → 发现不行 → 再修改代码 → 再重启...
（每次调整都要改代码，费时费力）
```

### 现在（配置驱动）
```
调整评分 → 修改配置 → 重启服务 → 测试 → 发现不行 → 再修改配置 → 再重启...
（只需改配置文件，快速迭代）
```

---

## 📞 需要帮助？

如果遇到问题：

1. **配置加载失败**: 检查文件路径是否正确
2. **配置不生效**: 检查是否重启了服务
3. **配置格式错误**: 检查YAML格式是否正确
4. **不知道如何修改**: 参考本指南的使用示例

---

**最后更新**: 2026-01-05
**状态**: ✅ 配置文件已创建，可以开始迁移
