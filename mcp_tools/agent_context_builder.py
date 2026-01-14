"""
Agent上下文构建器 - 动态生成Agent的系统提示词

遵循 agent-native 原则：
- 动态上下文注入：运行时注入可用资源和能力
- 丰富上下文：Agent知道所有可用的工具和配置
- 可组合性：新功能只需修改prompt，无需改代码
"""

import json
from typing import Dict, List, Any
from logger_utils import get_logger
from .config_tools import read_country_config
from .knowledge_tools import list_learned_patterns

logger = get_logger('agent_context_builder')


async def build_agent_system_prompt(country_code: str) -> str:
    """
    构建Agent的系统提示词（包含完整的上下文信息）

    Args:
        country_code: 国家代码，如 ID, SA, CN

    Returns:
        完整的系统提示词字符串，包含：
        - 国家教育体系配置
        - 年级和学科列表
        - 已学习的模式
        - 可用工具说明
        - 评分流程指导

    示例：
        >>> prompt = await build_agent_system_prompt("ID")
        >>> print(prompt)
        # 国家教育体系配置
        **国家**: Indonesia (ID)
        **语言**: id

        ## 年级体系
        - **Kelas 1** = 一年级 (ID: 1)
        - **Kelas 2** = 二年级 (ID: 2)
        ...
    """
    try:
        # 1. 读取国家配置
        config_result = await read_country_config(country_code)

        if not config_result["success"]:
            logger.error(f"无法读取国家配置 {country_code}: {config_result.get('error')}")
            return f"# 错误\n\n无法加载国家配置: {config_result.get('error')}"

        config = config_result["data"]

        # 2. 读取已学习的模式
        learned_result = await list_learned_patterns(
            country_code=country_code,
            status="verified",
            limit=100
        )

        learned_patterns = learned_result.get("data", [])

        # 3. 构建系统提示词
        prompt_parts = []

        # === 标题 ===
        prompt_parts.append(f"# {config['country_name']} 教育资源评分系统")
        prompt_parts.append("")

        # === 国家教育体系配置 ===
        prompt_parts.append("## 国家教育体系配置\n")
        prompt_parts.append(f"**国家**: {config['country_name']} ({config['country_code']})")
        prompt_parts.append(f"**语言**: {config['language_code']}")
        prompt_parts.append("")

        # === 年级体系 ===
        prompt_parts.append("## 年级体系\n")
        grades = config.get("grades", [])
        for grade in grades:
            grade_id = grade.get("grade_id", "N/A")
            prompt_parts.append(f"- **{grade['local_name']}** = {grade['zh_name']} (ID: {grade_id})")
        prompt_parts.append("")

        # === 学科列表 ===
        prompt_parts.append("## 学科列表\n")
        subjects = config.get("subjects", [])
        for subject in subjects:
            subject_id = subject.get("subject_id", "N/A")
            prompt_parts.append(f"- **{subject['local_name']}** = {subject['zh_name']} (ID: {subject_id})")
        prompt_parts.append("")

        # === 已学习的模式 ===
        if learned_patterns:
            prompt_parts.append("## 已学习的模式\n")
            prompt_parts.append("通过搜索结果和LLM提取，系统已学习到以下额外表达：\n")

            # 分组显示
            grade_patterns = [p for p in learned_patterns if p.get("pattern_type") == "grade"]
            subject_patterns = [p for p in learned_patterns if p.get("pattern_type") == "subject"]

            if grade_patterns:
                prompt_parts.append("**年级表达**:")
                for p in grade_patterns[:10]:  # 只显示前10个
                    status_emoji = "✅" if p.get("status") == "verified" else "⏳"
                    prompt_parts.append(f"- {status_emoji} {p['local_expression']} = {p['standard_name']} "
                                      f"(成功率: {p.get('success_rate', 0)*100:.0f}%)")
                prompt_parts.append("")

            if subject_patterns:
                prompt_parts.append("**学科表达**:")
                for p in subject_patterns[:10]:  # 只显示前10个
                    status_emoji = "✅" if p.get("status") == "verified" else "⏳"
                    prompt_parts.append(f"- {status_emoji} {p['local_expression']} = {p['standard_name']} "
                                      f"(成功率: {p.get('success_rate', 0)*100:.0f}%)")
                prompt_parts.append("")

        # === 可用工具 ===
        prompt_parts.append("## 可用工具\n")
        prompt_parts.append("你可以使用以下工具来完成评分任务：\n")

        prompt_parts.append("| 用户需求 | 使用工具 | 返回信息 |")
        prompt_parts.append("|---------|---------|---------|")
        prompt_parts.append("| 检查年级匹配 | `validate_grade_match` | 是否匹配 + 置信度 |")
        prompt_parts.append("| 提取年级信息 | `extract_grade_from_title` | 从标题识别年级 |")
        prompt_parts.append("| 提取学科信息 | `extract_subject_from_title` | 从标题识别学科 |")
        prompt_parts.append("| 检查URL质量 | `validate_url_quality` | 质量等级 + 是否过滤 |")
        prompt_parts.append("| 学习新模式 | `record_pattern_learning` | 记录到知识库（待验证） |")
        prompt_parts.append("|")

        # === 评分流程 ===
        prompt_parts.append("## 评分流程\n")
        prompt_parts.append("当收到搜索结果时，请按以下步骤操作：\n")

        prompt_parts.append("### 步骤1：提取信息")
        prompt_parts.append("使用 `extract_grade_from_title` 和 `extract_subject_from_title` 提取年级和学科。\n")

        prompt_parts.append("### 步骤2：验证匹配")
        prompt_parts.append("使用 `validate_grade_match` 验证年级是否匹配目标。\n")

        prompt_parts.append("### 步骤3：检查URL质量")
        prompt_parts.append("使用 `validate_url_quality` 检查URL来源是否可信。\n")

        prompt_parts.append("### 步骤4：综合评分")
        prompt_parts.append("**基础分**: 3.0分\n")
        prompt_parts.append("**加分项**:")
        prompt_parts.append("- 年级匹配: +3.0分")
        prompt_parts.append("- 学科匹配: +2.0分")
        prompt_parts.append("- YouTube视频: +1.5分")
        prompt_parts.append("- 播放列表: +1.0分")
        prompt_parts.append("- 详细描述: +1.0分\n")
        prompt_parts.append("**减分项**:")
        prompt_parts.append("- 年级不匹配: -5.0分（强制低分）")
        prompt_parts.append("- 社交媒体内容: -8.0分（强制过滤）")
        prompt_parts.append("- 非教育内容: -6.0分")
        prompt_parts.append("- URL质量低: -2.0分\n")

        prompt_parts.append("### 步骤5：生成推荐理由")
        prompt_parts.append("推荐理由格式：")
        prompt_parts.append("- **高分类（≥8分）**: \"年级和学科完全匹配（{年级} {学科}），来自可信平台\"")
        prompt_parts.append("- **中分类（5-7分）**: \"年级匹配（{年级}），学科相关，但内容质量一般\"")
        prompt_parts.append("- **低分类（<5分）**: \"年级不符（目标{目标年级}，标题{识别年级}），不推荐\"\n")

        prompt_parts.append("### 步骤6：记录学习")
        prompt_parts.append("如果遇到无法识别的年级/学科表达：")
        prompt_parts.append("1. 使用LLM推断")
        prompt_parts.append("2. 调用 `record_pattern_learning` 记录新模式")
        prompt_parts.append("3. 标记为\"待验证\"状态")
        prompt_parts.append("4. 在后续搜索中验证准确性\n")

        # === 示例 ===
        prompt_parts.append("## 示例\n")

        prompt_parts.append("**示例1：年级不匹配**")
        prompt_parts.append("```\n目标: 一年级 数学（印尼）")
        prompt_parts.append("标题: matematika Kelas 6 vol 1 LENGKAP\n")
        prompt_parts.append("你的分析：")
        prompt_parts.append("1. extract_grade_from_title → \"六年级\" (Kelas 6)")
        prompt_parts.append("2. validate_grade_match(target=\"Kelas 1\", identified=\"Kelas 6\") → 不匹配")
        prompt_parts.append("3. validate_url_quality → YouTube（可信）")
        prompt_parts.append("4. 评分: 3.0 - 5.0 = -2.0，调整为0.0（最低分）")
        prompt_parts.append("5. 推荐理由: \"年级不符（目标一年级，标题六年级 Kelas 6），不推荐\"")
        prompt_parts.append("```\n")

        prompt_parts.append("**示例2：完全匹配**")
        prompt_parts.append("```\n目标: 一年级 数学（印尼）")
        prompt_parts.append("标题: Matematika Kelas 1 SD - Bilangan 1-10\n")
        prompt_parts.append("你的分析：")
        prompt_parts.append("1. extract_grade_from_title → \"一年级\" (Kelas 1)")
        prompt_parts.append("2. validate_grade_match(target=\"Kelas 1\", identified=\"Kelas 1\") → 匹配")
        prompt_parts.append("3. validate_url_quality → YouTube（可信）")
        prompt_parts.append("4. 评分: 3.0 + 3.0 + 2.0 + 1.5 = 9.5")
        prompt_parts.append("5. 推荐理由: \"年级和学科完全匹配（一年级 数学），来自可信平台\"")
        prompt_parts.append("```\n")

        # === 重要注意事项 ===
        prompt_parts.append("## ⚠️ 重要注意事项\n")

        prompt_parts.append("### 年级识别必须准确")
        if country_code == "ID":
            prompt_parts.append("**印尼语年级映射（必须正确识别）**:")
            prompt_parts.append("- Kelas 1 = 一年级 ✅")
            prompt_parts.append("- Kelas 6 = 六年级 ❌（如果目标是一年级）")
            prompt_parts.append("- 不要被标题中的数字迷惑，必须准确提取年级ID\n")

        prompt_parts.append("### 社交媒体内容必须过滤")
        prompt_parts.append("- Facebook, Instagram, Twitter, TikTok, Twitch 等社交媒体内容必须给低分（0-2分）")
        prompt_parts.append("- 即使年级/学科匹配，社交媒体也不适合作为教育资源\n")

        prompt_parts.append("### 推荐理由必须实事求是")
        prompt_parts.append("- 如果年级不匹配，必须明确说明\"年级不符\"")
        prompt_parts.append("- 不要说\"年级正确\"但实际不匹配")
        prompt_parts.append("- 推荐理由要与评分一致\n")

        # 组合所有部分
        full_prompt = "\n".join(prompt_parts)

        logger.info(f"已构建Agent系统提示词 [{country_code}]: {len(full_prompt)} 字符")

        return full_prompt

    except Exception as e:
        logger.error(f"构建Agent系统提示词失败：{str(e)}")
        return f"# 错误\n\n无法构建系统提示词: {str(e)}"


