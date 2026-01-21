#!/usr/bin/env python3
"""
测试 VideoProcessorService 的基本功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.video_processor import VideoCrawler, process_video
from utils.logger_utils import get_logger

logger = get_logger('test_video_processor')


def test_imports():
    """测试导入"""
    print("="*50)
    print("测试1: 导入检查")
    print("="*50)
    
    try:
        from core.video_processor import VideoCrawler, process_video
        print("✅ VideoCrawler 导入成功")
        print("✅ process_video 函数导入成功")
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_instantiation():
    """测试实例化"""
    print("\n" + "="*50)
    print("测试2: 实例化检查")
    print("="*50)
    
    try:
        crawler = VideoCrawler()
        print("✅ VideoCrawler 实例化成功")
        return True
    except Exception as e:
        print(f"❌ 实例化失败: {e}")
        return False


def test_dependencies():
    """测试依赖检查"""
    print("\n" + "="*50)
    print("测试3: 依赖检查")
    print("="*50)
    
    try:
        import yt_dlp
        print("✅ yt-dlp 已安装")
    except ImportError:
        print("⚠️  yt-dlp 未安装，请运行: pip install yt-dlp")
    
    try:
        import ffmpeg
        print("✅ ffmpeg-python 已安装")
    except ImportError:
        print("⚠️  ffmpeg-python 未安装，请运行: pip install ffmpeg-python")
    
    # 检查 ffmpeg 二进制文件
    import subprocess
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                               capture_output=True, 
                               check=True, 
                               timeout=5)
        print("✅ ffmpeg 二进制文件已安装")
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        print("⚠️  ffmpeg 二进制文件未找到")
        print("   安装方法:")
        print("   - macOS: brew install ffmpeg")
        print("   - Linux: apt-get install ffmpeg 或 yum install ffmpeg")
        print("   - Windows: 下载 https://ffmpeg.org/download.html")


def test_method_signature():
    """测试方法签名"""
    print("\n" + "="*50)
    print("测试4: 方法签名检查")
    print("="*50)
    
    try:
        crawler = VideoCrawler()
        
        # 检查 process_video 方法
        import inspect
        sig = inspect.signature(crawler.process_video)
        params = list(sig.parameters.keys())
        
        expected_params = ['video_url', 'output_dir', 'video_quality', 'num_frames']
        print(f"✅ process_video 参数: {params}")
        
        if all(p in params for p in expected_params):
            print("✅ 方法签名正确")
            return True
        else:
            print(f"⚠️  缺少参数: {set(expected_params) - set(params)}")
            return False
    
    except Exception as e:
        print(f"❌ 方法签名检查失败: {e}")
        return False


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("VideoProcessorService 测试")
    print("="*60)
    
    results = []
    
    results.append(("导入检查", test_imports()))
    results.append(("实例化检查", test_instantiation()))
    test_dependencies()  # 只打印信息，不返回结果
    results.append(("方法签名检查", test_method_signature()))
    
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 所有测试通过！")
        print("\n使用示例:")
        print("  from core.video_processor import VideoCrawler")
        print("  crawler = VideoCrawler()")
        print("  result = crawler.process_video(")
        print("      video_url='https://www.youtube.com/watch?v=VIDEO_ID',")
        print("      output_dir='./output',")
        print("      video_quality='480p',")
        print("      num_frames=6")
        print("  )")
    else:
        print("\n⚠️  部分测试失败，请检查依赖安装情况")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())





