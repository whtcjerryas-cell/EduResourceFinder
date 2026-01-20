# Search Engine V2 优化方案

**创建时间**: 2026-01-20
**目标**: 简化搜索流程，提高搜索质量，减少API调用成本
**当前问题**: 7个查询 → 124个结果 → 仅保留20个（浪费资源）

---

## 📊 当前实现分析

### 搜索流程概览

```
[用户请求]
    ↓
[Step 0] 生成搜索策略 (2-5秒，LLM调用)
    - 生成5-7个高度差异化的搜索词
    - 确定搜索语言、平台、优先域名
    ↓
[Step 1] 选择第一个搜索词
    ↓
[Step 2] 并行搜索 (60-120秒)
    - 5x Tavily/Metaso搜索 (每个查询30结果) = 150结果
    - 1x Google搜索 (第一个查询20结果) = 20结果
    - 1x Baidu搜索 (如果中文，30结果) = 30结果
    - 1x 本地定向搜索 (20结果) = 20结果
    - 合计: ~220个原始结果
    ↓
[Step 3] URL去重
    - ~124个去重后结果
    ↓
[Step 4] 评分排序
    - 规则评分 (1-2秒)
    - LLM评分 (10-20秒)
    ↓
[Step 5] 返回前20个高质量结果
```

### 核心问题

| 问题 | 影响 | 严重程度 |
|------|------|----------|
| **过度搜索** | 7次API调用获取220结果，仅保留20个 | 🔴 高 |
| **语义重复** | 5个查询尽管"差异化"但仍高度重叠 | 🟡 中 |
| **资源浪费** | API成本浪费83% (220→20) | 🔴 高 |
| **响应慢** | 60-120秒用户体验差 | 🟡 中 |
| **逻辑复杂** | 7路并行搜索难以调试维护 | 🟡 中 |
| **质量波动** | 当所有结果质量低时无降级策略 | 🔴 高 |

### 性能数据

**当前实现**:
- 搜索次数: 7次并行
- 原始结果: 220个
- 去重后: 124个
- 最终返回: 20个
- 保留率: 16% (20/124)
- 浪费率: 84%
- 响应时间: 60-120秒
- API成本: 7x

---

## 🎯 优化目标

1. **简化流程**: 减少7次搜索到1-3次
2. **提高质量**: 保持或提升结果相关性
3. **降低成本**: 减少83%的API调用
4. **加快速度**: 目标响应时间 < 30秒
5. **质量保障**: 低质量结果的降级策略

---

## 📋 优化方案对比

### 方案一：渐进式搜索（推荐 ⭐⭐⭐⭐⭐）

**核心理念**: 从少到多，按需扩展

#### 实现逻辑

```
[用户请求]
    ↓
[Step 1] 高质量查询生成 (2-3秒)
    - 使用LLM生成1个最优查询（而非5-7个）
    - 包含: "playlist" + "subject" + "grade" + "country"
    ↓
[Step 2] 初始搜索 (15-20秒) ⚡
    - 1x Tavily/Metaso (30结果)
    - 使用最优查询
    ↓
[Step 3] 快速质量评估 (3-5秒)
    - 使用规则评分（不含LLM）
    - 计算前10个结果的平均分
    ↓
[质量判断]
    ├─ 高质量 (平均分 > 7.0)
    │   └─ 直接返回前20个 ✅ (总耗时: ~25秒)
    │
    ├─ 中等质量 (5.0 - 7.0)
    │   └─ [Step 4] 补充搜索 (+15秒)
    │       - 1x Google (20结果)
    │       - 使用相同查询
    │       - 合并后重新评分
    │       - 返回前20个 ✅ (总耗时: ~43秒)
    │
    └─ 低质量 (< 5.0)
        └─ [Step 5] 查询重试 (+20秒)
            - 使用不同关键词重新生成查询
            - 重新搜索1次 (Tavily/Metaso)
            - 重新评分
            - 返回前20个 ✅ (总耗时: ~48秒)
```

#### 伪代码

