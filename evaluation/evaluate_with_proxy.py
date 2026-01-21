#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
印尼一年级数学教育资源评估脚本（使用公司内部API + 代理）

功能：
1. 读取Excel中的教育网站列表
2. 使用代理访问公司内部Gemini 2.5 Pro进行AI分析评估
3. 将评估分数和评价写入Excel新列
"""

import os
import json
import time
import re
from typing import Dict, Any
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
import httpx

# 加载环境变量
load_dotenv()

# API配置
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "sk_4c34c16af4f8bb4bc102f3d1afd6439127c4d95a2912af34efcbda0")
INTERNAL_API_BASE_URL = os.getenv("INTERNAL_API_BASE_URL", "https://hk-intra-paas.transsion.com/tranai-proxy/v1")

# 代理配置
PROXY_URL = "http://127.0.0.1:7897"

# 导入JSON解析工具
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.json_parser import JSONParser
from utils.platform_detector import PlatformDetector


def setup_environment():
    """配置环境变量和代理"""
    # 设置代理环境变量
    os.environ["HTTP_PROXY"] = PROXY_URL
    os.environ["HTTPS_PROXY"] = PROXY_URL
    print(f"✅ 已设置代理: {PROXY_URL}")


class ResourceEvaluator:
    """教育资源评估器 - 使用公司内部 Gemini 2.5 Pro"""

    def __init__(self):
        # 使用 httpx 作为 HTTP 客户端，支持代理
        self.client = OpenAI(
            api_key=INTERNAL_API_KEY,
            base_url=INTERNAL_API_BASE_URL,
            http_client=httpx.Client(
                proxy=PROXY_URL,
                timeout=120.0,
                verify=False  # 如果有SSL证书问题可以禁用验证
            )
        )
        self.model = "gemini-2.5-pro"

    def evaluate(self, name: str, url: str) -> Dict[str, Any]:
        """
        使用 Gemini 2.5 Pro 进行评估

        Args:
            name: 资源名称
            url: 资源网址

        Returns:
            包含评估分数和评价的字典
        """
        print(f"\n🤖 Gemini 2.5 Pro 评估: {name}")

        platform = PlatformDetector.identify_platform(url)
        is_playlist = 'playlist' in url
        is_kurikulum_merdeka = 'merdeka' in url.lower() or 'merdeka' in name.lower()

        prompt = f"""你是一位专业的教育内容评估专家，专门评估印尼小学一年级数学教育资源。

**资源基本信息**:
- 资源名称: {name}
- 资源网址: {url}
- 所属平台: {platform}
- URL特征: {'YouTube播放列表' if is_playlist else '课程页面'}
- 教学大纲: {'符合Kurikulum Merdeka（印尼最新独立课程）' if is_kurikulum_merdeka else '需要人工核实'}

---

**评估背景**:
这是为印尼小学一年级学生（6-7岁）设计的数学教育资源。内容应该包括基础数数、简单加减法、形状认知、测量基础、数据收集基础等。

**平台背景**:
- Ruangguru: 印尼最大的在线教育平台，提供系统化课程，专业教师团队
- YouTube: 全球最大视频平台，有大量免费教育资源，访问便利

---

请从以下维度进行专业评估（每个维度0-10分）：

**1. 资源丰富程度 (0-10分)**
   - 内容数量和覆盖广度
   - 主题完整性
   - 配套资源（练习题、讲义等）
   - 更新频率

**2. 时效性 (0-10分)**
   - 是否符合Kurikulum Merdeka（印尼2022年实施的最新教育大纲）
   - 内容的更新维护状态
   - 教育理念的先进性

**3. 教学方法 (0-10分)**
   - 针对6-7岁儿童的教学设计
   - 趣味性和互动性
   - 教学节奏和讲解清晰度
   - 是否符合儿童认知发展规律
   - 视觉辅助和动画运用

**4. 画面质量 (0-10分)**
   - 视频画质和制作水准
   - 界面设计和用户体验
   - 动画和视觉效果
   - 音频质量

**5. 整体推荐度 (0-10分)**
   - 综合质量和价值
   - 性价比（如果需要付费）
   - 适用性和实用性
   - 是否值得采购推荐

---

请严格按照以下JSON格式返回评估结果，不要包含任何其他文字：
```json
{{
    "score_richness": 8.5,
    "score_timeliness": 7.0,
    "score_teaching_method": 9.0,
    "score_visual_quality": 8.0,
    "overall_score": 8.1,
    "evaluation_text": "详细评估内容，包括：\\n1. 资源特点分析\\n2. 各维度评分理由\\n3. 优点\\n4. 不足之处\\n5. 采购建议...",
    "recommendation": "强烈推荐"
}}
```

