#!/usr/bin/env python3
"""
Google vs Tavily 国外教育资源搜索对比测试
专门针对国际内容进行质量对比
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
    env_file = project_root / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

from search_strategist import SearchHunter
from llm_client import UnifiedLLMClient

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


# 测试查询集合（专门针对国外教育资源）
TEST_QUERIES = [
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
        "query": "Class 8 Maths algebra expressions video lessons Hindi complete",
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
    },
    {
        "category": "菲律宾-小学",
        "query": "Grade 4 Math fractions video lessons English Tagalog",
        "language": "en",
        "expected_domains": ["youtube.com", "khanacademy.org"],
        "keywords": ["Math", "Grade 4", "fractions", "video"]
    },
    {
        "category": "国际-综合",
        "query": "K12 education video lessons playlist science math complete curriculum",
        "language": "en",
        "expected_domains": ["youtube.com", "khanacademy.org", "educational.com"],
        "keywords": ["K12", "education", "video", "curriculum"]
    }
]


def evaluate_relevance(result: Dict[str, Any], keywords: List[str]) -> float:
    """
    评估结果相关性（0-1分）
    """
    title = result.get("title", "").lower()
    snippet = result.get("snippet", "").lower()

    score = 0.0

    # 检查标题中的关键词
    title_keyword_count = sum(1 for kw in keywords if kw.lower() in title)
    score += min(title_keyword_count * 0.3, 0.6)

    # 检查摘要中的关键词
    snippet_keyword_count = sum(1 for kw in keywords if kw.lower() in snippet)
    score += min(snippet_keyword_count * 0.1, 0.2)

    # 标题和摘要的存在性
    if title:
        score += 0.1
    if snippet:
        score += 0.1

    return min(score, 1.0)


def evaluate_source_quality(result: Dict[str, Any], expected_domains: List[str]) -> Dict[str, Any]:
    """
    评估来源质量
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

    # 教育平台列表
    edu_platforms = [
        "youtube.com", "khanacademy.org", "coursera.org", "edx.org", "udemy.com",
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
    if domain:
        score += 0.2

    return {
        "has_expected_domain": has_expected_domain,
        "is_edu_platform": is_edu_platform,
        "domain": domain,
        "score": score
    }


def test_search_engine(
    engine_name: str,
    hunter,
    llm_client,
    query_info: Dict[str, Any],
    max_results: int = 10
) -> Dict[str, Any]:
    """
    测试单个搜索引擎

    Args:
        engine_name: "Google" 或 "Tavily"
        hunter: SearchHunter 实例（用于 Google）
        llm_client: UnifiedLLMClient 实例（用于 Tavily）
        query_info: 查询信息
        max_results: 最大结果数

    Returns:
        测试结果字典
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
        if engine_name == "Google":
            results_raw = hunter.search(query, max_results=max_results)
            # 转换为统一格式
            results = [
                {
                    "title": r.title,
                    "url": r.url,
                    "snippet": r.snippet
                }
                for r in results_raw
            ]
        elif engine_name == "Tavily":
            results_raw = llm_client._search_with_tavily(query, max_results=max_results, include_domains=None, reason="测试")
            results = [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", "") or r.get("snippet", "") or r.get("raw_content", "")
                }
                for r in results_raw
            ]
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

    for i, result in enumerate(results[:5], 1):
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
        "top_results": results[:3]
    }


def compare_engines(google_hunter, tavily_client):
    """
    对比两个搜索引擎
    """
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print("=" * 70)
    print("  Google vs Tavily 国外教育资源搜索对比测试")
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

        # 测试 Google
        google_result = test_search_engine("Google", google_hunter, tavily_client, query_info, max_results=10)
        all_results.append(google_result)

        # 测试 Tavily
        tavily_result = test_search_engine("Tavily", google_hunter, tavily_client, query_info, max_results=10)
        all_results.append(tavily_result)

        # 对比总结
        print(f"\n{Colors.BOLD}{Colors.OKCYAN}📊 对比总结:{Colors.ENDC}")
        print(f"  • 响应时间: Google {google_result['response_time']:.2f}s vs "
              f"Tavily {tavily_result['response_time']:.2f}s")

        if google_result.get('error'):
            print(f"  • Google 状态: {Colors.FAIL}失败{Colors.ENDC}")
        elif tavily_result.get('error'):
            print(f"  • Tavily 状态: {Colors.FAIL}失败{Colors.ENDC}")
        else:
            print(f"  • 结果数量: Google {google_result['result_count']} vs "
                  f"Tavily {tavily_result['result_count']}")
            print(f"  • 平均相关性: Google {google_result['avg_relevance']:.2f} vs "
                  f"Tavily {tavily_result['avg_relevance']:.2f}")
            print(f"  • 平均质量: Google {google_result['avg_quality']:.2f} vs "
                  f"Tavily {tavily_result['avg_quality']:.2f}")
            print(f"  • 预期域名: Google {google_result['expected_domain_count']}/5 vs "
                  f"Tavily {tavily_result['expected_domain_count']}/5")

            # 判断胜者
            google_score = google_result['avg_relevance'] + google_result['avg_quality']
            tavily_score = tavily_result['avg_relevance'] + tavily_result['avg_quality']

            if google_score > tavily_score:
                print(f"  • {Colors.OKGREEN}🏆 胜者: Google (+{google_score - tavily_score:.2f}){Colors.ENDC}")
            elif tavily_score > google_score:
                print(f"  • {Colors.OKBLUE}🏆 胜者: Tavily (+{tavily_score - google_score:.2f}){Colors.ENDC}")
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

    # 分离 Google 和 Tavily 结果
    google_results = [r for r in all_results if r['engine'] == 'Google' and not r.get('error')]
    tavily_results = [r for r in all_results if r['engine'] == 'Tavily' and not r.get('error')]

    if not google_results or not tavily_results:
        print(f"{Colors.FAIL}❌ 无法生成报告：某个引擎所有测试都失败{Colors.ENDC}")
        return

    # 1. 响应时间对比
    google_avg_time = sum(r['response_time'] for r in google_results) / len(google_results)
    tavily_avg_time = sum(r['response_time'] for r in tavily_results) / len(tavily_results)

    print(f"{Colors.BOLD}1. 响应时间对比{Colors.ENDC}")
    print(f"   • Google 平均: {google_avg_time:.2f}s")
    print(f"   • Tavily 平均: {tavily_avg_time:.2f}s")
    if google_avg_time < tavily_avg_time:
        print(f"   • {Colors.OKGREEN}✅ Google 更快 ({(tavily_avg_time/google_avg_time - 1)*100:.1f}%){Colors.ENDC}")
    else:
        print(f"   • {Colors.OKBLUE}✅ Tavily 更快 ({(google_avg_time/tavily_avg_time - 1)*100:.1f}%){Colors.ENDC}")

    # 2. 结果数量对比
    google_avg_count = sum(r['result_count'] for r in google_results) / len(google_results)
    tavily_avg_count = sum(r['result_count'] for r in tavily_results) / len(tavily_results)

    print(f"\n{Colors.BOLD}2. 结果数量对比{Colors.ENDC}")
    print(f"   • Google 平均: {google_avg_count:.1f} 个")
    print(f"   • Tavily 平均: {tavily_avg_count:.1f} 个")
    if google_avg_count > tavily_avg_count:
        print(f"   • {Colors.OKGREEN}✅ Google 更多 ({google_avg_count/tavily_avg_count:.2f}x){Colors.ENDC}")
    else:
        print(f"   • {Colors.OKBLUE}✅ Tavily 更多 ({tavily_avg_count/google_avg_count:.2f}x){Colors.ENDC}")

    # 3. 平均相关性对比
    google_avg_relevance = sum(r['avg_relevance'] for r in google_results) / len(google_results)
    tavily_avg_relevance = sum(r['avg_relevance'] for r in tavily_results) / len(tavily_results)

    print(f"\n{Colors.BOLD}3. 平均相关性对比{Colors.ENDC}")
    print(f"   • Google 平均: {google_avg_relevance:.2f}/1.0")
    print(f"   • Tavily 平均: {tavily_avg_relevance:.2f}/1.0")
    if google_avg_relevance > tavily_avg_relevance:
        print(f"   • {Colors.OKGREEN}✅ Google 更相关 (+{(google_avg_relevance - tavily_avg_relevance)*100:.1f}%){Colors.ENDC}")
    else:
        print(f"   • {Colors.OKBLUE}✅ Tavily 更相关 (+{(tavily_avg_relevance - google_avg_relevance)*100:.1f}%){Colors.ENDC}")

    # 4. 平均质量对比
    google_avg_quality = sum(r['avg_quality'] for r in google_results) / len(google_results)
    tavily_avg_quality = sum(r['avg_quality'] for r in tavily_results) / len(tavily_results)

    print(f"\n{Colors.BOLD}4. 平均质量对比{Colors.ENDC}")
    print(f"   • Google 平均: {google_avg_quality:.2f}/1.0")
    print(f"   • Tavily 平均: {tavily_avg_quality:.2f}/1.0")
    if google_avg_quality > tavily_avg_quality:
        print(f"   • {Colors.OKGREEN}✅ Google 质量更高 (+{(google_avg_quality - tavily_avg_quality)*100:.1f}%){Colors.ENDC}")
    else:
        print(f"   • {Colors.OKBLUE}✅ Tavily 质量更高 (+{(tavily_avg_quality - google_avg_quality)*100:.1f}%){Colors.ENDC}")

    # 5. 胜率统计
    print(f"\n{Colors.BOLD}5. 胜率统计{Colors.ENDC}")

    google_wins = 0
    tavily_wins = 0
    ties = 0

    for i in range(0, len(all_results), 2):
        if i + 1 >= len(all_results):
            break

        gr = all_results[i]
        tr = all_results[i + 1]

        if gr.get('error') and not tr.get('error'):
            tavily_wins += 1
        elif not gr.get('error') and tr.get('error'):
            google_wins += 1
        elif gr.get('error') and tr.get('error'):
            ties += 1
        else:
            google_score = gr['avg_relevance'] + gr['avg_quality']
            tavily_score = tr['avg_relevance'] + tr['avg_quality']

            if google_score > tavily_score:
                google_wins += 1
            elif tavily_score > google_score:
                tavily_wins += 1
            else:
                ties += 1

    total = google_wins + tavily_wins + ties
    print(f"   • Google 胜: {google_wins}/{total} ({google_wins/total*100:.1f}%)")
    print(f"   • Tavily 胜: {tavily_wins}/{total} ({tavily_wins/total*100:.1f}%)")
    print(f"   • 平局: {ties}/{total} ({ties/total*100:.1f}%)")

    # 6. 最终推荐
    print(f"\n{Colors.BOLD}6. 最终推荐{Colors.ENDC}")

    google_total_score = google_avg_relevance + google_avg_quality + (1.0 - google_avg_time/10)
    tavily_total_score = tavily_avg_relevance + tavily_avg_quality + (1.0 - tavily_avg_time/10)

    print(f"\n   综合评分（考虑相关性、质量、响应时间）:")
    print(f"   • Google: {google_total_score:.2f}")
    print(f"   • Tavily: {tavily_total_score:.2f}")

    if google_total_score > tavily_total_score * 1.05:
        print(f"\n   {Colors.OKGREEN}{Colors.BOLD}🏆 推荐: Google{Colors.ENDC}")
        print(f"   综合表现更优，建议作为主要搜索引擎")
    elif tavily_total_score > google_total_score * 1.05:
        print(f"\n   {Colors.OKBLUE}{Colors.BOLD}🏆 推荐: Tavily{Colors.ENDC}")
        print(f"   综合表现更优，建议作为主要搜索引擎")
    else:
        print(f"\n   {Colors.WARNING}{Colors.BOLD}🤝 推荐: 混合使用{Colors.ENDC}")
        print(f"   两者表现接近，建议根据具体场景选择")

    # 7. 成本对比
    print(f"\n{Colors.BOLD}7. 成本对比{Colors.ENDC}")
    print(f"   • Google: 免费（10,000次/天，公司API）")
    print(f"   • Tavily: >¥0.03/次（无免费额度）")
    print(f"   • {Colors.OKGREEN}✅ Google 成本优势明显{Colors.ENDC}")

    print(f"\n{Colors.BOLD}{'='*70}{Colors.ENDC}\n")


def main():
    """主函数"""
    try:
        # 初始化客户端
        print(f"{Colors.BOLD}初始化搜索引擎客户端...{Colors.ENDC}\n")

        # 初始化 Google 搜索
        google_api_key = os.getenv("GOOGLE_API_KEY")
        google_cx = os.getenv("GOOGLE_CX")

        if not google_api_key or not google_cx:
            print(f"{Colors.WARNING}⚠️ Google 搜索未配置（需要 GOOGLE_API_KEY 和 GOOGLE_CX）{Colors.ENDC}")
            print(f"{Colors.WARNING}请在 .env 文件中配置 Google Custom Search API{Colors.ENDC}\n")
            sys.exit(1)

        google_hunter = SearchHunter(search_engine="google", llm_client=None)
        print(f"{Colors.OKGREEN}✅ Google 搜索客户端初始化成功{Colors.ENDC}")

        # 初始化 Tavily 搜索（通过 llm_client）
        llm_client = UnifiedLLMClient()
        print(f"{Colors.OKGREEN}✅ Tavily 搜索客户端初始化成功{Colors.ENDC}")

        # 开始对比测试
        compare_engines(google_hunter, llm_client)

        print(f"\n{Colors.OKGREEN}✅ 测试完成！{Colors.ENDC}\n")

    except Exception as e:
        print(f"\n{Colors.FAIL}❌ 错误: {e}{Colors.ENDC}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
