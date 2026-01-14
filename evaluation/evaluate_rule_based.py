#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
印尼一年级数学教育资源评估脚本（基于规则 + AI分析）

功能：
1. 读取Excel中的教育网站列表
2. 基于规则进行初步评估
3. 生成详细的评估报告
4. 将评估分数和评价写入Excel新列
"""

import os
import re
import pandas as pd
from typing import Dict, Any, Tuple
from urllib.parse import urlparse


class RuleBasedEvaluator:
    """基于规则的教育资源评估器"""

    def __init__(self):
        # 平台权重配置
        self.platform_scores = {
            'youtube': 0.5,  # YouTube免费但质量参差不齐
            'ruangguru': 1.5,  # Ruangguru专业教育平台
        }

        # 特征权重配置
        self.feature_weights = {
            'kurikulum_merdeka': 1.0,  # 符合最新大纲
            'playlist': 0.3,  # 播放列表
            'sd_kelas_1': 0.5,  # 明确标注一年级
            'topik': 0.3,  # 按主题组织
        }

    def identify_platform(self, url: str) -> str:
        """识别教育平台类型"""
        if 'youtube.com' in url or 'youtu.be' in url:
            return 'YouTube（全球最大视频平台，免费）'
        elif 'ruangguru.com' in url:
            return 'Ruangguru（印尼领先在线教育平台）'
        elif 'dafalulu.ruangguru.com' in url:
            return 'Ruangguru Dafalulu（Ruangguru子品牌）'
        else:
            return '其他平台'

    def extract_features(self, name: str, url: str) -> Dict[str, bool]:
        """提取资源特征"""
        return {
            'is_kurikulum_merdeka': 'merdeka' in url.lower() or 'merdeka' in name.lower(),
            'is_playlist': 'playlist' in url,
            'is_sd_kelas_1': 'sd kelas 1' in name.lower() or 'sd-kelas-1' in url.lower(),
            'is_topik': 'topik' in url.lower() or 'topik' in name.lower(),
            'is_dafalulu': 'dafalulu' in url.lower(),
            'is_youtube': 'youtube.com' in url,
            'is_ruangguru': 'ruangguru.com' in url,
        }

    def calculate_scores(self, name: str, url: str, features: Dict[str, bool]) -> Dict[str, float]:
        """计算各维度分数"""
        base_score = 6.0  # 基础分

        # 资源丰富程度评分
        richness = base_score
        if features['is_playlist']:
            richness += 1.5  # 播放列表通常包含多个视频
        if features['is_ruangguru']:
            richness += 1.0  # Ruangguru有系统化课程
        if features['is_dafalulu']:
            richness += 0.5
        richness = min(richness, 9.5)

        # 时效性评分
        timeliness = base_score
        if features['is_kurikulum_merdeka']:
            timeliness += 2.0  # Kurikulum Merdeka是2022年最新大纲
        elif features['is_youtube']:
            timeliness += 0.5  # YouTube内容更新较频繁
        timeliness = min(timeliness, 9.5)

        # 教学方法评分
        teaching = base_score + 1.0
        if features['is_topik']:
            teaching += 0.5  # 按主题组织有利于学习
        if features['is_sd_kelas_1']:
            teaching += 0.5  # 明确目标年级
        teaching = min(teaching, 9.0)

        # 画面质量评分
        visual = base_score + 0.5
        if features['is_ruangguru']:
            visual += 1.0  # 专业平台制作质量较高
        if features['is_youtube']:
            visual += 0.3  # YouTube画质普遍较好
        visual = min(visual, 8.5)

        # 整体推荐度（加权平均）
        weights = {
            'richness': 0.25,
            'timeliness': 0.25,
            'teaching': 0.30,
            'visual': 0.20,
        }

        overall = (
            richness * weights['richness'] +
            timeliness * weights['timeliness'] +
            teaching * weights['teaching'] +
            visual * weights['visual']
        )

        # 额外加分
        if features['is_kurikulum_merdeka'] and features['is_ruangguru']:
            overall += 0.5  # 专业平台 + 最新大纲
        overall = min(overall, 9.5)

        return {
            'richness': round(richness, 1),
            'timeliness': round(timeliness, 1),
            'teaching': round(teaching, 1),
            'visual': round(visual, 1),
            'overall': round(overall, 1),
        }

    def get_recommendation(self, overall_score: float, features: Dict[str, bool]) -> str:
        """根据分数和特征给出推荐意见"""
        if overall_score >= 8.5:
            return "强烈推荐"
        elif overall_score >= 7.5:
            return "推荐"
        elif overall_score >= 6.5:
            return "可以考虑"
        else:
            return "不推荐"

    def generate_evaluation_text(self, name: str, url: str, platform: str,
                                 features: Dict[str, bool], scores: Dict[str, float]) -> str:
        """生成详细评估文本"""
        lines = []

        # 资源概述
        lines.append("**资源概述**")
        lines.append(f"- 资源名称: {name}")
        lines.append(f"- 所属平台: {platform}")
        lines.append(f"- 资源类型: {'YouTube播放列表' if features['is_playlist'] else '在线课程页面'}")
        lines.append(f"- 教学大纲: {'符合Kurikulum Merdeka（2022年印尼最新教育大纲）' if features['is_kurikulum_merdeka'] else '需要人工核实是否符合最新大纲'}")

        # 平台分析
        lines.append("\n**平台分析**")
        if features['is_youtube']:
            lines.append("- YouTube平台优势: 完全免费、随时随地访问、大量优质教育资源")
            lines.append("- YouTube平台劣势: 内容质量参差不齐、需要人工筛选、广告干扰")
        if features['is_ruangguru']:
            lines.append("- Ruangguru平台优势: 印尼领先的在线教育平台、系统化课程设计、专业教师团队")
            lines.append("- Ruangguru平台劣势: 可能需要付费订阅、需要网络连接")

        # 维度分析
        lines.append("\n**各维度评分理由**")

        lines.append(f"\n1. 资源丰富程度 ({scores['richness']}/10)")
        if features['is_playlist']:
            lines.append("   - 播放列表形式，包含多个视频课程")
        if features['is_ruangguru']:
            lines.append("   - 专业教育平台，课程体系完整")
        lines.append("   - 预期覆盖基础数数、加减法、形状认知等一年级核心内容")

        lines.append(f"\n2. 时效性 ({scores['timeliness']}/10)")
        if features['is_kurikulum_merdeka']:
            lines.append("   - 明确符合Kurikulum Merdeka，时效性优秀")
            lines.append("   - Kurikulum Merdeka是印尼2022年实施的最新教育大纲")
        else:
            lines.append("   - 未明确标注是否符合最新大纲，建议人工核实")
            lines.append("   - 需要确认内容是否符合Kurikulum Merdeka要求")

        lines.append(f"\n3. 教学方法 ({scores['teaching']}/10)")
        lines.append("   - 针对6-7岁儿童设计的数学课程")
        if features['is_topik']:
            lines.append("   - 按主题组织教学内容，便于系统学习")
        lines.append("   - 预期采用直观教学、动画演示等适合低龄儿童的方法")

        lines.append(f"\n4. 画面质量 ({scores['visual']}/10)")
        if features['is_youtube']:
            lines.append("   - YouTube平台视频质量普遍较高")
        if features['is_ruangguru']:
            lines.append("   - 专业平台制作，画质和制作水准有保障")
        lines.append("   - 建议人工核实具体视频的清晰度和制作质量")

        # 优点
        lines.append("\n**主要优点**")
        if features['is_kurikulum_merdeka']:
            lines.append("- 符合印尼最新教育大纲Kurikulum Merdeka")
        if features['is_youtube']:
            lines.append("- 完全免费，无需付费订阅")
            lines.append("- 可以随时随地访问，灵活性好")
        if features['is_ruangguru']:
            lines.append("- 专业教育平台，教学质量有保障")
        if features['is_playlist']:
            lines.append("- 内容体系化，便于循序渐进学习")

        # 不足
        lines.append("\n**潜在不足**")
        if features['is_youtube']:
            lines.append("- 可能包含广告，影响学习体验")
            lines.append("- 内容质量可能参差不齐")
        if not features['is_kurikulum_merdeka']:
            lines.append("- 未明确是否符合最新教学大纲")
        lines.append("- 需要人工核实教学方法和儿童友好性")

        # 采购建议
        lines.append("\n**采购/使用建议**")
        recommendation = self.get_recommendation(scores['overall'], features)
        if recommendation == "强烈推荐":
            lines.append("- 该资源综合表现优秀，强烈推荐采购或使用")
            lines.append("- 可作为主要教学资源使用")
        elif recommendation == "推荐":
            lines.append("- 该资源整体表现良好，推荐使用")
            lines.append("- 可作为辅助教学资源")
        elif recommendation == "可以考虑":
            lines.append("- 该资源基本符合要求，可以考虑使用")
            lines.append("- 建议与其他资源配合使用")
        else:
            lines.append("- 该资源存在明显不足，不推荐使用")

        lines.append("- 建议先试用少量内容，确认质量后再全面采用")
        lines.append("- 建议定期更新资源，确保内容时效性")

        # 注意事项
        lines.append("\n**注意事项**")
        lines.append("- 本评估基于URL和资源名称分析，未进行深度内容审查")
        lines.append("- 建议人工访问资源，核实实际内容质量")
        lines.append("- 重点关注视频画质、讲解清晰度、教学方法儿童友好性")
        lines.append("- 确认内容完全覆盖印尼一年级数学教学大纲要求")

        return "\n".join(lines)

    def evaluate(self, name: str, url: str) -> Dict[str, Any]:
        """完整评估流程"""
        print(f"\n🔍 评估: {name}")

        platform = self.identify_platform(url)
        features = self.extract_features(name, url)
        scores = self.calculate_scores(name, url, features)
        recommendation = self.get_recommendation(scores['overall'], features)
        evaluation_text = self.generate_evaluation_text(name, url, platform, features, scores)

        print(f"✅ 评分: {scores['overall']}/10 | {recommendation}")

        return {
            "score_richness": scores['richness'],
            "score_timeliness": scores['timeliness'],
            "score_teaching_method": scores['teaching'],
            "score_visual_quality": scores['visual'],
            "overall_score": scores['overall'],
            "evaluation_text": evaluation_text,
            "recommendation": recommendation,
        }


def process_excel(input_file: str, output_file: str):
    """处理Excel文件"""
    print("=" * 70)
    print("印尼一年级数学教育资源评估系统")
    print("基于规则的专业评估")
    print("=" * 70)

    df = pd.read_excel(input_file)
    print(f"\n✅ 读取 {len(df)} 条记录")

    evaluator = RuleBasedEvaluator()
    scores = []
    evaluations = []

    for idx, row in df.iterrows():
        name = row.get('名称', '')
        url = row.get('网址', '')

        print(f"\n{'=' * 70}")
        print(f"[{idx + 1}/{len(df)}] {name}")
        print(f"网址: {url}")
        print(f"{'=' * 70}")

        evaluation = evaluator.evaluate(name, url)
        overall_score = evaluation.get('overall_score', 0)

        # 构建评估文本
        eval_text_parts = [
            f"【整体评分】: {overall_score:.1f}/10",
            f"【推荐意见】: {evaluation.get('recommendation', 'N/A')}",
        ]

        if 'score_richness' in evaluation:
            eval_text_parts.extend([
                f"\n【分项评分】",
                f"• 资源丰富程度: {evaluation['score_richness']:.1f}/10",
                f"• 时效性: {evaluation['score_timeliness']:.1f}/10",
                f"• 教学方法: {evaluation['score_teaching_method']:.1f}/10",
                f"• 画面质量: {evaluation['score_visual_quality']:.1f}/10",
            ])

        eval_text_parts.extend([
            f"\n【详细评估】",
            evaluation.get('evaluation_text', '')
        ])

        final_eval_text = "\n".join(eval_text_parts)
        scores.append(overall_score)
        evaluations.append(final_eval_text)

    df['评估分数'] = scores
    df['评估内容'] = evaluations
    df = df.sort_values('评估分数', ascending=False)

    df.to_excel(output_file, index=False, engine='openpyxl')
    print(f"\n💾 已保存到: {output_file}")

    # 打印统计信息
    print("\n" + "=" * 70)
    print("📊 评估统计")
    print("=" * 70)
    print(f"总评估数: {len(df)}")
    print(f"平均分数: {df['评估分数'].mean():.2f}/10")
    print(f"最高分数: {df['评估分数'].max():.1f}/10")
    print(f"最低分数: {df['评估分数'].min():.1f}/10")

    print("\n【推荐意见分布】")
    from collections import Counter
    recommendations = []
    for eval_text in df['评估内容']:
        match = re.search(r'【推荐意见】:\s*(\S+)', eval_text)
        if match:
            recommendations.append(match.group(1))
    for rec, count in Counter(recommendations).most_common():
        print(f"  {rec}: {count}个")

    print("\n【资源排名（按分数排序）】")
    for idx, (name, score, eval_text) in enumerate(df[['名称', '评估分数', '评估内容']].values, 1):
        match = re.search(r'【推荐意见】:\s*(\S+)', eval_text)
        rec = match.group(1) if match else 'N/A'
        print(f"  {idx}. {name}")
        print(f"     评分: {score:.1f}/10 | 推荐: {rec}")


if __name__ == "__main__":
    input_file = "印尼一年级数学.xlsx"
    output_file = "印尼一年级数学_评估结果.xlsx"
    process_excel(input_file, output_file)
    print("\n" + "=" * 70)
    print("🎉 评估完成！")
    print(f"📊 结果已保存到: {output_file}")
    print("=" * 70)
