"""
配置加载器
==================

用途：从YAML配置文件加载配置，支持缓存和热重载
作者：产品经理 + AI
日期：2026-01-05
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    配置加载器

    功能：
    1. 加载YAML配置文件
    2. 配置缓存（避免重复读取）
    3. 热重载（检测文件变化）
    4. 配置验证
    """

    def __init__(self, config_dir: str = "config"):
        """
        初始化配置加载器

        Args:
            config_dir: 配置文件目录（相对于项目根目录）
        """
        self.config_dir = Path(config_dir)
        if not self.config_dir.is_absolute():
            # 如果是相对路径，从当前文件位置推导
            self.config_dir = Path(__file__).parent.parent / config_dir

        self._cache: Dict[str, Dict[str, Any]] = {}
        self._last_modified: Dict[str, float] = {}

        logger.info(f"配置加载器初始化完成，配置目录: {self.config_dir}")

    def load(self, config_file: str, force_reload: bool = False) -> Dict[str, Any]:
        """
        加载配置文件

        Args:
            config_file: 配置文件名（如 'evaluation_weights.yaml'）
            force_reload: 是否强制重新加载（忽略缓存）

        Returns:
            配置字典
        """
        config_path = self.config_dir / config_file

        # 检查文件是否存在
        if not config_path.exists():
            logger.error(f"配置文件不存在: {config_path}")
            return {}

        # 检查是否需要重新加载
        if not force_reload and not self._is_modified(config_path):
            return self._cache.get(config_file, {})

        # 加载配置
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 缓存配置
            self._cache[config_file] = config
            self._last_modified[config_file] = os.path.getmtime(config_path)

            logger.info(f"配置加载成功: {config_file}")
            return config

        except Exception as e:
            logger.error(f"配置加载失败: {config_file}, 错误: {str(e)}")
            return {}

    def _is_modified(self, path: Path) -> bool:
        """
        检查文件是否被修改

        Args:
            path: 文件路径

        Returns:
            True if modified, False otherwise
        """
        path_str = str(path)
        if path_str not in self._last_modified:
            return True
        return os.path.getmtime(path) > self._last_modified[path_str]

    # ----------------------------------------
    # 便捷方法 - 评估配置
    # ----------------------------------------
    def get_evaluation_weights(self) -> Dict[str, Any]:
        """获取评估权重配置"""
        config = self.load('evaluation_weights.yaml')
        return config.get('evaluation', {})

    def get_overall_weights(self) -> Dict[str, float]:
        """获取综合评分权重"""
        eval_config = self.get_evaluation_weights()
        return eval_config.get('overall_weights', {
            'visual_quality': 0.2,
            'relevance': 0.4,
            'pedagogy': 0.3,
            'metadata': 0.1
        })

    def get_visual_quality_weights(self) -> Dict[str, float]:
        """获取视觉质量细分权重"""
        eval_config = self.get_evaluation_weights()
        vq_config = eval_config.get('visual_quality', {})
        return {
            'tech': vq_config.get('tech', 0.6),
            'design': vq_config.get('design', 0.4)
        }

    def get_metadata_weights(self) -> Dict[str, float]:
        """获取元数据细分权重"""
        eval_config = self.get_evaluation_weights()
        md_config = eval_config.get('metadata', {})
        return {
            'view_count': md_config.get('view_weight', 0.6),
            'like_ratio': md_config.get('like_weight', 0.4)
        }

    # ----------------------------------------
    # 便捷方法 - LLM配置
    # ----------------------------------------
    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM配置"""
        config = self.load('llm.yaml')
        return config.get('llm', {})

    def get_llm_models(self) -> Dict[str, str]:
        """获取LLM模型配置"""
        llm_config = self.get_llm_config()
        return llm_config.get('models', {})

    def get_llm_params(self, param_type: str = 'default') -> Dict[str, Any]:
        """
        获取LLM参数

        Args:
            param_type: 参数类型 (default, vision, gemini, evaluation, search)
        """
        llm_config = self.get_llm_config()
        params = llm_config.get('params', {})
        return params.get(param_type, params.get('default', {
            'temperature': 0.3,
            'max_tokens': 2000
        }))

    # ----------------------------------------
    # 便捷方法 - 搜索配置
    # ----------------------------------------
    def get_search_config(self) -> Dict[str, Any]:
        """获取搜索配置"""
        config = self.load('search.yaml')
        return config.get('search', {})

    def get_search_strategy(self) -> Dict[str, Any]:
        """获取搜索策略配置"""
        search_config = self.get_search_config()
        return search_config.get('strategy', {})

    def get_localization_keywords(self) -> Dict[str, str]:
        """获取本地化关键词"""
        search_config = self.get_search_config()
        return search_config.get('localization', {})

    def get_edtech_domains(self) -> list:
        """获取EdTech平台域名白名单"""
        search_config = self.get_search_config()
        return search_config.get('edtech_domains', [])

    # ----------------------------------------
    # 便捷方法 - 视频处理配置
    # ----------------------------------------
    def get_video_config(self) -> Dict[str, Any]:
        """获取视频处理配置"""
        config = self.load('video_processing.yaml')
        return config.get('video', {})

    def get_download_config(self) -> Dict[str, Any]:
        """获取下载配置"""
        video_config = self.get_video_config()
        return video_config.get('download', {})

    def get_frames_config(self) -> Dict[str, Any]:
        """获取帧提取配置"""
        video_config = self.get_video_config()
        return video_config.get('frames', {})

    def get_transcription_config(self) -> Dict[str, Any]:
        """获取转写配置"""
        video_config = self.get_video_config()
        return video_config.get('transcription', {})

    # ----------------------------------------
    # 便捷方法 - 提示词配置
    # ----------------------------------------
    def get_prompts_config(self) -> Dict[str, Any]:
        """获取提示词配置"""
        config = self.load('prompts/ai_search_strategy.yaml')
        return config.get('prompts', {})

    def get_prompt(self, prompt_name: str) -> Dict[str, Any]:
        """
        获取特定提示词

        Args:
            prompt_name: 提示词名称 (search_query_generation, knowledge_point_matching等)
        """
        prompts = self.get_prompts_config()
        return prompts.get(prompt_name, {})

    def get_system_prompt(self, prompt_name: str) -> str:
        """
        获取系统提示词

        Args:
            prompt_name: 提示词名称
        """
        prompt_config = self.get_prompt(prompt_name)
        return prompt_config.get('system_prompt', '')

    # ----------------------------------------
    # 工具方法
    # ----------------------------------------
    def reload_all(self) -> None:
        """重新加载所有配置"""
        logger.info("重新加载所有配置...")
        self._cache.clear()
        self._last_modified.clear()

    def get_config_info(self) -> Dict[str, Any]:
        """
        获取配置信息（用于调试）

        Returns:
            配置信息字典
        """
        return {
            'config_dir': str(self.config_dir),
            'cached_files': list(self._cache.keys()),
            'total_cached': len(self._cache)
        }


# ----------------------------------------
# 全局单例
# ----------------------------------------
_config_loader: Optional[ConfigLoader] = None


def get_config() -> ConfigLoader:
    """
    获取全局配置加载器实例

    Returns:
        ConfigLoader实例
    """
    global _config_loader
    if _config_loader is None:
        config_dir = os.getenv('CONFIG_DIR', 'config')
        _config_loader = ConfigLoader(config_dir)
    return _config_loader


# ----------------------------------------
# 使用示例
# ----------------------------------------
if __name__ == "__main__":
    # 测试配置加载器
    config = get_config()

    print("=" * 50)
    print("配置加载器测试")
    print("=" * 50)

    # 测试评估权重
    print("\n1. 评估权重配置:")
    overall_weights = config.get_overall_weights()
    print(f"   视觉质量: {overall_weights['visual_quality']}")
    print(f"   相关性: {overall_weights['relevance']}")
    print(f"   教学法: {overall_weights['pedagogy']}")
    print(f"   元数据: {overall_weights['metadata']}")

    # 测试LLM配置
    print("\n2. LLM模型配置:")
    models = config.get_llm_models()
    print(f"   内部API模型: {models['internal_api']}")
    print(f"   视觉分析模型: {models['vision']}")
    print(f"   转写模型: {models['transcription']}")

    # 测试搜索配置
    print("\n3. 搜索策略配置:")
    strategy = config.get_search_strategy()
    print(f"   最大尝试次数: {strategy['max_attempts_per_chapter']}")
    print(f"   重试延迟: {strategy['retry_delay_seconds']}秒")

    # 测试本地化关键词
    print("\n4. 本地化关键词:")
    keywords = config.get_localization_keywords()
    print(f"   印尼语: {keywords['id']}")
    print(f"   英语: {keywords['en']}")
    print(f"   中文: {keywords['zh']}")

    print("\n" + "=" * 50)
    print("配置加载器测试完成！")
    print("=" * 50)
