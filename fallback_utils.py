#!/usr/bin/env python3
"""
降级策略工具集

用于处理低质量搜索结果的降级策略
包括：查询重写、引擎切换、放宽筛选、历史缓存等
"""

from typing import Dict, List, Optional, Any
from logger_utils import get_logger

logger = get_logger('fallback_utils')


def detect_low_quality_results(results: List[Dict], request: Dict) -> bool:
    """
    检测搜索结果是否整体质量低

    检测方法：
    1. 平均分检测：前20个结果平均分 < 5.0
    2. 高分结果数量检测：前20个结果中 >= 7.0分的少于3个
    3. 标题相关性检测：前10个结果中相关标题少于5个

    Args:
        results: 评分后的结果列表（每个结果包含'score'字段）
        request: 原始请求字典（包含country, grade, subject）

    Returns:
        True if low quality, False otherwise
    """
    if not results:
        logger.warning("[低质量检测] 结果列表为空")
        return True

    # 方法1: 平均分检测
    scores = [r.get('score', 0) for r in results[:20]]
    avg_score = sum(scores) / len(scores) if scores else 0.0

    if avg_score < 5.0:
        logger.warning(f"[低质量检测] 平均分 {avg_score:.2f} < 5.0")
        return True

    # 方法2: 高分结果数量检测
    high_score_count = sum(1 for s in scores if s >= 7.0)

    if high_score_count < 3:
        logger.warning(f"[低质量检测] 高分结果仅 {high_score_count} 个 < 3")
        return True

    # 方法3: 标题相关性检测
    subject = request.get('subject', '').lower()
    grade = request.get('grade', '').lower()

    relevant_count = 0
    for r in results[:10]:
        title_lower = r.get('title', '').lower()

        # 检查标题是否包含subject或grade
        if subject in title_lower or grade in title_lower:
            relevant_count += 1

    if relevant_count < 5:
        logger.warning(f"[低质量检测] 相关标题仅 {relevant_count}/10 < 5")
        return True

    logger.info(f"[✅ 质量检测] 通过 (平均分: {avg_score:.2f}, 高分: {high_score_count}个, 相关: {relevant_count}/10)")
    return False


def fallback_query_rewriting(request: Dict, llm_client, strategy_agent) -> List[Dict]:
    """
    降级策略1: 查询重写

    使用不同的查询变体重试搜索

    Args:
        request: 搜索请求字典
        llm_client: LLM客户端
        strategy_agent: 搜索策略代理

    Returns:
        搜索结果列表
    """
    logger.warning("[降级策略1] 尝试查询重写...")

    subject = request.get('subject', '')
    grade = request.get('grade', '')
    country = request.get('country', '')
    semester = request.get('semester')

    # 重写选项
    rewrite_options = []

    # 选项1: 使用英文（如果原查询不是英文）
    rewrite_options.append({
        'query': f"{subject} {grade} playlist",
        'reason': '英文通用查询'
    })

    # 选项2: 添加"video"关键词
    rewrite_options.append({
        'query': f"{subject} {grade} video",
        'reason': '添加video关键词'
    })

    # 选项3: 使用"course"
    rewrite_options.append({
        'query': f"{subject} {grade} complete course",
        'reason': '使用course关键词'
    })

    # 选项4: 移除年级，只用学科
    rewrite_options.append({
        'query': f"{subject} playlist",
        'reason': '移除年级限制'
    })

    # 选项5: 使用YouTube特定语法
    rewrite_options.append({
        'query': f"site:youtube.com \"{subject}\" \"{grade}\" playlist",
        'reason': 'YouTube精确语法'
    })

    # 尝试每个重写选项
    for idx, option in enumerate(rewrite_options, 1):
        logger.info(f"[重试 {idx}/{len(rewrite_options)}] {option['reason']}: \"{option['query']}\"")

        try:
            results = llm_client.search(
                query=option['query'],
                max_results=30,
                country_code=country
            )

            if results and len(results) >= 10:  # 至少10个结果才算成功
                logger.info(f"[✅ 降级成功] 查询重写成功 (选项{idx}): {option['reason']}")
                return results

        except Exception as e:
            logger.warning(f"[⚠️ 重试 {idx}] 失败: {str(e)}")
            continue

    logger.error("[❌ 降级失败] 所有查询重写都失败")
    return []


