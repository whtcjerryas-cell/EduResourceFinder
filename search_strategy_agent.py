#!/usr/bin/env python3
"""
搜索策略 Agent - 根据国家、年级、科目制定个性化的搜索策略
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from config_manager import ConfigManager
from logger_utils import get_logger
from json_utils import extract_json_object

logger = get_logger('search_strategy_agent')


class SearchStrategy(BaseModel):
    """搜索策略"""
    search_language: str = Field(description="搜索语言代码（如：zh, en, id）")
    use_chinese_search_engine: bool = Field(description="是否使用中文搜索引擎（如百度、搜狗）", default=False)
    platforms: List[str] = Field(description="应该搜索的平台列表（如：bilibili.com, youtube.com）", default_factory=list)
    search_queries: List[str] = Field(description="多个搜索词变体", default_factory=list)
    priority_domains: List[str] = Field(description="优先搜索的域名列表", default_factory=list)
    notes: str = Field(description="策略说明", default="")


class SearchStrategyAgent:
    """搜索策略 Agent - 制定个性化搜索策略"""
    
    def __init__(self, llm_client, config_manager: ConfigManager):
        """
        初始化搜索策略 Agent
        
        Args:
            llm_client: LLM客户端（用于AI生成策略）
            config_manager: 配置管理器
        """
        self.llm_client = llm_client
        self.config_manager = config_manager
    
    def generate_strategy(self, country: str, grade: str, subject: str, semester: Optional[str] = None) -> SearchStrategy:
        """
        生成搜索策略
        
        Args:
            country: 国家代码（如：CN, ID, US）
            grade: 年级（如：初二, Kelas 2, Grade 8）
            subject: 学科（如：地理, Matematika, Geography）
            semester: 学期（可选）
        
        Returns:
            搜索策略对象
        """
        logger.info(f"[🎯 搜索策略] 开始为 {country}/{grade}/{subject} 制定搜索策略...")
        
        # 获取国家配置
        country_config = self.config_manager.get_country_config(country.upper())
        if not country_config:
            logger.warning(f"[⚠️ 搜索策略] 国家配置不存在: {country}")
            # 返回默认策略
            return self._get_default_strategy(country, grade, subject)
        
        # 使用LLM生成个性化搜索策略
        strategy = self._generate_strategy_with_llm(
            country=country,
            country_name=country_config.country_name,
            language_code=country_config.language_code,
            grade=grade,
            subject=subject,
            semester=semester,
            existing_domains=country_config.domains
        )
        
        logger.info(f"[✅ 搜索策略] 策略生成完成:")
        logger.info(f"  - 搜索语言: {strategy.search_language}")
        logger.info(f"  - 使用中文搜索引擎: {strategy.use_chinese_search_engine}")
        logger.info(f"  - 平台数量: {len(strategy.platforms)}")
        logger.info(f"  - 搜索词数量: {len(strategy.search_queries)}")
        logger.info(f"  - 优先域名数量: {len(strategy.priority_domains)}")
        
        return strategy
    
    def _generate_strategy_with_llm(
        self,
        country: str,
        country_name: str,
        language_code: str,
        grade: str,
        subject: str,
        semester: Optional[str],
        existing_domains: List[str]
    ) -> SearchStrategy:
        """使用LLM生成搜索策略"""
        
        system_prompt = """你是一个专业的搜索策略专家。你的任务是根据国家、年级、科目制定个性化的搜索策略。

**关键要求**：
1. 只能返回JSON格式，不能返回任何其他文本、解释、Markdown格式或代码块标记
2. 根据国家特点选择合适的搜索平台和搜索引擎
3. 对于中国，必须包含B站（bilibili.com）等中文平台，并使用中文搜索引擎
4. 对于其他国家，根据其常用平台和语言选择合适的策略

**输出格式**：
{
  "search_language": "语言代码（如：zh, en, id）",
  "use_chinese_search_engine": true/false,
  "platforms": ["平台列表，如：bilibili.com, youtube.com"],
  "search_queries": ["搜索词变体1", "搜索词变体2"],
  "priority_domains": ["优先搜索的域名列表"],
  "notes": "策略说明"
}

**重要**：直接返回JSON，不要添加任何前缀或后缀。"""
        
        user_prompt = f"""请为以下搜索请求制定搜索策略：

国家: {country} ({country_name})
语言代码: {language_code}
年级: {grade}
学科: {subject}
学期: {semester or '不指定'}

现有域名列表: {', '.join(existing_domains[:10]) if existing_domains else '无'}

**重要要求（针对视频资源）**：
- **优先搜索播放列表/合集**：因为播放列表包含完整的系列课程，效率更高
- **播放列表关键词**：playlist, complete course, full series, collection, 整套课程, 完整系列

**要求**：
1. 确定搜索语言（应该使用 {language_code}）
2. 如果是中国（CN）且学科是中文内容，必须设置 use_chinese_search_engine=true，并包含 bilibili.com
3. 根据国家特点选择合适的平台（如：中国用B站，印尼用YouTube和本地平台）
4. **生成4-5个搜索词变体**（必须包含播放列表相关的搜索词）：
   - 至少1个包含 "playlist" 关键词
   - 至少1个包含 "complete course" 或 "full series" 关键词
   - 至少1个包含本地语言的"整套课程"或"完整系列"表达
   - 剩余为常规教学视频搜索词
5. 确定优先搜索的域名（最多5个）

