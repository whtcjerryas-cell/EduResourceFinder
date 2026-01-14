# LLM模型A/B测试框架

## 📋 概述

这是Indonesia教育视频搜索引擎的LLM模型A/B测试框架，用于评估不同LLM模型在各个搜索环节上的性能。

### 支持的测试类型

1. **智能评分测试** (已实现) ⭐
   - 测试不同模型在智能评分任务上的准确性和性能
   - 100个测试用例，涵盖伊拉克、中国、印尼、美国

2. **搜索策略测试** (TODO)
   - 测试不同模型生成搜索策略的质量

3. **推荐理由测试** (TODO)
   - 测试不同模型生成推荐理由的质量

---

## 🚀 快速开始

### 前置要求

- Python 3.13
- 已配置的LLM客户端（`llm_client.py`）

### 安装

无需额外安装，直接使用项目依赖：

```bash
cd /Users/shmiwanghao8/Desktop/education/Indonesia
```

### 运行测试

#### 1. 运行智能评分测试（所有模型）

```bash
python3 tests/ab_testing/run_ab_test.py --test-type scoring
```

这将测试以下6个模型（按顺序）：
- gemini-3-pro-thinking-high
- gemini-3-pro-thinking-medium
- gpt-5.2-thinking-medium
- claude-3-7-sonnet
- gemini-2.5-pro
- gemini-2.5-flash (当前模型)

**预计时间**: 8-10小时（100个测试用例 × 6个模型）

#### 2. 运行智能评分测试（指定模型）

```bash
python3 tests/ab_testing/run_ab_test.py \
    --test-type scoring \
    --models gemini-2.5-pro gemini-2.5-flash
```

#### 3. 运行智能评分测试（限制测试用例数，快速验证）

```bash
python3 tests/ab_testing/run_ab_test.py \
    --test-type scoring \
    --test-cases 10
```

**预计时间**: 30-60分钟（10个测试用例 × 6个模型）

#### 4. 详细输出模式

```bash
python3 tests/ab_testing/run_ab_test.py \
    --test-type scoring \
    --test-cases 5 \
    --verbose
```

---

## 📊 测试数据

### 测试用例分布

| 国家 | 测试用例数 | 年级范围 | 学科 | 匹配度分布 |
|------|-----------|---------|------|-----------|
| 伊拉克（IQ） | 30个 | 1-12年级 | 数学、科学、物理 | 10个完全匹配、10个部分匹配、10个不匹配 |
| 中国（CN） | 30个 | 1-12年级 | 数学、语文、英语、物理 | 同上 |
| 印尼（ID） | 25个 | 1-12年级 | Matematika, IPA, Bahasa | 同上 |
| 美国（US） | 15个 | K-12 | Math, Science, Physics | 同上 |

### 测试用例结构

每个测试用例包含：
- **目标**: 国家、年级、学科（及其多语言表达变体）
- **搜索结果**: 4个模拟的搜索结果
  - 1个完全匹配（预期高分 9-10分）
  - 1个年级不符（预期低分 3-5分）
  - 1个学科不符（预期低分 3-5分）
  - 1个部分匹配（预期中等分数 7-8.5分）

### 重新生成测试用例

如果需要修改测试用例，运行：

```bash
python3 tests/ab_testing/generate_test_cases.py
```

---

## 📈 输出和报告

### 输出文件

测试完成后，会在 `tests/reports/weekly_reports/` 目录下生成：

1. **测试结果文件** (`scoring_test_YYYYMMDD_HHMMSS.json`)
   - 完整的测试结果数据
   - 包含每个模型的详细评分和评估

2. **测试报告** (`scoring_report_YYYYMMDD_HHMMSS.md`)
   - Markdown格式的测试报告
   - 包含汇总统计和详细结果

### 汇总指标

测试会计算以下指标：

- **准确率**: 评分在预期范围内的结果占比
- **年级识别准确率**: 正确识别年级的结果占比
- **学科识别准确率**: 正确识别学科的结果占比
- **平均评分偏差**: 实际评分与期望评分的平均偏差
- **平均响应时间**: 单次评分的平均耗时
- **成功率**: 成功完成评分的调用占比

---

## 🔬 测试流程

### 单个模型测试流程

