#!/usr/bin/env python3
"""
智能查询生成器 - 使用LLM生成本地化教育视频搜索词

基于用户输入（国家、年级、学科），使用LLM智能生成目标语言的搜索词。
支持多种输入格式（中文、英文、国家代码），自动选择合适的语言和术语。
"""

import re
from typing import Optional
from logger_utils import get_logger
from config_manager import ConfigManager
from core.config_loader import get_config

logger = get_logger('intelligent_query_generator')


class IntelligentQueryGenerator:
    """使用LLM智能生成本地化搜索词"""

    def __init__(self, llm_client, config_manager: ConfigManager = None):
        """
        初始化智能查询生成器

        Args:
            llm_client: LLM客户端
            config_manager: 配置管理器（可选，用于获取国家配置）
        """
        self.llm_client = llm_client
        self.config_manager = config_manager or ConfigManager()

        # 国家-语言映射参考表（用于LLM prompt）
        self.country_language_map = {
            "IQ": "Arabic (ar)",
            "Iraq": "Arabic (ar)",
            "伊拉克": "Arabic (ar)",
            "CN": "Chinese (zh)",
            "China": "Chinese (zh)",
            "中国": "Chinese (zh)",
            "ID": "Indonesian (id)",
            "Indonesia": "Indonesian (id)",
            "印尼": "Indonesian (id)",
            "印度尼西亚": "Indonesian (id)",
            "US": "English (en)",
            "USA": "English (en)",
            "美国": "English (en)",
            "MY": "Malay (ms)",
            "Malaysia": "Malay (ms)",
            "马来西亚": "Malay (ms)",
            "SA": "Arabic (ar)",
            "Saudi Arabia": "Arabic (ar)",
            "沙特": "Arabic (ar)",
            "EG": "Arabic (ar)",
            "Egypt": "Arabic (ar)",
            "埃及": "Arabic (ar)",
            "RU": "Russian (ru)",
            "Russia": "Russian (ru)",
            "俄罗斯": "Russian (ru)",
            "JP": "Japanese (ja)",
            "Japan": "Japanese (ja)",
            "日本": "Japanese (ja)",
            "KR": "Korean (ko)",
            "South Korea": "Korean (ko)",
            "韩国": "Korean (ko)",
            "TH": "Thai (th)",
            "Thailand": "Thai (th)",
            "泰国": "Thai (th)",
            "VN": "Vietnamese (vi)",
            "Vietnam": "Vietnamese (vi)",
            "越南": "Vietnamese (vi)",
            "PH": "Filipino (fil)",
            "Philippines": "Filipino (fil)",
            "菲律宾": "Filipino (fil)",
            "IN": "Hindi/English (hi/en)",
            "India": "Hindi/English (hi/en)",
            "印度": "Hindi/English (hi/en)",
            "PK": "Urdu (ur)",
            "Pakistan": "Urdu (ur)",
            "巴基斯坦": "Urdu (ur)",
            "NG": "English (en)",
            "Nigeria": "English (en)",
            "尼日利亚": "English (en)",
        }

        logger.info("[✅ IntelligentQueryGenerator] 初始化完成")

    def generate_query(
        self,
        country: str,
        grade: str,
        subject: str,
        semester: Optional[str] = None
    ) -> str:
        """
        使用LLM智能生成本地语言的搜索词

        Args:
            country: 国家（支持中文/英文/国家代码）
            grade: 年级（支持中文/英文）
            subject: 学科（支持中文/英文）
            semester: 学期（可选）

        Returns:
            目标语言的搜索词（如："الرياضيات الصف الثالث playlist"）
        """
        logger.info(f"[🤖 智能查询生成] 开始生成搜索词...")
        logger.info(f"  输入 - 国家: {country}, 年级: {grade}, 学科: {subject}, 学期: {semester or '不指定'}")

        try:
            # 构建system prompt
            system_prompt = self._build_system_prompt()

            # 构建user prompt
            user_prompt = self._build_user_prompt(country, grade, subject, semester)

            # 调用LLM（使用配置的快速推理模型）
            config = get_config()
            models = config.get_llm_models()
            fast_model = models.get('fast_inference', 'gemini-2.5-pro')

            logger.info(f"[📡 LLM调用] 使用快速推理模型: {fast_model}")

            # 📊 记录LLM调用开始
            import time
            llm_start = time.time()

            query = self.llm_client.call_llm(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=100,
                temperature=0.3,
                model=fast_model
            )

            # 📊 记录LLM调用结束
            llm_elapsed = time.time() - llm_start
            try:
                from core.search_log_collector import get_log_collector
                log_collector = get_log_collector()
                if log_collector.current_log:
                    # 🔥 不截断prompt和response
                    log_collector.record_llm_call(
                        model_name=fast_model,
                        function="智能查询生成",
                        provider="Internal API",
                        prompt=user_prompt,  # 🔥 完整提示词
                        input_data=f"国家: {country}, 年级: {grade}, 学科: {subject}",
                        output_data=query,  # 🔥 完整输出
                        execution_time=llm_elapsed
                    )
                    logger.debug(f"[📊 日志] LLM调用已记录: {fast_model}, 功能=智能查询生成, 耗时={llm_elapsed:.2f}秒")
            except Exception as e:
                logger.warning(f"[📊 日志] 记录LLM调用失败: {str(e)}")

            # 清理输出
            query = self._clean_query(query)

            logger.info(f"[✅ 智能查询生成] 成功生成搜索词: \"{query}\"")
            return query

        except Exception as e:
            logger.error(f"[❌ 智能查询生成] 生成失败: {str(e)}")
            # 降级：返回默认搜索词
            fallback_query = self._generate_fallback_query(country, grade, subject, semester)
            logger.warning(f"[⚠️ 降级] 使用默认搜索词: \"{fallback_query}\"")
            return fallback_query

    def _build_system_prompt(self) -> str:
        """构建system prompt"""
        # 构建国家-语言映射参考表
        mapping_table = "\n".join([
            f"- {country} → {lang}"
            for country, lang in sorted(self.country_language_map.items())
        ])

        system_prompt = f"""你是一个专业的多语言教育搜索专家。

**你的任务**:
根据用户提供的信息（国家、年级、学科），生成最合适的教育视频搜索词。

**关键原则**:
1. **语言选择**: 使用目标国家的官方语言或教育系统常用语言
   - 阿拉伯国家（伊拉克、沙特、埃及）→ 阿拉伯语
   - 中国 → 中文
   - 印尼 → 印尼语
   - 欧美国家 → 英语

2. **术语准确性**: 使用目标国家教育系统的本地术语
   - 伊拉克三年级数学 → "الرياضيات الصف الثالث"
   - 印尼七年级科学 → "IPA Kelas 7"
   - 中国五年级数学 → "五年级数学"

3. **搜索优化**: 优先搜索播放列表和完整课程
   - 包含 "playlist" 或当地语言的"完整课程"表达

4. **输出格式**: 只返回搜索词，不要任何解释、说明或其他文字

**国家-语言参考映射表**:
{mapping_table}

**输出示例**:
输入: 伊拉克, 三年级, 数学
输出: الرياضيات الصف الثالث playlist

输入: 印尼, 七年级, 自然科学
输出: IPA Kelas 7 playlist lengkap

输入: 中国, 五年级, 数学
输出: 五年级数学 播放列表

输入: 美国, Grade 3, Mathematics
输出: Grade 3 Mathematics playlist

**重要提醒**:
- 只返回搜索词本身，不要任何解释
- 不要添加引号
- 不要添加"搜索词："、"输出："等前缀
- 如果不确定语言，使用英语作为默认语言
"""

        return system_prompt

    def _build_user_prompt(
        self,
        country: str,
        grade: str,
        subject: str,
        semester: Optional[str]
    ) -> str:
        """构建user prompt"""
        semester_text = f", 学期: {semester}" if semester else ""

        user_prompt = f"""请生成教育视频搜索词：

国家: {country}
年级: {grade}
学科: {subject}{semester_text}

要求:
1. 使用 {country} 的官方语言或教育系统常用语言
2. 使用当地教育系统的标准术语
3. 优先包含"playlist"或当地语言的"完整课程"关键词
4. 只返回搜索词，不要解释

搜索词:"""

        return user_prompt

    def _clean_query(self, query: str) -> str:
        """
        清理LLM输出

        Args:
            query: LLM原始输出

        Returns:
            清理后的搜索词
        """
        # 去除首尾空白
        query = query.strip()

        # 去除引号
        query = query.strip('"').strip("'").strip('"').strip("'")

        # 去除可能的标记
        # 例如: "搜索词: الرياضيات الصف الثالث" → "الرياضيات الصف الثالث"
        patterns_to_remove = [
            r'^搜索词[:：]\s*',
            r'^输出[:：]\s*',
            r'^查询[:：]\s*',
            r'^Query[:：]\s*',
            r'^\*\*',  # markdown加粗
            r'\*\*$',  # markdown加粗
        ]

        for pattern in patterns_to_remove:
            query = re.sub(pattern, '', query, flags=re.IGNORECASE).strip()

        # 去除换行和多余空格
        query = " ".join(query.split())

        # 验证：如果查询过短（<3字符），可能是错误
        if len(query) < 3:
            logger.warning(f"[⚠️ 警告] 生成的搜索词过短: \"{query}\"")
            return query

        # 验证：如果查询过长（>200字符），可能包含解释
        if len(query) > 200:
            logger.warning(f"[⚠️ 警告] 生成的搜索词过长（{len(query)}字符），截取前100字符")
            return query[:100].strip()

        return query

    def _generate_fallback_query(
        self,
        country: str,
        grade: str,
        subject: str,
        semester: Optional[str]
    ) -> str:
        """
        生成降级搜索词（当LLM失败时使用）

        Args:
            country: 国家
            grade: 年级
            subject: 学科
            semester: 学期

        Returns:
            默认搜索词
        """
        # 尝试识别语言，使用英语作为默认
        fallback_query = f"{subject} {grade} playlist"

        if semester:
            fallback_query = f"{subject} {grade} semester {semester} playlist"

        logger.info(f"[🔄 降级策略] 生成默认搜索词: \"{fallback_query}\"")
        return fallback_query


# ============================================================================
# 单例模式
# ============================================================================

_intelligent_query_generator = None


def get_intelligent_query_generator():
    """获取IntelligentQueryGenerator单例"""
    global _intelligent_query_generator

    if _intelligent_query_generator is None:
        from search_engine_v2 import AIBuildersClient
        llm_client = AIBuildersClient()
        config_manager = ConfigManager()

        _intelligent_query_generator = IntelligentQueryGenerator(
            llm_client=llm_client,
            config_manager=config_manager
        )

    return _intelligent_query_generator
