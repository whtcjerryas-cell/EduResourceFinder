#!/usr/bin/env python3
"""
智能网页评估工具
使用 LLM + Chrome DevTools 评估教育资源网页
完全免费，无限制调用
"""

import os
import json
import base64
from typing import Dict, Any, Optional, List
from pathlib import Path
import requests
from llm_client import InternalAPIClient
from core.mcp_client import SimpleWebEvaluator
from logger_utils import get_logger

logger = get_logger('webpage_evaluator')


class ResourceEvaluator:
    """教育资源智能评估器"""

    def __init__(self, use_internal_api: bool = True):
        """
        初始化评估器

        Args:
            use_internal_api: 是否使用内部API（默认True，免费）
        """
        self.use_internal_api = use_internal_api

        # 初始化 LLM 客户端
        if use_internal_api:
            try:
                self.llm_client = InternalAPIClient()
                logger.info("[评估器] ✅ 使用内部API（免费）")
            except Exception as e:
                logger.warning(f"[评估器] ⚠️ 内部API初始化失败: {e}")
                self.llm_client = None
        else:
            self.llm_client = None

        # 简单评估器（作为备选）
        self.simple_evaluator = SimpleWebEvaluator()

        logger.info("[评估器] 初始化完成")

    def evaluate_youtube_resource(
        self,
        url: str,
        criteria: Dict[str, Any],
        screenshot_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        评估 YouTube 教育资源

        Args:
            url: YouTube URL
            criteria: 评估标准
                {
                    "country": "伊拉克",
                    "grade": "高中一年级",
                    "subject": "伊斯兰教育"
                }
            screenshot_path: 可选的截图路径（如果有）

        Returns:
            评估结果
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"[评估] 开始评估 YouTube 资源")
        logger.info(f"[评估] URL: {url}")
        logger.info(f"[评估] 标准: {json.dumps(criteria, ensure_ascii=False)}")
        logger.info(f"{'='*60}\n")

        # 1. 获取页面基本信息（通过 YouTube API 或 web-reader）
        try:
            page_info = self._get_youtube_page_info(url)
        except Exception as e:
            logger.error(f"[评估] 获取页面信息失败: {e}")
            page_info = {"title": "", "description": ""}

        # 2. 使用 LLM 进行深度分析
        if self.llm_client:
            llm_result = self._evaluate_with_llm(
                url=url,
                title=page_info.get("title", ""),
                description=page_info.get("description", ""),
                criteria=criteria,
                screenshot_path=screenshot_path
            )
        else:
            llm_result = None

        # 3. 使用规则引擎进行基础评估
        simple_result = self.simple_evaluator.evaluate_from_content(
            title=page_info.get("title", ""),
            description=page_info.get("description", ""),
            criteria=criteria
        )

        # 4. 合并结果
        final_result = {
            "url": url,
            "criteria": criteria,
            "page_info": page_info,
            "llm_evaluation": llm_result,
            "rule_evaluation": simple_result,
            "final_score": self._calculate_final_score(llm_result, simple_result),
            "recommendation": self._generate_recommendation(llm_result, simple_result)
        }

        # 5. 输出报告
        self._print_evaluation_report(final_result)

        return final_result

    def _get_youtube_page_info(self, url: str) -> Dict[str, str]:
        """
        获取 YouTube 页面信息

        Args:
            url: YouTube URL

        Returns:
            页面信息（标题、描述等）
        """
        logger.info(f"[网页信息] 获取 YouTube 页面信息")

        # 方案 1: 使用 YouTube Data API（如果配置了）
        # 方案 2: 使用 web scraping（需要处理动态内容）
        # 方案 3: 使用 web-reader MCP（如果有）

        # 这里使用简单的方案：通过 noembed 获取基本信息
        try:
            # 提取视频 ID
            if "v=" in url:
                video_id = url.split("v=")[1].split("&")[0]
            elif "youtu.be/" in url:
                video_id = url.split("youtu.be/")[1].split("?")[0]
            else:
                video_id = ""

            if video_id:
                # 使用 noembed API
                noembed_url = f"https://noembed.com/embed?url=https://www.youtube.com/watch?v={video_id}"
                response = requests.get(noembed_url, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "title": data.get("title", ""),
                        "description": data.get("author_name", ""),
                        "author": data.get("author_name", ""),
                        "thumbnail": ""
                    }

        except Exception as e:
            logger.warning(f"[网页信息] noembed 获取失败: {e}")

        # 失败时返回空信息
        return {
            "title": "",
            "description": "",
            "author": "",
            "thumbnail": ""
        }

    def _evaluate_with_llm(
        self,
        url: str,
        title: str,
        description: str,
        criteria: Dict[str, Any],
        screenshot_path: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        使用 LLM 进行深度评估

        Args:
            url: 网页 URL
            title: 页面标题
            description: 页面描述
            criteria: 评估标准
            screenshot_path: 可选的截图路径

        Returns:
            LLM 评估结果
        """
        try:
            logger.info("[LLM 评估] 开始 LLM 深度分析")

            # 构建提示词
            prompt = self._build_evaluation_prompt(
                url=url,
                title=title,
                description=description,
                criteria=criteria
            )

            # 如果有截图，编码为 base64
            image_data = None
            if screenshot_path and os.path.exists(screenshot_path):
                with open(screenshot_path, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                logger.info(f"[LLM 评估] 已包含截图: {screenshot_path}")

            # 调用 LLM
            if image_data:
                # 使用视觉模型
                response = self.llm_client.call_vision_api(
                    prompt=prompt,
                    image_base64=image_data,
                    model="gpt-4o"  # 或其他视觉模型
                )
            else:
                # 使用文本模型
                response = self.llm_client.call(
                    prompt=prompt,
                    model="gpt-4o"  # 或其他模型
                )

            # 解析响应
            result = self._parse_llm_response(response)

            logger.info(f"[LLM 评估] ✅ LLM 分析完成")
            return result

        except Exception as e:
            logger.error(f"[LLM 评估] ❌ LLM 分析失败: {e}")
            return None

    def _build_evaluation_prompt(
        self,
        url: str,
        title: str,
        description: str,
        criteria: Dict[str, Any]
    ) -> str:
        """构建评估提示词"""

        prompt = f"""你是一个教育资源评估专家。请评估以下 YouTube 教育资源是否符合要求。

## 网页信息
- URL: {url}
- 标题: {title}
- 描述: {description}

## 评估标准
- 国家/地区: {criteria.get('country', '未指定')}
- 年级: {criteria.get('grade', '未指定')}
- 学科: {criteria.get('subject', '未指定')}

## 评估要求

请从以下维度进行评估（每个维度 0-10 分）：

1. **年级匹配度**：内容是否适合目标年级
2. **学科匹配度**：是否属于目标学科
3. **地区相关性**：是否来自目标国家/地区或使用当地语言
4. **内容质量**：教学内容的准确性和完整性
5. **适用性**：是否适合作为主要教学资源

## 输出格式

请以 JSON 格式输出评估结果：

```json
{{
  "scores": {{
    "grade": <年级分数 0-10>,
    "subject": <学科分数 0-10>,
    "country": <地区分数 0-10>,
    "quality": <质量分数 0-10>,
    "applicability": <适用性分数 0-10>
  }},
  "overall_score": <总分 0-10>,
  "analysis": {{
    "strengths": ["优点1", "优点2"],
    "weaknesses": ["缺点1", "缺点2"],
    "notes": "其他分析说明"
  }},
  "recommendation": "强烈推荐 / 推荐 / 谨慎使用 / 不推荐"
}}
```

请开始评估：
"""

        return prompt

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析 LLM 响应"""
        try:
            # 尝试提取 JSON
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                # 尝试直接解析
                json_str = response.strip()

            result = json.loads(json_str)
            return result

        except Exception as e:
            logger.warning(f"[LLM 评估] JSON 解析失败: {e}")
            # 返回部分解析的结果
            return {
                "raw_response": response,
                "parse_error": str(e)
            }

    def _calculate_final_score(
        self,
        llm_result: Optional[Dict[str, Any]],
        simple_result: Dict[str, Any]
    ) -> float:
        """计算最终分数（结合 LLM 和规则引擎）"""
        scores = []

        if llm_result and "overall_score" in llm_result:
            scores.append(llm_result["overall_score"])

        if "overall_score" in simple_result:
            scores.append(simple_result["overall_score"])

        if scores:
            return round(sum(scores) / len(scores), 1)
        else:
            return 0.0

    def _generate_recommendation(
        self,
        llm_result: Optional[Dict[str, Any]],
        simple_result: Dict[str, Any]
    ) -> str:
        """生成推荐意见"""
        final_score = self._calculate_final_score(llm_result, simple_result)

        if final_score >= 9:
            return "✅ 强烈推荐 - 完全符合要求"
        elif final_score >= 7:
            return "✅ 推荐 - 高度符合要求"
        elif final_score >= 5:
            return "⚠️ 谨慎使用 - 部分符合要求"
        else:
            return "❌ 不推荐 - 不符合要求"

    def _print_evaluation_report(self, result: Dict[str, Any]):
        """打印评估报告"""
        print("\n" + "=" * 80)
        print("📊 教育资源评估报告")
        print("=" * 80)

        print(f"\n🔗 URL: {result['url']}")
        print(f"📋 页面标题: {result['page_info'].get('title', '未知')}")

        print(f"\n🎯 评估标准:")
        criteria = result['criteria']
        print(f"   • 国家/地区: {criteria.get('country', '未指定')}")
        print(f"   • 年级: {criteria.get('grade', '未指定')}")
        print(f"   • 学科: {criteria.get('subject', '未指定')}")

        print(f"\n⭐ 最终评分: {result['final_score']}/10")

        if result['rule_evaluation'].get('scores'):
            print(f"\n📈 详细评分:")
            for key, value in result['rule_evaluation']['scores'].items():
                key_name = {
                    'grade': '年级匹配',
                    'subject': '学科匹配',
                    'country': '地区相关'
                }.get(key, key)
                print(f"   • {key_name}: {value}/10")

        if result['llm_evaluation'] and result['llm_evaluation'].get('analysis'):
            print(f"\n🔍 LLM 深度分析:")
            analysis = result['llm_evaluation']['analysis']
            if analysis.get('strengths'):
                print(f"   ✅ 优点:")
                for strength in analysis['strengths']:
                    print(f"      • {strength}")
            if analysis.get('weaknesses'):
                print(f"   ⚠️ 缺点:")
                for weakness in analysis['weaknesses']:
                    print(f"      • {weakness}")
            if analysis.get('notes'):
                print(f"   📝 说明: {analysis['notes']}")

        print(f"\n💡 推荐意见: {result['recommendation']}")

        print("\n" + "=" * 80 + "\n")

        # 保存到文件
        self._save_evaluation_report(result)

    def _save_evaluation_report(self, result: Dict[str, Any]):
        """保存评估报告到文件"""
        try:
            reports_dir = Path("evaluation_reports")
            reports_dir.mkdir(exist_ok=True)

            # 生成文件名
            url = result['url']
            if "v=" in url:
                video_id = url.split("v=")[1].split("&")[0]
            else:
                video_id = "unknown"

            filename = f"evaluation_{video_id}.json"
            filepath = reports_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            logger.info(f"[报告] ✅ 评估报告已保存: {filepath}")

        except Exception as e:
            logger.error(f"[报告] ❌ 保存报告失败: {e}")


# 便捷函数
def evaluate_resource(
    url: str,
    country: str,
    grade: str,
    subject: str,
    screenshot_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    便捷的评估函数

    Args:
        url: 资源 URL
        country: 国家/地区
        grade: 年级
        subject: 学科
        screenshot_path: 可选的截图路径

    Returns:
        评估结果
    """
    evaluator = ResourceEvaluator()

    criteria = {
        "url": url,
        "country": country,
        "grade": grade,
        "subject": subject
    }

    return evaluator.evaluate_youtube_resource(
        url=url,
        criteria=criteria,
        screenshot_path=screenshot_path
    )


if __name__ == "__main__":
    # 测试评估器
    print("=" * 60)
    print("智能网页评估工具测试")
    print("=" * 60)

    # 测试用例
    test_url = "https://www.youtube.com/watch?v=epHRx091W7M&list=PLLbwDrE8zWWVLe3BCccgJLrArsNS-gWXG&index=1"

    result = evaluate_resource(
        url=test_url,
        country="伊拉克",
        grade="高中一年级",
        subject="伊斯兰教育"
    )

    print("\n✅ 评估完成！")