def fallback_engine_switching(request: Dict, llm_client, google_hunter=None,
                               baidu_hunter=None) -> List[Dict]:
    """
    降级策略2: 引擎切换

    尝试使用不同的搜索引擎

    Args:
        request: 搜索请求字典
        llm_client: LLM客户端（包含Tavily/Metaso）
        google_hunter: Google搜索客户端（可选）
        baidu_hunter: 百度搜索客户端（可选）

    Returns:
        搜索结果列表
    """
    logger.warning("[降级策略2] 尝试引擎切换...")

    query = f"{request.get('subject', '')} {request.get('grade', '')}"
    country_code = request.get('country', 'CN')

    # 定义引擎列表
    engines = []

    # 引擎1: Tavily/Metaso (已通过llm_client)
    engines.append({
        'name': 'Tavily/Metaso',
        'func': lambda q: llm_client.search(query=q, max_results=30, country_code=country_code)
    })

    # 引擎2: Google (如果可用)
    if google_hunter:
        engines.append({
            'name': 'Google',
            'func': lambda q: google_hunter.search(query=q, max_results=20)
        })

    # 引擎3: Baidu (如果可用)
    if baidu_hunter:
        engines.append({
            'name': 'Baidu',
            'func': lambda q: baidu_hunter.search(query=q, max_results=30)
        })

    # 尝试每个引擎
    for engine in engines:
        logger.info(f"[重试] 尝试 {engine['name']}...")

        try:
            results = engine['func'](query)

            if results and len(results) >= 5:
                logger.info(f"[✅ 降级成功] 引擎切换成功: {engine['name']}")
                return results

        except Exception as e:
            logger.warning(f"[⚠️ {engine['name']}] 失败: {str(e)}")
            continue

    logger.error("[❌ 降级失败] 所有引擎都失败")
    return []


def fallback_relax_filters(request: Dict, llm_client, result_scorer) -> List[Dict]:
    """
    降级策略3: 放宽筛选条件

    降低评分阈值，允许更多结果通过

    Args:
        request: 搜索请求字典
        llm_client: LLM客户端
        result_scorer: 结果评分器

    Returns:
        评分后的结果列表
    """
    logger.warning("[降级策略3] 放宽筛选条件...")

    query = f"{request.get('subject', '')} {request.get('grade', '')}"
    country_code = request.get('country', 'CN')

    try:
        # 增加搜索结果数量
        results = llm_client.search(
            query=query,
            max_results=50,  # 增加到50个
            country_code=country_code
        )

        if not results:
            logger.error("[❌ 降级失败] 搜索无结果")
            return []

        logger.info(f"[放宽筛选] 获取到 {len(results)} 个原始结果")

        # 使用宽松的评分标准
        metadata = {
            'country': country_code,
            'grade': request.get('grade', ''),
            'subject': request.get('subject', ''),
            'strict_mode': False,
            'min_score_threshold': 3.0,  # 降低到3.0
            'allow_partial_matches': True
        }

        scored_results = result_scorer.score_results(
            results,
            query,
            metadata=metadata
        )

        logger.info(f"[✅ 降级成功] 放宽筛选后返回 {len(scored_results)} 个结果")

        # 返回前30个结果（放宽到30个）
        return scored_results[:30]

    except Exception as e:
        logger.error(f"[❌ 降级失败] 放宽筛选失败: {str(e)}")
        return []


