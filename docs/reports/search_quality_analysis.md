# 搜索质量问题分析报告

**日期**: 2026-01-09
**搜索目标**: 伊拉克 一年级 数学 (الصف الأول - الرياضيات)
**结果数量**: 6个

---

## 🚨 严重问题汇总

### 问题1: 年级识别完全错误 ⚠️⚠️⚠️

#### 案例1: 结果2（六年级被识别为一年级）
```
标题: شرح رياضيات صف سادس منهج إماراتي وزاري
      (六年级数学 - 阿联酋教育部课程)
评分: 8.5分
推荐理由: "年级（一年级）与学科（数学）完全匹配"
实际年级: 六年级 (الصف السادس)
```

**问题**:
- 明显的六年级课程，但被识别为一年级
- 给了8.5分高分，应该≤5分（年级不符）
- 推荐理由完全错误

---

#### 案例2: 结果4和5（一年级被识别为"年级严重不符"）

**结果4**:
```
标题: الرياضيات الصف الأول - منهاج الأردن
      (一年级数学 - 约旦课程)
评分: 4.5分
推荐理由: "学科匹配（数学），但年级严重不符"
实际年级: 一年级 (الصف الأول) ✅
```

**结果5**:
```
标题: سلسلة شرح دروس الرياضيات للصف الأول الفصل الاول
      (一年级数学课程系列 - 第一章)
评分: 4.0分
推荐理由: "学科匹配，但年级严重不符"
实际年级: 一年级 (الصف الأول) ✅
```

**问题**:
- 明确包含"الصف الأول"（一年级），但被识别为不符
- 给了低分（4.0-4.5），应该≥8.5分
- 推荐理由完全错误

---

### 问题2: 阿拉伯语拼写变体识别失败

观察到的拼写变体：
- `الصف الأول` (标准形式，带alif)
- `الصف الاول` (不带alif)
- `صف سادس` (六年级，不带定冠词al)

**可能的失败原因**:
1. 字符匹配过于严格，没有处理变体
2. 阿拉伯语标准化处理（normalize）缺失
3. 没有考虑不同的拼写形式

---

### 问题3: 评分逻辑存在严重缺陷

| 结果 | 实际年级 | 识别年级 | 评分 | 应该评分 | 偏差 |
|------|---------|---------|------|---------|------|
| 1 | 不明确 | - | 9.5 | 7.0-8.0 | +1.5~2.5 |
| 2 | 六年级❌ | 一年级✅ | 8.5 | 3.0-4.0 | **+4.5** |
| 3 | 不明确 | - | 4.5 | 4.0-6.0 | 合理 |
| 4 | 一年级✅ | 不符❌ | 4.5 | 8.5-9.5 | **-4.0~5.0** |
| 5 | 一年级✅ | 不符❌ | 4.0 | 8.5-9.5 | **-4.5~5.5** |
| 6 | 英文 | - | 3.5 | 3.0-4.0 | 合理 |

**关键问题**:
- 年级不符的结果给高分（结果2: 8.5分）
- 年级正确反而给低分（结果4、5: 4.0-4.5分）
- **完全颠倒！**

---

### 问题4: 搜索结果排序错误

当前排序（按质量分数）:
```
1. 结果1: 9.5分 - 年级不明确
2. 结果2: 8.5分 - ❌ 六年级（严重错误）
3. 结果3: 4.5分 - 年级不明确
4. 结果4: 4.5分 - ✅ 一年级（但给低分）
5. 结果5: 4.0分 - ✅ 一年级（但给低分）
6. 结果6: 3.5分 - 英文内容
```

**应该的排序**:
```
1. 结果4: ✅ 一年级数学 - 约旦课程
2. 结果5: ✅ 一年级数学课程系列
3. 结果1: 可能是一年级（需要更多信息）
4. 结果3: 年级不明确
5. 结果6: 英文内容
6. 结果2: ❌ 六年级（完全不符）
```

---

## 🔍 根本原因分析

### 1. LLM评分问题

**可能原因**:
1. **Prompt不够明确**: 没有强调年级匹配的绝对重要性
2. **上下文不足**: LLM可能没有足够的信息理解"الصف الأول"
3. **推理能力限制**: 即使升级到gemini-2.5-pro，阿拉伯语理解仍不够准确

### 2. 阿拉伯语处理问题

**具体问题**:
- 没有进行阿拉伯语标准化（Arabic Normalization）
- 没有处理拼写变体（alif, ya, hamza等）
- 没有考虑不同的书写形式