请返回JSON格式的策略："""

        try:
            # 获取配置的搜索策略生成模型
            config_file = Path(__file__).parent / "config" / "llm.yaml"
            with open(config_file, 'r', encoding='utf-8') as f:
                llm_config = yaml.safe_load(f)

            strategy_model = llm_config['llm']['models'].get('search_strategy', 'gemini-2.5-pro')

            logger.info(f"[📡 LLM调用] 使用搜索策略模型: {strategy_model}")

            # 📊 记录LLM调用开始
            import time
            llm_start = time.time()

            response = self.llm_client.call_llm(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=500,
                temperature=0.2,
                model=strategy_model
            )

            # 📊 记录LLM调用结束
            llm_elapsed = time.time() - llm_start
            try:
                from core.search_log_collector import get_log_collector
                log_collector = get_log_collector()
                if log_collector.current_log:
                    # 🔥 不截断prompt和response
                    log_collector.record_llm_call(
                        model_name=strategy_model,
                        function="搜索策略生成",
                        provider="Internal API",  # 🔥 统一使用Internal API
                        prompt=user_prompt,  # 🔥 完整提示词
                        input_data=f"国家: {country}, 年级: {grade}, 学科: {subject}",
                        output_data=response,  # 🔥 完整输出
                        execution_time=llm_elapsed
                    )
                    logger.debug(f"[📊 日志] LLM调用已记录: {strategy_model}, 功能=搜索策略生成, 耗时={llm_elapsed:.2f}秒")
            except Exception as e:
                logger.warning(f"[📊 日志] 记录LLM调用失败: {str(e)}")

            # 解析JSON响应
            strategy_data = extract_json_object(response)
            if not strategy_data:
                logger.warning(f"[⚠️ 搜索策略] LLM返回非JSON格式，使用默认策略")
                return self._get_default_strategy(country, grade, subject)
            
            # 构建SearchStrategy对象
            strategy = SearchStrategy(
                search_language=strategy_data.get('search_language', language_code),
                use_chinese_search_engine=strategy_data.get('use_chinese_search_engine', False),
                platforms=strategy_data.get('platforms', []),
                search_queries=strategy_data.get('search_queries', []),
                priority_domains=strategy_data.get('priority_domains', existing_domains[:5]),
                notes=strategy_data.get('notes', '')
            )
            
            return strategy
            
        except Exception as e:
            logger.error(f"[❌ 搜索策略] LLM生成策略失败: {str(e)}")
            return self._get_default_strategy(country, grade, subject)
    
    def _get_default_strategy(self, country: str, grade: str, subject: str) -> SearchStrategy:
        """获取默认搜索策略"""
        
        # 根据国家确定语言和平台
        country_upper = country.upper()
        
        # 中国特殊处理
        if country_upper == "CN":
            return SearchStrategy(
                search_language="zh",
                use_chinese_search_engine=True,
                platforms=["bilibili.com", "youtube.com", "youku.com", "iqiyi.com"],
                search_queries=[
                    f"{subject} {grade} 播放列表",
                    f"{subject} {grade} 完整课程",
                    f"{subject} {grade} 教学视频",
                    f"{grade} {subject} 系列课程",
                    f"{subject} {grade} 全套教程"
                ],
                priority_domains=["bilibili.com", "youtube.com"],
                notes="中国搜索策略：使用中文搜索引擎，优先搜索B站播放列表"
            )
        
        # 其他国家默认策略
        country_config = self.config_manager.get_country_config(country_upper)
        language_code = country_config.language_code if country_config else "en"
        domains = country_config.domains[:5] if country_config else []

        # 根据语言代码确定播放列表关键词
        playlist_keywords_map = {
            "id": ["playlist", "complete course", "full series", "koleksi lengkap", "kursus lengkap"],
            "en": ["playlist", "complete course", "full series", "video collection"],
            "zh": ["播放列表", "完整课程", "系列教程"],
            "ms": ["playlist", "kursus lengkap", "siri lengkap"],
            "ar": ["قائمة التشغيل", "دورة كاملة"],
            "ru": ["плейлист", "полный курс"],
            "ja": ["プレイリスト", "完全なコース"],
            "fil": ["playlist", "complete course", "buong kurso"],
            "th": ["เพลย์ลิสต์", "หลักสูตรทั้งหมด"],
            "vi": ["playlist", "khóa học đầy đủ"],
        }

        playlist_keywords = playlist_keywords_map.get(language_code, ["playlist", "complete course"])

        # 生成多个播放列表优先的搜索查询
        # YouTube特定：使用site:youtube.com和list=操作符来专门搜索播放列表
        search_queries = [
            f"site:youtube.com {subject} {grade} {playlist_keywords[0]}",  # YouTube播放列表搜索
            f"{subject} {grade} {playlist_keywords[1] if len(playlist_keywords) > 1 else 'complete course'}",  # 通用播放列表搜索
            f"site:youtube.com \"{subject}\" \"{grade}\" playlist",  # YouTube精确匹配播放列表
            f"{subject} {grade} video lesson",  # 常规教学视频
            f"{grade} {subject} full course"  # 完整课程
        ]

        return SearchStrategy(
            search_language=language_code,
            use_chinese_search_engine=False,
            platforms=["youtube.com"] + domains[:3],
            search_queries=search_queries,
            priority_domains=domains[:5],
            notes=f"默认搜索策略：使用{language_code}语言，优先搜索YouTube播放列表"
        )





