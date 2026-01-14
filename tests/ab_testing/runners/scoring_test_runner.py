#!/usr/bin/env python3
"""
智能评分测试执行器

测试不同模型在智能评分任务上的准确性和性能
"""
import sys
import json
import time
import os
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from logger_utils import get_logger
from tests.ab_testing.utils.llm_caller import LLMCaller

logger = get_logger('scoring_test_runner')


class ScoringTestRunner:
    """智能评分测试执行器"""

    def __init__(
        self,
        models: List[str],
        test_cases_limit: int = None,
        verbose: bool = False
    ):
        """
        初始化测试执行器

        Args:
            models: 要测试的模型列表
            test_cases_limit: 测试用例数量限制
            verbose: 是否详细输出
        """
        self.models = models
        self.test_cases_limit = test_cases_limit
        self.verbose = verbose
        self.results = []

        # 加载测试用例
        self._load_test_cases()

        # 初始化LLM调用器
        self.llm_caller = LLMCaller()

    def _load_test_cases(self):
        """加载测试用例"""
        test_cases_path = Path(__file__).parent.parent / "test_data" / "test_cases_scoring.json"

        if not test_cases_path.exists():
            raise FileNotFoundError(f"测试用例文件不存在: {test_cases_path}")

        with open(test_cases_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.test_cases = data["test_cases"]

        # 限制测试用例数量
        if self.test_cases_limit:
            self.test_cases = self.test_cases[:self.test_cases_limit]

        logger.info(f"✅ 已加载 {len(self.test_cases)} 个测试用例")

    def run(self) -> List[Dict[str, Any]]:
        """
        运行测试

        Returns:
            测试结果列表
        """
        total_tests = len(self.models) * len(self.test_cases)
        current_test = 0

        for model in self.models:
            logger.info(f"\n{'='*80}")
            logger.info(f"🧪 测试模型: {model}")
            logger.info(f"{'='*80}")

            model_results = {
                "model": model,
                "test_results": [],
                "statistics": {
                    "total_tests": len(self.test_cases),
                    "total_time": 0,
                    "average_time": 0,
                }
            }

            for test_case in self.test_cases:
                current_test += 1
                logger.info(f"\n[{current_test}/{total_tests}] 测试用例: {test_case['id']}")

                # 运行单个测试
                test_result = self._run_single_test(model, test_case)
                model_results["test_results"].append(test_result)

                # 打印结果
                if self.verbose:
                    self._print_test_result(test_result)

            # 计算模型统计信息
            model_results["statistics"]["total_time"] = sum(
                r["execution_time"] for r in model_results["test_results"]
            )
            model_results["statistics"]["average_time"] = (
                model_results["statistics"]["total_time"] / len(model_results["test_results"])
            )

            self.results.append(model_results)

        # 生成汇总统计
        self._calculate_summary_statistics()

        return self.results

    def _run_single_test(self, model: str, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行单个测试

        Args:
            model: 模型名称
            test_case: 测试用例

        Returns:
            测试结果
        """
        start_time = time.time()

        # 准备测试数据
        target = test_case["target"]
        search_results = test_case["search_results"]

        test_result = {
            "test_case_id": test_case["id"],
            "target": target,
            "model": model,
            "results": [],
            "execution_time": 0,
        }

        # 对每个搜索结果进行评分
        for search_result in search_results:
            logger.info(f"  - 评分: {search_result['title'][:50]}...")

            try:
                # 调用评分器（使用指定模型）
                score, reason, identified_info = self._score_with_model(
                    result=search_result,
                    query=target,
                    model=model
                )

                # 评估结果
                expected = search_result.get("expected", {})
                evaluation = self._evaluate_score(
                    score=score,
                    reason=reason,
                    identified_info=identified_info,
                    expected=expected
                )

                result_eval = {
                    "title": search_result["title"],
                    "score": score,
                    "reason": reason,
                    "identified_info": identified_info,
                    "expected_score": expected.get("score"),
                    "evaluation": evaluation,
                    "success": evaluation["score_match"],
                }

            except Exception as e:
                logger.error(f"  ❌ 评分失败: {str(e)}")
                expected = search_result.get("expected", {})
                result_eval = {
                    "title": search_result["title"],
                    "score": None,
                    "reason": None,
                    "identified_info": None,
                    "expected_score": expected.get("score"),
                    "error": str(e),
                    "success": False,
                }

            test_result["results"].append(result_eval)

        # 计算执行时间
        test_result["execution_time"] = time.time() - start_time

        return test_result

    def _score_with_model(
        self,
        result: Dict[str, Any],
        query: Dict[str, Any],
        model: str
    ) -> tuple[float, str, Dict[str, Any]]:
        """
        使用指定模型进行评分

        Args:
            result: 搜索结果
            query: 查询信息（国家、年级、学科）
            model: 模型名称

        Returns:
            (评分, 推荐理由, 识别信息)
        """
        # 构建评分提示词
        target_grade = query["grade"]
        target_subject = query["subject"]
        country_code = query["country_code"]

        # 获取年级和学科的所有变体
        grade_variants = query.get("grade_variants", [target_grade])
        subject_variants = query.get("subject_variants", [target_subject])

        # 构建提示词
        grade_variants_str = ", ".join(grade_variants[:3])
        subject_variants_str = ", ".join(subject_variants[:3])

        prompt = f"""请为以下搜索结果评分（0-10分）：

**搜索目标**: {country_code} {target_grade} {target_subject}

**目标年级表达**: {grade_variants_str}
**目标学科表达**: {subject_variants_str}

**搜索结果**:
标题: {result['title']}
描述: {result.get('snippet', '')}

**评分要求**:
1. 年级匹配度（0-3分）：从标题中提取年级，与目标年级对比
2. 学科匹配度（0-3分）：从标题中提取学科，与目标学科对比
3. 资源质量（0-2分）：判断是否是完整课程/播放列表
4. 来源权威性（0-2分）：判断来源是否可信

**评分规则**:
- 年级不符必须大幅减分（≤5分）
- 学科不符必须大幅减分（≤5分）
- 完全匹配给高分（≥9分）

**输出格式**（JSON）:
{{
    "score": 评分（0-10分，浮点数）,
    "identified_grade": "从标题中识别的年级",
    "identified_subject": "从标题中识别的学科",
    "reason": "评分理由（30-50字）"
}}

请确保输出是有效的JSON格式。"""

        # 调用LLM
        llm_result = self.llm_caller.call_llm(
            prompt=prompt,
            model=model,
            max_tokens=200,
            temperature=0.3
        )

        if not llm_result["success"]:
            raise Exception(llm_result["error"])

        response = llm_result["response"]

        # 解析响应
        import re
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            data = json.loads(json_str)
            score = float(data.get("score", 5.0))
            identified_grade = data.get("identified_grade", "")
            identified_subject = data.get("identified_subject", "")
            reason = data.get("reason", "")
        else:
            # 解析失败，使用默认值
            logger.warning(f"⚠️ 无法解析JSON响应，使用默认评分")
            score = 5.0
            identified_grade = ""
            identified_subject = ""
            reason = "解析失败"

        identified_info = {
            "grade": identified_grade,
            "subject": identified_subject,
        }

        return score, reason, identified_info

    def _evaluate_score(
        self,
        score: float,
        reason: str,
        identified_info: Dict[str, Any],
        expected: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        评估评分结果

        Args:
            score: 实际评分
            reason: 评分理由
            identified_info: 识别的年级和学科
            expected: 期望结果

        Returns:
            评估结果
        """
        expected_score = expected.get("score", 5.0)
        score_range = expected.get("score_range", [expected_score - 1, expected_score + 1])

        # 检查评分是否在预期范围内
        score_match = score_range[0] <= score <= score_range[1]

        # 检查年级识别（如果有期望值）
        grade_match = expected.get("grade_match", True)
        if identified_info["grade"]:
            expected_grade = expected.get("identified_grade", "")
            if expected_grade:
                # 检查是否包含期望的年级表达
                grade_match = expected_grade in identified_info["grade"] or identified_info["grade"] in expected_grade

        # 检查学科识别（如果有期望值）
        subject_match = expected.get("subject_match", True)
        if identified_info["subject"]:
            expected_subject = expected.get("identified_subject", "")
            if expected_subject:
                # 检查是否包含期望的学科表达
                subject_match = expected_subject in identified_info["subject"] or identified_info["subject"] in expected_subject

        return {
            "score_match": score_match,
            "grade_match": grade_match,
            "subject_match": subject_match,
            "score_deviation": abs(score - expected_score),
            "all_match": score_match and grade_match and subject_match,
        }

    def _print_test_result(self, test_result: Dict[str, Any]):
        """打印测试结果"""
        logger.info(f"\n📊 测试结果: {test_result['test_case_id']}")
        logger.info(f"  模型: {test_result['model']}")
        logger.info(f"  执行时间: {test_result['execution_time']:.2f}秒")

        for i, result in enumerate(test_result["results"], 1):
            logger.info(f"\n  结果 {i}:")
            logger.info(f"    标题: {result['title'][:60]}...")
            logger.info(f"    实际评分: {result.get('score', 'N/A')}")
            logger.info(f"    期望评分: {result.get('expected_score', 'N/A')}")
            logger.info(f"    匹配: {'✅' if result.get('success') else '❌'}")

            if "evaluation" in result:
                eval_ = result["evaluation"]
                logger.info(f"    评分匹配: {'✅' if eval_.get('score_match') else '❌'}")
                logger.info(f"    年级匹配: {'✅' if eval_.get('grade_match') else '❌'}")
                logger.info(f"    学科匹配: {'✅' if eval_.get('subject_match') else '❌'}")
                logger.info(f"    评分偏差: {eval_.get('score_deviation', 0):.2f}")

            if result.get("identified_info"):
                logger.info(f"    识别年级: {result['identified_info'].get('grade', 'N/A')}")
                logger.info(f"    识别学科: {result['identified_info'].get('subject', 'N/A')}")

    def _calculate_summary_statistics(self):
        """计算汇总统计"""
        logger.info("\n" + "="*80)
        logger.info("📊 汇总统计")
        logger.info("="*80)

        for model_result in self.results:
            model = model_result["model"]
            stats = model_result["statistics"]

            # 计算准确率
            total_results = sum(len(r["results"]) for r in model_result["test_results"])
            successful_results = sum(
                sum(1 for r in test_result["results"] if r.get("success", False))
                for test_result in model_result["test_results"]
            )

            accuracy = successful_results / total_results if total_results > 0 else 0

            # 计算平均评分偏差
            score_deviations = [
                r["evaluation"]["score_deviation"]
                for test_result in model_result["test_results"]
                for r in test_result["results"]
                if "evaluation" in r and "score_deviation" in r["evaluation"]
            ]
            avg_score_deviation = sum(score_deviations) / len(score_deviations) if score_deviations else 0

            logger.info(f"\n模型: {model}")
            logger.info(f"  总测试数: {stats['total_tests']}")
            logger.info(f"  总结果数: {total_results}")
            logger.info(f"  成功数: {successful_results}")
            logger.info(f"  准确率: {accuracy:.2%}")
            logger.info(f"  平均评分偏差: {avg_score_deviation:.2f}")
            logger.info(f"  总耗时: {stats['total_time']:.2f}秒")
            logger.info(f"  平均耗时: {stats['average_time']:.2f}秒")

    def save_results(self, output_path: Path):
        """保存测试结果"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        logger.info(f"\n✅ 测试结果已保存: {output_path}")

    def generate_report(self, output_path: Path):
        """生成测试报告"""
        from datetime import datetime

        lines = []
        lines.append("# 智能评分A/B测试报告\n")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append("---\n\n")

        # 汇总统计
        lines.append("## 📊 汇总统计\n\n")
        lines.append("| 模型 | 总测试数 | 成功率 | 平均评分偏差 | 平均耗时 |\n")
        lines.append("|------|---------|--------|-------------|---------|\n")

        for model_result in self.results:
            model = model_result["model"]
            stats = model_result["statistics"]

            total_results = sum(len(r["results"]) for r in model_result["test_results"])
            successful_results = sum(
                sum(1 for r in test_result["results"] if r.get("success", False))
                for test_result in model_result["test_results"]
            )

            accuracy = successful_results / total_results if total_results > 0 else 0

            score_deviations = [
                r["evaluation"]["score_deviation"]
                for test_result in model_result["test_results"]
                for r in test_result["results"]
                if "evaluation" in r and "score_deviation" in r["evaluation"]
            ]
            avg_score_deviation = sum(score_deviations) / len(score_deviations) if score_deviations else 0

            lines.append(
                f"| {model} | {total_results} | {accuracy:.2%} | {avg_score_deviation:.2f} | {stats['average_time']:.2f}s |\n"
            )

        lines.append("\n---\n\n")

        # 详细结果
        lines.append("## 📋 详细结果\n\n")

        for model_result in self.results:
            model = model_result["model"]
            lines.append(f"### {model}\n\n")

            for test_result in model_result["test_results"][:10]:  # 只显示前10个测试用例
                lines.append(f"#### 测试用例: {test_result['test_case_id']}\n\n")
                lines.append(f"- 目标: {test_result['target']['country']} {test_result['target']['grade']} {test_result['target']['subject']}\n")
                lines.append(f"- 耗时: {test_result['execution_time']:.2f}秒\n\n")

                lines.append("| 标题 | 实际评分 | 期望评分 | 匹配 |\n")
                lines.append("|------|---------|---------|------|\n")

                for result in test_result["results"]:
                    title = result["title"][:40] + "..." if len(result["title"]) > 40 else result["title"]
                    score = result.get("score", "N/A")
                    expected = result.get("expected_score", "N/A")
                    match = "✅" if result.get("success", False) else "❌"

                    lines.append(f"| {title} | {score} | {expected} | {match} |\n")

                lines.append("\n")

        # 保存报告
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        logger.info(f"✅ 测试报告已生成: {output_path}")