```python
def incremental_search(request):
    # Step 1: 生成最优查询
    query = strategy_agent.generate_best_query(
        country=request.country,
        grade=request.grade,
        subject=request.subject
    )  # 2-3秒

    # Step 2: 初始搜索
    results = llm_client.search(
        query=query,
        max_results=30,
        engine="tavily"  # 或 metaso
    )  # 15-20秒

    # Step 3: 快速质量评估
    scored = rule_scorer.score_results(results, query)[:10]
    avg_score = sum(r['score'] for r in scored) / len(scored)

    # Step 4-5: 根据质量决定是否补充搜索
    if avg_score > 7.0:
        # 高质量，直接返回
        return scored[:20]
    elif avg_score > 5.0:
        # 中等质量，补充搜索
        google_results = google_hunter.search(query, max_results=20)
        all_results = deduplicate(results + google_results)
        return rule_scorer.score_results(all_results, query)[:20]
    else:
        # 低质量，查询重试
        retry_query = strategy_agent.generate_alternative_query(request)
        retry_results = llm_client.search(retry_query, max_results=30)
        return rule_scorer.score_results(retry_results, retry_query)[:20]
```

#### 优点
✅ **API成本降低**: 1-2次调用（当前7次）
✅ **平均响应快**: 25秒（当前60-120秒）
✅ **质量自适应**: 根据质量动态调整
✅ **实现简单**: 最小代码改动
✅ **易于调试**: 单线程流程清晰

#### 缺点
⚠️ 最坏情况略慢: 48秒（但比当前60-120秒仍快）
⚠️ 需要准确的质量阈值

#### 适用场景
- 90%的正常搜索请求
- 对响应时间敏感的场景
- API预算有限的情况

---

### 方案二：智能查询融合（推荐 ⭐⭐⭐⭐）

**核心理念**: 保留查询多样性，但减少搜索次数

#### 实现逻辑

```
[用户请求]
    ↓
[Step 1] 生成3个查询变体 (2-3秒)
    - Query 1: 播放列表查询 (playlist + subject + grade)
    - Query 2: 常规查询 (subject + grade + video lesson)
    - Query 3: 本地化查询 (subject + grade + 本地语言关键词)
    ↓
[Step 2] 智能搜索选择 (5-30秒)
    - 根据国家/语言自动选择最优引擎
    - 中文 → Google + Baidu
    - 英语 → Google + Metaso
    - 其他 → Tavily + Google
    ↓
[Step 3] 融合去重 (2-3秒)
    - 使用RRF (Reciprocal Rank Fusion)融合结果
    - URL去重
    ↓
[Step 4] 评分排序 (1-2秒)
    - 规则评分
    - 返回前20个
```

#### 伪代码

```python
def smart_fusion_search(request):
    # Step 1: 生成3个查询
    queries = strategy_agent.generate_3_queries(request)  # 2-3秒

    # Step 2: 智能引擎选择
    country_config = config_manager.get_country_config(request.country)
    language = country_config.language_code

    if language == 'zh':
        # 中文：Google + Baidu
        results_q1 = google_hunter.search(queries[0], max_results=20)
        results_q2 = baidu_hunter.search(queries[1], max_results=20)
        results_q3 = google_hunter.search(queries[2], max_results=10)
    elif language == 'en':
        # 英语：Google + Metaso
        results_q1 = google_hunter.search(queries[0], max_results=20)
        results_q2 = metaso_client.search(queries[1], max_results=20)
        results_q3 = google_hunter.search(queries[2], max_results=10)
    else:
        # 其他：Tavily + Google
        results_q1 = tavily_client.search(queries[0], max_results=30)
        results_q2 = google_hunter.search(queries[1], max_results=20)
        results_q3 = tavily_client.search(queries[2], max_results=10)

    # Step 3: RRF融合
    all_results = rrf_fuse([
        results_q1, results_q2, results_q3
    ])

    # Step 4: 评分返回
    return rule_scorer.score_results(all_results, query)[:20]
```

#### RRF融合算法

