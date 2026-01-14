#!/usr/bin/env python3
"""
测试多次搜索操作，模拟网页崩溃场景
"""
import urllib.request
import urllib.parse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://localhost:5000"

# 测试搜索组合
SEARCH_COMBINATIONS = [
    {"country": "NG", "grade": "Primary 1", "subject": "English Language"},
    {"country": "NG", "grade": "Primary 2", "subject": "Mathematics"},
    {"country": "NG", "grade": "Primary 3", "subject": "Science"},
    {"country": "NG", "grade": "Primary 4", "subject": "Social Studies"},
    {"country": "NG", "grade": "Primary 5", "subject": "English Language"},
    {"country": "NG", "grade": "Primary 6", "subject": "Mathematics"},
    {"country": "NG", "grade": "JSS 1", "subject": "English Language"},
    {"country": "NG", "grade": "JSS 2", "subject": "Mathematics"},
    {"country": "NG", "grade": "JSS 3", "subject": "Science"},
    {"country": "NG", "grade": "SSS 1", "subject": "English Language"},
]

def perform_search(combination, index):
    """执行单个搜索"""
    try:
        print(f"[搜索 {index+1}/{len(SEARCH_COMBINATIONS)}] 开始: {combination['country']} - {combination['grade']} - {combination['subject']}")
        
        # 使用urllib发送POST请求
        data = json.dumps(combination).encode('utf-8')
        req = urllib.request.Request(
            f"{BASE_URL}/api/search",
            data=data,
            headers={"Content-Type": "application/json"},
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=120) as response:
            status_code = response.getcode()
            if status_code == 200:
                data = json.loads(response.read().decode('utf-8'))
                result_count = len(data.get('results', []))
                print(f"[搜索 {index+1}/{len(SEARCH_COMBINATIONS)}] ✅ 完成: 结果数={result_count}, 成功={data.get('success', False)}")
                return {"success": True, "index": index, "result_count": result_count}
            else:
                print(f"[搜索 {index+1}/{len(SEARCH_COMBINATIONS)}] ❌ 失败: HTTP {status_code}")
                return {"success": False, "index": index, "error": f"HTTP {status_code}"}
            
    except Exception as e:
        print(f"[搜索 {index+1}/{len(SEARCH_COMBINATIONS)}] ❌ 异常: {str(e)}")
        return {"success": False, "index": index, "error": str(e)}

def test_concurrent_searches(max_workers=5):
    """并发搜索测试"""
    print("\n" + "=" * 80)
    print(f"测试: 并发搜索（max_workers={max_workers}）")
    print("=" * 80)
    
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(perform_search, combination, i): i
            for i, combination in enumerate(SEARCH_COMBINATIONS)
        }
        
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
    
    success_count = sum(1 for r in results if r.get('success'))
    print(f"\n并发搜索完成: 成功={success_count}/{len(results)}")
    return results

def test_multiple_rounds(rounds=3):
    """多轮测试"""
    print("\n" + "=" * 80)
    print(f"测试: 多轮测试（{rounds}轮）")
    print("=" * 80)
    
    all_results = []
    for round_num in range(rounds):
        print(f"\n--- 第 {round_num+1} 轮测试 ---")
        results = test_concurrent_searches(max_workers=5)
        all_results.extend(results)
        time.sleep(2)  # 每轮之间间隔2秒
    
    success_count = sum(1 for r in all_results if r.get('success'))
    print(f"\n多轮测试完成: 总成功={success_count}/{len(all_results)}")
    return all_results

if __name__ == "__main__":
    print("开始测试多次搜索操作...")
    print(f"服务器地址: {BASE_URL}")
    print(f"测试组合数: {len(SEARCH_COMBINATIONS)}")
    
    # 检查服务器是否运行
    try:
        req = urllib.request.Request(f"{BASE_URL}/")
        with urllib.request.urlopen(req, timeout=5) as response:
            status_code = response.getcode()
            print(f"✅ 服务器连接正常 (状态码: {status_code})")
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        print("请确保服务器正在运行: python3 web_app.py")
        exit(1)
    
    # 执行测试
    try:
        # 测试: 多轮并发搜索
        multi_round_results = test_multiple_rounds(rounds=3)
        
        print("\n" + "=" * 80)
        print("所有测试完成！")
        print("=" * 80)
        print("\n请检查日志文件以查看是否有错误或崩溃:")
        print("  - web_app.log")
        print("  - flask.log")
        print("  - search_system.log")
        print("\n特别关注是否有semaphore泄漏警告:")
        print("  - resource_tracker: There appear to be X leaked semaphore objects")
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
