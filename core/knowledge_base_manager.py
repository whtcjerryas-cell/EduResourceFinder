#!/usr/bin/env python3
"""
搜索知识库管理器
动态学习和优化每个国家/地区的搜索策略
"""

import os
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from pathlib import Path
from utils.logger_utils import get_logger

logger = get_logger('knowledge_base')


class KnowledgeBaseManager:
    """
    搜索知识库管理器

    功能：
    1. 存储每个国家的搜索经验（年级表达、关键词、成功/失败模式）
    2. 自动学习和发现新的表达方式
    3. 基于历史数据生成优化的搜索策略和评分prompt
    4. 记录LLM错误，持续改进
    """

    def __init__(self, country_code: str, knowledge_base_dir: str = None):
        """
        初始化知识库管理器

        Args:
            country_code: 国家代码 (如: IQ, ID, CN)
            knowledge_base_dir: 知识库目录 (默认: data/knowledge_base/)
        """
        self.country_code = country_code.upper()

        if knowledge_base_dir is None:
            # 默认知识库目录
            project_root = Path(__file__).parent.parent
            knowledge_base_dir = project_root / "data" / "knowledge_base"

        self.kb_dir = Path(knowledge_base_dir)
        self.kb_dir.mkdir(parents=True, exist_ok=True)

        self.kb_file = self.kb_dir / f"{self.country_code}_search_knowledge.json"
        self.knowledge = self.load_knowledge()

        logger.info(f"[📚 知识库] 已加载 {self.country_code} 知识库: {self.kb_file}")

    def load_knowledge(self) -> Dict:
        """加载知识库"""
        if self.kb_file.exists():
            try:
                with open(self.kb_file, 'r', encoding='utf-8') as f:
                    kb = json.load(f)
                logger.info(f"[📚 知识库] 成功加载已有知识库")
                return kb
            except Exception as e:
                logger.warning(f"[📚 知识库] 加载失败: {e}，将创建新知识库")
                return self.create_empty_knowledge()
        else:
            logger.info(f"[📚 知识库] 知识库不存在，创建初始知识库")
            return self.create_empty_knowledge()

    def create_empty_knowledge(self) -> Dict:
        """创建空知识库结构"""
        return {
            "metadata": {
                "country": self.country_code,
                "country_name": self._get_country_name(self.country_code),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "total_searches": 0,
                "avg_quality_score": 0.0
            },
            "grade_expressions": {},
            "subject_keywords": {},
            "search_patterns": {
                "successful_queries": [],
                "failed_queries": []
            },
            "domain_preferences": {
                "tier_1_platforms": [],
                "tier_2_platforms": [],
                "missing_platforms": []
            },
            "llm_insights": {
                "accuracy_issues": [],
                "discovered_variants": []
            }
        }

    def _get_country_name(self, country_code: str) -> str:
        """获取国家名称"""
        country_names = {
            "ID": "印度尼西亚",
            "CN": "中国",
            "IQ": "伊拉克",
            "SA": "沙特阿拉伯",
            "EG": "埃及",
            "RU": "俄罗斯",
            "US": "美国",
            "IN": "印度",
            "BR": "巴西",
            "MX": "墨西哥"
        }
        return country_names.get(country_code.upper(), country_code)

    # ========================================================================
    # 年级表达管理
    # ========================================================================

    def get_grade_variants(self, grade: str) -> List[str]:
        """
        获取年级的所有已知表达

        Args:
            grade: 年级 (如: "2", "3", "Grade 2")

        Returns:
            该年级的所有已知表达列表
        """
        # 标准化年级key
        grade_key = self._normalize_grade_key(grade)

        if grade_key in self.knowledge.get("grade_expressions", {}):
            variants_data = self.knowledge["grade_expressions"][grade_key].get("local_variants", [])
            variants = []
            for v in variants_data:
                if "arabic" in v:
                    variants.append(v["arabic"])
                if "english" in v:
                    variants.append(v["english"])
            return variants
        return []

    def _normalize_grade_key(self, grade: str) -> str:
        """标准化年级key"""
        grade = grade.strip()

        # 如果已经是 "Grade X" 格式
        if grade.startswith("Grade "):
            return grade

        # 如果是纯数字
        if grade.isdigit():
            return f"Grade {grade}"

        # 提取数字
        match = re.search(r'\d+', grade)
        if match:
            return f"Grade {match.group()}"

        return grade

    def add_discovered_variant(self, grade: str, variant: str, language: str,
                             confidence: float = 0.8, source: str = "ai",
                             note: str = ""):
        """
        添加新发现的年级表达

        Args:
            grade: 标准年级 (如: "Grade 2")
            variant: 发现的表达 (如: "الصف الثاني")
            language: 语言 (arabic, english, etc.)
            confidence: 置信度 (0-1)
            source: 来源 (ai, manual)
            note: 备注
        """
        grade_key = self._normalize_grade_key(grade)

        # 初始化年级
        if grade_key not in self.knowledge["grade_expressions"]:
            self.knowledge["grade_expressions"][grade_key] = {
                "local_variants": [],
                "common_mistakes": []
            }

        # 检查是否已存在
        for v in self.knowledge["grade_expressions"][grade_key]["local_variants"]:
            if language in v and v[language] == variant:
                logger.info(f"[📚 知识库] 表达已存在: {variant}")
                return

        # 添加新表达
        new_variant = {
            language: variant,
            "confidence": confidence,
            "verified_by": source,
            "discovered_at": datetime.now(timezone.utc).isoformat()
        }

        if note:
            new_variant["note"] = note

        self.knowledge["grade_expressions"][grade_key]["local_variants"].append(new_variant)

        logger.info(f"[📚 知识库] 发现新表达: {grade_key} -> {variant} ({language})")

        # 记录到discovered_variants
        discovery = {
            "grade": grade_key,
            "variant": variant,
            "language": language,
            "confidence": confidence,
            "discovered_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending_review"  # pending_review, approved, rejected
        }
        self.knowledge["llm_insights"]["discovered_variants"].append(discovery)

    # ========================================================================
    # 学科关键词管理
    # ========================================================================

    def get_subject_variants(self, subject: str) -> List[str]:
        """获取学科的所有已知表达"""
        # 标准化学科
        subject_key = self._normalize_subject_key(subject)

        if subject_key in self.knowledge.get("subject_keywords", {}):
            variants_data = self.knowledge["subject_keywords"][subject_key].get("local_variants", [])
            variants = []
            for v in variants_data:
                if "arabic" in v:
                    variants.append(v["arabic"])
                if "english" in v:
                    variants.append(v["english"])
            return variants
        return []

    def _normalize_subject_key(self, subject: str) -> str:
        """标准化学科key"""
        subject_mapping = {
            "math": "Mathematics",
            "mathematics": "Mathematics",
            "رياضيات": "Mathematics",
            "matematika": "Mathematics",
            "科学": "Science",
            "علوم": "Science",
        }
        return subject_mapping.get(subject.lower(), subject.title())

    # ========================================================================
    # LLM错误记录
    # ========================================================================

    def record_llm_mistake(self, mistake_type: str, example: str,
                          correction: str, severity: str = "high"):
        """
        记录LLM错误到知识库

        Args:
            mistake_type: 错误类型 (grade_mismatch, language_error, etc.)
            example: 错误示例
            correction: 修正方案
            severity: 严重程度 (high, medium, low)
        """
        # 检查是否已记录
        for issue in self.knowledge["llm_insights"]["accuracy_issues"]:
            if issue["example"] == example:
                logger.info(f"[📚 知识库] 错误已记录: {example}")
                return

        mistake = {
            "issue": mistake_type,
            "example": example,
            "fix": correction,
            "severity": severity,
            "status": "pending_fix",  # pending_fix, fixed, ignored
            "reported_at": datetime.now(timezone.utc).isoformat(),
            "frequency": 1
        }

        self.knowledge["llm_insights"]["accuracy_issues"].append(mistake)
        logger.warning(f"[📚 知识库] 记录LLM错误: {mistake_type} - {example}")

    def mark_issue_fixed(self, example: str):
        """标记问题已修复"""
        for issue in self.knowledge["llm_insights"]["accuracy_issues"]:
            if issue["example"] == example:
                issue["status"] = "fixed"
                issue["fixed_at"] = datetime.now(timezone.utc).isoformat()
                logger.info(f"[📚 知识库] 问题已标记为修复: {example}")
                return

    # ========================================================================
    # 搜索结果记录
    # ========================================================================

    def record_search_results(self, query: str, results: List[Dict],
                             quality_report: Dict):
        """
        记录搜索结果到知识库

        Args:
            query: 使用的查询词
            results: 搜索结果列表
            quality_report: 质量评估报告
        """
        # 更新元数据
        self.knowledge["metadata"]["total_searches"] += 1
        self.knowledge["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()

        # 更新平均质量分
        current_avg = self.knowledge["metadata"]["avg_quality_score"]
        total_searches = self.knowledge["metadata"]["total_searches"]
        new_score = quality_report.get("overall_quality_score", 0)

        if current_avg > 0:
            self.knowledge["metadata"]["avg_quality_score"] = (
                (current_avg * (total_searches - 1) + new_score) / total_searches
            )
        else:
            self.knowledge["metadata"]["avg_quality_score"] = new_score

        # 记录成功/失败查询
        avg_score = quality_report.get("overall_quality_score", 0)
        results_count = len(results)

        # 分析来源分布
        domains = self._extract_domains(results)
        youtube_ratio = domains.count("youtube.com") / len(domains) if domains else 0

        if avg_score >= 7.0:
            # 成功查询
            success_query = {
                "query": query,
                "avg_score": avg_score,
                "results_count": results_count,
                "youtube_ratio": youtube_ratio,
                "notes": "",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self.knowledge["search_patterns"]["successful_queries"].append(success_query)
            logger.info(f"[📚 知识库] 记录成功查询: {query} (分数: {avg_score})")
        else:
            # 失败查询
            failed_query = {
                "query": query,
                "avg_score": avg_score,
                "results_count": results_count,
                "reason": "质量分数过低",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self.knowledge["search_patterns"]["failed_queries"].append(failed_query)
            logger.warning(f"[📚 知识库] 记录失败查询: {query} (分数: {avg_score})")

        # 更新域名偏好
        self._update_domain_preferences(domains, avg_score)

    def _extract_domains(self, results: List[Dict]) -> List[str]:
        """从结果中提取域名"""
        domains = []
        for result in results:
            url = result.get("url", "")
            if "://" in url:
                domain = url.split("/")[2]
                # 去掉www.
                if domain.startswith("www."):
                    domain = domain[4:]
                domains.append(domain)
        return domains

    def _update_domain_preferences(self, domains: List[Dict], avg_score: float):
        """更新域名偏好"""
        domain_counts = {}
        for domain in domains:
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

        for domain, count in domain_counts.items():
            # 查找是否已存在
            found = False
            for platform in self.knowledge["domain_preferences"]["tier_1_platforms"]:
                if platform["domain"] == domain:
                    # 更新平均质量
                    old_quality = platform.get("avg_quality", 0)
                    old_count = platform.get("results_count", 0)
                    new_quality = (old_quality * old_count + avg_score) / (old_count + 1)
                    platform["avg_quality"] = new_quality
                    platform["results_count"] = old_count + count
                    found = True
                    break

            if not found and count >= 2:  # 至少出现2次才记录
                self.knowledge["domain_preferences"]["tier_1_platforms"].append({
                    "domain": domain,
                    "avg_quality": avg_score,
                    "abundance": "high" if count >= 5 else "medium",
                    "results_count": count
                })

    # ========================================================================
    # Prompt生成
    # ========================================================================

    def generate_evaluation_prompt(self, base_prompt: str) -> str:
        """
        基于知识库生成增强的评估prompt

        Args:
            base_prompt: 基础prompt

        Returns:
            增强后的prompt
        """
        enhanced = base_prompt

        # 添加年级表达
        if self.knowledge.get("grade_expressions"):
            grade_section = "\n## 重要年级表达（必须识别）\n"
            for grade_key, grade_data in self.knowledge["grade_expressions"].items():
                grade_section += f"\n### {grade_key}\n"
                for variant in grade_data.get("local_variants", []):
                    if "arabic" in variant:
                        grade_section += f"- {variant['arabic']} (阿拉伯语)\n"
                    if "english" in variant:
                        note = f" - {variant.get('note', '')}" if variant.get('note') else ""
                        grade_section += f"- {variant['english']} (英语){note}\n"

                # 添加常见错误
                for mistake in grade_data.get("common_mistakes", []):
                    grade_section += f"⚠️ 常见错误: {mistake['mistake']} -> {mistake['correction']}\n"

            enhanced += grade_section

        # 添加常见错误（必须避免）
        if self.knowledge["llm_insights"]["accuracy_issues"]:
            mistakes_section = "\n## 常见LLM错误（必须避免）\n"
            for issue in self.knowledge["llm_insights"]["accuracy_issues"]:
                if issue["status"] != "fixed":
                    mistakes_section += f"- ❌ {issue['issue']}: {issue['example']}\n"
                    mistakes_section += f"  ✅ 修正: {issue['fix']}\n\n"

            enhanced += mistakes_section

        return enhanced

    def generate_search_strategy(self) -> Dict[str, Any]:
        """
        基于知识库生成优化的搜索策略

        Returns:
            搜索策略字典
        """
        strategy = {
            "preferred_languages": [],
            "grade_variants": {},
            "subject_variants": {},
            "avoid_keywords": [],
            "domain_focus": []
        }

        # 从成功查询中提取模式
        successful_queries = self.knowledge["search_patterns"]["successful_queries"]
        if successful_queries:
            # 找出平均分最高的查询
            best_queries = sorted(successful_queries,
                                key=lambda x: x["avg_score"],
                                reverse=True)[:3]

            for q in best_queries:
                # 提取关键词
                words = q["query"].split()
                for word in words:
                    if len(word) > 2 and word not in strategy["avoid_keywords"]:
                        # 如果这个词在多个高分查询中出现，保留它
                        if all(word in other_q["query"] for other_q in best_queries):
                            pass  # 这个词是好词

        # 添加年级变体
        for grade_key, grade_data in self.knowledge.get("grade_expressions", {}).items():
            variants = []
            for v in grade_data.get("local_variants", []):
                if "arabic" in v:
                    variants.append(v["arabic"])
                if "english" in v:
                    variants.append(v["english"])
            strategy["grade_variants"][grade_key] = variants

        # 添加学科变体
        for subject_key, subject_data in self.knowledge.get("subject_keywords", {}).items():
            variants = []
            for v in subject_data.get("local_variants", []):
                if "arabic" in v:
                    variants.append(v["arabic"])
                if "english" in v:
                    variants.append(v["english"])
            strategy["subject_variants"][subject_key] = variants

        # 域名优先级
        tier_1 = self.knowledge["domain_preferences"]["tier_1_platforms"]
        if tier_1:
            # 按平均质量排序
            sorted_platforms = sorted(tier_1,
                                     key=lambda x: x.get("avg_quality", 0),
                                     reverse=True)
            strategy["domain_focus"] = [p["domain"] for p in sorted_platforms[:5]]

        logger.info(f"[📚 知识库] 生成搜索策略: {len(strategy['grade_variants'])} 个年级, "
                   f"{len(strategy['domain_focus'])} 个优选域名")

        return strategy

    # ========================================================================
    # 保存和导出
    # ========================================================================

    def save(self):
        """保存知识库到文件"""
        try:
            # 更新最后更新时间
            self.knowledge["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()

            # 保存到文件
            with open(self.kb_file, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge, f, ensure_ascii=False, indent=2)

            logger.info(f"[📚 知识库] 已保存: {self.kb_file}")
        except Exception as e:
            logger.error(f"[📚 知识库] 保存失败: {e}")

    def export_summary(self) -> str:
        """导出知识库摘要（便于查看）"""
        summary = f"""
# {self.country_code} 搜索知识库摘要

## 元数据
- 国家: {self.knowledge['metadata']['country_name']}
- 总搜索次数: {self.knowledge['metadata']['total_searches']}
- 平均质量分数: {self.knowledge['metadata']['avg_quality_score']:.1f}/100
- 最后更新: {self.knowledge['metadata']['last_updated']}

## 年级表达 ({len(self.knowledge.get('grade_expressions', {}))} 个年级)
"""
        for grade, data in self.knowledge.get("grade_expressions", {}).items():
            summary += f"\n### {grade}\n"
            for variant in data.get("local_variants", []):
                if "arabic" in variant:
                    summary += f"- {variant['arabic']} (置信度: {variant['confidence']})\n"

        summary += f"\n## LLM错误记录 ({len(self.knowledge['llm_insights']['accuracy_issues'])} 个)\n"
        for issue in self.knowledge["llm_insights"]["accuracy_issues"]:
            status_emoji = "✅" if issue["status"] == "fixed" else "⚠️"
            summary += f"- {status_emoji} {issue['issue']}: {issue['example']}\n"

        summary += f"\n## 优选域名 ({len(self.knowledge['domain_preferences']['tier_1_platforms'])} 个)\n"
        for platform in self.knowledge["domain_preferences"]["tier_1_platforms"][:10]:
            summary += f"- {platform['domain']} (质量: {platform.get('avg_quality', 0):.1f})\n"

        return summary


# ========================================================================
# 全局单例
# ========================================================================

_managers = {}

def get_knowledge_base_manager(country_code: str) -> KnowledgeBaseManager:
    """获取知识库管理器实例（单例模式）"""
    country_code = country_code.upper()
    if country_code not in _managers:
        _managers[country_code] = KnowledgeBaseManager(country_code)
    return _managers[country_code]