```python
def rrf_fuse(result_lists, k=60):
    """
    Reciprocal Rank Fusion 融合多个搜索结果列表

    Args:
        result_lists: 多个搜索引擎的结果列表
        k: 常数（通常60）

    Returns:
        融合后的排序结果
    """
    scores = {}

    for results in result_lists:
        for rank, result in enumerate(results, 1):
            url = result['url']
            if url not in scores:
                scores[url] = {
                    'result': result,
                    'rrf_score': 0.0
                }
            # RRF公式: 1/(k + rank)
            scores[url]['rrf_score'] += 1.0 / (k + rank)

    # 按RRF分数排序
    sorted_results = sorted(
        scores.values(),
        key=lambda x: x['rrf_score'],
        reverse=True
    )

    return [item['result'] for item in sorted_results]
```

#### 优点
✅ **平衡多样性与效率**: 3个查询覆盖不同场景
✅ **智能引擎选择**: 根据语言自动优化
✅ **RRF融合**: 更科学的排名融合
✅ **API成本降低**: 2-3次调用（当前7次）
✅ **质量稳定**: 多查询保证覆盖率

#### 缺点
⚠️ RRF需要调优k参数
⚠️ 引擎选择逻辑需要维护
⚠️ 代码复杂度中等

#### 适用场景
- 需要覆盖多语言市场
- 对结果质量要求高
- 有一定API预算

---

### 方案三：混合评分优化（推荐 ⭐⭐⭐）

**核心理念**: 保留7次搜索，但优化评分质量

#### 实现逻辑

```
[用户请求]
    ↓
[Step 1-2] 保持当前搜索流程
    - 生成5-7个查询
    - 7次并行搜索
    - 获取~124个结果
    ↓
[Step 3] 多级评分漏斗 (15-25秒)
    Level 1: 快速过滤 (1秒)
        - 移除明显无关结果
        - URL黑名单过滤
        - 标题关键词匹配
        → 124 → ~80个结果
    ↓
    Level 2: 规则评分 (2秒)
        - URL质量、标题相关性、来源可信度
        → ~80 → ~40个结果
    ↓
    Level 3: LLM精选评分 (15-20秒)
        - 仅对前40个结果使用LLM深度评分
        - 批量评分（一次API调用）
        → ~40 → 20个最佳结果
    ↓
[Step 4] 返回前20个
```

#### 伪代码

```python
def hybrid_scoring_search(request):
    # Step 1-2: 保持原有搜索逻辑
    queries = strategy_agent.generate_strategy(request).search_queries
    results = parallel_search(queries[:5])  # 7次并行搜索
    results = deduplicate(results)  # ~124个

    # Step 3: 多级评分漏斗

    # Level 1: 快速过滤
    filtered = []
    for r in results:
        # URL黑名单
        if is_blacklisted(r['url']):
            continue
        # 标题关键词匹配（必须包含subject或相关词）
        if not has_relevant_keywords(r['title'], request.subject):
            continue
        filtered.append(r)
    # ~124 → ~80个

    # Level 2: 规则评分
    scored = rule_scorer.score_results(filtered, query)
    scored.sort(key=lambda x: x['score'], reverse=True)
    top_40 = scored[:40]
    # ~80 → ~40个

    # Level 3: LLM精选评分（仅前40个）
    if should_use_llm_scoring(request):
        batch_prompt = build_batch_prompt(top_40, request)
        llm_scores = llm_client.call_llm(
            prompt=batch_prompt,
            max_tokens=8000,
            model="gemini-2.5-flash"
        )
        # 解析LLM评分并合并
        final_results = merge_scores(top_40, llm_scores)
    else:
        final_results = top_40

    return final_results[:20]
```

#### 优点
✅ **最大化利用现有结果**: 不浪费已获取的124个结果
✅ **质量最高**: 多级漏斗保证结果质量
✅ **渐进式成本**: Level 3 LLM评分可选
✅ **灵活控制**: 可根据配置调整各级阈值

#### 缺点
⚠️ API成本仍然高: 7次搜索调用
⚠️ 响应时间仍慢: 75-145秒
⚠️ 复杂度高: 多级过滤逻辑