推荐度可选值: "强烈推荐", "推荐", "可以考虑", "不推荐"

**评估文本要求**:
- 详细说明每个维度的评分理由
- 分析该资源的特色和优势
- 指出可能存在的不足
- 给出具体的采购或使用建议
- 特别关注是否适合印尼一年级学生的认知水平
- 用中文撰写，专业且具体"""

        try:
            print(f"   正在通过代理调用 {self.model} 模型...")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位专业的教育内容评估专家，拥有10年以上的K12数学教育评估经验，熟悉印尼教育体系。请严格按照JSON格式返回评估结果，不要包含任何其他文字。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=3000,
                timeout=120
            )

            result_text = response.choices[0].message.content.strip()

            # 提取JSON部分
            json_text = JSONParser.extract_json_from_response(result_text)

            # 解析JSON
            evaluation = json.loads(json_text)

            print(f"✅ 评估完成")
            print(f"   整体评分: {evaluation.get('overall_score', 'N/A')}/10")
            print(f"   推荐: {evaluation.get('recommendation', 'N/A')}")

            return evaluation

        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            print(f"   原始响应: {result_text[:300]}...")
            return self._create_error_evaluation(str(e), result_text[:500] if 'result_text' in locals() else '')
        except Exception as e:
            print(f"❌ 评估失败: {str(e)}")
            # 如果代理调用失败，返回基于规则的后备评估
            return self._create_rule_based_fallback(name, url, platform, str(e))

    def _create_error_evaluation(self, error_msg: str, raw_text: str) -> Dict[str, Any]:
        """创建错误评估结果"""
        return {
            "overall_score": 0,
            "evaluation_text": f"评估失败: {error_msg}",
            "recommendation": "评估失败",
            "error": error_msg,
            "raw_response": raw_text
        }

    def _create_rule_based_fallback(self, name: str, url: str, platform: str, error_msg: str) -> Dict[str, Any]:
        """创建基于规则的后备评估"""
        is_kurikulum_merdeka = 'merdeka' in url.lower() or 'merdeka' in name.lower()
        is_youtube = 'youtube.com' in url
        is_ruangguru = 'ruangguru.com' in url

        # 基于规则的简单评分
        base_score = 7.0

        if is_ruangguru:
            base_score += 1.0  # Ruangguru是专业教育平台
        if is_kurikulum_merdeka:
            base_score += 0.5  # 符合最新大纲
        if is_youtube:
            base_score += 0.5  # YouTube免费且易于访问

        base_score = min(base_score, 9.0)

        evaluation_text = f"""⚠️ 注意：由于网络原因，AI评估暂时不可用。以下是基于规则的后备评估：

**资源分析**:
- 平台: {platform}
- 类型: {'YouTube播放列表（免费视频资源）' if is_youtube else '在线课程平台'}
- 教学大纲: {'符合Kurikulum Merdeka（2022年印尼最新教育大纲）' if is_kurikulum_merdeka else '需要人工核实是否符合最新大纲'}

**评估说明**:
{f"- Ruangguru是印尼领先的在线教育平台，课程系统性强" if is_ruangguru else "- YouTube提供免费视频资源，访问便利"}
{f"- 明确标注符合Kurikulum Merdeka，时效性较好" if is_kurikulum_merdeka else "- 建议人工核实是否符合Kurikulum Merdeka"}
- {'视频播放列表形式，适合学生自主学习' if is_youtube else '- 结构化课程，可能有配套练习'}

**技术说明**:
- API调用遇到问题: {error_msg[:100]}
- 建议检查代理设置或网络连接
- 此评估为后备方案，建议人工核实

