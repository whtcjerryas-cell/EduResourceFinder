#!/usr/bin/env python3
"""
分析Excel搜索结果，查找质量问题
"""

import sys
from pathlib import Path
import pandas as pd

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

excel_file = project_root / "outputs/批量搜索_2026-01-13 (1).xlsx"

if not excel_file.exists():
    print(f"❌ 文件不存在: {excel_file}")
    sys.exit(1)

# 读取Excel
df = pd.read_excel(excel_file)

print("=" * 80)
print(f"分析搜索结果: {excel_file.name}")
print("=" * 80)
print(f"\n总结果数: {len(df)}\n")

# 统计各列的基本信息
print("列名:")
for col in df.columns:
    print(f"  - {col}")

print("\n" + "=" * 80)
print("质量分数分布")
print("=" * 80)

score_stats = df['质量分数'].describe()
print(f"\n最小值: {score_stats['min']:.1f}")
print(f"最大值: {score_stats['max']:.1f}")
print(f"平均值: {score_stats['mean']:.1f}")
print(f"中位数: {score_stats['50%']:.1f}")

# 按分数段统计
print("\n分数段分布:")
bins = [0, 3, 5, 7, 10]
labels = ['低分 (0-3)', '中低分 (3-5)', '中高分 (5-7)', '高分 (7-10)']
df['分数段'] = pd.cut(df['质量分数'], bins=bins, labels=labels, include_lowest=True)
score_distribution = df['分数段'].value_counts().sort_index()

for label, count in score_distribution.items():
    percentage = count / len(df) * 100
    print(f"  {label}: {count} 条 ({percentage:.1f}%)")

# 分析问题
print("\n" + "=" * 80)
print("问题分析")
print("=" * 80)

issues = []

# 1. 高分但年级可能不匹配
print("\n1. 高分结果 (≥8分) 需要人工审查:")
high_score = df[df['质量分数'] >= 8.0]
print(f"   数量: {len(high_score)} 条")

for idx, row in high_score.head(10).iterrows():
    title = str(row.get('标题', ''))[:70]
    score = row.get('质量分数', 0)
    grade = str(row.get('年级', ''))
    subject = str(row.get('学科', ''))
    reason = str(row.get('推荐理由', ''))[:60]

    print(f"\n   [{idx+1}] 分数: {score}")
    print(f"       标题: {title}")
    print(f"       年级/学科: {grade} / {subject}")
    print(f"       理由: {reason}...")

    # 检查是否有明显问题
    if 'Kelas 6' in title and 'Kelas 1' in grade:
        issues.append({
            'type': '年级不匹配但高分',
            'idx': idx,
            'title': title,
            'score': score,
            'reason': '标题包含Kelas 6但搜索Kelas 1'
        })
    elif 'instagram.com' in row.get('链接', '').lower() and score > 0:
        issues.append({
            'type': '社交媒体未过滤',
            'idx': idx,
            'title': title,
            'score': score,
            'reason': 'Instagram URL应该给0分'
        })
    elif 'facebook.com' in row.get('链接', '').lower() and score > 0:
        issues.append({
            'type': '社交媒体未过滤',
            'idx': idx,
            'title': title,
            'score': score,
            'reason': 'Facebook URL应该给0分'
        })

# 2. 检查低分结果
print("\n2. 低分结果 (<5分) 分析:")
low_score = df[df['质量分数'] < 5.0]
print(f"   数量: {len(low_score)} 条")

for idx, row in low_score.head(5).iterrows():
    title = str(row.get('标题', ''))[:70]
    score = row.get('质量分数', 0)
    reason = str(row.get('推荐理由', ''))[:80]
    print(f"\n   [{idx+1}] 分数: {score}")
    print(f"       标题: {title}")
    print(f"       理由: {reason}...")

# 总结问题
print("\n" + "=" * 80)
print("发现的问题")
print("=" * 80)

if issues:
    print(f"\n共发现 {len(issues)} 个问题:\n")
    for i, issue in enumerate(issues, 1):
        print(f"{i}. [{issue['type']}]")
        print(f"   位置: 结果 #{issue['idx']+1}")
        print(f"   标题: {issue['title']}")
        print(f"   分数: {issue['score']}")
        print(f"   问题: {issue['reason']}")
        print()
else:
    print("\n✅ 未发现明显问题")

# 保存问题列表到CSV
if issues:
    issues_df = pd.DataFrame(issues)
    issues_file = project_root / "outputs/质量问题分析.csv"
    issues_df.to_csv(issues_file, index=False, encoding='utf-8-sig')
    print(f"问题列表已保存到: {issues_file}")

print("\n" + "=" * 80)