#### 适用场景
- 对结果质量要求极高
- API预算充足
- 不在意响应时间

---

### 方案四：AsyncIO异步搜索（推荐 ⭐⭐⭐⭐）

**核心理念**: 使用异步I/O加速搜索

#### 实现逻辑

```python
import asyncio
import aiohttp

class AsyncSearchEngine:
    async def search_async(self, query: str, engine: str):
        """异步搜索单个引擎"""
        if engine == "tavily":
            return await self._search_tavily_async(query)
        elif engine == "google":
            return await self._search_google_async(query)
        # ...

    async def parallel_search_async(self, queries: List[str]):
        """并行搜索多个查询"""
        tasks = []
        for query in queries[:3]:  # 只用前3个查询
            # 同时发起Tavily和Google
            tasks.append(self.search_async(query, "tavily"))
            tasks.append(self.search_async(query, "google"))

        # 并行执行，等待所有完成
        results = await asyncio.gather(*tasks)
        return merge_results(results)

    def search(self, request):
        """同步入口"""
        queries = strategy_agent.generate_queries(request)[:3]
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(
            self.parallel_search_async(queries)
        )
        return score_and_filter(results)[:20]
```

#### 性能提升

| 搜索方式 | 并行度 | 耗时 |
|----------|--------|------|
| **当前 (ThreadPool)** | 7个任务 | 60-120秒 |
| **AsyncIO (3查询x2引擎)** | 6个任务 | 20-30秒 |
| **提升** | - | **60-75%** |

#### 优点
✅ **性能最佳**: 异步I/O性能最优
✅ **代码简洁**: Python原生async/await
✅ **资源利用率高**: 非阻塞I/O
✅ **API成本适中**: 3-6次调用

#### 缺点
⚠️ 需要重写搜索客户端为异步
⚠️ 需要处理异步错误
⚠️ 学习曲线

#### 适用场景
- 追求极致性能
- 有Python异步编程经验
- 长期维护的项目

---

### 方案五：缓存优先策略（推荐 ⭐⭐⭐⭐⭐）

**核心理念**: 优先返回缓存结果，按需搜索

#### 实现逻辑

```
[用户请求]
    ↓
[Step 1] 检查L1内存缓存 (5ms)
    - 缓存键: country+grade+subject
    - TTL: 5分钟
    - 如果命中 → 直接返回 ✅
    ↓
[Step 2] 检查L2 Redis缓存 (50ms)
    - TTL: 1小时
    - 如果命中 → 更新L1，返回 ✅
    ↓
[Step 3] 检查L3磁盘缓存 (100ms)
    - TTL: 24小时
    - 如果命中 → 更新L1/L2，返回 ✅
    ↓
[Step 4] 执行实际搜索 (25-48秒)
    - 使用[方案一]渐进式搜索
    - 更新所有缓存层级
    - 返回结果 ✅
```

#### 伪代码

```python
class CachedSearchEngine:
    def __init__(self):
        self.l1_cache = {}  # 内存缓存
        self.l2_cache = Redis()  # Redis缓存
        self.l3_cache = DiskCache()  # 磁盘缓存

    def search(self, request):
        cache_key = f"{request.country}:{request.grade}:{request.subject}"

        # L1: 内存缓存
        if cache_key in self.l1_cache:
            logger.info("[缓存L1] 命中")
            return self.l1_cache[cache_key]

        # L2: Redis缓存
        l2_result = self.l2_cache.get(cache_key)
        if l2_result:
            logger.info("[缓存L2] 命中")
            self.l1_cache[cache_key] = l2_result
            return l2_result

        # L3: 磁盘缓存
        l3_result = self.l3_cache.get(cache_key)
        if l3_result:
            logger.info("[缓存L3] 命中")
            self.l1_cache[cache_key] = l3_result
            self.l2_cache.set(cache_key, l3_result, ttl=3600)
            return l3_result

        # 未命中，执行实际搜索
        logger.info("[缓存未命中] 执行搜索")
        results = self.incremental_search(request)

        # 更新所有缓存层级
        self.l1_cache[cache_key] = results
        self.l2_cache.set(cache_key, results, ttl=300)  # 5分钟
        self.l3_cache.set(cache_key, results, ttl=86400)  # 24小时

        return results
```

