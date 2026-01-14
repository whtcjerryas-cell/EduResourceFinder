#!/usr/bin/env python3
"""
阿拉伯语理解能力对比测试
对比不同LLM模型对阿拉伯语教育内容的理解能力
"""

import os
import sys
import json
import time
from typing import Dict, List, Tuple
from datetime import datetime

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from openai import OpenAI


class ArabicLanguageBenchmark:
    """阿拉伯语理解能力基准测试"""

    def __init__(self):
        """初始化测试"""
        self.api_key = os.getenv("INTERNAL_API_KEY")
        self.base_url = os.getenv("INTERNAL_API_BASE_URL", "https://hk-intra-paas.transsion.com/tranai-proxy/v1")

        if not self.api_key:
            print("❌ 请设置 INTERNAL_API_KEY 环境变量")
            sys.exit(1)

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        # 测试用例
        self.test_cases = [
            {
                "name": "小学二年级 - 正确",
                "title": "رياضيات للصف الثاني ابتدائي",
                "expected_grade": "Grade 2 (小学)",
                "expected_subject": "Mathematics",
                "should_match": True,
                "description": "小学二年级数学 - 应该识别为匹配"
            },
            {
                "name": "初中二年级 - 错误",
                "title": "الرياضيات الصف الثاني متوسط",
                "expected_grade": "Grade 8 (初中)",
                "expected_subject": "Mathematics",
                "should_match": False,
                "description": "初中二年级数学 - 不应该匹配小学二年级"
            },
            {
                "name": "十二年级 - 错误",
                "title": "شرح رياضيات الصف الثاني عشر",
                "expected_grade": "Grade 12 (高中)",
                "expected_subject": "Mathematics",
                "should_match": False,
                "description": "十二年级数学 - 不应该匹配小学二年级"
            },
            {
                "name": "G2缩写 - 正确",
                "title": "G2 فيديو كرتون الرياضيات",
                "expected_grade": "Grade 2",
                "expected_subject": "Mathematics",
                "should_match": True,
                "description": "G2数学卡通视频 - 应该识别为二年级"
            },
            {
                "name": "纯阿拉伯语 - 正确",
                "title": "جميع دروس منهاج الرياضيات الصف الثاني",
                "expected_grade": "Grade 2",
                "expected_subject": "Mathematics",
                "should_match": True,
                "description": "二年级数学完整课程 - 应该识别为匹配"
            }
        ]

        # 要测试的模型列表
        self.models_to_test = [
            # OpenAI 系列
            "gpt-5.2",
            "gpt-5-mini",
            "gpt-5.2-thinking-high",
            "gpt-4.1",

            # Gemini 系列
            "gemini-2.5-flash",
            "gemini-2.5-pro",

            # Claude 系列
            "claude-3-7-sonnet@20250219",

            # Ali 系列
            "qwen3-max",

            # TranAI 系列
            "tranai/deepseek-v3.1"
        ]

        self.results = []

    def test_grade_recognition(self, model: str, test_case: Dict) -> Dict:
        """测试年级识别能力"""

        prompt = f"""你是一个教育内容分析专家。请分析以下阿拉伯语标题，提取年级信息。

标题: {test_case['title']}

请回答以下问题：
1. 标题中的年级是什么？（用阿拉伯语或英语）
2. 这个年级对应中国学制的哪个年级？（例如：小学一年级、初中二年级、高中三年级）
3. 如果标题是"الصف الثاني"，它是二年级、十二年级还是初二？请说明理由。

请用JSON格式回答：
{{
    "detected_grade_arabic": "检测到的阿拉伯语年级",
    "detected_grade_english": "对应的英语年级",
    "chinese_equivalent": "对应中国学制",
    "confidence": 0.0-1.0,
    "reasoning": "判断理由"
}}
"""

        try:
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一个专业的多语言教育内容分析师，擅长阿拉伯语。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=500,
                timeout=60
            )
            elapsed_time = time.time() - start_time

            response_text = response.choices[0].message.content

            # 解析JSON
            import re
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                result['elapsed_time'] = elapsed_time
                result['raw_response'] = response_text
                return result
            else:
                return {
                    "error": "无法解析JSON",
                    "raw_response": response_text,
                    "elapsed_time": elapsed_time
                }

        except Exception as e:
            return {
                "error": str(e),
                "elapsed_time": time.time() - start_time
            }

    def test_scoring_accuracy(self, model: str, test_case: Dict) -> Dict:
        """测试评分准确性"""

        prompt = f"""请为以下教育资源评分（0-10分）：

【目标年级】小学二年级 (Grade 2)
【目标学科】数学 (Mathematics)

【资源标题】{test_case['title']}

评分标准：
- 年级完全匹配（小学二年级）：3分
- 学科完全匹配（数学）：3分
- 年级不符（如初中、高中）：0分

请返回JSON：
{{
    "score": 0.0-10.0,
    "grade_match": true/false,
    "subject_match": true/false,
    "reasoning": "评分理由"
}}
"""

        try:
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是教育内容评分专家，擅长阿拉伯语。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=300,
                timeout=60
            )
            elapsed_time = time.time() - start_time

            response_text = response.choices[0].message.content

            # 解析JSON
            import re
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                result['elapsed_time'] = elapsed_time

                # 判断评分是否正确
                expected_low_score = not test_case['should_match']
                actual_low_score = result.get('score', 10) < 6.0

                if expected_low_score:
                    result['correct'] = actual_low_score  # 应该低分，实际低分 = 正确
                else:
                    result['correct'] = not actual_low_score and result.get('grade_match', False)  # 应该高分，实际高分 = 正确

                result['raw_response'] = response_text
                return result
            else:
                return {
                    "error": "无法解析JSON",
                    "raw_response": response_text,
                    "elapsed_time": elapsed_time,
                    "correct": False
                }

        except Exception as e:
            return {
                "error": str(e),
                "elapsed_time": time.time() - start_time,
                "correct": False
            }

    def run_benchmark(self):
        """运行完整基准测试"""

        print("=" * 120)
        print("🧪 阿拉伯语理解能力对比测试")
        print("=" * 120)
        print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 API: {self.base_url}")
        print(f"📊 测试模型数: {len(self.models_to_test)}")
        print(f"📝 测试用例数: {len(self.test_cases)}")
        print("=" * 120)

        for model in self.models_to_test:
            print(f"\n{'=' * 120}")
            print(f"🤖 测试模型: {model}")
            print(f"{'=' * 120}")

            model_results = {
                "model": model,
                "tests": [],
                "total_correct": 0,
                "total_tests": 0,
                "avg_time": 0
            }

            total_time = 0

            for i, test_case in enumerate(self.test_cases, 1):
                print(f"\n  [{i}/{len(self.test_cases)}] 测试: {test_case['name']}")
                print(f"  标题: {test_case['title']}")
                print(f"  期望: {test_case['expected_grade']} - {'应该匹配' if test_case['should_match'] else '不应该匹配'}")

                # 测试1: 年级识别
                print(f"  📝 测试年级识别...")
                recognition_result = self.test_grade_recognition(model, test_case)

                # 测试2: 评分准确性
                print(f"  🎯 测试评分准确性...")
                scoring_result = self.test_scoring_accuracy(model, test_case)

                # 记录结果
                test_result = {
                    "test_case": test_case['name'],
                    "recognition": recognition_result,
                    "scoring": scoring_result
                }

                model_results['tests'].append(test_result)

                # 判断是否正确
                is_correct = (
                    scoring_result.get('correct', False) and
                    not scoring_result.get('error')
                )

                if is_correct:
                    model_results['total_correct'] += 1
                    print(f"  ✅ 通过 - 耗时: {scoring_result.get('elapsed_time', 0):.2f}s")
                else:
                    print(f"  ❌ 失败 - 原因: {scoring_result.get('error', '评分不正确')[:60]}")

                model_results['total_tests'] += 1
                total_time += scoring_result.get('elapsed_time', 0)

            # 计算统计
            model_results['avg_time'] = total_time / len(self.test_cases)
            model_results['accuracy'] = model_results['total_correct'] / model_results['total_tests'] if model_results['total_tests'] > 0 else 0

            print(f"\n  📊 {model} 统计:")
            print(f"     准确率: {model_results['accuracy']:.1%}")
            print(f"     正确数: {model_results['total_correct']}/{model_results['total_tests']}")
            print(f"     平均耗时: {model_results['avg_time']:.2f}s")

            self.results.append(model_results)

        # 生成总结报告
        self.generate_summary_report()

    def generate_summary_report(self):
        """生成总结报告"""

        print("\n\n" + "=" * 120)
        print("📊 测试总结报告")
        print("=" * 120)

        # 按准确率排序
        sorted_results = sorted(self.results, key=lambda x: x['accuracy'], reverse=True)

        print(f"\n{'模型':<35} {'准确率':<10} {'正确/总数':<12} {'平均耗时':<10} {'排名':<5}")
        print("-" * 120)

        for i, result in enumerate(sorted_results, 1):
            model = result['model']
            accuracy = result['accuracy']
            correct = result['total_correct']
            total = result['total_tests']
            avg_time = result['avg_time']

            print(f"{model:<35} {accuracy:>8.1%} {correct:>3}/{total:<8} {avg_time:>8.2f}s   #{i}")

        # 推荐最佳模型
        print("\n" + "=" * 120)
        print("💡 推荐")

        best_accuracy = sorted_results[0]
        fastest = min(self.results, key=lambda x: x['avg_time'])

        print(f"🏆 准确率最高: {best_accuracy['model']} ({best_accuracy['accuracy']:.1%})")
        print(f"⚡ 速度最快: {fastest['model']} ({fastest['avg_time']:.2f}s)")

        # 平衡性能和速度
        best_balance = None
        best_score = -1

        for result in self.results:
            # 综合评分 = 准确率 * 2 - (平均耗时 / 10)
            score = result['accuracy'] * 2 - (result['avg_time'] / 10)
            if score > best_score:
                best_score = score
                best_balance = result

        if best_balance:
            print(f"⭐ 性价比最高: {best_balance['model']} (准确率 {best_balance['accuracy']:.1%}, 耗时 {best_balance['avg_time']:.2f}s)")

        print("\n" + "=" * 120)
        print("❓ 建议")

        if best_accuracy['accuracy'] >= 0.8:
            print(f"✅ 找到高准确率模型 ({best_accuracy['model']})，知识库可能不需要")
        elif best_accuracy['accuracy'] >= 0.6:
            print(f"⚠️ 准确率中等 ({best_accuracy['model']})，知识库可以作为辅助")
        else:
            print(f"❌ 所有模型准确率都较低 (<60%)，知识库方案是必要的")

        # 保存详细报告
        self.save_detailed_report(sorted_results)

    def save_detailed_report(self, sorted_results):
        """保存详细报告到文件"""

        report = {
            "timestamp": datetime.now().isoformat(),
            "api_base_url": self.base_url,
            "summary": {
                "best_accuracy": {
                    "model": sorted_results[0]['model'],
                    "accuracy": sorted_results[0]['accuracy']
                },
                "fastest": min(self.results, key=lambda x: x['avg_time'])['model']
            },
            "detailed_results": sorted_results
        }

        output_file = "arabic_benchmark_report.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n📄 详细报告已保存到: {output_file}")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    阿拉伯语理解能力对比测试                                  ║
║                  Arabic Language Understanding Benchmark                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

🎯 测试目标：对比不同LLM模型对阿拉伯语教育内容的理解能力
📊 测试内容：年级识别、评分准确性、响应速度
🔧 使用API：公司内部 TranAI API
    """)

    benchmark = ArabicLanguageBenchmark()

    try:
        benchmark.run_benchmark()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
