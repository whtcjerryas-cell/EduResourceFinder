#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
印尼一年级数学教育资源评估脚本（使用MCP工具）

功能：
1. 读取Excel中的教育网站列表
2. 使用MCP web-reader工具获取网页内容
3. 使用Gemini 2.5 Pro进行AI分析评估
4. 将评估分数和评价写入Excel新列
"""

import os
import json
import time
import re
from typing import Dict, Any, List
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# API配置
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "sk_4c34c16af4f8bb4bc102f3d1afd6439127c4d95a2912af34efcbda0")
INTERNAL_API_BASE_URL = os.getenv("INTERNAL_API_BASE_URL", "https://hk-intra-paas.transsion.com/tranai-proxy/v1")

# 导入统一的代理工具（proxy_utils 模块导入时会自动禁用代理）
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.proxy_utils import disable_proxy  # 导入即自动禁用代理（见 proxy_utils.py:78）
from utils.json_parser import JSONParser
from utils.platform_detector import PlatformDetector

# 注意：无需手动调用 disable_proxy()，因为导入 core.proxy_utils 时已自动执行


class ResourceEvaluator:
    """教育资源评估器 - 使用Gemini 2.5 Pro"""

    def __init__(self):
        self.client = OpenAI(
            api_key=INTERNAL_API_KEY,
            base_url=INTERNAL_API_BASE_URL
        )
        self.model = "gemini-2.5-pro"

    def evaluate_by_info(self, name: str, url: str, page_info: str = "") -> Dict[str, Any]:
        """
        基于资源信息进行评估

        Args:
            name: 资源名称
            url: 资源网址
            page_info: 网页信息（可选）

        Returns:
            包含评估分数和评价的字典
        """
        print(f"\n🤖 AI评估: {name}")

        platform = PlatformDetector.identify_platform(url)
        is_playlist = 'playlist' in url
        is_kurikulum_merdeka = 'merdeka' in url.lower() or 'merdeka' in name.lower()
        is_youtube = 'youtube.com' in url

        # 构建评估提示词
        page_info_section = f"\n**网页信息**:\n{page_info[:1000]}\n" if page_info else ""

        prompt = f"""你是一位专业的教育内容评估专家，专门评估印尼小学一年级数学教育资源。

**资源基本信息**:
- 资源名称: {name}
- 资源网址: {url}
- 所属平台: {platform}
- URL特征: {'YouTube播放列表' if is_youtube and is_playlist else '课程页面'}
- 教学大纲: {'符合Kurikulum Merdeka（印尼最新独立课程）' if is_kurikulum_merdeka else '需要人工核实'}
{page_info_section}

---

**评估背景**:
这是为印尼小学一年级学生（6-7岁）设计的数学教育资源。内容应该包括基础数数、简单加减法、形状认知、测量基础等。

**平台背景**:
- Ruangguru: 印尼最大的在线教育平台，提供系统化课程
- YouTube: 全球最大视频平台，有大量免费教育资源

---

请从以下维度评估（0-10分）：
1. 资源丰富程度（内容数量、覆盖范围、配套资源）
2. 时效性（是否符合Kurikulum Merdeka、内容更新）
3. 教学方法（适合6-7岁儿童、趣味性、互动性）
4. 画面质量（画质、制作水准、视觉效果）
5. 整体推荐度（综合价值、性价比、是否值得采购）

请严格按照JSON格式返回：
```json
{{
    "score_richness": 8.5,
    "score_timeliness": 7.0,
    "score_teaching_method": 9.0,
    "score_visual_quality": 8.0,
    "overall_score": 8.1,
    "evaluation_text": "详细评估，包括资源特点、各维度理由、优点、不足、采购建议",
    "recommendation": "强烈推荐"
}}
```

推荐度: "强烈推荐", "推荐", "可以考虑", "不推荐"
- 详细说明评分理由
- 分析资源特色和优势
- 指出不足
- 给出采购建议
- 用中文撰写"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是专业的教育内容评估专家，熟悉印尼教育体系。严格按JSON格式返回结果。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2500,
                timeout=120
            )

            result_text = response.choices[0].message.content.strip()

            # 提取JSON
            json_text = JSONParser.extract_json_from_response(result_text)
            evaluation = json.loads(json_text)

            print(f"✅ 评分: {evaluation.get('overall_score', 'N/A')}/10 | {evaluation.get('recommendation', 'N/A')}")
            return evaluation

        except Exception as e:
            print(f"❌ 评估失败: {str(e)[:100]}")
            return self._create_error_evaluation(str(e))

    def _create_error_evaluation(self, error_msg: str) -> Dict[str, Any]:
        """创建错误评估结果"""
        return {
            "overall_score": 5.0,
            "score_richness": 5.0,
            "score_timeliness": 5.0,
            "score_teaching_method": 5.0,
            "score_visual_quality": 5.0,
            "evaluation_text": f"⚠️ 自动评估遇到技术问题: {error_msg}\n\n建议: 人工核实此资源的质量和内容。",
            "recommendation": "待人工评估"
        }


def process_excel(input_file: str, output_file: str):
    """处理Excel文件"""
    print("=" * 70)
    print("印尼一年级数学教育资源评估系统")
    print("基于 Gemini 2.5 Pro AI分析")
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

        # 基于URL信息进行评估（不抓取网页内容，避免被拦截）
        evaluation = evaluator.evaluate_by_info(name, url)

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
    print("📊 评估结果")
    print("=" * 70)
    for idx, (name, score, eval_text) in enumerate(df[['名称', '评估分数', '评估内容']].values, 1):
        match = re.search(r'【推荐意见】:\s*(\S+)', eval_text)
        rec = match.group(1) if match else 'N/A'
        print(f"{idx}. {name} - {score:.1f}/10 - {rec}")


if __name__ == "__main__":
    input_file = "印尼一年级数学.xlsx"
    output_file = "印尼一年级数学_评估结果.xlsx"
    process_excel(input_file, output_file)
    print("\n🎉 评估完成！")
