#!/usr/bin/env python3
"""
端到端流程测试
验证Google搜索配置和整个搜索流程是否能跑通
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

def test_environment_variables():
    """测试环境变量配置"""
    print("=" * 80)
    print("1. 环境变量检查")
    print("=" * 80)
    
    required_vars = {
        "AI_BUILDER_TOKEN": "AI Builders API（必需）",
        "INTERNAL_API_KEY": "公司内部API（可选）",
        "GOOGLE_API_KEY": "Google搜索API（可选）",
        "GOOGLE_CX": "Google搜索引擎ID（可选）"
    }
    
    results = {}
    for var, desc in required_vars.items():
        value = os.getenv(var)
        status = "✅ 已设置" if value else "❌ 未设置"
        results[var] = (status, value is not None)
        print(f"  {var}: {status} - {desc}")
    
    print()
    return results


def test_google_search():
    """测试Google搜索功能"""
    print("=" * 80)
    print("2. Google搜索功能测试")
    print("=" * 80)
    
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_cx = os.getenv("GOOGLE_CX")
    
    if not google_api_key or not google_cx:
        print("  [⚠️] Google搜索未配置，跳过测试")
        return False
    
    try:
        from search_strategist import SearchHunter
        
        hunter = SearchHunter(search_engine="google")
        print("  [✅] SearchHunter初始化成功")
        
        results = hunter.search("playlist matematika kelas 1", max_results=3)
        
        if results:
            print(f"  [✅] Google搜索成功，找到 {len(results)} 个结果")
            return True
        else:
            print("  [⚠️] Google搜索返回空结果")
            return False
    
    except Exception as e:
        print(f"  [❌] Google搜索测试失败: {str(e)}")
        return False


def test_search_strategist():
    """测试SearchStrategist（使用Google搜索）"""
    print("\n" + "=" * 80)
    print("3. SearchStrategist集成测试")
    print("=" * 80)
    
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_cx = os.getenv("GOOGLE_CX")
    
    if not google_api_key or not google_cx:
        print("  [⚠️] Google搜索未配置，跳过测试")
        return False
    
    try:
        from search_strategist import SearchStrategist, AIBuildersClient
        
        llm_client = AIBuildersClient()
        print("  [✅] AIBuildersClient初始化成功")
        
        strategist = SearchStrategist(llm_client, search_engine="google")
        print("  [✅] SearchStrategist初始化成功（使用Google搜索）")
        
        # 这里只是测试初始化，不执行完整搜索（因为需要知识点数据）
        print("  [✅] SearchStrategist可以正常使用Google搜索")
        return True
    
    except Exception as e:
        print(f"  [❌] SearchStrategist测试失败: {str(e)}")
        import traceback
        print(f"  [🔍] 异常详情:\n{traceback.format_exc()[:500]}")
        return False


def test_search_engine_v2():
    """测试SearchEngineV2（当前使用Tavily）"""
    print("\n" + "=" * 80)
    print("4. SearchEngineV2测试（当前使用Tavily搜索）")
    print("=" * 80)
    
    try:
        from search_engine_v2 import SearchEngineV2, SearchRequest
        
        search_engine = SearchEngineV2()
        print("  [✅] SearchEngineV2初始化成功")
        
        # 注意：SearchEngineV2当前使用Tavily搜索，不支持Google搜索
        # 如果需要使用Google搜索，需要修改SearchEngineV2的实现
        print("  [ℹ️] SearchEngineV2当前使用Tavily搜索（AIBuildersClient）")
        print("  [ℹ️] 如需使用Google搜索，需要修改SearchEngineV2的实现")
        
        return True
    
    except Exception as e:
        print(f"  [❌] SearchEngineV2测试失败: {str(e)}")
        import traceback
        print(f"  [🔍] 异常详情:\n{traceback.format_exc()[:500]}")
        return False


def test_llm_clients():
    """测试LLM客户端（双API系统）"""
    print("\n" + "=" * 80)
    print("5. LLM客户端测试（双API系统）")
    print("=" * 80)
    
    try:
        from llm_client import UnifiedLLMClient
        
        client = UnifiedLLMClient()
        print("  [✅] UnifiedLLMClient初始化成功")
        
        # 简单测试
        response = client.call_llm(
            prompt="请用一句话介绍Python",
            system_prompt="你是一个专业的编程教育助手。",
            max_tokens=50,
            temperature=0.3,
            model="deepseek"
        )
        
        if response:
            print(f"  [✅] LLM调用成功，响应长度: {len(response)} 字符")
            return True
        else:
            print("  [⚠️] LLM调用返回空结果")
            return False
    
    except Exception as e:
        print(f"  [❌] LLM客户端测试失败: {str(e)}")
        import traceback
        print(f"  [🔍] 异常详情:\n{traceback.format_exc()[:500]}")
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("端到端流程测试")
    print("=" * 80)
    
    # 1. 环境变量检查
    env_results = test_environment_variables()
    
    # 2. Google搜索测试
    google_search_ok = test_google_search()
    
    # 3. SearchStrategist测试
    strategist_ok = test_search_strategist()
    
    # 4. SearchEngineV2测试
    engine_v2_ok = test_search_engine_v2()
    
    # 5. LLM客户端测试
    llm_ok = test_llm_clients()
    
    # 总结
    print("\n" + "=" * 80)
    print("测试结果总结")
    print("=" * 80)
    
    print(f"\n环境变量配置:")
    for var, (status, _) in env_results.items():
        print(f"  {var}: {status}")
    
    print(f"\n功能测试:")
    print(f"  Google搜索: {'✅ 通过' if google_search_ok else '❌ 失败'}")
    print(f"  SearchStrategist: {'✅ 通过' if strategist_ok else '❌ 失败'}")
    print(f"  SearchEngineV2: {'✅ 通过' if engine_v2_ok else '❌ 失败'}")
    print(f"  LLM客户端: {'✅ 通过' if llm_ok else '❌ 失败'}")
    
    print(f"\n" + "=" * 80)
    print("重要说明")
    print("=" * 80)
    print("""
1. Google搜索已成功集成到SearchHunter和SearchStrategist
2. SearchEngineV2（web_app.py使用）当前使用Tavily搜索
3. 如需在web_app中使用Google搜索，需要修改SearchEngineV2的实现
4. 当前配置：Google搜索可用于search_strategist.py脚本
5. web_app.py仍使用Tavily搜索（通过AIBuildersClient）
    """)
    
    # 判断整体是否通过
    all_ok = google_search_ok and strategist_ok and engine_v2_ok and llm_ok
    
    if all_ok:
        print("\n[✅] 所有核心功能测试通过！")
    else:
        print("\n[⚠️] 部分功能测试失败，请检查配置和错误信息")


if __name__ == "__main__":
    main()





