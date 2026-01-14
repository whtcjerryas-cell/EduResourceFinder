#!/usr/bin/env python3
"""
诊断搜索多个条件导致崩溃的问题
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.concurrency_limiter import get_concurrency_limiter
import threading
import time

def test_concurrency_limiter():
    """测试并发限制器"""
    print("=" * 60)
    print("测试并发限制器")
    print("=" * 60)
    
    limiter = get_concurrency_limiter()
    print(f"最大并发数: {limiter.max_concurrent}")
    print(f"当前并发数: {len(limiter.active_requests)}")
    print(f"统计信息: {limiter.get_stats()}")
    
    # 测试acquire/release配对
    print("\n测试acquire/release配对...")
    acquired = limiter.acquire(timeout=1.0)
    if acquired:
        print("✅ acquire成功")
        print(f"当前并发数: {len(limiter.active_requests)}")
        limiter.release()
        print("✅ release成功")
        print(f"当前并发数: {len(limiter.active_requests)}")
    else:
        print("❌ acquire失败")
    
    # 测试多次acquire/release
    print("\n测试多次acquire/release...")
    for i in range(5):
        acquired = limiter.acquire(timeout=1.0)
        if acquired:
            print(f"✅ 第{i+1}次acquire成功")
            limiter.release()
            print(f"✅ 第{i+1}次release成功")
        else:
            print(f"❌ 第{i+1}次acquire失败")
    
    print(f"\n最终统计信息: {limiter.get_stats()}")
    print("=" * 60)

def test_multiple_threads():
    """测试多线程并发"""
    print("\n" + "=" * 60)
    print("测试多线程并发")
    print("=" * 60)
    
    limiter = get_concurrency_limiter()
    results = []
    
    def worker(thread_id):
        """工作线程"""
        try:
            acquired = limiter.acquire(timeout=5.0)
            if acquired:
                results.append(f"线程{thread_id}: acquire成功")
                time.sleep(0.5)  # 模拟工作
                limiter.release()
                results.append(f"线程{thread_id}: release成功")
            else:
                results.append(f"线程{thread_id}: acquire超时")
        except Exception as e:
            results.append(f"线程{thread_id}: 异常 - {str(e)}")
    
    # 启动5个线程（超过最大并发数2）
    threads = []
    for i in range(5):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    # 等待所有线程完成
    for t in threads:
        t.join()
    
    print("\n结果:")
    for result in results:
        print(f"  {result}")
    
    print(f"\n最终统计信息: {limiter.get_stats()}")
    print("=" * 60)

if __name__ == "__main__":
    test_concurrency_limiter()
    test_multiple_threads()
    
    print("\n✅ 诊断完成")
    print("\n如果看到以下问题，请检查：")
    print("1. ❌ acquire/release不配对 - 检查web_app.py中的acquired_limiter标志")
    print("2. ❌ 并发数超过限制 - 检查MAX_CONCURRENT_SEARCHES环境变量")
    print("3. ❌ 线程异常 - 检查错误处理逻辑")