**标准化示例**:
```python
# 原始文本
"الصف الأول"  # 标准形式
"الصف الاول"  # 不带alif

# 应该标准化为
"الصف اول"    # 统一去掉特殊字符
```

### 3. 评分后验证缺失

**当前流程**:
```
LLM评分 → 直接使用 → 排序
```

**应该的流程**:
```
LLM评分 → 规则验证 → 修正 → 排序
```

### 4. 知识库未充分利用

虽然有知识库支持（`core/knowledge_base_manager.py`），但可能：
- 知识库内容不够全面
- 没有包含阿拉伯语变体
- LLM没有正确利用知识库

---

## 💡 改进方案

### 方案1: 优化评分Prompt ⭐⭐⭐⭐⭐ (最高优先级)

**当前问题**: Prompt可能不够强调年级匹配的重要性

**改进方案**:

```python
# 改进后的Prompt
prompt = f"""请为以下搜索结果评分（0-10分）：

**搜索目标**: {country_code} {target_grade} {target_subject}

**目标年级表达**: {grade_variants_str}
**目标学科表达**: {subject_variants_str}

**⚠️ 关键要求**：
1. 年级匹配是**最关键**的因素
2. 如果年级不符，**必须**给≤5分
3. 如果年级正确，**必须**给≥8分

**搜索结果**:
标题: {result['title']}
描述: {result.get('snippet', '')}

**评分标准**（总分10分）：
1. 年级匹配度（0-4分）：⭐ **最重要的维度**
   - 完全匹配：4分
   - 部分匹配：2-3分
   - 不符：0分

2. 学科匹配度（0-3分）
   - 完全匹配：3分
   - 部分匹配：1-2分
   - 不符：0分

3. 资源质量（0-2分）
   - 完整课程/播放列表：2分
   - 单个视频：1分

4. 来源权威性（0-1分）

**评分规则**：
- ✅ 年级正确 + 学科正确 → 给8-10分
- ❌ 年级不符 → 必须给≤5分（不管其他因素）
- ❌ 学科不符 → 必须给≤5分（不管其他因素）
- ⚠️ 年级不明确 → 给5-7分

**特别注意阿拉伯语**：
- "الصف الأول" = "الصف الاول" = "صف اول" = 一年级
- "الصف الثاني" = "صف ثاني" = 二年级
- "الصف الثالث" = "صف ثالث" = 三年级
- "الصف السادس" = "صف سادس" = 六年级

**输出格式**（JSON）:
{{
    "score": 评分（0-10分，浮点数）,
    "identified_grade": "从标题中识别的年级（必须仔细检查）",
    "identified_subject": "从标题中识别的学科",
    "reason": "评分理由（必须明确说明年级匹配情况）"
}}

请确保：
1. 仔细检查标题中的年级表达
2. 年级不符时务必给低分
3. 输出有效的JSON格式
"""
```

**预期效果**:
- 年级不符的评分大幅降低
- 年级正确的评分提高
- 评分更准确

---

### 方案2: 阿拉伯语标准化处理 ⭐⭐⭐⭐⭐

**实施方案**:

```python
# core/arabic_normalizer.py (新建)
import re

class ArabicNormalizer:
    """阿拉伯语标准化处理"""

    @staticmethod
    def normalize_grade(text: str) -> str:
        """
        标准化阿拉伯语年级表达

        Args:
            text: 原始文本

        Returns:
            标准化后的文本
        """
        # 移除所有alif变体
        text = re.sub(r'[إأآا]', 'ا', text)

        # 移除所有ya变体
        text = re.sub(r'[يى]', 'ي', text)

        # 移除所有hamza变体
        text = re.sub(r'[ؤئء]', 'ء', text)

        # 移除ta marbuta
        text = re.sub(r'ة', 'ه', text)

        # 标准化空格
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    @staticmethod
    def extract_grade_arabic(title: str) -> dict:
        """
        从阿拉伯语标题中提取年级信息

        Returns:
            {
                "grade": "一年级/二年级/...",
                "confidence": "high/medium/low",
                "original": "原始文本"
            }
        """
        # 标准化
        normalized = ArabicNormalizer.normalize_grade(title)

        # 年级关键词映射
        grade_patterns = {
            'اول': '一年级',
            'ثاني': '二年级',
            'ثالث': '三年级',
            'رابع': '四年级',
            'خامس': '五年级',
            'سادس': '六年级',
            'سابع': '七年级',
            'ثامن': '八年级',
            'تاسع': '九年级',
            'عاشر': '十年级',
        }

        # 检查是否包含"صف"
        if 'صف' in normalized:
            # 提取年级
            for arabic_num, chinese in grade_patterns.items():
                if arabic_num in normalized:
                    return {
                        "grade": chinese,
                        "confidence": "high",
                        "original": title[normalized.index(arabic_num)-10 : normalized.index(arabic_num)+20]
                    }

        return {
            "grade": None,
            "confidence": "low",
            "original": ""
        }
```

