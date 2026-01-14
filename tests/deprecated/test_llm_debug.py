#!/usr/bin/env python3
"""Debug the search response format"""

import requests
import json

SERVER_URL = "http://localhost:5001"
SEARCH_ENDPOINT = f"{SERVER_URL}/api/search"

search_data = {
    "country": "Indonesia",
    "countryCode": "ID",
    "grade": "Grade 2",
    "semester": "Semester 1",
    "subject": "Mathematics",
    "query": "penjumlahan dan pengurangan",
    "resourceType": "video",
    "maxResults": 5
}

print("🔍 发送搜索请求...")
response = requests.post(
    SEARCH_ENDPOINT,
    json=search_data,
    timeout=120,
    headers={"Content-Type": "application/json"}
)

print(f"状态码: {response.status_code}")
print(f"\n完整响应:")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
