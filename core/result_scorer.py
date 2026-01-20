#!/usr/bin/env python3
"""
智能结果评分模块 - 纯LLM评估版本
只使用大模型进行评分，移除所有硬编码规则和知识库
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import re
import json
import hashlib
from functools import lru_cache
from typing import Dict, List, Any, Optional
from logger_utils import get_logger
from llm_client import InternalAPIClient, AIBuildersAPIClient
from config.llm_config import get_batch_evaluation_params

logger = get_logger('result_scorer')


# ==============================================================================
# LLM调用缓存（使用 functools.lru_cache）
# ==============================================================================
@lru_cache(maxsize=1000)
def _call_llm_with_cache(
    cache_key: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    temperature: float
) -> str:
    """
    带缓存的LLM调用（使用 functools.lru_cache）

    Args:
        cache_key: 缓存键（MD5哈希）
        system_prompt: 系统提示
        user_prompt: 用户提示
        max_tokens: 最大token数
        temperature: 温度参数

    Returns:
        LLM响应文本

    Note:
        此函数在模块级别定义，以便使用 lru_cache
        实际的LLM调用通过内部的 _llm_client_for_cache 完成
    """
    # 获取全局LLM客户端（需要在类初始化时设置）
    global _llm_client_for_cache
    if _llm_client_for_cache is None:
        logger.warning("LLM客户端未初始化，返回空响应")
        return "[]"

    try:
        response = _llm_client_for_cache.call_llm(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response
    except Exception as e:
        logger.error(f"LLM调用失败: {str(e)}")
        return "[]"


# 全局LLM客户端（用于缓存函数）
_llm_client_for_cache = None


class IntelligentResultScorer:
    """
    智能结果评分器 - 纯LLM版本
    
    只使用大模型（LLM）进行评估，移除所有硬编码评分规则和知识库
    """

    def __init__(self, country_code: str = None, log_collector=None):
        """
        初始化评分器

        Args:
            country_code: 国家代码 (保留参数兼容性，但不使用)
            log_collector: 搜索日志收集器（可选），用于记录模型调用
        """
        self.log_collector = log_collector  # 保存日志收集器引用
        # 初始化LLM客户端（优先使用 Internal API 的 gemini-2.5-pro）
        try:
            self.llm_client = InternalAPIClient(model_type='vision')  # 使用 vision 类型，实际会用 gemini-2.5-pro
            self.model_name = 'gemini-2.5-pro'
            logger.info(f"✅ LLM客户端初始化成功，使用公司内部 API (gemini-2.5-pro)")
        except Exception as e:
            logger.warning(f"⚠️ 公司内部 API 初始化失败: {str(e)}，尝试 AI Builders API")
            try:
                self.llm_client = AIBuildersAPIClient()
                self.model_name = 'deepseek'
                logger.info(f"✅ 使用 AI Builders API，模型: {self.model_name}")
            except Exception as e2:
                logger.error(f"❌ LLM客户端初始化失败: {str(e2)}")
                self.llm_client = None
                self.model_name = 'none'

        # 设置全局LLM客户端（用于缓存函数）
        global _llm_client_for_cache
        _llm_client_for_cache = self.llm_client

        logger.info("✅ 评分器初始化完成（纯LLM模式，使用 lru_cache)")

    # ==============================================================================
    # 缓存键生成
    # ==============================================================================
    def _generate_llm_cache_key(self, batch: List[Dict[str, Any]], query: str, metadata: Optional[Dict] = None) -> str:
        """生成LLM缓存键"""
        key_data = {
            'query': query,
            'metadata': metadata,
            'titles': [r.get('title', '') for r in batch]
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _safe_extract_metadata(self, metadata: Optional[Dict], field: str, max_len: int = 50) -> str:
        """
        安全提取元数据字段

        Args:
            metadata: 元数据字典
            field: 字段名（会自动尝试 field_name 作为后备）
            max_len: 最大长度（默认50）

        Returns:
            提取的字符串值，如果未找到则返回空字符串
        """
        if not metadata:
            return ''

        # 尝试获取字段（支持 field 和 field_name 两种形式）
        value = metadata.get(field) or metadata.get(f'{field}_name', '')

        # 转换为字符串并限制长度
        return str(value)[:max_len] if value else ''

    # ==============================================================================
    # 黑名单过滤（安全功能，保留）
    # ==============================================================================
    def _should_filter_by_blacklist(self, result: Dict[str, Any], metadata: Optional[Dict] = None) -> tuple[bool, str]:
        """
        检查结果是否应该被黑名单过滤
        
        Returns:
            (should_filter, filter_reason)
        """
        # 简化的黑名单检查
        blacklist_keywords = [
            'porn', 'xxx', 'casino', 'gambling', 'betting',
            'viagra', 'cialis', 'loan', 'debt', 'insurance'
        ]
        
        title = result.get('title', '').lower()
        url = result.get('url', '').lower()
        combined = f"{title} {url}"
        
        for keyword in blacklist_keywords:
            if keyword in combined:
                return True, f"包含黑名单关键词: {keyword}"
        
        return False, ""

    # ==============================================================================
    # MCP工具丰富（保留用于获取上下文信息）
    # ==============================================================================
    def _enrich_result_with_mcp_tools(self, result: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用MCP工具丰富结果信息（视频缩略图、网页内容等）
        这些信息将作为上下文传递给LLM，而不是直接生成评分
        """
        # 简化版本：保留结构但实际不做丰富
        # 实际丰富逻辑可以后续添加
        return result

    # ==============================================================================
    # LLM批量评估方法（核心）
    # ==============================================================================
    def _evaluate_batch_with_llm(self, results: List[Dict[str, Any]], query: str, metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        使用LLM批量评估多个结果
        
        Args:
            results: 搜索结果列表（最多10个结果）
            query: 搜索查询
            metadata: 额外的元数据
        
        Returns:
            包含评分的结果列表
        """
        if not self.llm_client or not results:
            return results
        
        # ✨ 优化性能：减少批量大小（10个 → 5个），降低单次LLM评分时间，避免超时
        # 配合前端超时从180秒增加到300秒的优化，确保搜索请求在合理时间内完成
        BATCH_SIZE = 5
        batches = [results[i:i + BATCH_SIZE] for i in range(0, len(results), BATCH_SIZE)]
        
        scored_results = []
        for batch in batches:
            batch_scores = self._call_llm_for_batch(batch, query, metadata)
            scored_results.extend(batch_scores)
        
        return scored_results

    def _call_llm_for_batch(self, batch: List[Dict[str, Any]], query: str, metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """为一个批次的结果调用LLM进行批量评分"""
        if not self.llm_client:
            return batch
        
        try:
            # 构建批量评估的prompt
            system_prompt = """你是一个精准的教育资源批量评分专家。请按照给定的评分规则，一次性评估多个教育资源。

【🚨 评分维度】（总分10分）
1. ⭐ 年级匹配度（0-3分）【最关键】
2. ⭐ 学科匹配度（0-3分）【关键】
3. 资源质量（0-2分）
4. 内容完整性（0-2分）

【🔴 评分规则 - 必须遵守】
- 年级不符 → 必须给 ≤5分
- 学科不符 → 必须给 ≤5分
- 年级和学科都不符 → 必须给 ≤3分

【📝 推荐理由要求】
推荐理由必须是详细的自然语言描述，具体说明：
- 年级是否匹配（为什么匹配或不匹配）
- 学科是否匹配（为什么匹配或不匹配）
- 资源质量如何（YouTube播放列表、官方内容等）
- 内容是否完整（视频数量、课程覆盖等）

【📝 批量输出格式】
返回JSON数组，每个元素包含一个结果的评分：
[
  {"index":0,"score":9.5,"reason":"这个YouTube播放列表专门针对Kelas 3 SD（三年级）设计的数学课程，完全符合目标年级和学科。播放列表包含多个章节的完整教学内容，来自教育频道，资源质量高。"},
  {"index":1,"score":3.0,"reason":"虽然标题包含数学内容，但针对的是SMU kelas 3（高中三年级），与目标年级（小学三年级）不符。内容关于SNMPTN大学入学考试，并非小学数学教育。"},
  ...
]

其中index是结果在输入列表中的索引（从0开始）。

【⚠️ 重要】
- reason必须是详细的自然语言说明（至少20字），而不是简短的关键词
- 不要使用"年级匹配度优秀（3分）"这种格式化表达
- 使用自然、流畅的语言解释评分原因
"""

            # 获取元数据（使用辅助方法）
            safe_grade = self._safe_extract_metadata(metadata, 'grade')
            safe_subject = self._safe_extract_metadata(metadata, 'subject')
            safe_query = query[:200] if query else ''

            # 构建用户prompt
            user_prompt_parts = [
                f"【目标信息】",
                f"- 目标年级：{safe_grade}",
                f"- 目标学科：{safe_subject}",
                f"- 搜索查询：{safe_query}",
                f"",
                f"【待评估的 {len(batch)} 个资源】"
            ]

            # 添加每个结果的信息
            for idx, result in enumerate(batch):
                safe_title = result.get('title', '')[:200]
                safe_snippet = result.get('snippet', '')[:500]
                url = result.get('url', '')

                user_prompt_parts.append(f"\n【资源 {idx}】")
                user_prompt_parts.append(f"- 标题：{safe_title}")
                user_prompt_parts.append(f"- 描述：{safe_snippet}")
                user_prompt_parts.append(f"- URL：{url}")

            user_prompt_parts.append("\n【任务】")
            user_prompt_parts.append(f"请评估以上 {len(batch)} 个资源，返回JSON数组格式的评分结果。")
            user_prompt_parts.append("确保每个资源都有对应的评分，index必须正确对应。")

            user_prompt = "\n".join(user_prompt_parts)

            # 生成缓存键
            cache_key = self._generate_llm_cache_key(batch, query, metadata)

            # 记录开始时间
            import time
            start_time = time.time()

            # 获取LLM参数（使用配置管理）
            llm_params = get_batch_evaluation_params(max_results=len(batch))

            # 调用LLM（使用 lru_cache 自动缓存）
            response = _call_llm_with_cache(
                cache_key=cache_key,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=llm_params['max_tokens'],
                temperature=llm_params['temperature']
            )

            # 计算执行时间
            execution_time = time.time() - start_time

            # ✅ 记录LLM调用到日志收集器
            if self.log_collector:
                try:
                    # 构建输入信息摘要（使用辅助方法）
                    input_summary = f"批量评估 {len(batch)} 个搜索结果\n"
                    input_summary += f"目标年级: {self._safe_extract_metadata(metadata, 'grade')}\n"
                    input_summary += f"目标学科: {self._safe_extract_metadata(metadata, 'subject')}"

                    # 截取输出结果（限制长度）
                    output_summary = response[:500] + "..." if len(response) > 500 else response

                    # 记录LLM调用
                    # 根据模型名称确定提供商
                    provider = "Internal API" if "gemini" in self.model_name else "AI Builders API"

                    self.log_collector.record_llm_call(
                        model_name=self.model_name,
                        function="批量结果评分",
                        provider=provider,
                        prompt=user_prompt[:200] + "..." if len(user_prompt) > 200 else user_prompt,
                        input_data=input_summary,
                        output_data=output_summary,
                        execution_time=execution_time,
                        tokens_used=None,  # 暂未返回token数
                        cost=None
                    )
                    logger.debug(f"        [📝 日志] 批量评分LLM调用已记录")
                except Exception as log_err:
                    logger.warning(f"        [⚠️ 警告] 记录批量评分LLM调用失败: {log_err}")

            # 解析响应
            scored_batch = self._parse_batch_response(response, batch)

            return scored_batch

        except Exception as e:
            logger.warning(f"批量LLM评估失败: {str(e)[:200]}")
            # 返回原始结果（后续会重试）
            return batch

    def _parse_batch_response(self, response: str, original_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """解析批量LLM响应并更新原始结果"""
        try:
            # 尝试提取JSON
            from core.json_utils import extract_json_array
            scores_array = extract_json_array(response)

            if not scores_array or len(scores_array) == 0:
                raise ValueError("未能提取有效的JSON数组")

            scored_results = []

            for idx, item in enumerate(original_batch):
                result_copy = item.copy()
                original_index = idx
                matching_score = None

                for score_item in scores_array:
                    if score_item.get('index') == original_index:
                        matching_score = score_item
                        break

                if matching_score:
                    result_copy['score'] = matching_score.get('score', 0.0)
                    result_copy['recommendation_reason'] = matching_score.get('reason', 'LLM批量评估')
                    result_copy['evaluation_method'] = 'LLM (Batch)'
                else:
                    logger.warning(f"索引 {original_index} 未找到评分")
                    result_copy['evaluation_method'] = 'LLM (Batch) - 未找到评分'
                
                scored_results.append(result_copy)

            return scored_results

        except Exception as e:
            logger.error(f"解析批量响应失败: {str(e)[:200]}")
            return original_batch

    # ==============================================================================
    # 单个结果LLM评估
    # ==============================================================================
    def _evaluate_with_llm(self, result: Dict[str, Any], query: str, metadata: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        使用LLM评估单个结果
        
        Returns:
            包含score和recommendation_reason的字典
        """
        if not self.llm_client:
            return None

        try:
            title_debug = result.get('title', 'Unknown')[:50]
            logger.info(f"[🔍 LLM评估] 开始评估: {title_debug}...")

            # 构建评估提示词
            title = result.get('title', '')
            url = result.get('url', '')
            snippet = result.get('snippet', '')

            # 获取元数据（使用辅助方法）
            safe_grade = self._safe_extract_metadata(metadata, 'grade')
            safe_subject = self._safe_extract_metadata(metadata, 'subject')

            system_prompt = """你是一个精准的教育资源评分专家。请严格按照以下规则评分：

【🚨 评分维度】（总分10分）
1. ⭐ 年级匹配度（0-3分）【最关键】
2. ⭐ 学科匹配度（0-3分）【关键】
3. 资源质量（0-2分）
4. 内容完整性（0-2分）

【🔴 评分规则 - 必须遵守】
- 年级不符 → 必须给 ≤5分
- 学科不符 → 必须给 ≤5分
- 年级和学科都不符 → 必须给 ≤3分

【📝 推荐理由要求】
推荐理由必须是详细的自然语言描述，至少20字，说明：
- 年级是否匹配及原因
- 学科是否匹配及原因
- 资源质量和内容完整性

【📝 输出格式】
返回JSON：{"score":8.5,"reason":"详细理由..."}
"""

            user_prompt = f"""【目标信息】
- 目标年级：{safe_grade}
- 目标学科：{safe_subject}
- 搜索查询：{query[:200]}

【待评估资源】
- 标题：{title[:200]}
- 描述：{snippet[:500]}
- URL：{url}

【任务】
请评估以上资源，返回JSON格式的评分结果。"""

            # 记录开始时间
            import time
            start_time = time.time()

            # 获取LLM参数（使用配置管理）
            llm_params = get_batch_evaluation_params(max_results=1)

            # 调用LLM
            response = self.llm_client.call_llm(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=llm_params['max_tokens'],
                temperature=llm_params['temperature']
            )

            # 计算执行时间
            execution_time = time.time() - start_time

            # ✅ 记录LLM调用到日志收集器
            if self.log_collector:
                try:
                    # 构建输入信息摘要
                    input_summary = f"评估单个搜索结果\n"
                    input_summary += f"标题: {result.get('title', '')[:100]}\n"
                    input_summary += f"目标年级: {safe_grade}\n"
                    input_summary += f"目标学科: {safe_subject}"

                    # 截取输出结果（限制长度）
                    output_summary = response[:300] + "..." if len(response) > 300 else response

                    # 记录LLM调用
                    # 根据模型名称确定提供商
                    provider = "Internal API" if "gemini" in self.model_name else "AI Builders API"

                    self.log_collector.record_llm_call(
                        model_name=self.model_name,
                        function="单个结果评分",
                        provider=provider,
                        prompt=user_prompt[:200] + "..." if len(user_prompt) > 200 else user_prompt,
                        input_data=input_summary,
                        output_data=output_summary,
                        execution_time=execution_time,
                        tokens_used=None,
                        cost=None
                    )
                    logger.debug(f"        [📝 日志] 单个评分LLM调用已记录")
                except Exception as log_err:
                    logger.warning(f"        [⚠️ 警告] 记录单个评分LLM调用失败: {log_err}")

            # 解析响应
            import json
            try:
                # 🔧 先清理响应中的markdown代码块标记
                cleaned_response = response.strip()
                if cleaned_response.startswith('```'):
                    # 移除markdown代码块标记
                    lines = cleaned_response.split('\n')
                    if lines[0].startswith('```'):
                        lines = lines[1:]  # 移除第一行标记
                    if lines and lines[-1].startswith('```'):
                        lines = lines[:-1]  # 移除最后一行标记
                    cleaned_response = '\n'.join(lines)

                # 尝试解析JSON
                result_data = json.loads(cleaned_response)
                score = float(result_data.get('score', 5.0))
                reason = result_data.get('reason', '根据搜索匹配度推荐')
            except:
                # 尝试正则提取（处理被截断的响应）
                score_match = re.search(r'"score"\s*:\s*([\d.]+)', response)
                # 改进的正则：匹配reason字段，即使包含换行或未闭合
                reason_match = re.search(r'"reason"\s*:\s*"([^"]*(?:"[^"]*)*)', response, re.DOTALL)

                if score_match:
                    score = float(score_match.group(1))
                    if reason_match:
                        reason = reason_match.group(1)
                        # 清理reason中的转义字符
                        reason = reason.replace('\\"', '"').replace('\\n', '\n')
                        if len(reason) > 100:
                            reason = reason[:100]
                    else:
                        reason = "LLM评估响应被截断"
                    logger.info(f"✅ LLM评估成功（正则解析）: score={score:.1f}")
                else:
                    logger.error(f"无法解析LLM响应: {response[:200]}")
                    return None

            # 确保分数在0-10范围内
            score = max(0.0, min(10.0, score))

            logger.info(f"✅ LLM评估成功: score={score:.1f}, reason={reason[:30]}...")

            return {
                'score': score,
                'recommendation_reason': reason,
                'evaluation_method': 'LLM'
            }

        except Exception as e:
            logger.warning(f"⚠️ LLM评估失败: {str(e)[:100]}")
            return None

    # ==============================================================================
    # 主评估入口
    # ==============================================================================
    def score_results(self, results: List[Dict[str, Any]], query: str, metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        对多个结果进行评分（纯LLM版本）
        
        Args:
            results: 搜索结果列表
            query: 搜索查询
            metadata: 额外的元数据
        
        Returns:
            评分后的结果列表
        """
        logger.info(f"📊 开始批量评估 {len(results)} 个搜索结果（纯LLM模式）")

        # 步骤0: 黑名单前置过滤
        filtered_results = []
        filtered_count = 0

        for result in results:
            should_filter, filter_reason = self._should_filter_by_blacklist(result, metadata)

            if should_filter:
                filtered_count += 1
                logger.warning(f"[🚫 黑名单过滤] {filter_reason}: {result.get('title', '')[:50]}")
                result['score'] = 0.0
                result['filtered'] = True
                result['filter_reason'] = filter_reason
                result['recommendation_reason'] = f"触发黑名单过滤：{filter_reason}"
                result['evaluation_method'] = 'Blacklist'
                filtered_results.append(result)
            else:
                result['filtered'] = False
                filtered_results.append(result)

        logger.info(f"[📊 黑名单过滤统计] 总计: {len(results)}, 过滤: {filtered_count}, 保留: {len(results) - filtered_count}")

        # 步骤1: 使用批量LLM评估
        try:
            scored_results = self._evaluate_batch_with_llm(filtered_results, query, metadata)
            batch_llm_count = sum(1 for r in scored_results if r.get('evaluation_method') == 'LLM (Batch)')
            logger.info(f"✅ 批量LLM评估完成: {len(filtered_results)}个结果，{batch_llm_count}个使用批量LLM评估")
            
            if batch_llm_count > 0:
                return scored_results
        except Exception as e:
            logger.warning(f"批量LLM评估失败: {str(e)[:200]}")

        # 步骤2: 降级到逐个LLM评估
        logger.info(f"📊 降级到逐个LLM评估")
        scored_results = []
        
        for idx, result in enumerate(filtered_results):
            try:
                llm_evaluation = self._evaluate_with_llm(result, query, metadata)
                if llm_evaluation:
                    result['score'] = llm_evaluation['score']
                    result['recommendation_reason'] = llm_evaluation['recommendation_reason']
                    result['evaluation_method'] = llm_evaluation.get('evaluation_method', 'LLM')
                else:
                    # LLM评估失败，设置默认值
                    result['score'] = 5.0
                    result['recommendation_reason'] = 'LLM评估失败，请手动检查'
                    result['evaluation_method'] = 'Failed'
                
                scored_results.append(result)
            except Exception as e:
                logger.error(f"结果评估失败 (索引{idx}): {str(e)[:100]}")
                result['score'] = 5.0
                result['recommendation_reason'] = '评估失败，请手动检查'
                result['evaluation_method'] = 'Error'
                scored_results.append(result)

        llm_count = sum(1 for r in scored_results if r.get('evaluation_method') in ['LLM', 'LLM (Batch)'])
        logger.info(f"✅ 评估完成: {len(results)}个结果 (LLM: {llm_count})")

        return scored_results


# ==============================================================================
# 全局辅助函数（保持向后兼容）
# ==============================================================================
_result_scorer_instance = None

def get_result_scorer(country_code: str = None, log_collector=None) -> IntelligentResultScorer:
    """
    获取评分器单例实例

    Args:
        country_code: 国家代码
        log_collector: 搜索日志收集器（可选），用于记录模型调用

    Returns:
        IntelligentResultScorer实例
    """
    # 如果传入了log_collector，创建新实例（不使用全局单例）
    if log_collector is not None:
        return IntelligentResultScorer(country_code, log_collector)

    # 使用全局单例（向后兼容）
    global _result_scorer_instance
    if _result_scorer_instance is None:
        _result_scorer_instance = IntelligentResultScorer(country_code)
    return _result_scorer_instance