**集成到评分流程**:

```python
# core/result_scorer.py
from arabic_normalizer import ArabicNormalizer

def _score_with_model(...):
    # ... 原有代码 ...

    # 预处理：阿拉伯语标准化
    if self._is_arabic(result['title']):
        grade_info = ArabicNormalizer.extract_grade_arabic(result['title'])
        if grade_info['grade']:
            # 将识别的年级信息添加到prompt中
            prompt += f"\n**提示**: 标题中识别到年级: {grade_info['grade']} ({grade_info['original']})"
```

---

### 方案3: 规则验证 + LLM评分 ⭐⭐⭐⭐⭐

**双保险机制**:

```python
# core/result_scorer.py

def score_result_with_validation(result, query, model):
    """评分 + 规则验证"""

    # 步骤1: 规则验证（优先级最高）
    rule_based_score = _validate_with_rules(result, query)

    # 步骤2: LLM评分
    llm_score = _score_with_llm(result, query, model)

    # 步骤3: 冲突处理
    final_score = _resolve_conflict(rule_based_score, llm_score, result, query)

    return final_score

def _validate_with_rules(result, query):
    """基于规则的验证"""
    title = result['title']
    target_grade = query['grade']

    # 阿拉伯语年级检测
    if 'الصف الأول' in title or 'الصف الاول' in title or 'صف اول' in title:
        if target_grade in ['一年级', 'Grade 1']:
            return {
                "score": 9.0,  # 规则强制高分
                "confidence": "high",
                "method": "rule_based",
                "reason": "规则检测: 明确包含一年级关键词"
            }

    # 六年级检测
    if 'الصف السادس' in title or 'صف سادس' in title:
        if target_grade in ['一年级', 'Grade 1']:
            return {
                "score": 3.0,  # 规则强制低分
                "confidence": "high",
                "method": "rule_based",
                "reason": "规则检测: 明确是六年级，不符"
            }

    # 无法判断，返回None
    return None

def _resolve_conflict(rule_score, llm_score, result, query):
    """解决规则和LLM评分的冲突"""

    # 如果规则验证置信度高，优先使用规则
    if rule_score and rule_score['confidence'] == 'high':
        logger.warning(f"[⚠️ 评分冲突] LLM: {llm_score['score']}, 规则: {rule_score['score']}")
        logger.warning(f"   使用规则评分: {rule_score['reason']}")

        return {
            **rule_score,
            "llm_score": llm_score['score'],
            "final_method": "rule_override"
        }

    # 否则使用LLM评分
    return {
        **llm_score,
        "rule_score": rule_score['score'] if rule_score else None,
        "final_method": "llm"
    }
```

---

### 方案4: 增强知识库 ⭐⭐⭐⭐

**添加阿拉伯语年级变体**:

```python
# data/knowledge_base/iraq_grades.yaml (新建)

iraq_grade_variants:
 一年级:
    - الصف الأول
    - الصف الاول
    - صف اول
    - Primary 1
    - Grade 1

  二年级:
    - الصف الثاني
    - الصف الثاني
    - صف ثاني
    - Primary 2
    - Grade 2

  三年级:
    - الصف الثالث
    - الصف الثالث
    - صف ثالث
    - Primary 3
    - Grade 3

  六年级:
    - الصف السادس
    - الصف السادس
    - صف سادس
    - Primary 6
    - Grade 6

iraq_subject_variants:
  数学:
    - الرياضيات
    - رياضيات
    - Math
    - Mathematics

  科学:
    - العلوم
    - Science

  物理:
    - الفيزياء
    - Physics
```

**集成到Prompt**:

```python
def _build_prompt_with_knowledge_base(result, query):
    """构建包含知识库的Prompt"""

    # 加载知识库
    kb = load_knowledge_base(query['country'])

    # 获取所有年级变体
    grade_variants = kb.get('grade_variants', [])

    # 获取所有学科变体
    subject_variants = kb.get('subject_variants', [])

    prompt = f"""请为以下搜索结果评分：

**搜索目标**: {query['grade']} {query['subject']}

**所有年级变体**（必须检查是否包含这些）:
{chr(10).join(f"- {v}" for v in grade_variants)}

**所有学科变体**（必须检查是否包含这些）:
{chr(10).join(f"- {v}" for v in subject_variants)}

**搜索结果**:
标题: {result['title']}

⚠️ **必须仔细检查标题中是否包含上述任一年级和学科表达**
"""
    return prompt
```

---

### 方案5: 添加评分后检查 ⭐⭐⭐

**实现逻辑检查**:

```python
def post_process_score(score_data, result, query):
    """评分后处理"""

    score = score_data['score']
    identified_grade = score_data['identified_grade']
    title = result['title']
    target_grade = query['grade']

    # 检查1: 年级不符但高分
    if 'الصف السادس' in title and target_grade == '一年级':
        if score > 5.0:
            logger.warning(f"[🚨 评分错误] 六年级给了{score}分，强制修正为3.0分")
            score_data['score'] = 3.0
            score_data['corrected'] = True
            score_data['correction_reason'] = '六年级误识别为一年级'

    # 检查2: 年级正确但低分
    if 'الصف الأول' in title and target_grade == '一年级':
        if score < 8.0:
            logger.warning(f"[🚨 评分错误] 一年级给了{score}分，强制修正为9.0分")
            score_data['score'] = 9.0
            score_data['corrected'] = True
            score_data['correction_reason'] = '一年级误识别为不符'

    return score_data
```

---

## 🎯 实施优先级

### 立即实施（今天）⭐⭐⭐⭐⭐

1. **优化评分Prompt** (30分钟)
   - 强调年级匹配的重要性
   - 添加阿拉伯语示例
   - 明确评分规则

2. **添加阿拉伯语标准化** (1小时)
   - 创建 `arabic_normalizer.py`
   - 实现标准化函数
   - 集成到评分流程

3. **添加规则验证** (1小时)
   - 实现双保险机制
   - 优先级：规则 > LLM
   - 记录冲突和修正

### 短期实施（本周）⭐⭐⭐⭐

4. **增强知识库** (2小时)
   - 添加完整的阿拉伯语变体
   - 添加中国、印尼、美国的多语言变体
   - 集成到Prompt

5. **添加评分后检查** (1小时)
   - 实现逻辑检查
   - 自动修正明显错误
   - 记录修正日志

### 中期实施（下周）⭐⭐⭐

6. **优化排序逻辑** (2小时)
   - 综合考虑评分、年级匹配、来源权威性
   - 降级不符的结果
   - 提升正确的结果

7. **添加监控** (2小时)
   - 统计评分修正率
   - 分析常见错误
   - 持续优化

---

## 📊 预期效果

### 实施前（当前）

| 指标 | 值 |
|------|-----|
| 年级识别准确率 | ~50% |
| 评分合理性 | ~60% |
| 排序准确性 | ~50% |

### 实施后（预期）

| 指标 | 值 | 提升 |
|------|-----|------|
| 年级识别准确率 | ~95% | **+45%** |
| 评分合理性 | ~90% | **+30%** |
| 排序准确性 | ~90% | **+40%** |

---

## 🔬 验证方案

### 测试用例

```python
test_cases = [
    {
        "title": "الرياضيات الصف الأول - منهاج الأردن",
        "target_grade": "一年级",
        "expected_score": 9.0,
        "expected_reason": "年级正确，应该给高分"
    },
    {
        "title": "شرح رياضيات صف سادس",
        "target_grade": "一年级",
        "expected_score": 3.0,
        "expected_reason": "年级不符（六年级），应该给低分"
    },
    {
        "title": "مادة الرياضيات للصف الاول",
        "target_grade": "一年级",
        "expected_score": 8.5,
        "expected_reason": "年级正确，应该给高分"
    },
    {
        "title": "Mini Math Movies",
        "target_grade": "一年级",
        "expected_score": 4.0,
        "expected_reason": "年级不明确，英文内容"
    },
]
```

---

## 🚀 下一步行动

建议按以下顺序实施：

1. ✅ **立即**: 优化评分Prompt（最快见效）
2. ✅ **今天**: 添加阿拉伯语标准化
3. ✅ **今天**: 添加规则验证（双保险）
4. ✅ **本周**: 增强知识库
5. ✅ **本周**: 添加评分后检查

需要我帮你实施这些改进吗？
