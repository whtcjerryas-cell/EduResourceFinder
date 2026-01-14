# feat: AI驱动的通用多国教育资源搜索系统

## 🎯 核心目标

建立一个**通用的、可扩展的**多国教育资源搜索系统，使用AI动态适配不同国家的教育系统，而不依赖预配置的规则。

### 关键特性

- ✅ **通用性**：支持任何国家/地区（印尼、沙特、中国、美国等）
- ✅ **准确性**：LLM理解当地教育术语、主流平台、课程标准
- ✅ **简洁性**：~200行代码，2个核心函数，简单prompt工程
- ✅ **可维护**：不需要维护100+个国家的配置文件

### 与之前方案的区别

| 维度 | Agent-Native方案 | 通用规则方案 | **AI驱动方案（本方案）** |
|------|-----------------|-------------|----------------------|
| 架构复杂度 | 5层、5个组件 | 硬编码规则 | **2个函数** |
| 代码量 | ~3000行 | ~500行 | **~200行** |
| 扩展性 | 需要训练 | 需要配置 | **开箱即用** |
| 维护成本 | 需要专家团队 | 需要更新配置 | **零维护** |
| 实施时间 | 6-8周 | 2-3周 | **1-2周** |

---

## 💡 设计思路

### 核心洞察

**为什么用AI？**

传统方法需要为每个国家配置：
```python
# ❌ 传统方法：需要大量配置
country_configs = {
    'ID': {
        'grade_1': 'SD Kelas 1',
        'math': 'Matematika',
        'curriculum': 'Kurikulum Merdeka',
        'platforms': ['ruangguru.com', 'youtube.com'],
        'search_queries': [...]
    },
    'SA': {
        'grade_1': 'الصف الأول',
        'math': 'الرياضيات',
        'curriculum': '؟',
        'platforms': ['؟'],
        'search_queries': [...]
    },
    'CN': {
        'grade_1': '一年级',
        'math': '数学',
        'curriculum': '义务教育课程标准',
        'platforms': [...],
        'search_queries': [...]
    },
    # ... 需要维护200+个国家
}
```

**AI驱动方法**：
```python
# ✅ AI方法：只需要国家代码
def search_education_resources(country, grade, subject):
    # 1. LLM生成本地化查询
    queries = llm_generate_localized_queries(country, grade, subject)

    # 2. 搜索引擎获取结果
    results = search_engines.search(queries)

    # 3. LLM评估本地化质量
    ranked = llm_score_localized_results(country, grade, subject, results)

    return ranked
```

### 为什么这样设计？

1. **LLM已经学习了各国教育系统**
   - 训练数据包含印尼的SD、沙特的、中国的义务教育
   - 比人工规则更全面、更准确

2. **不需要维护配置**
   - 新增国家（如南非）→ 只需传入`country='ZA'`
   - LLM自动知道南非的教育术语

3. **更好的准确性**
   - LLM理解文化细微差异
   - 能识别当地主流教育平台
   - 能根据当地课程标准评分

---

## 🏗️ 架构设计

### 系统架构（简化版）

```
┌─────────────────────────────────────────────────────────┐
│                    用户搜索请求                          │
│              country=ID, grade=1, subject=math           │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              1. LocalizedQueryGenerator                  │
│         使用LLM生成本地化搜索查询（2-5秒）                │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ├─→ "Matematika SD Kelas 1 Kurikulum Merdeka"
                          ├─→ "Ruangguru Matematika Kelas 1"
                          └─→ "belajar matematika kelas 1 sd"
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              2. MultiSearchEngine                         │
│          调用Google/Baidu/Tavily并行搜索（5-10秒）          │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ├─→ Ruangguru课程
                          ├─→ YouTube播放列表
                          └─→ 其他资源
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              3. LocalizedResultScorer                    │
│       使用LLM根据本地标准评估质量（3-5秒/资源，并行）        │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   返回排序后的结果                         │
│      Ruangguru课程(9.2分) > YouTube播放列表(8.7分)        │
└─────────────────────────────────────────────────────────┘
```

### 核心组件（仅2个）

#### 组件1：LocalizedQueryGenerator

**功能**：使用LLM生成本地化搜索查询

**输入**：
```python
{
    'country': 'ID',      # 国家代码
    'grade': 'Kelas 1',   # 年级
    'subject': 'Matematika',  # 学科
    'language': 'id'      # 可选，指定语言
}
```

