#!/usr/bin/env python3
"""
测试本地化搜索修复效果
验证：
1. 域名过滤逻辑已取消（EdTech平台也被包含）
2. 本地搜索词不包含"playlist"
3. site:语法正确添加
"""

from search_engine_v2 import SearchEngineV2, SearchRequest
from config_manager import ConfigManager

def test_local_search():
    """测试印尼本地搜索"""
    print("="*80)
    print("🧪 测试本地化搜索修复")
    print("="*80)
    
    # 初始化
    engine = SearchEngineV2()
    config_manager = ConfigManager()
    
    # 获取印尼配置
    id_config = config_manager.get_country_config("ID")
    if not id_config:
        print("❌ 错误: 无法获取印尼配置")
        return
    
    print(f"\n📋 印尼配置信息:")
    print(f"   国家: {id_config.country_name}")
    print(f"   语言: {id_config.language_code}")
    print(f"   域名数量: {len(id_config.domains)}")
    print(f"   域名列表:")
    for idx, domain in enumerate(id_config.domains, 1):
        print(f"      {idx}. {domain}")
    
    # 创建搜索请求
    request = SearchRequest(
        country="ID",
        grade="Kelas 3",
        subject="Matematika",
        language="id"
    )
    
    print(f"\n🔍 搜索请求:")
    print(f"   国家: {request.country}")
    print(f"   年级: {request.grade}")
    print(f"   学科: {request.subject}")
    
    # 执行搜索
    print(f"\n🚀 开始执行搜索...")
    print("="*80)
    
    try:
        response = engine.search(request)
        
        print("\n" + "="*80)
        print("📊 搜索结果统计:")
        print("="*80)
        print(f"   成功: {response.success}")
        print(f"   查询词: {response.query}")
        print(f"   结果总数: {response.total_count}")
        print(f"   播放列表数: {response.playlist_count}")
        print(f"   视频数: {response.video_count}")
        
        # 检查本地平台结果
        print(f"\n📋 结果详情（前10个）:")
        local_platforms = ["ruangguru.com", "zenius.net", "quipper.com", "vidio.com"]
        local_count = 0
        
        for idx, result in enumerate(response.results[:10], 1):
            url_lower = result.url.lower()
            is_local = any(platform in url_lower for platform in local_platforms)
            
            marker = "✅" if is_local else "  "
            if is_local:
                local_count += 1
            
            print(f"   {marker} {idx}. {result.title[:60]}...")
            print(f"      URL: {result.url}")
            if result.score > 0:
                print(f"      评分: {result.score:.1f}")
        
        print(f"\n📊 本地平台结果统计:")
        print(f"   本地平台结果数: {local_count}/{len(response.results[:10])}")
        
        # 验证查询词
        print(f"\n✅ 验证检查:")
        print(f"   1. 查询词包含site:语法: {'site:' in response.query}")
        print(f"   2. 查询词不包含playlist（针对本地搜索）: {'playlist' not in response.query.lower()}")
        
        if local_count > 0:
            print(f"\n✅ 测试通过: 找到 {local_count} 个本地平台结果")
        else:
            print(f"\n⚠️ 警告: 未找到本地平台结果，可能需要检查搜索逻辑")
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_local_search()