#### 缓存命中率预估

| 场景 | 命中率 | 说明 |
|------|--------|------|
| **热门查询** | 80-90% | 如: Indonesia/Kelas 1/Matematika |
| **常规查询** | 40-60% | 相同年级/学科的不同学期 |
| **长尾查询** | 10-20% | 新国家/冷门学科 |

#### 优点
✅ **响应极快**: 缓存命中 < 100ms
✅ **API成本最低**: 80%+请求无需API调用
✅ **用户体验最佳**: 热门内容秒开
✅ **降级友好**: 缓存失败不影响搜索

#### 缺点
⚠️ 需要Redis服务器
⚠️ 缓存更新策略复杂
⚠️ 可能返回过时内容

#### 适用场景
- 有大量重复查询
- 对响应时间要求极高
- 有Redis基础设施

---

## 🎯 低质量结果处理策略

### 检测方法

```python
def detect_low_quality_results(results: List[Dict], request) -> bool:
    """
    检测搜索结果是否整体质量低

    Args:
        results: 评分后的结果列表
        request: 原始请求

    Returns:
        True if low quality, False otherwise
    """
    if not results:
        return True

    # 方法1: 平均分检测
    scores = [r.get('score', 0) for r in results[:20]]
    avg_score = sum(scores) / len(scores)
    if avg_score < 5.0:
        logger.warning(f"[低质量] 平均分 {avg_score:.2f} < 5.0")
        return True

    # 方法2: 高分结果数量检测
    high_score_count = sum(1 for s in scores if s >= 7.0)
    if high_score_count < 3:
        logger.warning(f"[低质量] 高分结果仅 {high_score_count} 个")
        return True

    # 方法3: 标题相关性检测
    relevant_count = 0
    for r in results[:10]:
        title_lower = r.get('title', '').lower()
        if any(keyword in title_lower for keyword in
               [request.subject.lower(), request.grade.lower()]):
            relevant_count += 1

    if relevant_count < 5:
        logger.warning(f"[低质量] 相关标题仅 {relevant_count}/10")
        return True

    return False
```

### 降级策略

#### 策略1: 查询重写

```python
def fallback_query_rewriting(request):
    """降级策略1: 查询重写"""
    logger.warning("[降级] 尝试查询重写...")

    # 原查询
    original_query = f"{request.subject} {request.grade}"

    # 重写选项
    rewrite_options = [
        # 选项1: 使用英文
        f"{translate_to_english(request.subject)} {translate_to_english(request.grade)}",

        # 选项2: 添加"video"关键词
        f"{original_query} video",

        # 选项3: 使用"course"
        f"{original_query} course",

        # 选项4: 移除年级，只用学科
        f"{request.subject}",

        # 选项5: 使用YouTube特定语法
        f"site:youtube.com {original_query}"
    ]

    # 尝试每个重写选项，直到获得高质量结果
    for rewrite_query in rewrite_options:
        logger.info(f"[重试] 使用重写查询: {rewrite_query}")
        results = llm_client.search(rewrite_query, max_results=30)
        scored = rule_scorer.score_results(results, rewrite_query)

        if not detect_low_quality_results(scored, request):
            logger.info(f"[✅ 降级成功] 查询: {rewrite_query}")
            return scored[:20]

    # 所有重写都失败，返回混合结果
    logger.error("[❌ 降级失败] 所有重写查询都失败")
    return merge_all_attempts[:20]
```

#### 策略2: 引擎切换