**建议**:
1. 人工访问资源查看实际内容质量
2. 核实是否完全符合印尼一年级教学大纲
3. 检查视频画质和制作水准"""

        return {
            "overall_score": base_score,
            "score_richness": base_score - 0.5,
            "score_timeliness": base_score - 0.2 if is_kurikulum_merdeka else base_score - 1.0,
            "score_teaching_method": base_score,
            "score_visual_quality": base_score - 0.3,
            "evaluation_text": evaluation_text,
            "recommendation": "可以考虑" if base_score >= 7.5 else "待人工评估",
            "fallback": True
        }


def process_excel(input_file: str, output_file: str):
    """处理Excel文件"""
    print("=" * 70)
    print("印尼一年级数学教育资源评估系统")
    print("基于 Gemini 2.5 Pro AI分析（通过代理访问）")
    print("=" * 70)

    # 配置环境
    setup_environment()

    # 读取Excel文件
    print(f"\n📂 读取Excel文件: {input_file}")
    df = pd.read_excel(input_file)
    print(f"✅ 成功读取 {len(df)} 条记录")

    # 初始化评估器
    evaluator = ResourceEvaluator()

    # 准备新列
    scores = []
    evaluations = []

    # 逐行处理
    for idx, row in df.iterrows():
        name = row.get('名称', '')
        url = row.get('网址', '')

        print(f"\n{'=' * 70}")
        print(f"[{idx + 1}/{len(df)}] 评估资源")
        print(f"名称: {name}")
        print(f"网址: {url}")
        print(f"{'=' * 70}")

        # 评估资源
        evaluation = evaluator.evaluate(name, url)

        # 提取分数
        overall_score = evaluation.get('overall_score', 0)

        # 构建评估文本
        eval_text_parts = []

        # 标题行
        eval_text_parts.append(f"【整体评分】: {overall_score:.1f}/10")
        eval_text_parts.append(f"【推荐意见】: {evaluation.get('recommendation', 'N/A')}")

        # 分项评分
        if 'score_richness' in evaluation:
            eval_text_parts.append(f"\n【分项评分】")
            eval_text_parts.append(f"• 资源丰富程度: {evaluation['score_richness']:.1f}/10")
            eval_text_parts.append(f"• 时效性: {evaluation['score_timeliness']:.1f}/10")
            eval_text_parts.append(f"• 教学方法: {evaluation['score_teaching_method']:.1f}/10")
            eval_text_parts.append(f"• 画面质量: {evaluation['score_visual_quality']:.1f}/10")

        # 详细评估
        eval_text_parts.append(f"\n【详细评估】")
        eval_text_parts.append(evaluation.get('evaluation_text', ''))

        # 如果是后备评估，添加说明
        if evaluation.get('fallback'):
            eval_text_parts.append(f"\n【⚠️ 说明】")
            eval_text_parts.append("此评估使用后备规则生成，AI深度评估暂时不可用。建议人工核实资源质量。")

        # 错误信息
        if 'error' in evaluation and not evaluation.get('fallback'):
            eval_text_parts.append(f"\n【错误信息】")
            eval_text_parts.append(f"评估过程中出现错误: {evaluation['error']}")

        final_eval_text = "\n".join(eval_text_parts)

        scores.append(overall_score)
        evaluations.append(final_eval_text)

        # 避免请求过快
        if idx < len(df) - 1:  # 最后一个不需要等待
            print(f"\n⏳ 等待3秒后处理下一个...")
            time.sleep(3)

    # 添加新列
    df['评估分数'] = scores
    df['评估内容'] = evaluations

    # 按分数降序排序
    df = df.sort_values('评估分数', ascending=False)

    # 保存到Excel
    print(f"\n💾 保存评估结果到: {output_file}")
    df.to_excel(output_file, index=False, engine='openpyxl')
    print("✅ 保存成功！")

    # 打印统计信息
    print("\n" + "=" * 70)
    print("📊 评估统计")
    print("=" * 70)
    print(f"总评估数: {len(df)}")
    print(f"平均分数: {df['评估分数'].mean():.2f}/10")
    print(f"最高分数: {df['评估分数'].max():.1f}/10")
    print(f"最低分数: {df['评估分数'].min():.1f}/10")

    # 推荐分布
    print("\n【推荐意见分布】")
    recommendations = []
    for eval_text in df['评估内容']:
        match = re.search(r'【推荐意见】:\s*(\S+)', eval_text)
        if match:
            recommendations.append(match.group(1))
    if recommendations:
        from collections import Counter
        for rec, count in Counter(recommendations).most_common():
            print(f"  {rec}: {count}个")

    # 显示所有资源按分数排序
    print("\n【资源排名（按分数排序）】")
    for idx, (name, score, rec) in enumerate(df[['名称', '评估分数', '评估内容']].values, 1):
        match = re.search(r'【推荐意见】:\s*(\S+)', rec)
        recommendation = match.group(1) if match else 'N/A'
        print(f"  {idx}. {name}")
        print(f"     评分: {score:.1f}/10 | 推荐: {recommendation}")


if __name__ == "__main__":
    # 文件路径
    input_file = "印尼一年级数学.xlsx"
    output_file = "印尼一年级数学_评估结果.xlsx"

    # 执行评估
    process_excel(input_file, output_file)

    print("\n" + "=" * 70)
    print("🎉 评估完成！")
    print(f"📊 结果已保存到: {output_file}")
    print("=" * 70)