**输出**：
```python
{
    'queries': [
        'Matematika SD Kelas 1 Kurikulum Merdeka',
        'Ruangguru Matematika Kelas 1 SD',
        'belajar matematika kelas 1 sd playlist',
        'video matematika kelas 1 bilangan cacah'
    ],
    'localized_terms': {
        'grade': 'SD Kelas 1',
        'subject': 'Matematika',
        'curriculum': 'Kurikulum Merdeka',
        'major_platforms': ['Ruangguru', 'YouTube', 'Zenius']
    },
    'reasoning': '印尼小学称为SD，一年级称为Kelas 1...'
}
```

**LLM Prompt**（简化版）：
```python
prompt = f"""你是{country}的教育搜索专家。

请为以下搜索生成本地化查询：
- 国家：{country}
- 年级：{grade}
- 学科：{subject}

要求：
1. 使用当地语言（如印尼语、阿拉伯语、中文）
2. 包含当地教育术语（如SD、Grade 1、一年级）
3. 提及主流教育平台（如Ruangguru、）
4. 参考当地课程标准（如Kurikulum Merdeka）

返回3-5个查询，每行一个。"""
```

#### 组件2：LocalizedResultScorer

**功能**：使用LLM根据本地标准评估资源质量

**输入**：
```python
{
    'country': 'ID',
    'grade': 'Kelas 1',
    'subject': 'Matematika',
    'result': {
        'title': 'Matematika Kelas 1 Kurikulum Merdeka',
        'url': 'https://app.ruangguru.com/...',
        'description': '...'
    }
}
```

**输出**：
```python
{
    'overall_score': 9.2,
    'relevance_score': 9.5,
    'quality_score': 9.0,
    'reasoning': '符合Kurikulum Merdeka大纲，来自主流平台Ruangguru...',
    'recommendation': '强烈推荐'
}
```

**LLM Prompt**（简化版）：
```python
prompt = f"""你是{country}的教育内容评估专家。

请评估以下教育资源是否适合当地{grade}年级{subject}学习：

- 标题：{title}
- 网址：{url}
- 描述：{description}

评估维度（0-10分）：
1. **相关性**：是否匹配当地年级和课程标准
2. **质量**：内容质量、教学水平、适合儿童
3. **本地化**：是否使用当地语言、符合当地文化

返回JSON：
{{
    "overall_score": 9.2,
    "relevance_score": 9.5,
    "quality_score": 9.0,
    "reasoning": "符合Kurikulum Merdeka...",
    "recommendation": "强烈推荐"
}}"""
```

---

## 📝 实现细节

### 文件1：localized_query_generator.py