```python
def fallback_engine_switching(request):
    """降级策略2: 引擎切换"""
    logger.warning("[降级] 尝试引擎切换...")

    query = f"{request.subject} {request.grade}"

    # 尝试不同引擎
    engines = [
        ("Tavily", lambda q: tavily_client.search(q, max_results=30)),
        ("Google", lambda q: google_hunter.search(q, max_results=20)),
        ("Metaso", lambda q: metaso_client.search(q, max_results=20)),
        ("Baidu", lambda q: baidu_hunter.search(q, max_results=30))
    ]

    for engine_name, search_func in engines:
        logger.info(f"[重试] 尝试 {engine_name}...")
        try:
            results = search_func(query)
            scored = rule_scorer.score_results(results, query)

            if not detect_low_quality_results(scored, request):
                logger.info(f"[✅ 降级成功] 引擎: {engine_name}")
                return scored[:20]
        except Exception as e:
            logger.warning(f"[⚠️ {engine_name}] 失败: {e}")

    logger.error("[❌ 降级失败] 所有引擎都失败")
    return []
```

#### 策略3: 放宽筛选条件

```python
def fallback_relax_filters(request):
    """降级策略3: 放宽筛选条件"""
    logger.warning("[降级] 放宽筛选条件...")

    query = f"{request.subject} {request.grade}"

    # 正常搜索
    all_results = llm_client.search(query, max_results=50)  # 增加到50

    # 第一轮: 严格评分（正常阈值）
    scored_strict = rule_scorer.score_results(
        all_results,
        query,
        metadata={'strict_mode': True}
    )

    if not detect_low_quality_results(scored_strict, request):
        return scored_strict[:20]

    # 第二轮: 宽松评分（降低阈值）
    logger.warning("[降级] 使用宽松评分...")
    scored_relaxed = rule_scorer.score_results(
        all_results,
        query,
        metadata={
            'strict_mode': False,
            'min_score_threshold': 3.0,  # 降低到3.0
            'allow_partial_matches': True
        }
    )

    return scored_relaxed[:20]
```

#### 策略4: 返回缓存历史结果

```python
def fallback_historical_cache(request):
    """降级策略4: 返回历史缓存"""
    logger.warning("[降级] 使用历史缓存...")

    cache_key = f"{request.country}:{request.grade}:{request.subject}"

    # 查找历史缓存（即使是过期的）
    historical_results = []

    # L3: 磁盘缓存（包括已过期的）
    l3_data = l3_cache.get(cache_key, include_expired=True)
    if l3_data:
        historical_results.append({
            'source': 'L3_disk_cache',
            'age_hours': l3_data['age_hours'],
            'results': l3_data['results']
        })

    # 查找相似查询的缓存
    similar_keys = l3_cache.find_similar(cache_key, max_results=5)
    for key in similar_keys:
        data = l3_cache.get(key, include_expired=True)
        if data:
            historical_results.append({
                'source': f'similar_cache:{key}',
                'age_hours': data['age_hours'],
                'results': data['results']
            })

    if historical_results:
        # 返回最新的历史结果，并标记为降级
        best = historical_results[0]
        logger.info(f"[✅ 降级] 返回历史缓存 (来源: {best['source']}, "
                   f"时效: {best['age_hours']:.1f}小时)")

        # 添加降级标记
        for r in best['results']:
            r['_fallback'] = True
            r['_fallback_source'] = best['source']
            r['_fallback_age'] = best['age_hours']

        return best['results'][:20]

    logger.error("[❌ 降级失败] 无可用历史缓存")
    return []
```

### 综合降级流程

```python
def comprehensive_fallback(request):
    """综合降级流程"""

    # 尝试1: 查询重写
    results = fallback_query_rewriting(request)
    if results:
        return results

    # 尝试2: 引擎切换
    results = fallback_engine_switching(request)
    if results:
        return results

    # 尝试3: 放宽筛选条件
    results = fallback_relax_filters(request)
    if results:
        return results

    # 尝试4: 历史缓存
    results = fallback_historical_cache(request)
    if results:
        return results

    # 最终降级: 返回空结果 + 建议反馈
    logger.error("[❌ 所有降级失败] 返回空结果")
    return {
        'results': [],
        'message': '未找到相关资源，请尝试调整搜索关键词或联系管理员',
        'suggestions': [
            '尝试使用更通用的学科名称',
            '减少年级限制',
            '使用英文搜索'
        ]
    }
```

