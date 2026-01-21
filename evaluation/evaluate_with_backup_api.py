#!/usr/bin/env python3
from utils.json_parser import JSONParser
from utils.platform_detector import PlatformDetector
# -*- coding: utf-8 -*-
"""
印尼一年级数学教育资源评估脚本（使用AI Builders API）

功能：
1. 读取Excel中的教育网站列表
2. 使用AI Builders API + DeepSeek进行AI分析评估
3. 将评估分数和评价写入Excel新列
"""

import os
import json
import time
import re
from typing import Dict, Any
import requests
import pandas as pd
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# AI Builders API配置（备用方案）
AI_BUILDER_TOKEN = os.getenv("AI_BUILDER_TOKEN", "sk_6a24cd2c_9032fc7dbd6cebc0525ee452b69ff858a194")
AI_BUILDERS_BASE_URL = "https://space.ai-builders.com/backend/v1"


class ResourceEvaluator:
    """教育资源评估器 - 使用AI Builders DeepSeek模型"""

    def __init__(self):
        self.api_token = AI_BUILDER_TOKEN
        self.base_url = AI_BUILDERS_BASE_URL
        self.model = "deepseek"  # AI Builders的DeepSeek模型

    def evaluate(self, name: str, url: str) -> Dict[str, Any]:
        """
        基于资源信息进行评估

        Args:
            name: 资源名称
            url: 资源网址

        Returns:
            包含评估分数和评价的字典
        """
        print(f"\n🤖 AI评估: {name}")

        platform = PlatformDetector.identify_platform(url)
        is_playlist = 'playlist' in url
        is_kurikulum_merdeka = 'merdeka' in url.lower() or 'merdeka' in name.lower()

        prompt = f"""你是一位专业的教育内容评估专家，专门评估印尼小学一年级数学教育资源。

**资源信息**:
- 名称: {name}
- 网址: {url}
- 平台: {platform}
- 类型: {'YouTube播放列表' if is_playlist else '课程页面'}
- 大纲: {'Kurikulum Merdeka' if is_kurikulum_merdeka else '未知'}

请评估（0-10分）：
1. 资源丰富程度
2. 时效性（是否符合Kurikulum Merdeka）
3. 教学方法（适合6-7岁儿童）
4. 画面质量
5. 整体推荐度

严格按JSON返回：
```json
{{
    "score_richness": 8.0,
    "score_timeliness": 7.0,
    "score_teaching_method": 8.5,
    "score_visual_quality": 7.5,
    "overall_score": 7.75,
    "evaluation_text": "详细评估说明",
    "recommendation": "推荐"
}}
```

推荐度: "强烈推荐", "推荐", "可以考虑", "不推荐"

用中文撰写评估。"""

        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }

            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "你是专业的教育内容评估专家，熟悉印尼教育体系。严格按JSON格式返回。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 2500
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                result_text = result['choices'][0]['message']['content'].strip()

                # 提取JSON
                json_text = JSONParser.extract_json_from_response(result_text)
                evaluation = json.loads(json_text)

                print(f"✅ 评分: {evaluation.get('overall_score', 'N/A')}/10 | {evaluation.get('recommendation', 'N/A')}")
                return evaluation
            else:
                print(f"❌ API错误: {response.status_code}")
                return self._create_fallback_evaluation(name, url, platform)

        except Exception as e:
            print(f"❌ 评估失败: {str(e)[:100]}")
            return self._create_fallback_evaluation(name, url, platform)

    def _create_fallback_evaluation(self, name: str, url: str, platform: str) -> Dict[str, Any]:
        """创建后备评估结果"""
        is_kurikulum_merdeka = 'merdeka' in url.lower() or 'merdeka' in name.lower()
        is_youtube = 'youtube.com' in url

        # 基于规则的简单评分
        base_score = 7.0

        if platform == 'Ruangguru':
            base_score += 1.0  # Ruangguru是专业教育平台
        if is_kurikulum_merdeka:
            base_score += 0.5  # 符合最新大纲
        if is_youtube:
            base_score += 0.5  # YouTube免费且易于访问

        base_score = min(base_score, 9.0)

        return {
            "overall_score": base_score,
            "score_richness": base_score - 0.5,
            "score_timeliness": base_score - 0.2 if is_kurikulum_merdeka else base_score - 1.0,
            "score_teaching_method": base_score,
            "score_visual_quality": base_score - 0.3,
            "evaluation_text": f"""基于资源特征的初步评估：

【资源分析】
- 平台: {platform}
- 类型: {'YouTube播放列表（免费视频资源）' if is_youtube else '在线课程平台'}
- 教学大纲: {'符合Kurikulum Merdeka（2022年印尼最新教育大纲）' if is_kurikulum_merdeka else '需要人工核实是否符合最新大纲'}

【评估说明】
{f"- Ruangguru是印尼领先的在线教育平台，课程系统性强" if platform == "Ruangguru" else "- YouTube提供免费视频资源，访问便利"}
{f"- 明确标注符合Kurikulum Merdeka，时效性较好" if is_kurikulum_merdeka else "- 建议人工核实是否符合Kurikulum Merdeka"}
- {'视频播放列表形式，适合学生自主学习' if is_youtube else '- 结构化课程，可能有配套练习'}

【建议】
此评估基于URL和资源名称分析。建议：
1. 人工访问资源查看实际内容质量
2. 核实是否完全符合印尼一年级教学大纲
3. 检查视频画质和制作水准
4. 评估教学方法和儿童友好性""",
            "recommendation": "可以考虑" if base_score >= 7.5 else "待人工评估"
        }


def process_excel(input_file: str, output_file: str):
    """处理Excel文件"""
    print("=" * 70)
    print("印尼一年级数学教育资源评估系统")
    print("基于 AI Builders DeepSeek模型")
    print("=" * 70)

    df = pd.read_excel(input_file)
    print(f"\n✅ 读取 {len(df)} 条记录")

    evaluator = ResourceEvaluator()
    scores = []
    evaluations = []

    for idx, row in df.iterrows():
        name = row.get('名称', '')
        url = row.get('网址', '')

        print(f"\n{'=' * 70}")
        print(f"[{idx + 1}/{len(df)}] {name}")
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

        if idx < len(df) - 1:
            time.sleep(2)

    df['评估分数'] = scores
    df['评估内容'] = evaluations
    df = df.sort_values('评估分数', ascending=False)

    df.to_excel(output_file, index=False, engine='openpyxl')
    print(f"\n💾 已保存到: {output_file}")

    print("\n" + "=" * 70)
    print("📊 评估结果排名")
    print("=" * 70)
    for idx, (name, score, eval_text) in enumerate(df[['名称', '评估分数', '评估内容']].values, 1):
        match = re.search(r'【推荐意见】:\s*(\S+)', eval_text)
        rec = match.group(1) if match else 'N/A'
        print(f"{idx}. {name}")
        print(f"   评分: {score:.1f}/10 | 推荐: {rec}")


if __name__ == "__main__":
    input_file = "印尼一年级数学.xlsx"
    output_file = "印尼一年级数学_评估结果.xlsx"
    process_excel(input_file, output_file)
    print("\n🎉 评估完成！")