```python
# core/localized_query_generator.py
"""
使用LLM生成本地化教育搜索查询
"""

import json
from typing import Dict, List
from llm_client import get_llm_client

class LocalizedQueryGenerator:
    """本地化查询生成器"""

    def __init__(self):
        self.llm = get_llm_client()
        self.cache = {}  # 简单的内存缓存

    def generate_queries(
        self,
        country: str,
        grade: str,
        subject: str,
        num_queries: int = 5
    ) -> Dict:
        """
        生成本地化搜索查询

        Args:
            country: 国家代码（ID, SA, CN, US等）
            grade: 年级（1, Grade 1, 一年级等）
            subject: 学科（math, 数学, Matematika等）
            num_queries: 生成查询数量

        Returns:
            {
                'queries': [...],
                'localized_terms': {...},
                'reasoning': '...'
            }
        """

        # 检查缓存
        cache_key = f"{country}:{grade}:{subject}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # 构建prompt
        prompt = self._build_prompt(country, grade, subject, num_queries)

        # 调用LLM
        response = self.llm.generate(
            prompt=prompt,
            temperature=0.3,  # 低温度保证稳定性
            max_tokens=1000
        )

        # 解析响应
        result = self._parse_response(response, country)

        # 缓存结果
        self.cache[cache_key] = result

        return result

    def _build_prompt(
        self,
        country: str,
        grade: str,
        subject: str,
        num_queries: int
    ) -> str:
        """构建LLM prompt"""

        return f"""你是{country}国家的教育搜索专家，熟悉当地教育体系和主流教育平台。

请为以下搜索请求生成本地化的搜索查询：

**搜索信息**：
- 国家：{country}
- 年级：{grade}
- 学科：{subject}

**要求**：
1. **使用当地语言**：如印尼语、阿拉伯语、中文、英语等
2. **包含当地教育术语**：
   - 印尼：SD（小学）、Kelas 1（一年级）、Matematika（数学）
   - 沙特：الصف الأول（一年级）、الرياضيات（数学）
   - 中国：小学一年级、数学
3. **提及主流平台**：如Ruangguru、YouTube、本地教育平台
4. **参考课程标准**：如Kurikulum Merdeka（印尼）、义务教育课标（中国）
5. **优化搜索类型**：添加"playlist"、"kursus lengkap"等

请生成{num_queries}个优化的搜索查询，每行一个。

**输出格式**（JSON）：
{{
    "queries": [
        "查询1",
        "查询2",
        ...
    ],
    "localized_terms": {{
        "grade": "当地年级表达",
        "subject": "当地学科表达",
        "curriculum": "当地课程标准",
        "major_platforms": ["平台1", "平台2"]
    }},
    "reasoning": "为什么选择这些查询和术语"
}}

只返回JSON，不要包含其他文字。"""

    def _parse_response(self, response: str, country: str) -> Dict:
        """解析LLM响应"""

        try:
            # 提取JSON
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_text = response[json_start:json_end]

            result = json.loads(json_text)

            # 验证必需字段
            if 'queries' not in result or 'localized_terms' not in result:
                raise ValueError("Missing required fields")

            return result

        except Exception as e:
            # 降级方案：返回通用查询
            print(f"⚠️ LLM解析失败: {e}, 使用降级方案")
            return self._get_fallback_queries(country)

    def _get_fallback_queries(self, country: str) -> Dict:
        """降级方案：返回通用查询"""

        # 简单的映射表（仅用于降级）
        fallback_map = {
            'ID': ['Matematika SD Kelas 1', 'belajar matematika kelas 1'],
            'SA': ['تعلم الرياضيات للصف الأول', 'الرياضيات الصف الأول'],
            'CN': ['小学一年级数学', '一年级数学课程'],
            'US': ['Grade 1 math', 'first grade math lessons']
        }

        queries = fallback_map.get(country, ['Grade 1 math', 'mathematics grade 1'])

        return {
            'queries': queries,
            'localized_terms': {},
            'reasoning': 'Fallback: 使用预定义查询'
        }
```

### 文件2：localized_result_scorer.py

