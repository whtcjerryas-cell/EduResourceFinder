#!/usr/bin/env python3
"""测试Excel导出功能"""

import requests
import json

# 先进行搜索
search_data = {
    "country": "Egypt",
    "countryCode": "EG",
    "grade": "Grade 1",
    "semester": "Semester 1",
    "subject": "Physics",
    "query": "physics grade 1",
    "resourceType": "video"
}

print("🔍 步骤1: 执行搜索...")
response = requests.post(
    "http://localhost:5001/api/search",
    json=search_data,
    timeout=60,
    headers={"Content-Type": "application/json"}
)

result = response.json()
results = result.get('results', [])
print(f"✅ 搜索完成，找到 {len(results)} 个结果\n")

# 取前3个结果测试导出
test_results = results[:3]
print(f"📊 步骤2: 导出前3个结果到Excel...")

export_data = {
    "selected_results": test_results,
    "search_params": {
        "country": "Egypt",
        "grade": "Grade 1",
        "subject": "Physics",
        "semester": "Semester 1"
    }
}

print(f"导出数据:")
print(f"  - 结果数量: {len(export_data['selected_results'])}")
print(f"  - search_params: {export_data['search_params']}")

response = requests.post(
    "http://localhost:5001/api/export_excel",
    json=export_data,
    timeout=30,
    headers={"Content-Type": "application/json"}
)

if response.status_code == 200:
    # 保存Excel文件
    output_file = "/tmp/test_export.xlsx"
    with open(output_file, 'wb') as f:
        f.write(response.content)

    print(f"\n✅ Excel导出成功!")
    print(f"   文件大小: {len(response.content)} bytes")
    print(f"   保存位置: {output_file}")

    # 读取Excel文件并检查内容
    try:
        import pandas as pd
        df = pd.read_excel(output_file, sheet_name='搜索结果')

        print(f"\n📋 Excel内容检查:")
        print(f"   - 总行数: {len(df)}")
        print(f"   - 列名: {list(df.columns)}")

        # 检查第一行的国家、年级、学科
        if len(df) > 0:
            first_row = df.iloc[0]
            print(f"\n🔍 第一行数据:")
            print(f"   - 序号: {first_row['序号']}")
            print(f"   - 国家: '{first_row['国家']}'")
            print(f"   - 年级: '{first_row['年级']}'")
            print(f"   - 学科: '{first_row['学科']}'")

            # 检查是否为空
            if pd.isna(first_row['国家']) or first_row['国家'] == '':
                print("   ❌ 国家列为空!")
            else:
                print("   ✅ 国家列有数据")

            if pd.isna(first_row['年级']) or first_row['年级'] == '':
                print("   ❌ 年级列为空!")
            else:
                print("   ✅ 年级列有数据")

            if pd.isna(first_row['学科']) or first_row['学科'] == '':
                print("   ❌ 学科列为空!")
            else:
                print("   ✅ 学科列有数据")
    except Exception as e:
        print(f"❌ 读取Excel失败: {e}")
else:
    print(f"❌ Excel导出失败: {response.status_code}")
    print(f"   错误信息: {response.text}")
