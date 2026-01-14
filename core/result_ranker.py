#!/usr/bin/env python3
"""
高级结果排名算法
结合多个因素对搜索结果进行智能排序
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.result_scorer import get_result_scorer
from logger_utils import get_logger

logger = get_logger('result_ranker')


class AdvancedResultRanker:
    """
    高级结果排名器

    特性:
    1. 多因素评分（URL、标题、内容、来源）
    2. 上下文感知（国家、年级、学科）
    3. 学习风格适配
    4. 去重和聚类
    5. 个性化排序（可选）
    """

    def __init__(self):
        """初始化排名器"""
        self.scorer = get_result_scorer()
        logger.info("✅ 高级结果排名器初始化完成")

    def rank_results(self,
                    results: List[Dict[str, Any]],
                    query: str,
                    context: Optional[Dict] = None,
                    max_results: int = 20) -> List[Dict[str, Any]]:
        """
        对搜索结果进行智能排名

        Args:
            results: 搜索结果列表
            query: 搜索查询
            context: 上下文信息（国家、年级、学科、学习风格）
            max_results: 最大返回结果数

        Returns:
            排序后的结果列表
        """
        if not results:
            return []

        context = context or {}
        country = context.get('country', '')
        grade = context.get('grade', '')
        subject = context.get('subject', '')

        # 1. 基础评分
        scored_results = self.scorer.score_results(results, query, context)

        # 2. 上下文增强评分
        for result in scored_results:
            base_score = result.get('score', 5.0)

            # 学习风格适配
            learning_style = context.get('learning_style', '')
            if learning_style:
                bonus = self._score_by_learning_style(result, learning_style)
                result['score'] = min(10.0, base_score + bonus)

            # 年级适配
            if grade:
                bonus = self._score_by_grade_relevance(result, grade)
                result['score'] = min(10.0, result['score'] + bonus)

            # 新鲜度加分
            result['score'] = min(10.0, result['score'] + self._score_freshness(result))

        # 3. 去重（基于URL相似度）
        deduped_results = self._deduplicate_results(scored_results)

        # 4. 多样性平衡（确保不同类型资源）
        diversified_results = self._diversify_results(deduped_results)

        # 5. 最终排序
        diversified_results.sort(key=lambda x: x.get('score', 0), reverse=True)

        # 6. 限制返回数量
        final_results = diversified_results[:max_results]

        # 7. 添加排名信息
        for i, result in enumerate(final_results, 1):
            result['rank'] = i

        logger.info(f"✅ 排名完成: {len(results)}个输入 → {len(final_results)}个输出")
        return final_results

    def _score_by_learning_style(self, result: Dict, learning_style: str) -> float:
        """根据学习风格评分"""
        bonus = 0.0
        url = result.get('url', '').lower()
        title = result.get('title', '').lower()
        combined = url + title

        if learning_style == 'visual':
            # 视觉学习者偏好视频和图像
            if any(kw in combined for kw in ['video', 'youtube', 'watch', 'animation']):
                bonus += 0.5

        elif learning_style == 'textual':
            # 文本学习者偏好文章和文档
            if any(kw in combined for kw in ['article', 'text', 'document', 'notes', 'book']):
                bonus += 0.5

        elif learning_style == 'interactive':
            # 交互学习者偏好练习和测验
            if any(kw in combined for kw in ['quiz', 'practice', 'interactive', 'exercise']):
                bonus += 0.5

        return bonus

    def _score_by_grade_relevance(self, result: Dict, grade: str) -> float:
        """根据年级相关性评分"""
        bonus = 0.0
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        combined = title + snippet

        # 检查是否包含年级信息
        if grade.lower() in combined:
            bonus += 0.3

        return bonus

    def _score_freshness(self, result: Dict) -> float:
        """新鲜度评分（优先较新的内容）"""
        # 这是一个简化版本，实际可以检查日期
        return 0.0  # 暂不实现

    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """去重相似的URL"""
        seen_urls = set()
        deduped = []

        for result in results:
            url = result.get('url', '')

            # 简单去重：完全相同的URL
            if url not in seen_urls:
                seen_urls.add(url)
                deduped.append(result)

        return deduped

    def _diversify_results(self, results: List[Dict]) -> List[Dict]:
        """确保结果多样性（不同类型的资源）"""
        if len(results) <= 10:
            return results

        # 分类结果
        playlists = []
        videos = []
        articles = []
        others = []

        for result in results:
            url = result.get('url', '').lower()
            title = result.get('title', '').lower()
            combined = url + title

            if 'playlist' in combined or 'list=' in url:
                playlists.append(result)
            elif 'youtube.com/watch' in url or 'video' in combined:
                videos.append(result)
            elif 'article' in combined or 'text' in combined:
                articles.append(result)
            else:
                others.append(result)

        # 混合返回（确保多样性）
        diversified = []

        # 优先播放列表（更完整）
        diversified.extend(playlists[:3])

        # 添加视频
        diversified.extend(videos[:5])

        # 添加其他
        diversified.extend(others[:5])

        # 添加剩余的高分结果
        remaining = playlists[3:] + videos[5:] + articles + others[5:]
        remaining.sort(key=lambda x: x.get('score', 0), reverse=True)
        diversified.extend(remaining[:10])

        return diversified


# 全局单例
_global_ranker: Optional[AdvancedResultRanker] = None


def get_result_ranker() -> AdvancedResultRanker:
    """获取全局结果排名器实例"""
    global _global_ranker
    if _global_ranker is None:
        _global_ranker = AdvancedResultRanker()
    return _global_ranker