```python
# core/localized_result_scorer.py
"""
使用LLM根据本地标准评估教育资源质量
"""

import json
from typing import Dict, List
from llm_client import get_llm_client

class LocalizedResultScorer:
    """本地化结果评分器"""

    def __init__(self):
        self.llm = get_llm_client()
        self.cache = {}  # 简单的内存缓存

    def score_results(
        self,
        country: str,
        grade: str,
        subject: str,
        results: List[Dict],
        max_results: int = 20
    ) -> List[Dict]:
        """
        批量评分搜索结果

        Args:
            country: 国家代码
            grade: 年级
            subject: 学科
            results: 搜索结果列表
            max_results: 最多评分结果数

        Returns:
            评分后的结果列表（按分数降序）
        """

        # 只评分前N个结果
        results_to_score = results[:max_results]

        # 并行评分（如果可能）
        scored_results = []
        for result in results_to_score:
            score_data = self.score_single_result(
                country, grade, subject, result
            )
            result.update(score_data)
            scored_results.append(result)

        # 按分数排序
        scored_results.sort(
            key=lambda x: x.get('overall_score', 0),
            reverse=True
        )

        return scored_results

    def score_single_result(
        self,
        country: str,
        grade: str,
        subject: str,
        result: Dict
    ) -> Dict:
        """评分单个结果"""

        # 检查缓存（基于URL）
        url = result.get('url', '')
        if url in self.cache:
            return self.cache[url]

        # 构建prompt
        prompt = self._build_prompt(
            country, grade, subject, result
        )

        # 调用LLM
        try:
            response = self.llm.generate(
                prompt=prompt,
                temperature=0.2,  # 低温度保证一致性
                max_tokens=800
            )

            # 解析响应
            score_data = self._parse_response(response)

        except Exception as e:
            print(f"⚠️ LLM评分失败: {e}, 使用规则评分")
            score_data = self._rule_based_score(result, country)

        # 缓存结果
        self.cache[url] = score_data

        return score_data

    def _build_prompt(
        self,
        country: str,
        grade: str,
        subject: str,
        result: Dict
    ) -> str:
        """构建评分prompt"""

        title = result.get('title', '')
        url = result.get('url', '')
        description = result.get('description', '')

        return f"""你是{country}国家的教育内容评估专家，熟悉当地教育体系和课程标准。

请评估以下教育资源是否适合当地{grade}年级{subject}学习：

**资源信息**：
- 标题：{title}
- 网址：{url}
- 描述：{description}

**评估维度**（0-10分，保留一位小数）：

1. **相关性**（relevance_score）：
   - 是否匹配当地年级和课程标准
   - 内容是否适合目标年龄段
   - 学科内容是否准确

2. **质量**（quality_score）：
   - 教学方法是否适合儿童
   - 内容质量（画质、音频、讲解）
   - 教育价值

3. **本地化**（localization_score）：
   - 是否使用当地语言
   - 是否符合当地文化
   - 是否引用当地课程

**整体评分**（overall_score）：
- 相关性 50% + 质量 30% + 本地化 20%

**推荐意见**（recommendation）：
- 9.0-10.0: "强烈推荐"
- 7.5-8.9: "推荐"
- 6.0-7.4: "可以考虑"
- <6.0: "不推荐"

请返回JSON：
{{
    "overall_score": 9.2,
    "relevance_score": 9.5,
    "quality_score": 9.0,
    "localization_score": 8.8,
    "reasoning": "简要说明评分理由（50字内）",
    "recommendation": "强烈推荐"
}}

只返回JSON，不要包含其他文字。"""

    def _parse_response(self, response: str) -> Dict:
        """解析LLM响应"""

        try:
            # 提取JSON
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_text = response[json_start:json_end]

            return json.loads(json_text)

        except Exception as e:
            raise ValueError(f"JSON解析失败: {e}")

    def _rule_based_score(self, result: Dict, country: str) -> Dict:
        """降级方案：规则评分"""

        url = result.get('url', '').lower()
        title = result.get('title', '').lower()

        score = 5.0  # 基础分

        # 域名加分
        if 'ruangguru.com' in url and country == 'ID':
            score += 3.0
        elif 'youtube.com' in url:
            score += 2.0
        elif 'khanacademy.org' in url:
            score += 2.5

        # 关键词加分
        if 'kurikulum merdeka' in title and country == 'ID':
            score += 1.5

        # 归一化
        score = min(score, 10.0)

        return {
            'overall_score': score,
            'relevance_score': score,
            'quality_score': score,
            'localization_score': score,
            'reasoning': 'Rule-based scoring',
            'recommendation': '推荐' if score >= 7.0 else '可以考虑'
        }
```

### 文件3：ai_search_coordinator.py

```python
# core/ai_search_coordinator.py
"""
AI驱动的通用搜索协调器
"""

from localized_query_generator import LocalizedQueryGenerator
from localized_result_scorer import LocalizedResultScorer
from search_engine_v2 import MultiSearchEngine

class AISearchCoordinator:
    """AI搜索协调器"""

    def __init__(self):
        self.query_gen = LocalizedQueryGenerator()
        self.result_scorer = LocalizedResultScorer()
        self.search_engine = MultiSearchEngine()

    def search(
        self,
        country: str,
        grade: str,
        subject: str,
        max_results: int = 20
    ) -> Dict:
        """
        执行AI驱动的搜索

        Args:
            country: 国家代码（ID, SA, CN, US等）
            grade: 年级
            subject: 学科
            max_results: 返回结果数

        Returns:
            {
                'results': [...],
                'localized_info': {...},
                'search_metadata': {...}
            }
        """

        print(f"\n🔍 AI驱动搜索: {country} - {grade} - {subject}")

        # 步骤1：生成本地化查询
        print("📝 步骤1: 生成本地化查询...")
        query_result = self.query_gen.generate_queries(
            country=country,
            grade=grade,
            subject=subject,
            num_queries=5
        )

        queries = query_result['queries']
        localized_terms = query_result['localized_terms']

        print(f"  ✅ 生成{len(queries)}个查询:")
        for q in queries:
            print(f"     - {q}")

        print(f"  📚 本地化术语: {localized_terms}")

        # 步骤2：并行搜索
        print("\n🌐 步骤2: 并行搜索...")
        all_results = []

        for query in queries:
            results = self.search_engine.search(query, country=country)
            all_results.extend(results)
            print(f"  ✅ '{query}' → 找到{len(results)}个结果")

        # 去重
        all_results = self._deduplicate_results(all_results)
        print(f"  📊 去重后: {len(all_results)}个结果")

        # 步骤3：本地化评分
        print("\n⭐ 步骤3: 本地化评分...")
        scored_results = self.result_scorer.score_results(
            country=country,
            grade=grade,
            subject=subject,
            results=all_results,
            max_results=max_results
        )

        # 返回前N个
        final_results = scored_results[:max_results]

        print(f"  ✅ 返回前{len(final_results)}个结果")

        # 返回完整结果
        return {
            'results': final_results,
            'localized_info': {
                'country': country,
                'grade': localized_terms.get('grade', grade),
                'subject': localized_terms.get('subject', subject),
                'curriculum': localized_terms.get('curriculum', 'N/A'),
                'major_platforms': localized_terms.get('major_platforms', [])
            },
            'search_metadata': {
                'queries_used': queries,
                'total_found': len(all_results),
                'top_score': final_results[0]['overall_score'] if final_results else 0
            }
        }

    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """去重（基于URL）"""

        seen_urls = set()
        unique_results = []

        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)

        return unique_results
```

