#!/usr/bin/env python3
"""
Metaso vs Tavily 搜索引擎对比测试
测试国内外教育资源搜索的质量
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载 .env
try:
    from dotenv import load_dotenv
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    # 手动加载
    env_file = project_root / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

from metaso_search_client import MetasoSearchClient
from llm_client import UnifiedLLMClient
from logger_utils import get_logger

logger = get_logger('search_comparison')

# ANSI 颜色
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


# 测试查询集合（覆盖不同国家/语言）
TEST_QUERIES = [
    {
        "category": "中国-初中",
        "query": "初二地理 全册教程 视频播放列表",
        "language": "zh",
        "expected_domains": ["bilibili.com", "youtube.com", "iqiyi.com"],
        "keywords": ["地理", "初二", "教程", "视频"]
    },
    {
        "category": "中国-小学",
        "query": "小学三年级数学 乘法口诀 视频教程",
        "language": "zh",
        "expected_domains": ["bilibili.com", "youtube.com", "qq.com"],
        "keywords": ["数学", "乘法口诀", "三年级", "小学"]
    },
    {
        "category": "印尼-小学",
        "query": "Kelas 1 Matematika video pembelajaran lengkap",
        "language": "id",
        "expected_domains": ["youtube.com", "ruangguru.com", "zenius.net", "quipper.com"],
        "keywords": ["Matematika", "Kelas 1", "video", "pembelajaran"]
    },
    {
        "category": "印尼-初中",
        "query": "Kelas 7 IPA fisika listrik dinamis video",
        "language": "id",
        "expected_domains": ["youtube.com", "ruangguru.com", "zenius.net"],
        "keywords": ["IPA", "fisika", "listrik", "Kelas 7"]
    },
    {
        "category": "美国-小学",
        "query": "Grade 5 Science energy transformation video lessons playlist",
        "language": "en",
        "expected_domains": ["youtube.com", "khanacademy.org", "study.com"],
        "keywords": ["Science", "Grade 5", "energy", "video"]
    },
    {
        "category": "美国-初中",
        "query": "Middle School Math algebra equations video tutorial complete course",
        "language": "en",
        "expected_domains": ["youtube.com", "khanacademy.org", "educational.com"],
        "keywords": ["algebra", "middle school", "equations", "video"]
    },
    {
        "category": "印度-初中",
        "query": "Class 8 Maths algebra expressions video lessons Hindi",
        "language": "en",
        "expected_domains": ["youtube.com", "khanacademy.org", "byjus.com"],
        "keywords": ["Class 8", "Maths", "algebra", "video"]
    },
    {
        "category": "俄罗斯-小学",
        "query": "5 класс математика видео уроки полный курс",
        "language": "ru",
        "expected_domains": ["youtube.com", "uchi.ru", "interneturok.ru"],
        "keywords": ["математика", "5 класс", "видео", "уроки"]
    }
]


def evaluate_relevance(result: Dict[str, Any], keywords: List[str]) -> float:
    """
    评估结果相关性（0-1分）

    考虑因素：
    1. 标题中关键词出现次数
    2. 摘要中关键词出现次数
    3. 标题和摘要的完整性
    """
    title = result.get("title", "").lower()
    snippet = result.get("snippet", "").lower()

    score = 0.0

    # 检查标题中的关键词
    title_keyword_count = sum(1 for kw in keywords if kw.lower() in title)
    score += min(title_keyword_count * 0.3, 0.6)  # 最多0.6分

    # 检查摘要中的关键词
    snippet_keyword_count = sum(1 for kw in keywords if kw.lower() in snippet)
    score += min(snippet_keyword_count * 0.1, 0.2)  # 最多0.2分

    # 标题和摘要的存在性
    if title:
        score += 0.1
    if snippet:
        score += 0.1

    return min(score, 1.0)


def evaluate_source_quality(result: Dict[str, Any], expected_domains: List[str]) -> Dict[str, Any]:
    """
    评估来源质量

    返回：{
        "has_expected_domain": bool,
        "is_edu_platform": bool,
        "domain": str,
        "score": float
    }
    """
    url = result.get("url", "")

    # 提取域名
    domain = ""
    if "://" in url:
        domain = url.split("://")[1].split("/")[0]
    else:
        domain = url.split("/")[0]

    # 检查是否包含预期域名
    has_expected_domain = any(exp in domain for exp in expected_domains)

    # 教育平台列表（扩展）
    edu_platforms = [
        "youtube.com", "bilibili.com", "iqiyi.com", "qq.com",
        "khanacademy.org", "coursera.org", "edx.org", "udemy.com",
        "ruangguru.com", "zenius.net", "quipper.com", "rumahbelajar.com",
        "uchi.ru", "interneturok.ru", "infourok.ru",
        "byjus.com", "vedantu.com", "toppr.com",
        "study.com", "brainly.com", "chegg.com",
        ".edu.", "ac.", "sch.", "school"
    ]

    is_edu_platform = any(platform in domain for platform in edu_platforms)

    # 计算质量分数
    score = 0.0
    if has_expected_domain:
        score += 0.5
    if is_edu_platform:
        score += 0.3
    if domain:  # 有域名
        score += 0.2

    return {
        "has_expected_domain": has_expected_domain,
        "is_edu_platform": is_edu_platform,
        "domain": domain,
        "score": score
    }


def test_search_engine(
    engine_name: str,
    client,
    query_info: Dict[str, Any],
    max_results: int = 10,
    use_llm_client: bool = False
) -> Dict[str, Any]:
    """
    测试单个搜索引擎

    Args:
        engine_name: 引擎名称（"Metaso" 或 "Tavily"）
        client: 客户端实例（MetasoSearchClient 或 UnifiedLLMClient）
        query_info: 查询信息
        max_results: 最大结果数
        use_llm_client: 是否使用 llm_client（用于 Tavily）

    返回：{
        "engine": str,
        "query": str,
        "results": list,
        "response_time": float,
        "result_count": int,
        "avg_relevance": float,
        "avg_quality": float,
        "expected_domain_count": int,
        "edu_platform_count": int,
        "top_results": list
    }
    """
    query = query_info["query"]
    keywords = query_info["keywords"]
    expected_domains = query_info["expected_domains"]

    print(f"\n{'='*60}")
    print(f"🔍 测试引擎: {Colors.BOLD}{engine_name}{Colors.ENDC}")
    print(f"📝 查询: {query}")
    print(f"{'='*60}")

    # 执行搜索
    start_time = time.time()

    try:
        if engine_name == "Metaso":
            # 直接使用 MetasoSearchClient
            results = client.search(query, max_results=max_results)
        elif engine_name == "Tavily":
            # 使用 llm_client._search_with_tavily
            results = client._search_with_tavily(query, max_results=max_results)
        else:
            results = []
    except Exception as e:
        print(f"{Colors.FAIL}❌ 搜索失败: {e}{Colors.ENDC}")
        return {
            "engine": engine_name,
            "query": query,
            "error": str(e),
            "results": [],
            "response_time": time.time() - start_time
        }

    response_time = time.time() - start_time

    if not results:
        print(f"{Colors.WARNING}⚠️ 未返回结果{Colors.ENDC}")
        return {
            "engine": engine_name,
            "query": query,
            "results": [],
            "response_time": response_time,
            "result_count": 0
        }

    # 评估结果
    relevance_scores = []
    quality_scores = []
    expected_domain_count = 0
    edu_platform_count = 0

    print(f"\n{Colors.OKBLUE}📊 结果分析:{Colors.ENDC}")

    for i, result in enumerate(results[:5], 1):  # 只显示前5个
        relevance = evaluate_relevance(result, keywords)
        quality_info = evaluate_source_quality(result, expected_domains)

        relevance_scores.append(relevance)
        quality_scores.append(quality_info["score"])

        if quality_info["has_expected_domain"]:
            expected_domain_count += 1
        if quality_info["is_edu_platform"]:
            edu_platform_count += 1

        # 显示结果
        print(f"\n  {i}. {result.get('title', 'N/A')[:60]}")
        print(f"     URL: {result.get('url', 'N/A')[:60]}")
        print(f"     {Colors.OKGREEN}相关性: {relevance:.2f}{Colors.ENDC} | "
              f"{Colors.OKCYAN}质量: {quality_info['score']:.2f}{Colors.ENDC}")

        if quality_info["has_expected_domain"]:
            print(f"     {Colors.OKGREEN}✅ 包含预期域名: {quality_info['domain']}{Colors.ENDC}")
        if quality_info["is_edu_platform"]:
            print(f"     {Colors.OKGREEN}🎓 教育平台{Colors.ENDC}")

    # 统计
    avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

    print(f"\n{Colors.BOLD}📈 统计摘要:{Colors.ENDC}")
    print(f"  • 响应时间: {response_time:.2f}s")
    print(f"  • 结果数量: {len(results)}")
    print(f"  • 平均相关性: {avg_relevance:.2f}/1.0")
    print(f"  • 平均质量: {avg_quality:.2f}/1.0")
    print(f"  • 预期域名匹配: {expected_domain_count}/{min(len(results), 5)}")
    print(f"  • 教育平台: {edu_platform_count}/{min(len(results), 5)}")

    return {
        "engine": engine_name,
        "query": query,
        "category": query_info["category"],
        "language": query_info["language"],
        "results": results,
        "response_time": response_time,
        "result_count": len(results),
        "avg_relevance": avg_relevance,
        "avg_quality": avg_quality,
        "expected_domain_count": expected_domain_count,
        "edu_platform_count": edu_platform_count,
        "top_results": results[:3]  # 保存前3个结果用于对比
    }


def compare_engines(metaso_client, llm_client):
    """
    对比两个搜索引擎

    Args:
        metaso_client: MetasoSearchClient 实例
        llm_client: UnifiedLLMClient 实例（包含 Tavily）
    """
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print("=" * 70)
    print("  Metaso vs Tavily 搜索引擎对比测试")
    print("=" * 70)
    print(f"{Colors.ENDC}\n")

    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试查询数量: {len(TEST_QUERIES)}")
    print(f"每个查询结果数: 10")
    print(f"评估维度: 相关性、质量、响应时间、域名匹配\n")

    all_results = []

    for query_info in TEST_QUERIES:
        print(f"\n\n{Colors.HEADER}{Colors.BOLD}")
        print("=" * 70)
        print(f"  测试场景: {query_info['category']}")
        print(f"  语言: {query_info['language']}")
        print("=" * 70)
        print(f"{Colors.ENDC}")

        # 测试 Metaso（直接使用 MetasoSearchClient）
        metaso_result = test_search_engine("Metaso", metaso_client, query_info, use_llm_client=False)
        all_results.append(metaso_result)

        # 测试 Tavily（使用 llm_client._search_with_tavily）
        tavily_result = test_search_engine("Tavily", llm_client, query_info, use_llm_client=True)
        all_results.append(tavily_result)

        # 对比总结
        print(f"\n{Colors.BOLD}{Colors.OKCYAN}📊 对比总结:{Colors.ENDC}")
        print(f"  • 响应时间: Metaso {metaso_result['response_time']:.2f}s vs "
              f"Tavily {tavily_result['response_time']:.2f}s")

        if metaso_result.get('error'):
            print(f"  • Metaso 状态: {Colors.FAIL}失败{Colors.ENDC}")
        elif tavily_result.get('error'):
            print(f"  • Tavily 状态: {Colors.FAIL}失败{Colors.ENDC}")
        else:
            print(f"  • 结果数量: Metaso {metaso_result['result_count']} vs "
                  f"Tavily {tavily_result['result_count']}")
            print(f"  • 平均相关性: Metaso {metaso_result['avg_relevance']:.2f} vs "
                  f"Tavily {tavily_result['avg_relevance']:.2f}")
            print(f"  • 平均质量: Metaso {metaso_result['avg_quality']:.2f} vs "
                  f"Tavily {tavily_result['avg_quality']:.2f}")
            print(f"  • 预期域名: Metaso {metaso_result['expected_domain_count']}/5 vs "
                  f"Tavily {tavily_result['expected_domain_count']}/5")

            # 判断胜者
            metaso_score = metaso_result['avg_relevance'] + metaso_result['avg_quality']
            tavily_score = tavily_result['avg_relevance'] + tavily_result['avg_quality']

            if metaso_score > tavily_score:
                print(f"  • {Colors.OKGREEN}🏆 胜者: Metaso (+{metaso_score - tavily_score:.2f}){Colors.ENDC}")
            elif tavily_score > metaso_score:
                print(f"  • {Colors.OKBLUE}🏆 胜者: Tavily (+{tavily_score - metaso_score:.2f}){Colors.ENDC}")
            else:
                print(f"  • {Colors.WARNING}🤝 平局{Colors.ENDC}")

    # 生成总结报告
    generate_summary_report(all_results)


def generate_summary_report(all_results: List[Dict[str, Any]]):
    """
    生成总结报告
    """
    print(f"\n\n{Colors.HEADER}{Colors.BOLD}")
    print("=" * 70)
    print("  📋 总体对比报告")
    print("=" * 70)
    print(f"{Colors.ENDC}\n")

    # 分离 Metaso 和 Tavily 结果
    metaso_results = [r for r in all_results if r['engine'] == 'Metaso' and not r.get('error')]
    tavily_results = [r for r in all_results if r['engine'] == 'Tavily' and not r.get('error')]

    if not metaso_results or not tavily_results:
        print(f"{Colors.FAIL}❌ 无法生成报告：某个引擎所有测试都失败{Colors.ENDC}")
        return

    # 1. 响应时间对比
    metaso_avg_time = sum(r['response_time'] for r in metaso_results) / len(metaso_results)
    tavily_avg_time = sum(r['response_time'] for r in tavily_results) / len(tavily_results)

    print(f"{Colors.BOLD}1. 响应时间对比{Colors.ENDC}")
    print(f"   • Metaso 平均: {metaso_avg_time:.2f}s")
    print(f"   • Tavily 平均: {tavily_avg_time:.2f}s")
    if metaso_avg_time < tavily_avg_time:
        print(f"   • {Colors.OKGREEN}✅ Metaso 更快 ({(tavily_avg_time/metaso_avg_time - 1)*100:.1f}%){Colors.ENDC}")
    else:
        print(f"   • {Colors.OKBLUE}✅ Tavily 更快 ({(metaso_avg_time/tavily_avg_time - 1)*100:.1f}%){Colors.ENDC}")

    # 2. 结果数量对比
    metaso_avg_count = sum(r['result_count'] for r in metaso_results) / len(metaso_results)
    tavily_avg_count = sum(r['result_count'] for r in tavily_results) / len(tavily_results)

    print(f"\n{Colors.BOLD}2. 结果数量对比{Colors.ENDC}")
    print(f"   • Metaso 平均: {metaso_avg_count:.1f} 个")
    print(f"   • Tavily 平均: {tavily_avg_count:.1f} 个")
    if metaso_avg_count > tavily_avg_count:
        print(f"   • {Colors.OKGREEN}✅ Metaso 更多 ({metaso_avg_count/tavily_avg_count:.2f}x){Colors.ENDC}")
    else:
        print(f"   • {Colors.OKBLUE}✅ Tavily 更多 ({tavily_avg_count/metaso_avg_count:.2f}x){Colors.ENDC}")

    # 3. 平均相关性对比
    metaso_avg_relevance = sum(r['avg_relevance'] for r in metaso_results) / len(metaso_results)
    tavily_avg_relevance = sum(r['avg_relevance'] for r in tavily_results) / len(tavily_results)

    print(f"\n{Colors.BOLD}3. 平均相关性对比{Colors.ENDC}")
    print(f"   • Metaso 平均: {metaso_avg_relevance:.2f}/1.0")
    print(f"   • Tavily 平均: {tavily_avg_relevance:.2f}/1.0")
    if metaso_avg_relevance > tavily_avg_relevance:
        print(f"   • {Colors.OKGREEN}✅ Metaso 更相关 (+{(metaso_avg_relevance - tavily_avg_relevance)*100:.1f}%){Colors.ENDC}")
    else:
        print(f"   • {Colors.OKBLUE}✅ Tavily 更相关 (+{(tavily_avg_relevance - metaso_avg_relevance)*100:.1f}%){Colors.ENDC}")

    # 4. 平均质量对比
    metaso_avg_quality = sum(r['avg_quality'] for r in metaso_results) / len(metaso_results)
    tavily_avg_quality = sum(r['avg_quality'] for r in tavily_results) / len(tavily_results)

    print(f"\n{Colors.BOLD}4. 平均质量对比{Colors.ENDC}")
    print(f"   • Metaso 平均: {metaso_avg_quality:.2f}/1.0")
    print(f"   • Tavily 平均: {tavily_avg_quality:.2f}/1.0")
    if metaso_avg_quality > tavily_avg_quality:
        print(f"   • {Colors.OKGREEN}✅ Metaso 质量更高 (+{(metaso_avg_quality - tavily_avg_quality)*100:.1f}%){Colors.ENDC}")
    else:
        print(f"   • {Colors.OKBLUE}✅ Tavily 质量更高 (+{(tavily_avg_quality - metaso_avg_quality)*100:.1f}%){Colors.ENDC}")

    # 5. 按地区对比
    print(f"\n{Colors.BOLD}5. 按地区对比{Colors.ENDC}")

    regions = {
        "中国": [r for r in metaso_results if r['language'] == 'zh'],
        "国际": [r for r in metaso_results if r['language'] != 'zh']
    }

    for region_name, metaso_region_results in regions.items():
        if not metaso_region_results:
            continue

        # 找到对应的 Tavily 结果
        tavily_region_results = [
            r for r in tavily_results
            if r['query'] in [mr['query'] for mr in metaso_region_results]
        ]

        if not tavily_region_results:
            continue

        metaso_region_score = sum(r['avg_relevance'] + r['avg_quality'] for r in metaso_region_results) / len(metaso_region_results)
        tavily_region_score = sum(r['avg_relevance'] + r['avg_quality'] for r in tavily_region_results) / len(tavily_region_results)

        print(f"\n   {Colors.BOLD}📍 {region_name}内容:{Colors.ENDC}")
        print(f"   • Metaso 综合得分: {metaso_region_score:.2f}")
        print(f"   • Tavily 综合得分: {tavily_region_score:.2f}")

        if metaso_region_score > tavily_region_score:
            print(f"   • {Colors.OKGREEN}✅ Metaso 更适合{region_name}内容 (+{(metaso_region_score - tavily_region_score)*100:.1f}%){Colors.ENDC}")
        elif tavily_region_score > metaso_region_score:
            print(f"   • {Colors.OKBLUE}✅ Tavily 更适合{region_name}内容 (+{(tavily_region_score - metaso_region_score)*100:.1f}%){Colors.ENDC}")
        else:
            print(f"   • {Colors.WARNING}🤝 平局{Colors.ENDC}")

    # 6. 胜率统计
    print(f"\n{Colors.BOLD}6. 胜率统计{Colors.ENDC}")

    metaso_wins = 0
    tavily_wins = 0
    ties = 0

    for i in range(0, len(all_results), 2):
        if i + 1 >= len(all_results):
            break

        mr = all_results[i]
        tr = all_results[i + 1]

        if mr.get('error') and not tr.get('error'):
            tavily_wins += 1
        elif not mr.get('error') and tr.get('error'):
            metaso_wins += 1
        elif mr.get('error') and tr.get('error'):
            ties += 1
        else:
            metaso_score = mr['avg_relevance'] + mr['avg_quality']
            tavily_score = tr['avg_relevance'] + tr['avg_quality']

            if metaso_score > tavily_score:
                metaso_wins += 1
            elif tavily_score > metaso_score:
                tavily_wins += 1
            else:
                ties += 1

    total = metaso_wins + tavily_wins + ties
    print(f"   • Metaso 胜: {metaso_wins}/{total} ({metaso_wins/total*100:.1f}%)")
    print(f"   • Tavily 胜: {tavily_wins}/{total} ({tavily_wins/total*100:.1f}%)")
    print(f"   • 平局: {ties}/{total} ({ties/total*100:.1f}%)")

    # 7. 最终推荐
    print(f"\n{Colors.BOLD}7. 最终推荐{Colors.ENDC}")

    metaso_total_score = metaso_avg_relevance + metaso_avg_quality + (1.0 - metaso_avg_time/10)  # 考虑响应时间
    tavily_total_score = tavily_avg_relevance + tavily_avg_quality + (1.0 - tavily_avg_time/10)

    print(f"\n   综合评分（考虑相关性、质量、响应时间）:")
    print(f"   • Metaso: {metaso_total_score:.2f}")
    print(f"   • Tavily: {tavily_total_score:.2f}")

    if metaso_total_score > tavily_total_score * 1.05:  # 5%以上优势
        print(f"\n   {Colors.OKGREEN}{Colors.BOLD}🏆 推荐: Metaso{Colors.ENDC}")
        print(f"   综合表现更优，建议作为主要搜索引擎")
    elif tavily_total_score > metaso_total_score * 1.05:
        print(f"\n   {Colors.OKBLUE}{Colors.BOLD}🏆 推荐: Tavily{Colors.ENDC}")
        print(f"   综合表现更优，建议作为主要搜索引擎")
    else:
        print(f"\n   {Colors.WARNING}{Colors.BOLD}🤝 推荐: 混合使用{Colors.ENDC}")
        print(f"   两者表现接近，建议:")
        print(f"   • 中文内容优先 Metaso")
        print(f"   • 国际内容根据实际质量选择")
        print(f"   • 保留 Tavily 作为备用")

    # 8. 成本对比
    print(f"\n{Colors.BOLD}8. 成本对比{Colors.ENDC}")
    print(f"   • Metaso: ¥0.03/次（5,000次免费）")
    print(f"   • Tavily: >¥0.03/次（无免费额度）")
    print(f"   • {Colors.OKGREEN}✅ Metaso 成本优势明显{Colors.ENDC}")

    print(f"\n{Colors.BOLD}{'='*70}{Colors.ENDC}\n")


def main():
    """主函数"""
    try:
        # 初始化客户端
        print(f"{Colors.BOLD}初始化搜索引擎客户端...{Colors.ENDC}\n")

        # 初始化 Metaso 客户端
        metaso_client = MetasoSearchClient()
        print(f"{Colors.OKGREEN}✅ Metaso 客户端初始化成功{Colors.ENDC}")

        # 初始化 LLM 客户端（包含 Tavily）
        llm_client = UnifiedLLMClient()

        print(f"{Colors.OKGREEN}✅ Tavily 客户端初始化成功{Colors.ENDC}")

        # 开始对比测试
        compare_engines(metaso_client, llm_client)

        # 保存详细结果到 JSON
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = project_root / f"search_comparison_{timestamp}.json"

        # 这里可以保存 all_results，但需要先在 compare_engines 中返回
        print(f"\n{Colors.OKGREEN}✅ 测试完成！{Colors.ENDC}\n")

    except Exception as e:
        print(f"\n{Colors.FAIL}❌ 错误: {e}{Colors.ENDC}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
