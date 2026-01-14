#!/usr/bin/env python3
"""
搜索建议模块
提供智能搜索建议和自动完成功能
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Optional, Set
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from logger_utils import get_logger

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = get_logger('search_suggestions')


class SearchSuggestions:
    """
    搜索建议引擎

    功能:
    1. 基于历史的建议
    2. 热门搜索建议
    3. 自动完成
    4. 多语言支持
    """

    def __init__(self, history_file: str = "data/config/search_history.json"):
        """
        初始化搜索建议引擎

        Args:
            history_file: 搜索历史文件路径
        """
        self.history_file = Path(history_file)
        self.search_history: List[Dict] = []
        self.popular_searches: Dict[str, Counter] = defaultdict(Counter)

        # 预定义热门搜索
        self.predefined_popular = {
            "Indonesia": [
                "Kelas 10 Matematika",
                "Kelas 11 Fisika",
                "Kelas 12 Kimia",
                "Kelas 10 Biologi",
                "Kelas 11 Bahasa Indonesia"
            ],
            "China": [
                "高中一 数学",
                "高中一 物理",
                "高中二 化学",
                "高中三 生物",
                "高中二 英语"
            ],
            "India": [
                "Class 10 Mathematics",
                "Class 12 Physics",
                "Class 11 Chemistry",
                "Class 10 Biology",
                "Class 12 English"
            ],
            "Russia": [
                "10 класс Математика",
                "11 класс Физика",
                "10 класс Химия",
                "11 класс Биология",
                "10 класс Русский язык"
            ],
            "Philippines": [
                "Grade 10 Mathematics",
                "Grade 11 Science",
                "Grade 12 Physics",
                "Grade 10 Chemistry",
                "Grade 11 Biology"
            ]
        }

        self._load_history()
        self._build_popular_index()

        logger.info("✅ 搜索建议引擎初始化完成")

    def _load_history(self):
        """加载搜索历史"""
        if not self.history_file.exists():
            logger.warning(f"搜索历史文件不存在: {self.history_file}")
            return

        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                self.search_history = json.load(f)

            logger.info(f"✅ 加载了 {len(self.search_history)} 条搜索历史")
        except Exception as e:
            logger.error(f"加载搜索历史失败: {str(e)}")

    def _build_popular_index(self):
        """构建热门搜索索引"""
        for entry in self.search_history:
            country = entry.get('country', '')
            grade = entry.get('grade', '')
            subject = entry.get('subject', '')

            if country and grade and subject:
                key = f"{country}|{grade}|{subject}"
                self.popular_searches[country][key] += 1

        logger.info(f"✅ 构建了 {len(self.popular_searches)} 个国家的热门搜索索引")

    def get_suggestions(self,
                       prefix: str,
                       country: Optional[str] = None,
                       limit: int = 10) -> List[Dict[str, str]]:
        """
        获取搜索建议

        Args:
            prefix: 搜索前缀
            country: 国家代码（可选）
            limit: 返回建议数量

        Returns:
            建议列表
        """
        suggestions = []
        prefix_lower = prefix.lower().strip()

        if not prefix_lower:
            # 如果没有前缀，返回热门搜索
            return self._get_popular_suggestions(country, limit)

        # 1. 从历史中匹配
        history_suggestions = self._match_from_history(prefix_lower, country, limit)
        suggestions.extend(history_suggestions)

        # 2. 从预定义热门搜索中匹配
        predefined_suggestions = self._match_from_predefined(prefix_lower, country, limit)
        suggestions.extend(predefined_suggestions)

        # 3. 去重并限制数量
        unique_suggestions = []
        seen = set()

        for suggestion in suggestions:
            key = suggestion['text']
            if key not in seen:
                seen.add(key)
                unique_suggestions.append(suggestion)

                if len(unique_suggestions) >= limit:
                    break

        return unique_suggestions[:limit]

    def _get_popular_suggestions(self, country: Optional[str], limit: int) -> List[Dict[str, str]]:
        """获取热门搜索建议"""
        suggestions = []

        if country and country in self.predefined_popular:
            for search_text in self.predefined_popular[country][:limit]:
                suggestions.append({
                    "text": search_text,
                    "type": "popular",
                    "country": country
                })

        return suggestions

    def _match_from_history(self, prefix: str, country: Optional[str], limit: int) -> List[Dict[str, str]]:
        """从历史记录中匹配"""
        suggestions = []

        for entry in reversed(self.search_history[-1000:]):  # 只看最近1000条
            entry_country = entry.get('country', '')
            grade = entry.get('grade', '')
            subject = entry.get('subject', '')

            # 过滤国家
            if country and entry_country != country:
                continue

            # 构建搜索文本
            search_text = f"{grade} {subject}"

            # 匹配前缀
            if prefix_lower in search_text.lower():
                suggestions.append({
                    "text": search_text,
                    "type": "history",
                    "country": entry_country
                })

                if len(suggestions) >= limit:
                    break

        return suggestions

    def _match_from_predefined(self, prefix: str, country: Optional[str], limit: int) -> List[Dict[str, str]]:
        """从预定义热门搜索中匹配"""
        suggestions = []

        countries_to_check = [country] if country else self.predefined_popular.keys()

        for check_country in countries_to_check:
            if check_country not in self.predefined_popular:
                continue

            for search_text in self.predefined_popular[check_country]:
                if prefix_lower in search_text.lower():
                    suggestions.append({
                        "text": search_text,
                        "type": "popular",
                        "country": check_country
                    })

                    if len(suggestions) >= limit:
                        break

        return suggestions

    def get_trending_searches(self, country: Optional[str] = None, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取趋势搜索（最近N天最流行的搜索）

        Args:
            country: 国家代码（可选）
            days: 天数
            limit: 返回数量

        Returns:
            趋势搜索列表
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_searches: Counter = Counter()

        for entry in self.search_history:
            # 检查时间
            timestamp_str = entry.get('timestamp', '')
            if not timestamp_str:
                continue

            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                if timestamp < cutoff_date:
                    continue
            except:
                continue

            # 过滤国家
            entry_country = entry.get('country', '')
            if country and entry_country != country:
                continue

            # 构建键
            key = f"{entry.get('grade', '')} {entry.get('subject', '')}"
            recent_searches[key] += 1

        # 获取最热门的
        trending = []
        for search_text, count in recent_searches.most_common(limit):
            trending.append({
                "text": search_text,
                "count": count,
                "type": "trending"
            })

        return trending

    def add_search_to_history(self, country: str, grade: str, subject: str):
        """
        添加搜索到历史

        Args:
            country: 国家
            grade: 年级
            subject: 学科
        """
        entry = {
            "country": country,
            "grade": grade,
            "subject": subject,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        self.search_history.append(entry)
        self._build_popular_index()

        logger.debug(f"添加搜索历史: {country} - {grade} - {subject}")


# 全局单例
_global_suggestions: Optional[SearchSuggestions] = None


def get_search_suggestions() -> SearchSuggestions:
    """获取全局搜索建议引擎实例"""
    global _global_suggestions
    if _global_suggestions is None:
        _global_suggestions = SearchSuggestions()
    return _global_suggestions


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("搜索建议引擎测试")
    print("=" * 60)

    suggestions = SearchSuggestions()

    # 测试1: 获取建议
    print("\n测试1: 获取数学相关建议")
    results = suggestions.get_suggestions("mat", country="Indonesia", limit=5)
    print(f"查询: 'mat' (Indonesia)")
    for r in results:
        print(f"  - {r['text']} [{r['type']}]")

    # 测试2: 获取热门搜索
    print("\n测试2: 获取热门搜索 (Indonesia)")
    results = suggestions.get_suggestions("", country="Indonesia", limit=5)
    for r in results:
        print(f"  - {r['text']} [{r['type']}]")

    # 测试3: 获取趋势搜索
    print("\n测试3: 获取趋势搜索 (最近7天)")
    results = suggestions.get_trending_searches(days=7, limit=5)
    if results:
        for r in results:
            print(f"  - {r['text']} (搜索次数: {r['count']})")
    else:
        print("  暂无趋势数据")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