---

## 🚀 实施计划

### Week 1: 核心功能开发

**Day 1-2: LocalizedQueryGenerator**
- [ ] 实现查询生成器（100行）
- [ ] 编写LLM prompt
- [ ] 添加降级方案（预定义查询映射）
- [ ] 测试印尼、沙特、中国、美国

**Day 3-4: LocalizedResultScorer**
- [ ] 实现评分器（100行）
- [ ] 编写评分prompt
- [ ] 添加规则评分降级
- [ ] 测试准确性

**Day 5: AISearchCoordinator**
- [ ] 实现协调器（50行）
- [ ] 集成查询生成、搜索、评分
- [ ] 添加去重逻辑
- [ ] 端到端测试

### Week 2: 测试和优化

**Day 1-2: 多国测试**
- [ ] 测试印尼：搜索"印尼一年级数学"
- [ ] 测试沙特：搜索"沙特一年级数学"
- [ ] 测试中国：搜索"中国一年级数学"
- [ ] 测试美国：搜索"美国一年级数学"

**Day 3-4: 性能优化**
- [ ] 添加缓存（查询缓存、评分缓存）
- [ ] 并行化LLM调用
- [ ] 优化prompt（减少token）
- [ ] 性能测试（目标<15秒）

**Day 5: 文档和部署**
- [ ] 编写使用文档
- [ ] 添加示例代码
- [ ] 部署到测试环境
- [ ] 监控和日志

---

## ✅ 验收标准

### 功能验收

- [ ] 支持至少5个国家（印尼、沙特、中国、美国、印度）
- [ ] 搜索准确率>80%（前10个结果中至少8个相关）
- [ ] 评分准确率>85%（与人工评估对比）
- [ ] 降级方案可用（LLM失败时使用规则）

### 性能验收

- [ ] 端到端搜索时间<15秒
- [ ] 查询生成<5秒
- [ ] 结果评分<10秒（20个结果）
- [ ] 缓存命中率>50%

### 质量验收

- [ ] LLM prompt经过优化（<200 tokens）
- [ ] 降级方案覆盖主流国家
- [ ] 错误处理完善
- [ ] 日志和监控完整

---

## 🎯 成功指标

| 指标 | 目标 | 测量方法 |
|------|------|----------|
| 覆盖国家数 | 10+ | 支持的国家代码 |
| 搜索准确率 | >80% | 人工评估前10结果 |
| 评分准确率 | >85% | 与人工评分对比 |
| 响应时间 | <15秒 | 端到端计时 |
| 缓存命中率 | >50% | 重复查询统计 |
| 降级可用性 | 100% | LLM失败时仍可用 |

---

## 💰 成本分析

### LLM调用成本

**假设使用Gemini 2.5 Pro**：
- 输入：$0.50 / 1M tokens
- 输出：$1.50 / 1M tokens

**单次搜索成本**：
```
查询生成：500 input + 300 output = 800 tokens
结果评分：20结果 × 600 input + 200 output = 16,000 tokens
总计：16,800 tokens

成本：(800 + 16000) × $1.0 / 1M ≈ $0.017 / 搜索
```

**月度成本**（假设1000次搜索/月）：
```
1000 × $0.017 = $17 / 月
```

**年度成本**：
```
$17 × 12 = $204 / 年
```

### 与规则方案对比

| 维度 | 规则方案 | AI方案 |
|------|---------|--------|
| 初始成本 | 2-3周开发 | 1-2周开发 |
| 维护成本 | 每新增国家需要配置 | 零维护 |
| 运行成本 | $0 | $200/年 |
| 覆盖范围 | 仅配置的国家 | 任何国家 |

