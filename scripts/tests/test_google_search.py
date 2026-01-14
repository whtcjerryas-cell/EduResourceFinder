#!/usr/bin/env python3
"""
测试Google Custom Search API集成
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 支持从 .env 文件读取环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    def load_dotenv():
        env_file = project_root / '.env'
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip().strip('"').strip("'")
    load_dotenv()

from search_strategist import SearchHunter, AIBuildersClient


def test_google_search():
    """测试Google搜索功能"""
    print("=" * 80)
    print("测试Google Custom Search API")
    print("=" * 80)
    
    # 检查环境变量
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_cx = os.getenv("GOOGLE_CX", "56e7e6dc917ed481e")
    
    print(f"\n[📋] 环境变量检查:")
    print(f"  GOOGLE_API_KEY: {'✅ 已设置' if google_api_key else '❌ 未设置'}")
    print(f"  GOOGLE_CX: {google_cx}")
    
    if not google_api_key:
        print("\n[❌] 错误: 请设置 GOOGLE_API_KEY 环境变量")
        print("   在 .env 文件中添加: GOOGLE_API_KEY=your_api_key")
        return False
    
    # 初始化搜索器
    try:
        hunter = SearchHunter(search_engine="google")
        print("\n[✅] Google搜索器初始化成功")
    except Exception as e:
        print(f"\n[❌] 初始化失败: {str(e)}")
        return False
    
    # 测试搜索
    test_queries = [
        "Zootopia2",
        "playlist matematika kelas 1",
        "ruangguru playlist"
    ]
    
    for query in test_queries:
        print(f"\n{'=' * 80}")
        print(f"测试查询: \"{query}\"")
        print(f"{'=' * 80}")
        
        try:
            results = hunter.search(query, max_results=5)
            
            if results:
                print(f"\n[✅] 搜索成功，找到 {len(results)} 个结果:")
                for i, result in enumerate(results, 1):
                    print(f"\n  [{i}] {result.title}")
                    print(f"      URL: {result.url}")
                    print(f"      Snippet: {result.snippet[:100]}...")
            else:
                print(f"\n[⚠️] 搜索返回空结果")
        
        except Exception as e:
            print(f"\n[❌] 搜索失败: {str(e)}")
            import traceback
            print(f"[🔍] 异常详情:\n{traceback.format_exc()[:500]}")
            return False
    
    print(f"\n{'=' * 80}")
    print("[✅] 所有测试通过！")
    print(f"{'=' * 80}")
    return True


if __name__ == "__main__":
    success = test_google_search()
    sys.exit(0 if success else 1)