async def build_scoring_context(
    country_code: str,
    target_grade: str,
    target_subject: str,
    search_query: str
) -> str:
    """
    构建评分任务的上下文信息

    Args:
        country_code: 国家代码
        target_grade: 目标年级
        target_subject: 目标学科
        search_query: 搜索查询

    Returns:
        评分任务上下文字符串
    """
    try:
        # 获取系统提示词
        system_prompt = await build_agent_system_prompt(country_code)

        # 构建任务特定上下文
        task_context = f"""

## 当前评分任务

**目标年级**: {target_grade}
**目标学科**: {target_subject}
**搜索查询**: {search_query}

请根据以上系统提示词中的流程，对搜索结果进行评分和推荐理由生成。
"""

        return system_prompt + task_context

    except Exception as e:
        logger.error(f"构建评分上下文失败：{str(e)}")
        return f"错误：{str(e)}"


def build_tools_documentation() -> str:
    """
    构建MCP工具的使用文档（供Agent参考）

    Returns:
        工具使用文档字符串
    """
    doc = """# MCP工具使用文档

## 可用工具列表

### 1. read_country_config
读取国家教育配置

**参数**:
- country_code: 国家代码（如 ID, SA, CN）

**返回**:
- grades: 年级列表
- subjects: 学科列表
- grade_patterns: 年级匹配模式
- subject_patterns: 学科匹配模式

**示例**:
```python
result = await read_country_config("ID")
grades = result["data"]["grades"]
```

### 2. extract_grade_from_title
从标题中提取年级信息

**参数**:
- title: 资源标题
- country_code: 国家代码

**返回**:
- grade_id: 年级ID
- grade_name: 中文名称
- local_name: 本地名称
- confidence: 置信度

**示例**:
```python
result = await extract_grade_from_title("Matematika Kelas 1 SD", "ID")
grade_id = result["data"]["grade_id"]  # "1"
```

### 3. extract_subject_from_title
从标题中提取学科信息

**参数**:
- title: 资源标题
- country_code: 国家代码

**返回**:
- subject_id: 学科ID
- subject_name: 中文名称
- local_name: 本地名称
- confidence: 置信度

**示例**:
```python
result = await extract_subject_from_title("Matematika Kelas 1", "ID")
subject_id = result["data"]["subject_id"]  # "math"
```

### 4. validate_grade_match
验证年级是否匹配

**参数**:
- target_grade: 目标年级
- identified_grade: 识别出的年级
- country_code: 国家代码

**返回**:
- match: 是否匹配
- confidence: 置信度
- reason: 匹配/不匹配的原因

**示例**:
```python
result = await validate_grade_match("Kelas 1", "Kelas 6", "ID")
is_match = result["data"]["match"]  # False
```

### 5. validate_url_quality
验证URL来源质量

**参数**:
- url: 资源URL
- title: 资源标题（可选）

**返回**:
- quality: 质量等级 (high/medium/low)
- reason: 原因
- filter: 是否应该过滤
- score_adjustment: 分数调整值

**示例**:
```python
result = await validate_url_quality("https://www.youtube.com/watch?v=xxx", "Math Tutorial")
quality = result["data"]["quality"]  # "high"
```

### 6. record_pattern_learning
记录新学到的模式

**参数**:
- country_code: 国家代码
- pattern_type: 模式类型 ("grade" 或 "subject")
- local_expression: 本地表达
- standard_name: 标准中文名
- source: 来源
- confidence: 置信度 (0-1)

**返回**:
- pattern_id: 模式ID
- status: 状态

**示例**:
```python
result = await record_pattern_learning("ID", "grade", "Kelas 1", "一年级", "llm_extraction", 0.9)
```

### 7. list_learned_patterns
列出已学习的模式

**参数**:
- country_code: 国家代码（可选）
- pattern_type: 模式类型（可选）
- status: 状态（可选）
- limit: 最大数量

**返回**:
- 模式列表

**示例**:
```python
result = await list_learned_patterns("ID", "grade", "verified")
patterns = result["data"]
```

### 8. verify_pattern
验证学到的模式

**参数**:
- pattern_id: 模式ID
- verified: 是否验证通过
- country_code: 国家代码（可选）
- pattern_type: 模式类型（可选）

**返回**:
- status: 更新后的状态

**示例**:
```python
result = await verify_pattern("pattern_xxx", True)
```
"""

    return doc
