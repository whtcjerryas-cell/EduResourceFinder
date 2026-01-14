#!/usr/bin/env python3
"""
配置诊断工具（独立工具，不修改现有代码）
用于诊断现有配置系统的问题
"""

import os
import json
import sys
from typing import Dict, List, Any
from datetime import datetime

class ConfigDiagnostic:
    """配置诊断器"""

    def __init__(self, config_file: str = "data/config/countries_config.json"):
        self.config_file = config_file
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": [],
            "issues": [],
            "recommendations": []
        }

    def run_all_checks(self) -> Dict[str, Any]:
        """运行所有诊断检查"""
        print("[🔍 诊断] 开始配置系统诊断...")

        # 检查 1: 文件存在性
        self._check_file_exists()

        # 检查 2: JSON 格式
        self._check_json_format()

        # 检查 3: 配置结构
        self._check_config_structure()

        # 检查 4: 国家配置完整性
        self._check_country_configs()

        # 检查 5: 年级-学科映射
        self._check_grade_subject_mappings()

        # 生成报告
        return self._generate_report()

    def _check_file_exists(self):
        """检查配置文件是否存在"""
        check_name = "文件存在性检查"
        print(f"  [*] {check_name}")

        exists = os.path.exists(self.config_file)
        if exists:
            file_size = os.path.getsize(self.config_file)
            self.results["checks"].append({
                "name": check_name,
                "status": "✅ 通过",
                "details": f"文件存在，大小: {file_size} 字节"
            })
        else:
            self.results["checks"].append({
                "name": check_name,
                "status": "❌ 失败",
                "details": "配置文件不存在"
            })
            self.results["issues"].append({
                "severity": "critical",
                "category": "file",
                "message": "配置文件不存在",
                "solution": "创建默认配置文件或从备份恢复"
            })

    def _check_json_format(self):
        """检查 JSON 格式是否正确"""
        check_name = "JSON 格式检查"
        print(f"  [*] {check_name}")

        if not os.path.exists(self.config_file):
            self.results["checks"].append({
                "name": check_name,
                "status": "⏭️ 跳过",
                "details": "文件不存在"
            })
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            country_count = len(config.keys())
            self.results["checks"].append({
                "name": check_name,
                "status": "✅ 通过",
                "details": f"JSON 格式正确，包含 {country_count} 个国家"
            })
        except json.JSONDecodeError as e:
            self.results["checks"].append({
                "name": check_name,
                "status": "❌ 失败",
                "details": f"JSON 格式错误: {str(e)}"
            })
            self.results["issues"].append({
                "severity": "critical",
                "category": "format",
                "message": f"JSON 格式错误: {str(e)}",
                "solution": "修复 JSON 语法错误或从备份恢复"
            })

    def _check_config_structure(self):
        """检查配置结构是否完整"""
        check_name = "配置结构检查"
        print(f"  [*] {check_name}")

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            required_fields = [
                "country_code",
                "country_name",
                "language_code",
                "grades",
                "subjects"
            ]

            issues = []
            for country_code, country_data in config.items():
                missing_fields = [f for f in required_fields if f not in country_data]
                if missing_fields:
                    issues.append(f"{country_code}: 缺少字段 {missing_fields}")

            if issues:
                self.results["checks"].append({
                    "name": check_name,
                    "status": "⚠️ 警告",
                    "details": f"发现 {len(issues)} 个结构问题"
                })
                self.results["issues"].extend([
                    {
                        "severity": "warning",
                        "category": "structure",
                        "message": issue,
                        "solution": "补充缺失的字段"
                    }
                    for issue in issues
                ])
            else:
                self.results["checks"].append({
                    "name": check_name,
                    "status": "✅ 通过",
                    "details": "所有国家配置结构完整"
                })
        except Exception as e:
            self.results["checks"].append({
                "name": check_name,
                "status": "❌ 失败",
                "details": f"检查失败: {str(e)}"
            })

    def _check_country_configs(self):
        """检查各个国家配置的完整性"""
        check_name = "国家配置完整性检查"
        print(f"  [*] {check_name}")

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            empty_grades = []
            empty_subjects = []

            for country_code, country_data in config.items():
                if not country_data.get("grades"):
                    empty_grades.append(country_code)
                if not country_data.get("subjects"):
                    empty_subjects.append(country_code)

            if empty_grades or empty_subjects:
                issues = []
                if empty_grades:
                    issues.append(f"年级为空: {', '.join(empty_grades)}")
                if empty_subjects:
                    issues.append(f"学科为空: {', '.join(empty_subjects)}")

                self.results["checks"].append({
                    "name": check_name,
                    "status": "⚠️ 警告",
                    "details": f"发现问题: {', '.join(issues)}"
                })
            else:
                self.results["checks"].append({
                    "name": check_name,
                    "status": "✅ 通过",
                    "details": f"所有 {len(config)} 个国家配置完整"
                })
        except Exception as e:
            self.results["checks"].append({
                "name": check_name,
                "status": "❌ 失败",
                "details": f"检查失败: {str(e)}"
            })

    def _check_grade_subject_mappings(self):
        """检查年级-学科映射"""
        check_name = "年级-学科映射检查"
        print(f"  [*] {check_name}")

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            total_mappings = 0
            no_mapping_countries = []

            for country_code, country_data in config.items():
                mappings = country_data.get("grade_subject_mappings", {})
                if mappings:
                    total_mappings += len(mappings)
                else:
                    no_mapping_countries.append(country_code)

            self.results["checks"].append({
                "name": check_name,
                "status": "✅ 通过",
                "details": f"总共 {total_mappings} 个映射，{len(no_mapping_countries)} 个国家无映射"
            })

            if no_mapping_countries:
                self.results["recommendations"].append(
                    f"建议为以下国家添加年级-学科映射: {', '.join(no_mapping_countries)}"
                )
        except Exception as e:
            self.results["checks"].append({
                "name": check_name,
                "status": "❌ 失败",
                "details": f"检查失败: {str(e)}"
            })

    def _generate_report(self) -> Dict[str, Any]:
        """生成诊断报告"""
        print("\n[📊 诊断报告]")

        # 统计
        total_checks = len(self.results["checks"])
        passed = sum(1 for c in self.results["checks"] if "✅" in c["status"])
        warnings = sum(1 for c in self.results["checks"] if "⚠️" in c["status"])
        failed = sum(1 for c in self.results["checks"] if "❌" in c["status"])

        print(f"  总检查数: {total_checks}")
        print(f"  ✅ 通过: {passed}")
        print(f"  ⚠️ 警告: {warnings}")
        print(f"  ❌ 失败: {failed}")

        # 问题
        if self.results["issues"]:
            print(f"\n[⚠️  发现 {len(self.results['issues'])} 个问题]")
            for i, issue in enumerate(self.results["issues"], 1):
                severity_icon = {
                    "critical": "🔴",
                    "warning": "🟡",
                    "info": "🔵"
                }.get(issue["severity"], "⚪")

                print(f"  {i}. {severity_icon} [{issue['severity'].upper()}] {issue['message']}")
                print(f"     解决方案: {issue['solution']}")

        # 建议
        if self.results["recommendations"]:
            print(f"\n[💡 建议]")
            for i, rec in enumerate(self.results["recommendations"], 1):
                print(f"  {i}. {rec}")

        return self.results


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Indonesia 配置诊断工具")
    parser.add_argument(
        "--config",
        default="data/config/countries_config.json",
        help="配置文件路径"
    )
    parser.add_argument(
        "--output",
        help="输出诊断报告到文件"
    )

    args = parser.parse_args()

    # 运行诊断
    diagnostic = ConfigDiagnostic(args.config)
    report = diagnostic.run_all_checks()

    # 输出报告
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n[✅ 报告已保存] {args.output}")

    # 返回退出码
    critical_issues = [i for i in report["issues"] if i["severity"] == "critical"]
    sys.exit(1 if critical_issues else 0)


if __name__ == "__main__":
    main()