**结论**：AI方案在覆盖范围和维护成本上有明显优势。

---

## 🔧 优化策略

### 1. 缓存策略

**查询缓存**：
```python
# 相同的国家/年级/学科使用缓存
cache_key = f"{country}:{grade}:{subject}"
if cache_key in cache:
    return cache[cache_key]
```

**评分缓存**：
```python
# 相同的URL使用缓存
if url in score_cache:
    return score_cache[url]
```

**预期效果**：
- 缓存命中率>50%
- 平均响应时间减少40%

### 2. Prompt优化

**当前prompt**：~300 tokens

**优化后**：~150 tokens
- 移除冗余说明
- 使用简洁的指令
- 合并相似要求

**预期效果**：
- Token使用减少50%
- 成本降低50%
- 响应速度提升30%

### 3. 并行化

**当前**：串行评分20个结果（20 × 5秒 = 100秒）

**优化后**：并行评分（5秒）

**实现**：
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [
        executor.submit(score_single_result, r)
        for r in results
    ]
    scored = [f.result() for f in futures]
```

**预期效果**：
- 评分时间：100秒 → 10秒
- 端到端时间：120秒 → 15秒

---

## 🚨 风险和缓解

### 风险1：LLM幻觉

**风险**：LLM生成错误的本地化术语

**缓解**：
- 设置低温度（temperature=0.2-0.3）
- 提供示例引导正确输出
- 验证输出格式（JSON解析）
- 降级方案（预定义映射表）

### 风险2：成本失控

**风险**：大量搜索导致LLM成本过高

**缓解**：
- 实施缓存策略（命中率>50%）
- 限制评分数量（最多20个结果）
- 设置月度预算上限
- 监控成本使用情况

### 风险3：性能问题

**风险**：LLM调用导致搜索缓慢

**缓解**：
- 并行化LLM调用
- 使用快速模型（如Gemini 2.5 Flash）
- 实施渐进式评分（先评分前10个）
- 提供降级方案（规则评分）

---

## 📚 参考资料

### LLM Prompt工程

- [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)
- [Google Prompting Guidelines](https://ai.google.dev/docs/prompt_best_practices)

### 教育系统参考

- 印尼：Kurikulum Merdeka
- 沙特：المنهج الدراسي
- 中国：义务教育课程标准
- 美国：Common Core State Standards

### 技术实现

- 现有LLM客户端：`llm_client.py`
- 搜索引擎：`search_engine_v2.py`
- 结果评分：`result_scorer.py`

---

## 🎓 后续改进

### 短期（1个月）

- [ ] 添加用户反馈机制（👍/👎）
- [ ] 基于反馈优化prompt
- [ ] 扩展到更多学科（物理、化学、生物）
- [ ] 支持更多年级（幼儿园到高中）

### 中期（3个月）

- [ ] 实现个性化推荐（基于用户历史）
- [ ] 添加内容质量检测（视频质量、更新频率）
- [ ] 集成更多教育平台API
- [ ] 支持混合语言搜索（如中英混合）

### 长期（6个月）

- [ ] 建立教育资源知识图谱
- [ ] 实现智能问答（基于搜索结果）
- [ ] 添加学习路径推荐
- [ ] 支持教师协作和分享

---

## 💡 关键洞察

### 为什么AI驱动是正确的选择？

1. **通用性**：
   - 不需要为每个国家配置规则
   - LLM已经学习了各国教育系统
   - 新增国家只需传入国家代码

2. **准确性**：
   - LLM理解文化细微差异
   - 能识别当地主流平台
   - 能根据当地标准评分

3. **简洁性**：
   - ~200行核心代码
   - 2个主要组件
   - 简单的prompt工程

4. **可维护性**：
   - 不需要维护配置文件
   - 不需要更新规则
   - LLM升级自动获得改进

### 与Agent-Native方案的区别

| 维度 | Agent-Native | AI驱动方案 |
|------|-------------|-----------|
| 复杂度 | 5层架构、自我优化 | 2个函数、简单prompt |
| 代码量 | ~3000行 | ~200行 |
| 实施时间 | 6-8周 | 1-2周 |
| 维护成本 | 需要专家团队 | 零维护 |
| 可扩展性 | 需要训练 | 开箱即用 |

**结论**：AI驱动方案在保持简洁性的同时，提供了更好的通用性和可扩展性。

---

**文档版本**: 1.0
**创建日期**: 2026-01-11
**预计工作量**: 1-2周
**优先级**: 🔥 HIGH（通用解决方案）