```
对于每个模型:
  对于每个测试用例 (100个):
    对于每个搜索结果 (4个):
      1. 构建评分提示词（包含目标年级、学科及其多语言变体）
      2. 调用LLM进行评分
      3. 解析LLM响应（JSON格式）
      4. 评估结果（对比预期评分、年级识别、学科识别）
      5. 记录结果
```

### 评分提示词

```
请为以下搜索结果评分（0-10分）：

**搜索目标**: CN 五年级 数学

**目标年级表达**: 五年级, Grade 5, Kelas 5
**目标学科表达**: 数学, Mathematics

**搜索结果**:
标题: 五年级数学上册全册讲解
描述: 完整讲解五年级数学上册所有知识点

**评分要求**:
1. 年级匹配度（0-3分）：从标题中提取年级，与目标年级对比
2. 学科匹配度（0-3分）：从标题中提取学科，与目标学科对比
3. 资源质量（0-2分）：判断是否是完整课程/播放列表
4. 来源权威性（0-2分）：判断来源是否可信

**评分规则**:
- 年级不符必须大幅减分（≤5分）
- 学科不符必须大幅减分（≤5分）
- 完全匹配给高分（≥9分）

**输出格式**（JSON）:
{
    "score": 评分（0-10分，浮点数）,
    "identified_grade": "从标题中识别的年级",
    "identified_subject": "从标题中识别的学科",
    "reason": "评分理由（30-50字）"
}
```

---

## 📁 目录结构

```
tests/
├── ab_testing/
│   ├── __init__.py
│   ├── README.md                          # 本文档
│   ├── run_ab_test.py                     # 主测试入口
│   ├── generate_test_cases.py             # 测试用例生成器
│   ├── test_data/
│   │   └── test_cases_scoring.json        # 100个评分测试用例
│   ├── runners/
│   │   ├── __init__.py
│   │   └── scoring_test_runner.py         # 智能评分测试执行器
│   ├── evaluators/
│   │   ├── __init__.py
│   │   ├── scoring_evaluator.py           # 智能评分评估器
│   │   ├── strategy_evaluator.py          # 搜索策略评估器（TODO）
│   │   └── recommendation_evaluator.py    # 推荐理由评估器（TODO）
│   ├── models/
│   │   ├── __init__.py
│   │   ├── test_result.py                 # 测试结果数据模型（TODO）
│   │   └── evaluation_report.py           # 评估报告数据模型（TODO）
│   └── utils/
│       ├── __init__.py
│       ├── llm_caller.py                  # LLM调用工具（带监控）
│       └── metrics_calculator.py          # 指标计算工具（TODO）
└── reports/
    └── weekly_reports/                    # 测试报告输出目录
        ├── scoring_test_YYYYMMDD_HHMMSS.json
        └── scoring_report_YYYYMMDD_HHMMSS.md
```

---

## 🎯 预期测试结果

### 优秀模型的标准

- **准确率**: ≥85%
- **年级识别准确率**: ≥95%
- **学科识别准确率**: ≥95%
- **平均评分偏差**: ≤1.0分
- **平均响应时间**: ≤5秒
- **成功率**: ≥98%

### 评级标准

- **A+ (优秀)**: 所有指标达到优秀水平
- **A (良好)**: 大部分指标达到良好水平
- **B (一般)**: 部分指标未达标
- **C (需改进)**: 多项关键指标不达标

---

## 🔧 故障排除

### 问题1: 测试用例文件不存在

**错误**: `FileNotFoundError: 测试用例文件不存在: ...`

**解决**:
```bash
python3 tests/ab_testing/generate_test_cases.py
```

### 问题2: LLM调用失败

**错误**: `❌ LLM调用失败 (xxx): ...`

**解决**:
- 检查LLM客户端配置（`llm_client.py`）
- 检查网络连接
- 检查API密钥

### 问题3: JSON解析失败

**警告**: `⚠️ 无法解析JSON响应，使用默认评分`

**说明**: 这是正常的，部分模型可能返回非JSON格式的响应。测试框架会使用默认评分（5.0分）继续运行。

---

## 📝 TODO

- [ ] 实现搜索策略测试 (`strategy_test_runner.py`)
- [ ] 实现推荐理由测试 (`recommendation_test_runner.py`)
- [ ] 添加测试结果的自动分析和可视化
- [ ] 添加成本统计
- [ ] 实现端到端测试 (`e2e_test_runner.py`)

---

## 📧 联系方式

如有问题或建议，请联系项目负责人。

---

**最后更新**: 2025-01-09
