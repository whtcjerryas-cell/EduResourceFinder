#!/usr/bin/env python3
"""
分析搜索结果Excel文件
"""
import sys
import pandas as pd
from pathlib import Path

def analyze_excel(file_path):
    """分析单个Excel文件"""
    print(f"\n{'='*80}")
    print(f"📄 文件: {Path(file_path).name}")
    print(f"{'='*80}")

    try:
        # 读取Excel文件
        df = pd.read_excel(file_path)

        print(f"\n📊 基本信息:")
        print(f"  总行数: {len(df)}")
        print(f"  列数: {len(df.columns)}")
        print(f"  列名: {list(df.columns)}")

        if len(df) == 0:
            print("  ⚠️ 文件为空！")
            return {
                'total_rows': 0,
                'countries': {},
                'issues': ['文件为空']
            }

        # 显示前几行
        print(f"\n📋 前5行数据:")
        print(df.head().to_string())

        # 分析国家分布
        if '国家' in df.columns:
            country_counts = df['国家'].value_counts().to_dict()
            print(f"\n🌍 国家分布:")
            for country, count in country_counts.items():
                print(f"  {country}: {count}条")

            return {
                'total_rows': len(df),
                'countries': country_counts,
                'issues': []
            }
        else:
            print("  ⚠️ 未找到'国家'列")
            return {
                'total_rows': len(df),
                'countries': {},
                'issues': ['未找到国家列']
            }

    except Exception as e:
        print(f"❌ 读取失败: {str(e)}")
        return {
            'total_rows': 0,
            'countries': {},
            'issues': [f"读取失败: {str(e)}"]
        }


def main():
    """主函数"""
    base_path = "/Users/shmiwanghao8/Downloads"

    files = [
        "批量搜索_2026-01-09 (4).xlsx",
        "批量搜索_2026-01-09 (5).xlsx",
        "批量搜索_2026-01-09 (6).xlsx",
    ]

    results = {}

    for file in files:
        file_path = f"{base_path}/{file}"
        if Path(file_path).exists():
            results[file] = analyze_excel(file_path)
        else:
            print(f"\n⚠️ 文件不存在: {file}")
            results[file] = {
                'total_rows': 0,
                'countries': {},
                'issues': ['文件不存在']
            }

    # 汇总分析
    print(f"\n{'='*80}")
    print("📊 汇总分析")
    print(f"{'='*80}")

    for file, data in results.items():
        print(f"\n{file}:")
        print(f"  总行数: {data['total_rows']}")
        if data['countries']:
            print(f"  国家分布:")
            for country, count in data['countries'].items():
                print(f"    {country}: {count}条")
        if data['issues']:
            print(f"  问题: {', '.join(data['issues'])}")

    # 问题诊断
    print(f"\n{'='*80}")
    print("🔍 问题诊断")
    print(f"{'='*80}")

    for file, data in results.items():
        if data['total_rows'] == 0:
            print(f"\n❌ {file}: 结果为空")
            print("   可能原因:")
            print("   1. 搜索引擎调用失败")
            print("   2. API限制/配额用尽")
            print("   3. 网络问题")
            print("   4. 搜索词生成错误")
        elif data['total_rows'] < 10:
            print(f"\n⚠️ {file}: 结果过少（{data['total_rows']}条）")
            print("   可能原因:")
            print("   1. 搜索词不够精准")
            print("   2. 搜索引擎限制")
            print("   3. 目标内容确实稀缺")
        else:
            print(f"\n✅ {file}: 结果正常（{data['total_rows']}条）")


if __name__ == "__main__":
    main()
