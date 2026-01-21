#!/usr/bin/env python3
"""
A/B测试主入口

运行LLM模型A/B测试，支持：
- 智能评分测试
- 搜索策略测试（TODO）
- 推荐理由测试（TODO）
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logger_utils import get_logger
from tests.ab_testing.runners.scoring_test_runner import ScoringTestRunner

logger = get_logger('run_ab_test')


def main():
    parser = argparse.ArgumentParser(
        description="运行LLM模型A/B测试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行智能评分测试（所有模型）
  python tests/ab_testing/run_ab_test.py --test-type scoring

  # 运行智能评分测试（指定模型）
  python tests/ab_testing/run_ab_test.py --test-type scoring --models gemini-2.5-pro gemini-2.5-flash

  # 运行智能评分测试（限制测试用例数）
  python tests/ab_testing/run_ab_test.py --test-type scoring --test-cases 10

  # 详细输出
  python tests/ab_testing/run_ab_test.py --test-type scoring --verbose
        """
    )

    parser.add_argument(
        "--test-type",
        choices=["scoring", "strategy", "recommendation", "all"],
        default="scoring",
        help="测试类型（默认: scoring）"
    )
    parser.add_argument(
        "--models",
        nargs="+",
        help="要测试的模型列表（默认测试所有配置的模型）"
    )
    parser.add_argument(
        "--test-cases",
        type=int,
        help="测试用例数量限制"
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).parent.parent / "reports" / "weekly_reports"),
        help="报告输出目录"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细输出"
    )

    args = parser.parse_args()

    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 测试配置
    test_configs = {
        "scoring": {
            "name": "智能评分测试",
            "models": args.models or [
                "gemini-3-pro-thinking-high",
                "gemini-3-pro-thinking-medium",
                "gpt-5.2-thinking-medium",
                "claude-3-7-sonnet",
                "gemini-2.5-pro",
                "gemini-2.5-flash",
            ],
            "test_cases_file": "test_cases_scoring.json",
            "runner": ScoringTestRunner,
        },
        "strategy": {
            "name": "搜索策略测试",
            "models": args.models or [
                "gemini-2.5-pro",
                "gemini-2.5-flash",
                "claude-3-7-sonnet",
                "gpt-4o",
                "grok-4-fast",
            ],
            "test_cases_file": "test_cases_strategy.json",
            "runner": None,  # TODO: 实现
        },
        "recommendation": {
            "name": "推荐理由测试",
            "models": args.models or [
                "gemini-2.5-pro",
                "claude-3-7-sonnet",
                "gpt-4o",
                "gemini-2.5-flash",
            ],
            "test_cases_file": "test_cases_recommendation.json",
            "runner": None,  # TODO: 实现
        },
    }

    # 运行测试
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if args.test_type in ["scoring", "all"]:
        print("\n" + "="*80)
        print("🧪 开始智能评分测试")
        print("="*80)

        config = test_configs["scoring"]

        if config["runner"] is None:
            print(f"⚠️ {config['name']}尚未实现，跳过")
        else:
            print(f"\n📋 测试配置:")
            print(f"  - 模型数量: {len(config['models'])}")
            print(f"  - 模型列表: {', '.join(config['models'])}")
            print(f"  - 测试用例数: {args.test_cases or '全部'}")
            print(f"  - 详细输出: {'是' if args.verbose else '否'}")

            runner = config["runner"](
                models=config["models"],
                test_cases_limit=args.test_cases,
                verbose=args.verbose
            )

            results = runner.run()

            # 保存结果
            results_path = output_dir / f"scoring_test_{timestamp}.json"
            runner.save_results(results_path)

            # 生成报告
            report_path = output_dir / f"scoring_report_{timestamp}.md"
            runner.generate_report(report_path)

            print(f"\n✅ {config['name']}完成！")
            print(f"  - 结果: {results_path}")
            print(f"  - 报告: {report_path}")

    if args.test_type in ["strategy", "all"]:
        print("\n" + "="*80)
        print("🧪 开始搜索策略测试")
        print("="*80)

        config = test_configs["strategy"]

        if config["runner"] is None:
            print(f"⚠️ {config['name']}尚未实现，跳过")
        else:
            # TODO: 实现搜索策略测试
            pass

    if args.test_type in ["recommendation", "all"]:
        print("\n" + "="*80)
        print("🧪 开始推荐理由测试")
        print("="*80)

        config = test_configs["recommendation"]

        if config["runner"] is None:
            print(f"⚠️ {config['name']}尚未实现，跳过")
        else:
            # TODO: 实现推荐理由测试
            pass

    print("\n" + "="*80)
    print("✅ 所有测试完成")
    print("="*80)


if __name__ == "__main__":
    main()
