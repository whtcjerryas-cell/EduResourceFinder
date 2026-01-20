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
- **查询多样性关键**：每个搜索词必须使用不同的关键词组合和表达方式，避免语义重复

**要求**：
1. 确定搜索语言（应该使用 {language_code}）
2. 如果是中国（CN）且学科是中文内容，必须设置 use_chinese_search_engine=true，并包含 bilibili.com
3. 根据国家特点选择合适的平台（如：中国用B站，印尼用YouTube和本地平台）
4. **生成5-7个高度差异化的搜索词变体**（必须包含播放列表相关的搜索词）：
   - ✨ **多样性要求**：每个搜索词必须使用不同的关键词组合，避免语义重复
   - 至少1个包含 "playlist" 关键词（使用 site:youtube.com 语法）
   - 至少1个包含 "complete course" 或 "full series" 关键词
   - 至少1个包含本地语言的"整套课程"或"完整系列"表达
   - 至少1个使用 "grade level" + "subject" + "chapter" 组合
   - 至少1个使用 "curriculum" + "semester" 组合
   - 剩余为常规教学视频搜索词（使用不同的同义词和表达方式）
   - ✨ 例如：避免生成 "math grade 1 playlist" 和 "playlist math grade 1" 这种仅仅是词序不同的查询
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
                max_tokens=2000,  # 增加以避免JSON被截断
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
                    f"site:bilibili.com {subject} {grade} 播放列表",
                    f"{subject} {grade} 完整课程 series",
                    f"{grade} {subject} 全套教程 collection",
                    f"{subject} {grade} 教学视频 chapter",
                    f"{grade} {subject} 课程体系 curriculum",
                    f"bilibili {subject} {grade} 系统课程",
                    f"{subject} {grade} 知识点讲解"
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

        # 生成多个播放列表优先的搜索查询（7个高度差异化的变体）
        # ✨ 增加查询多样性：每个查询使用不同的关键词组合
        # ⚠️ 重要：对于非中文国家，确保不使用中文词汇，使用英文或当地语言

        # 检测grade和subject是否包含中文/非ASCII字符
        def contains_non_ascii(text):
            try:
                text.encode('ascii')
                return False
            except UnicodeEncodeError:
                return True

        # 如果grade或subject包含非ASCII字符（如中文、阿拉伯语），使用英文作为备选
        grade_clean = grade if not contains_non_ascii(grade) else f"Grade {grade.split()[-1] if grade.split() else '8'}"
        subject_clean = subject if not contains_non_ascii(subject) else subject

        # 对于阿拉伯语等国家，添加英文翻译的搜索词
        if language_code == "ar":
            search_queries = [
                f"site:youtube.com {subject_clean} {grade_clean} {playlist_keywords[0]}",  # YouTube播放列表搜索（阿拉伯语）
                f"site:youtube.com {subject_clean} {grade_clean} playlist",  # YouTube播放列表搜索（英文）
                f"{subject_clean} {grade_clean} {playlist_keywords[1] if len(playlist_keywords) > 1 else 'complete course'}",  # 通用播放列表搜索
                f"{subject_clean} {grade_clean} video lesson chapter",  # 按章节划分的课程
                f"{grade_clean} {subject_clean} full course curriculum",  # 完整课程体系
                f"{subject_clean} for {grade_clean} students tutorial",  # 学生导向的教程
                f"{grade_clean} {subject_clean} learning series complete"  # 系列学习资源
            ]
        else:
            search_queries = [
                f"site:youtube.com {subject} {grade} {playlist_keywords[0]}",  # YouTube播放列表搜索
                f"{subject} {grade} {playlist_keywords[1] if len(playlist_keywords) > 1 else 'complete course'}",  # 通用播放列表搜索
                f"site:youtube.com \"{subject}\" \"{grade}\" playlist",  # YouTube精确匹配播放列表
                f"{subject} {grade} video lesson chapter",  # 按章节划分的课程
                f"{grade} {subject} full course curriculum",  # 完整课程体系
                f"{subject} for {grade} students tutorial",  # 学生导向的教程
                f"{grade} {subject} learning series complete"  # 系列学习资源
            ]

        return SearchStrategy(
            search_language=language_code,
            use_chinese_search_engine=False,
            platforms=["youtube.com"] + domains[:3],
            search_queries=search_queries,
            priority_domains=domains[:5],
            notes=f"默认搜索策略：使用{language_code}语言，优先搜索YouTube播放列表（7个差异化查询）"
        )

    def generate_best_query(self, country: str, grade: str, subject: str,
                           semester: Optional[str] = None) -> str:
        """
        生成单个最优搜索查询（渐进式搜索优化）

        用于方案一：渐进式搜索，专注于生成1个高质量查询
        包含playlist + subject + grade + country关键词

        Args:
            country: 国家代码（如：CN, ID, US）
            grade: 年级（如：初二, Kelas 2, Grade 8）
            subject: 学科（如：地理, Matematika, Geography）
            semester: 学期（可选）

        Returns:
            单个最优查询字符串
        """
        logger.info(f"[🎯 最优查询] 为 {country}/{grade}/{subject} 生成单个最优查询...")

        # 获取国家配置
        country_config = self.config_manager.get_country_config(country.upper())
        if not country_config:
            logger.warning(f"[⚠️ 最优查询] 国家配置不存在: {country}，使用默认查询")
            return self._get_default_best_query(country, grade, subject, semester)

        # 使用LLM生成1个最优查询
        try:
            best_query = self._generate_best_query_with_llm(
                country=country,
                country_name=country_config.country_name,
                language_code=country_config.language_code,
                grade=grade,
                subject=subject,
                semester=semester
            )

            logger.info(f"[✅ 最优查询] 生成完成: \"{best_query}\"")
            return best_query

        except Exception as e:
            logger.error(f"[❌ 最优查询] LLM生成失败: {str(e)}，使用默认查询")
            return self._get_default_best_query(country, grade, subject, semester)

    def _generate_best_query_with_llm(
        self,
        country: str,
        country_name: str,
        language_code: str,
        grade: str,
        subject: str,
        semester: Optional[str]
    ) -> str:
        """使用LLM生成单个最优查询"""

        system_prompt = """你是一个专业的搜索查询优化专家。你的任务是根据国家、年级、科目生成单个最优搜索查询。

**关键要求**：
1. 专注于教育视频资源的搜索
2. **必须优先搜索播放列表/完整课程**（因为包含系统性的系列内容）
3. 只返回1个查询字符串，不要添加任何解释或引号
4. 查询应该简洁但包含关键信息

**查询格式**：
- YouTube: site:youtube.com [subject] [grade] playlist
- 通用: [subject] [grade] complete course/full series
- 本地化: [subject] [grade] [本地语言的"完整课程"关键词]

**重要**：直接返回查询字符串，不要添加引号、JSON格式或其他文本。"""

        user_prompt = f"""请为以下搜索请求生成单个最优查询：

国家: {country} ({country_name})
语言代码: {language_code}
年级: {grade}
学科: {subject}
学期: {semester or '不指定'}

**要求**：
1. 生成1个最优查询（不是多个）
2. 必须包含 "playlist" 或 "complete course" 或 "full series" 关键词
3. 如果是YouTube内容，使用 site:youtube.com 语法
4. 如果知道本地语言的"完整课程"表达，使用本地语言
5. 查询应该简洁但包含所有关键信息（学科、年级、课程类型）

**示例**：
- 英语: "site:youtube.com mathematics Grade 8 playlist"
- 印尼语: "Matematika Kelas 8 playlist lengkap"
- 中文: "site:bilibili.com 数学 初二 播放列表"

请返回查询字符串："""

        try:
            config_file = Path(__file__).parent / "config" / "llm.yaml"
            with open(config_file, 'r', encoding='utf-8') as f:
                llm_config = yaml.safe_load(f)

            strategy_model = llm_config['llm']['models'].get('search_strategy', 'gemini-2.5-pro')

            logger.info(f"[📡 LLM调用] 使用最优查询生成模型: {strategy_model}")

            import time
            llm_start = time.time()

            response = self.llm_client.call_llm(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=200,  # 只需要1个查询，不需要太多tokens
                temperature=0.3,
                model=strategy_model
            )

            llm_elapsed = time.time() - llm_start
            try:
                from core.search_log_collector import get_log_collector
                log_collector = get_log_collector()
                if log_collector.current_log:
                    log_collector.record_llm_call(
                        model_name=strategy_model,
                        function="最优查询生成",
                        provider="Internal API",
                        prompt=user_prompt,
                        input_data=f"国家: {country}, 年级: {grade}, 学科: {subject}",
                        output_data=response,
                        execution_time=llm_elapsed
                    )
                    logger.debug(f"[📊 日志] LLM调用已记录: {strategy_model}, 功能=最优查询生成, 耗时={llm_elapsed:.2f}秒")
            except Exception as e:
                logger.warning(f"[📊 日志] 记录LLM调用失败: {str(e)}")

            # 清理响应（移除可能的引号、换行等）
            best_query = response.strip().strip('"\'')

            logger.info(f"[✅ LLM生成最优查询]: \"{best_query}\"")
            return best_query

        except Exception as e:
            logger.error(f"[❌ 最优查询] LLM生成失败: {str(e)}")
            raise

    def _get_default_best_query(self, country: str, grade: str, subject: str,
                                semester: Optional[str] = None) -> str:
        """获取默认最优查询（降级方案）"""

        country_upper = country.upper()

        # 中国特殊处理
        if country_upper == "CN":
            return f"site:bilibili.com {subject} {grade} 播放列表"

        # 其他国家
        country_config = self.config_manager.get_country_config(country_upper)
        language_code = country_config.language_code if country_config else "en"

        # 根据语言生成默认查询
        if language_code == "id":
            return f"site:youtube.com {subject} {grade} playlist lengkap"
        elif language_code == "ar":
            return f"site:youtube.com {subject} {grade} playlist"
        elif language_code == "ms":
            return f"site:youtube.com {subject} {grade} playlist lengkap"
        else:
            return f"site:youtube.com {subject} {grade} playlist"

    def generate_alternative_query(self, country: str, grade: str, subject: str,
                                  semester: Optional[str] = None,
                                  attempt_number: int = 1) -> str:
        """
        生成备选搜索查询（降级策略）

        当最优查询失败时，生成不同风格的备选查询
        每次调用返回不同的查询变体

        Args:
            country: 国家代码（如：CN, ID, US）
            grade: 年级（如：初二, Kelas 2, Grade 8）
            subject: 学科（如：地理, Matematika, Geography）
            semester: 学期（可选）
            attempt_number: 重试次数（1-5），决定使用哪种备选策略

        Returns:
            备选查询字符串
        """
        logger.info(f"[🔄 备选查询] 为 {country}/{grade}/{subject} 生成第 {attempt_number} 个备选查询...")

        country_config = self.config_manager.get_country_config(country.upper())
        language_code = country_config.language_code if country_config else "en"

        # 定义5种备选策略
        strategies = [
            # 策略1: 使用英文（如果原查询不是英文）
            lambda: self._alternative_english(subject, grade, language_code),

            # 策略2: 添加"video"关键词
            lambda: self._alternative_with_video(subject, grade, language_code),

            # 策略3: 使用"course"关键词
            lambda: self._alternative_with_course(subject, grade, language_code),

            # 策略4: 移除年级，只用学科
            lambda: self._alternative_without_grade(subject, language_code),

            # 策略5: 使用YouTube精确语法
            lambda: self._alternative_youtube_exact(subject, grade, language_code)
        ]

        # 根据重试次数选择策略（循环使用）
        strategy_index = (attempt_number - 1) % len(strategies)
        alternative_query = strategies[strategy_index]()

        logger.info(f"[✅ 备选查询] 生成完成 (策略{strategy_index + 1}): \"{alternative_query}\"")
        return alternative_query

    def _alternative_english(self, subject: str, grade: str, language_code: str) -> str:
        """备选策略1: 使用英文"""
        # 如果已经是英文，尝试移除site限制
        if language_code == "en":
            return f"{subject} {grade} complete course"
        else:
            return f"site:youtube.com {subject} {grade} playlist"

    def _alternative_with_video(self, subject: str, grade: str, language_code: str) -> str:
        """备选策略2: 添加video关键词"""
        if language_code == "zh":
            return f"{subject} {grade} 视频"
        elif language_code == "id":
            return f"{subject} {grade} video pembelajaran"
        else:
            return f"{subject} {grade} video"

    def _alternative_with_course(self, subject: str, grade: str, language_code: str) -> str:
        """备选策略3: 使用course关键词"""
        if language_code == "zh":
            return f"{subject} {grade} 完整课程"
        elif language_code == "id":
            return f"{subject} {grade} kursus lengkap"
        else:
            return f"{subject} {grade} full course"

    def _alternative_without_grade(self, subject: str, language_code: str) -> str:
        """备选策略4: 移除年级限制"""
        if language_code == "zh":
            return f"site:bilibili.com {subject} 播放列表"
        else:
            return f"site:youtube.com {subject} playlist"

    def _alternative_youtube_exact(self, subject: str, grade: str, language_code: str) -> str:
        """备选策略5: YouTube精确匹配语法"""
        if language_code == "zh":
            return f'site:bilibili.com "{subject}" "{grade}" 播放列表'
        else:
            return f'site:youtube.com "{subject}" "{grade}" playlist'