---

## 📊 方案对比总结

| 方案 | API调用 | 响应时间 | 质量 | 复杂度 | 推荐度 |
|------|---------|----------|------|--------|--------|
| **方案一: 渐进式搜索** | 1-2次 | 25-48秒 | ⭐⭐⭐⭐ | 低 | ⭐⭐⭐⭐⭐ |
| **方案二: 智能融合** | 2-3次 | 25-35秒 | ⭐⭐⭐⭐⭐ | 中 | ⭐⭐⭐⭐ |
| **方案三: 混合评分** | 7次 | 75-145秒 | ⭐⭐⭐⭐⭐ | 高 | ⭐⭐⭐ |
| **方案四: AsyncIO** | 3-6次 | 20-30秒 | ⭐⭐⭐⭐ | 中 | ⭐⭐⭐⭐ |
| **方案五: 缓存优先** | 0.2-1次 | <100ms-48秒 | ⭐⭐⭐⭐ | 中 | ⭐⭐⭐⭐⭐ |

---

## 🚀 推荐实施路线

### 阶段1: 快速优化（1-2天）

**实施方案一（渐进式搜索）**:

1. 修改 `search_strategy_agent.py`:
   - 修改 `generate_strategy()` 返回1个最优查询
   - 添加 `generate_alternative_query()` 备用方法

2. 修改 `search_engine_v2.py`:
   - 简化并行搜索逻辑为单次搜索
   - 添加质量评估逻辑
   - 实现补充搜索和重试机制

3. 添加降级策略:
   - 实现 `detect_low_quality_results()`
   - 实现 `fallback_query_rewriting()`

**预期收益**:
- API成本降低 83% (7→1-2次)
- 平均响应时间提升 58% (60→25秒)
- 代码可维护性显著提升

### 阶段2: 性能优化（3-5天）

**实施方案四（AsyncIO）+ 方案五（缓存）**:

1. 重构搜索客户端为异步:
   - `async_tavily_client.py`
   - `async_google_client.py`

2. 实现三级缓存:
   - L1: 内存缓存 (5分钟TTL)
   - L2: Redis缓存 (1小时TTL)
   - L3: 磁盘缓存 (24小时TTL)

3. 优化降级策略:
   - 添加引擎切换逻辑
   - 添加历史缓存降级

**预期收益**:
- 缓存命中时响应 < 100ms
- 未命中时响应 20-30秒
- 80%+ 请求无需API调用

### 阶段3: 质量提升（5-7天）

**实施方案二（智能融合）**:

1. 实现RRF融合算法
2. 优化查询生成逻辑（3个查询）
3. 根据语言智能选择引擎
4. A/B测试验证效果

**预期收益**:
- 结果质量提升 20-30%
- 多语言支持优化
- API成本保持低位

---

## ✅ 验收标准

### 功能验收

- [ ] 搜索结果数量 >= 20个（除非无结果）
- [ ] 低质量结果自动触发降级
- [ ] 降级策略至少实现3种（查询重写、引擎切换、放宽条件）
- [ ] 缓存命中率 >= 50%（模拟测试）
- [ ] 所有降级场景都有明确日志

### 性能验收

- [ ] 平均响应时间 < 30秒（方案一）
- [ ] 90%响应时间 < 45秒
- [ ] API调用次数 <= 2次/请求（方案一）
- [ ] 缓存命中响应 < 100ms（方案五）

### 质量验收

- [ ] 结果相关性评分 >= 7.0（平均值）
- [ ] 播放列表占比 >= 30%
- [ ] 域名匹配率 >= 60%

### 代码质量

- [ ] 单元测试覆盖率 >= 70%
- [ ] 所有降级路径都有日志
- [ ] 代码注释完整（中文）
- [ ] 错误处理完善

---

## 📝 实施建议

### 优先级排序

1. **立即实施**: 方案一（渐进式搜索）
   - 立竿见影的效果
   - 实施风险低
   - 成本节省明显

