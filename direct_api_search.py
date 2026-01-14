#!/usr/bin/env python3
"""
直接调用后端API进行批量搜索并导出Excel
不需要前端，直接请求后端服务
"""
import requests
import json
import pandas as pd
from datetime import datetime
import time
import os

# API配置
API_BASE_URL = "http://localhost:5001"
SEARCH_ENDPOINT = f"{API_BASE_URL}/api/search"

# 搜索配置
COUNTRY = "伊拉克"
GRADES = ["一年级", "二年级", "三年级"]
SUBJECTS = ["数学", "英语"]

# 搜索次数（每个年级-学科组合）
NUM_ROUNDS = 3  # 每个组合搜索3次以获取更多结果

# 输出文件
OUTPUT_DIR = "./data/batch_search_results"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"伊拉克_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)


def search_api(country, grade, subject, timeout=180):
    """
    调用搜索API

    Args:
        country: 国家
        grade: 年级
        subject: 学科
        timeout: 超时时间（秒）

    Returns:
        搜索结果字典，如果失败返回None
    """
    payload = {
        "country": country,
        "grade": grade,
        "subject": subject
    }

    try:
        print(f"  🔄 搜索: {country} - {grade} - {subject}")
        response = requests.post(
            SEARCH_ENDPOINT,
            json=payload,
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                results = data.get("results", [])
                print(f"  ✅ 成功: 找到 {len(results)} 条结果")
                return {
                    "country": country,
                    "grade": grade,
                    "subject": subject,
                    "results": results,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                print(f"  ⚠️ API返回失败: {data.get('message', '未知错误')}")
                return None
        else:
            print(f"  ❌ HTTP错误: {response.status_code}")
            return None

    except requests.exceptions.Timeout:
        print(f"  ⏱️ 超时: 请求超过 {timeout} 秒")
        return None
    except Exception as e:
        print(f"  ❌ 异常: {str(e)}")
        return None


def flatten_results(search_data):
    """
    将搜索结果扁平化为DataFrame

    Args:
        search_data: 搜索数据字典

    Returns:
        pandas DataFrame
    """
    flattened = []

    for result in search_data.get("results", []):
        row = {
            "国家": search_data["country"],
            "年级": search_data["grade"],
            "学科": search_data["subject"],
            "标题": result.get("title", ""),
            "URL": result.get("url", ""),
            "描述": result.get("snippet", ""),
            "评分": result.get("score", 0),
            "推荐理由": result.get("recommendation_reason", ""),
            "资源类型": result.get("resource_type", "unknown"),
            "搜索时间": search_data["timestamp"]
        }
        flattened.append(row)

    return pd.DataFrame(flattened)


def main():
    """主函数"""
    print("=" * 80)
    print("伊拉克教育资源批量搜索 - 直接API调用")
    print("=" * 80)
    print(f"目标: {COUNTRY}")
    print(f"年级: {', '.join(GRADES)}")
    print(f"学科: {', '.join(SUBJECTS)}")
    print(f"输出: {OUTPUT_FILE}")
    print("=" * 80)

    # 检查服务器是否运行
    try:
        response = requests.get(API_BASE_URL, timeout=5)
        if response.status_code != 200:
            print(f"❌ 服务器未响应，请先启动服务器:")
            print(f"   cd /Users/shmiwanghao8/Desktop/education/Indonesia")
            print(f"   source venv/bin/activate")
            # 从环境变量读取API密钥进行显示（安全改进：不再硬编码）
            api_key = os.getenv('INTERNAL_API_KEY', 'your-api-key-here')
            # 只显示密钥的前8个和后4个字符，中间用星号代替
            masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
            print(f"   INTERNAL_API_KEY={api_key} \\")
            print(f"   python3 web_app.py")
            return
    except Exception as e:
        print(f"❌ 无法连接到服务器: {str(e)}")
        print(f"   请确保服务器正在运行在 {API_BASE_URL}")
        return

    print("✅ 服务器连接正常")
    print()

    # 收集所有搜索结果
    all_results = []
    total_searches = len(GRADES) * len(SUBJECTS) * NUM_ROUNDS
    completed_searches = 0

    # 执行批量搜索
    for grade in GRADES:
        for subject in SUBJECTS:
            print(f"\n{'=' * 60}")
            print(f"搜索组合: {grade} - {subject}")
            print(f"{'=' * 60}")

            round_results = []
            for round_num in range(1, NUM_ROUNDS + 1):
                print(f"\n第 {round_num} 轮搜索:")
                search_data = search_api(COUNTRY, grade, subject, timeout=180)

                if search_data:
                    round_results.extend(search_data.get("results", []))

                completed_searches += 1
                print(f"进度: {completed_searches}/{total_searches} ({completed_searches*100//total_searches}%)")

                # 每轮之间等待2秒，避免服务器过载
                if round_num < NUM_ROUNDS:
                    print("  ⏸️ 等待2秒...")
                    time.sleep(2)

            # 合并该组合的所有轮次结果（去重）
            if round_results:
                # 按URL去重
                unique_results = {}
                for result in round_results:
                    url = result.get("url", "")
                    if url and url not in unique_results:
                        unique_results[url] = result

                combined_search_data = {
                    "country": COUNTRY,
                    "grade": grade,
                    "subject": subject,
                    "results": list(unique_results.values()),
                    "timestamp": datetime.now().isoformat()
                }

                df = flatten_results(combined_search_data)
                if not df.empty:
                    all_results.append(df)
                    print(f"  📊 该组合总计: {len(df)} 条唯一结果")

    # 合并所有结果到一个DataFrame
    if all_results:
        print(f"\n{'=' * 80}")
        print("合并所有结果并导出Excel...")
        print(f"{'=' * 80}")

        final_df = pd.concat(all_results, ignore_index=True)

        # 按评分降序排序
        final_df = final_df.sort_values(by=["评分"], ascending=False)

        # 重置索引
        final_df.reset_index(drop=True, inplace=True)

        # 保存到Excel
        print(f"💾 保存到: {OUTPUT_FILE}")
        final_df.to_excel(OUTPUT_FILE, index=False, engine='openpyxl')

        print(f"\n{'=' * 80}")
        print(f"✅ 导出完成!")
        print(f"{'=' * 80}")
        print(f"总结果数: {len(final_df)} 条")
        print(f"文件位置: {OUTPUT_FILE}")
        print(f"\n按年级统计:")
        print(final_df.groupby("年级").size())
        print(f"\n按学科统计:")
        print(final_df.groupby("学科").size())
        print(f"\n评分分布:")
        print(final_df["评分"].describe())
        print(f"{'=' * 80}")

        # 显示前10条结果
        print(f"\n📋 前10条结果:")
        print(f"{'=' * 80}")
        for idx, row in final_df.head(10).iterrows():
            print(f"\n{idx + 1}. [{row['评分']:.1f}分] {row['标题'][:60]}")
            print(f"   年级: {row['年级']} | 学科: {row['学科']}")
            print(f"   推荐: {row['推荐理由'][:80]}")

    else:
        print(f"\n❌ 没有找到任何结果")


if __name__ == "__main__":
    main()