def fallback_historical_cache(request: Dict, cache_manager) -> List[Dict]:
    """
    降级策略4: 历史缓存

    返回历史缓存的搜索结果（即使是过期的）

    Args:
        request: 搜索请求字典
        cache_manager: 缓存管理器（支持多级缓存）

    Returns:
        搜索结果列表（带有降级标记）
    """
    logger.warning("[降级策略4] 使用历史缓存...")

    cache_key = f"{request.get('country', '')}:{request.get('grade', '')}:{request.get('subject', '')}"

    try:
        # 查找历史缓存（包括已过期的）
        historical_results = []

        # 尝试从L3磁盘缓存获取（包括已过期的）
        if hasattr(cache_manager, 'get_l3_cache'):
            l3_data = cache_manager.get_l3_cache(cache_key, include_expired=True)
            if l3_data:
                historical_results.append({
                    'source': 'L3_disk_cache',
                    'age_hours': l3_data.get('age_hours', 0),
                    'results': l3_data.get('results', [])
                })

        # 查找相似查询的缓存
        if hasattr(cache_manager, 'find_similar'):
            similar_keys = cache_manager.find_similar(cache_key, max_results=5)
            for key in similar_keys:
                data = cache_manager.get(key, include_expired=True)
                if data:
                    historical_results.append({
                        'source': f'similar_cache:{key}',
                        'age_hours': data.get('age_hours', 0),
                        'results': data.get('results', [])
                    })

        if historical_results:
            # 返回最新的历史结果
            best = max(historical_results, key=lambda x: x['age_hours'])

            # 添加降级标记
            for r in best['results']:
                if isinstance(r, dict):
                    r['_fallback'] = True
                    r['_fallback_source'] = best['source']
                    r['_fallback_age'] = best['age_hours']

            logger.info(f"[✅ 降级成功] 返回历史缓存 (来源: {best['source']}, "
                       f"时效: {best['age_hours']:.1f}小时, 结果数: {len(best['results'])})")

            return best['results']

        logger.error("[❌ 降级失败] 无可用历史缓存")
        return []

    except Exception as e:
        logger.error(f"[❌ 降级失败] 历史缓存失败: {str(e)}")
        return []


def comprehensive_fallback(request: Dict, llm_client, strategy_agent,
                          result_scorer=None, google_hunter=None,
                          baidu_hunter=None, cache_manager=None) -> List[Dict]:
    """
    综合降级流程

    依次尝试所有降级策略，直到成功或全部失败

    Args:
        request: 搜索请求字典
        llm_client: LLM客户端
        strategy_agent: 搜索策略代理
        result_scorer: 结果评分器（可选，用于放宽筛选）
        google_hunter: Google搜索客户端（可选）
        baidu_hunter: 百度搜索客户端（可选）
        cache_manager: 缓存管理器（可选）

    Returns:
        搜索结果列表，或空列表（如果所有降级都失败）
    """
    logger.warning("="*80)
    logger.warning("[🚨 综合降级] 开始执行降级策略...")
    logger.warning("="*80)

    # 尝试1: 查询重写
    results = fallback_query_rewriting(request, llm_client, strategy_agent)
    if results and len(results) >= 5:
        return results

    # 尝试2: 引擎切换
    results = fallback_engine_switching(request, llm_client, google_hunter, baidu_hunter)
    if results and len(results) >= 5:
        return results

    # 尝试3: 放宽筛选条件（需要评分器）
    if result_scorer:
        results = fallback_relax_filters(request, llm_client, result_scorer)
        if results and len(results) >= 5:
            return results

    # 尝试4: 历史缓存（需要缓存管理器）
    if cache_manager:
        results = fallback_historical_cache(request, cache_manager)
        if results and len(results) >= 5:
            return results

    # 最终降级: 返回空结果 + 建议
    logger.error("[❌ 所有降级失败] 返回空结果")
    logger.error("[建议] 用户可以尝试:")
    logger.error("  1. 使用更通用的学科名称")
    logger.error("  2. 减少年级限制")
    logger.error("  3. 使用英文搜索")

    return []