2. **短期实施**: 方案五（缓存优先）
   - 用户体感提升最明显
   - 需要Redis基础设施

3. **中期实施**: 方案四（AsyncIO）
   - 需要重构现有代码
   - 性能提升明显

4. **长期优化**: 方案二（智能融合）+ 方案三（混合评分）
   - 根据实际效果决定
   - 需要大量A/B测试

### 风险管理

| 风险 | 应对策略 |
|------|----------|
| **质量下降** | 保留旧版本，灰度发布，A/B测试对比 |
| **缓存一致性问题** | 设置合理TTL，提供手动刷新接口 |
| **降级失败** | 实现多层降级，避免单点故障 |
| **API额度用尽** | 监控API使用，实现自动降级到免费引擎 |

---

## 🔧 配置建议

### 环境变量

```bash
# 搜索引擎配置
ENABLE_PARALLEL_SEARCH=false  # 禁用并行搜索（方案一）
ENABLE_MULTI_CACHE=true       # 启用多级缓存（方案五）
ENABLE_ASYNC_SEARCH=true      # 启用异步搜索（方案四）

# 质量阈值
QUALITY_THRESHOLD_HIGH=7.0    # 高质量阈值
QUALITY_THRESHOLD_LOW=5.0     # 低质量阈值
MIN_RESULTS_COUNT=15          # 最少结果数量

# 降级策略
ENABLE_FALLBACK_QUERY_REWRITE=true   # 查询重写
ENABLE_FALLBACK_ENGINE_SWITCH=true   # 引擎切换
ENABLE_FALLBACK_RELAX_FILTERS=true   # 放宽筛选
ENABLE_FALLBACK_HISTORICAL_CACHE=true # 历史缓存

# 缓存配置
REDIS_URL=redis://localhost:6379/0
L1_CACHE_TTL=300          # 5分钟
L2_CACHE_TTL=3600         # 1小时
L3_CACHE_TTL=86400        # 24小时
```

### 配置文件 (config/search.yaml)

```yaml
search_engine:
  # 优化方案选择: incremental/fusion/async/cached
  strategy: incremental

  # 查询生成
  query_generation:
    max_queries: 1  # 方案一只用1个查询
    use_llm: true
    include_playlist: true
    include_localized: true

  # 搜索引擎配置
  engines:
    primary: tavily    # 主引擎
    secondary: google  # 辅助引擎
    fallback: metaso   # 降级引擎

  # 质量控制
  quality:
    high_threshold: 7.0
    low_threshold: 5.0
    min_results: 15
    enable_llm_scoring: false  # 方案一不使用LLM评分

  # 降级策略
  fallback:
    enabled: true
    max_attempts: 3
    strategies:
      - query_rewrite
      - engine_switch
      - relax_filters
      - historical_cache

  # 缓存配置
  cache:
    enabled: true
    l1_enabled: true   # 内存缓存
    l2_enabled: true   # Redis缓存
    l3_enabled: true   # 磁盘缓存
```

---

## 📚 参考资料

### 外部资源

- **RRF论文**: [Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
- **AsyncIO文档**: [Python asyncio官方文档](https://docs.python.org/3/library/asyncio.html)
- **Tavily API**: [Tavily Search API Documentation](https://docs.tavily.com/docs/tavily-api/rest-api)
- **Google Custom Search**: [Google Programmable Search](https://developers.google.com/custom-search)

### 内部文档

- 当前实现: `search_engine_v2.py:1100-1300`
- 搜索策略: `search_strategy_agent.py:1-300`
- LLM客户端: `llm_client.py:915-1020`
- 评分系统: `scoring/scorer.py`, `core/result_scorer.py`

### 最佳实践

- **渐进式优化**: 从简单方案开始，逐步优化
- **A/B测试**: 对比新旧方案效果
- **监控指标**: API调用次数、响应时间、缓存命中率
- **降级优先**: 优先保证服务可用性

---

**最后更新**: 2026-01-20
**文档版本**: v1.0
**负责人**: Claude Code
**审核状态**: 待审核
