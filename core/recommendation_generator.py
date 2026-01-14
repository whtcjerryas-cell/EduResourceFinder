#!/usr/bin/env python3
"""
基于LLM的智能推荐理由生成器
为每个搜索结果生成个性化的推荐理由
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from typing import Dict, List, Any, Optional
from logger_utils import get_logger

logger = get_logger('recommendation_generator')


class LLMRecommendationGenerator:
    """基于LLM的推荐理由生成器"""

    def __init__(self, country_code: str = None):
        """
        初始化生成器

        Args:
            country_code: 国家代码，用于加载知识库
        """
        self.country_code = country_code
        self.kb_manager = None
        self.llm_client = None

        # 如果提供了country_code，初始化知识库管理器
        if country_code:
            try:
                from core.knowledge_base_manager import get_knowledge_base_manager
                self.kb_manager = get_knowledge_base_manager(country_code)
                logger.info(f"[✅ 推荐生成器] 已加载 {country_code} 知识库")
            except Exception as e:
                logger.warning(f"[⚠️ 推荐生成器] 知识库加载失败: {str(e)}")

        self._init_llm_client()

    def _init_llm_client(self):
        """延迟初始化LLM客户端"""
        try:
            from llm_client import get_llm_client
            self.llm_client = get_llm_client()
            logger.info("✅ 推荐理由生成器初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ LLM客户端初始化失败: {str(e)}")

    def generate_recommendations_batch(
        self,
        results: List[Dict[str, Any]],
        query: str,
        metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        批量生成推荐理由（使用LLM，超时则回退到规则）

        Args:
            results: 搜索结果列表
            query: 搜索查询
            metadata: 元数据（国家、年级、学科）

        Returns:
            添加了推荐理由的结果列表
        """
        if not results:
            return results

        # 如果LLM客户端未初始化，直接使用规则生成
        if not self.llm_client:
            logger.info(f"[推荐理由生成] LLM客户端未初始化，使用规则生成")
            return self._fallback_to_rules(results, query, metadata)

        # 尝试使用LLM生成推荐理由
        try:
            logger.info(f"[推荐理由生成] 正在使用LLM生成 {len(results)} 个结果的推荐理由")

            # 构建提示词
            prompt = self._build_batch_prompt(results, query, metadata)

            # 获取推荐模型配置（使用 gemini-2.5-pro 提升质量）
            from core.config_loader import get_config
            config = get_config()
            models = config.get_llm_models()
            recommendation_model = 'gemini-2.5-pro'  # 🔥 使用更高质量的模型

            logger.info(f"[推荐理由生成] 使用推荐模型: {recommendation_model}")

            # 调用LLM（超时控制在客户端内部处理）
            import concurrent.futures
            import time

            # 📊 记录LLM调用开始
            llm_start = time.time()

            def call_llm():
                response = self.llm_client.call_llm(
                    prompt=prompt,
                    max_tokens=150 * len(results),  # 每个结果约150字
                    temperature=0.7,
                    model=recommendation_model  # 🔥 使用 gemini-2.5-pro
                )

                # 📊 记录LLM调用结束
                llm_elapsed = time.time() - llm_start
                try:
                    from core.search_log_collector import get_log_collector
                    log_collector = get_log_collector()
                    if log_collector.current_log:
                        # 🔥 不截断prompt和response
                        log_collector.record_llm_call(
                            model_name=recommendation_model,
                            function="推荐理由生成",
                            provider="Internal API",
                            prompt=prompt,  # 🔥 完整提示词
                            input_data=f"结果数量: {len(results)}, 查询: {query}",
                            output_data=response,  # 🔥 完整输出
                            execution_time=llm_elapsed
                        )
                        logger.debug(f"[📊 日志] LLM调用已记录: {fast_model}, 功能=推荐理由生成, 耗时={llm_elapsed:.2f}秒")
                except Exception as e:
                    logger.warning(f"[📊 日志] 记录LLM调用失败: {str(e)}")

                return response

            # 使用线程池执行，设置15秒超时（快速模型2-3秒，留足余量）
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(call_llm)
                try:
                    response = future.result(timeout=15)
                    logger.info(f"[推荐理由生成] LLM调用成功")
                except concurrent.futures.TimeoutError:
                    logger.warning(f"[推荐理由生成] LLM调用超时（15秒），回退到规则生成")
                    future.cancel()
                    return self._fallback_to_rules(results, query, metadata)

            # 解析响应
            recommendations = self._parse_batch_response(response, len(results))

            # 添加推荐理由到结果中
            for i, result in enumerate(results):
                if i < len(recommendations):
                    result['recommendation_reason'] = recommendations[i]
                else:
                    result['recommendation_reason'] = f"根据搜索匹配度推荐"

            return results

        except TimeoutError as e:
            logger.warning(f"[推荐理由生成] LLM调用超时: {str(e)}，回退到规则生成")
            return self._fallback_to_rules(results, query, metadata)
        except Exception as e:
            logger.warning(f"[推荐理由生成] LLM调用失败: {str(e)}，回退到规则生成")
            return self._fallback_to_rules(results, query, metadata)

    def _build_batch_prompt(
        self,
        results: List[Dict[str, Any]],
        query: str,
        metadata: Optional[Dict]
    ) -> str:
        """构建批量生成提示词"""

        # 获取上下文信息
        context_parts = []
        if metadata:
            country = metadata.get('country', '')
            grade = metadata.get('grade', '')
            subject = metadata.get('subject', '')

            if country:
                context_parts.append(f"国家: {country}")
            if grade:
                context_parts.append(f"年级: {grade}")
            if subject:
                context_parts.append(f"学科: {subject}")

        context = "\n".join(context_parts) if context_parts else "通用教育内容搜索"

        # 📚 添加知识库内容（如果有）
        knowledge_section = ""
        if self.kb_manager and self.kb_manager.knowledge:
            knowledge = self.kb_manager.knowledge

            # 添加年级表达
            if 'grade_expressions' in knowledge and knowledge['grade_expressions']:
                knowledge_section += "\n**📚 重要年级表达（必须正确识别）**:\n"
                for grade_key, grade_info in knowledge['grade_expressions'].items():
                    variants = grade_info.get('local_variants', [])
                    if variants:
                        variant_list = []
                        for v in variants:
                            if 'arabic' in v:
                                variant_list.append(f"{v['arabic']}")
                            elif 'english' in v:
                                note = f" ({v.get('note', '')})" if v.get('note') else ''
                                variant_list.append(f"{v['english']}{note}")

                        knowledge_section += f"- {grade_key}: {', '.join(variant_list)}\n"

                # 添加常见错误
                for grade_key, grade_info in knowledge['grade_expressions'].items():
                    mistakes = grade_info.get('common_mistakes', [])
                    if mistakes:
                        knowledge_section += f"\n⚠️ **{grade_key} 常见错误（必须避免）**:\n"
                        for m in mistakes:
                            knowledge_section += f"  • ❌ {m['mistake']}\n"
                            knowledge_section += f"  • ✅ {m['correction']}\n"

            # 添加学科关键词
            if 'subject_keywords' in knowledge and knowledge['subject_keywords']:
                knowledge_section += "\n**📖 学科关键词表达**:\n"
                for subject_key, subject_info in knowledge['subject_keywords'].items():
                    variants = subject_info.get('local_variants', [])
                    if variants:
                        variant_list = []
                        for v in variants:
                            if 'arabic' in v:
                                variant_list.append(v['arabic'])
                            elif 'english' in v:
                                variant_list.append(v['english'])
                        knowledge_section += f"- {subject_key}: {', '.join(variant_list)}\n"

            # 添加LLM已知问题
            if 'llm_insights' in knowledge and knowledge['llm_insights']:
                insights = knowledge['llm_insights']
                if 'accuracy_issues' in insights and insights['accuracy_issues']:
                    # 只显示未修复的问题
                    pending_issues = [i for i in insights['accuracy_issues']
                                    if i.get('status') != 'fixed']
                    if pending_issues:
                        knowledge_section += "\n**⚠️ 已知LLM识别问题（必须注意）**:\n"
                        for issue in pending_issues[:3]:  # 最多显示3个
                            knowledge_section += f"• 问题: {issue.get('issue', '')}\n"
                            knowledge_section += f"  修复: {issue.get('fix', '')}\n"

        # 构建结果摘要（只显示前10个结果）
        results_summary = []
        for i, result in enumerate(results[:10], 1):
            title = result.get('title', '未知标题')[:80]
            url = result.get('url', '')[:60]
            snippet = result.get('snippet', '')[:100]

            results_summary.append(
                f"{i}. 标题: {title}\n"
                f"   URL: {url}\n"
                f"   描述: {snippet}\n"
            )

        results_text = "\n".join(results_summary)

        if len(results) > 10:
            results_text += f"\n... 还有 {len(results) - 10} 个结果\n"

        prompt = f"""请为以下搜索结果生成简洁的推荐理由（每条20-50字）：

**搜索查询**: {query}

**搜索背景**:
{context}
{knowledge_section}

**搜索结果**:
{results_text}

**要求**:
1. 为每个结果生成1条推荐理由
2. 推荐理由要具体、个性化，不要雷同
3. 突出每个结果的独特优势
4. 每条理由20-50字
5. 使用JSON数组格式返回
6. **必须正确识别年级和学科表达**（参考上面的年级表达和常见错误）

**输出格式**:
[
    "推荐理由1",
    "推荐理由2",
    ...
]

请确保输出是有效的JSON数组格式。"""

        return prompt

    def _parse_batch_response(self, response: str, expected_count: int) -> List[str]:
        """解析批量响应"""
        import re
        import json

        try:
            # 提取JSON数组
            json_match = re.search(r'\[\s*".*"\s*\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                recommendations = json.loads(json_str)

                if isinstance(recommendations, list) and len(recommendations) == expected_count:
                    return recommendations

            # 如果解析失败或数量不匹配，使用规则生成
            logger.warning(f"[推荐理由生成] LLM返回数量不匹配，使用规则生成")
            return [f"根据搜索匹配度推荐"] * expected_count

        except Exception as e:
            logger.error(f"[推荐理由生成] 解析失败: {str(e)}")
            return [f"根据搜索匹配度推荐"] * expected_count

    def _fallback_to_rules(
        self,
        results: List[Dict[str, Any]],
        query: str,
        metadata: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """回退到规则生成"""
        from core.result_scorer import IntelligentResultScorer

        scorer = IntelligentResultScorer()

        for result in results:
            score = result.get('score', 5.0)
            reason = scorer._generate_recommendation_reason(result, score)
            result['recommendation_reason'] = reason

        return results


# 全局实例字典（支持多个国家的实例）
_generator_instances: Dict[str, LLMRecommendationGenerator] = {}
_default_instance: Optional[LLMRecommendationGenerator] = None


def get_recommendation_generator(country_code: str = None) -> LLMRecommendationGenerator:
    """
    获取推荐理由生成器实例

    Args:
        country_code: 国家代码，用于获取带知识库的实例

    Returns:
        推荐理由生成器实例
    """
    global _default_instance

    # 如果提供了country_code，返回国家特定的实例
    if country_code:
        country_key = country_code.upper()
        if country_key not in _generator_instances:
            _generator_instances[country_key] = LLMRecommendationGenerator(country_code)
            logger.info(f"[推荐生成器] 创建 {country_key} 专用实例")
        return _generator_instances[country_key]

    # 否则返回默认实例（不带知识库）
    if _default_instance is None:
        _default_instance = LLMRecommendationGenerator()
    return _default_instance
