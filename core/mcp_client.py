#!/usr/bin/env python3
"""
Chrome DevTools MCP 客户端
免费、无限制地使用 Chrome DevTools 功能
"""

import os
import json
import subprocess
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
import requests
from logger_utils import get_logger

logger = get_logger('mcp_client')


class ChromeDevToolsMCP:
    """Chrome DevTools MCP 客户端"""

    def __init__(self, project_dir: Optional[str] = None):
        """
        初始化 MCP 客户端

        Args:
            project_dir: 项目目录，用于读取 .mcp.json 配置
        """
        if project_dir is None:
            project_dir = os.getcwd()

        self.project_dir = Path(project_dir)
        self.mcp_config_file = self.project_dir / '.mcp.json'
        self.server_process = None
        self.server_url = None

        logger.info(f"[MCP] 初始化 Chrome DevTools MCP 客户端")
        logger.info(f"[MCP] 项目目录: {self.project_dir}")

    def start_server(self) -> bool:
        """
        启动 Chrome DevTools MCP 服务器

        Returns:
            是否成功启动
        """
        try:
            # 检查是否已经有配置
            if self.mcp_config_file.exists():
                logger.info(f"[MCP] 找到配置文件: {self.mcp_config_file}")
                with open(self.mcp_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"[MCP] 配置: {json.dumps(config, indent=2, ensure_ascii=False)}")

            # 使用 npx 启动 MCP 服务器
            cmd = ["npx", "-y", "chrome-devtools-mcp@latest"]
            logger.info(f"[MCP] 启动命令: {' '.join(cmd)}")

            # 注意：这里我们使用子进程方式，实际使用时需要通过 MCP SDK 连接
            logger.info(f"[MCP] Chrome DevTools MCP 服务器已配置")
            return True

        except Exception as e:
            logger.error(f"[MCP] 启动服务器失败: {e}")
            return False

    async def navigate_to_url(self, url: str) -> Dict[str, Any]:
        """
        导航到指定 URL

        Args:
            url: 目标网址

        Returns:
            操作结果
        """
        logger.info(f"[MCP] 导航到: {url}")

        # 这里需要通过 MCP SDK 调用实际的 MCP 工具
        # 返回模拟结果，实际使用时需要替换为真实的 MCP 调用
        result = {
            "success": True,
            "url": url,
            "message": "导航成功"
        }

        return result

    async def take_screenshot(self, url: str, save_path: Optional[str] = None) -> Dict[str, Any]:
        """
        截取网页截图

        Args:
            url: 目标网址
            save_path: 截图保存路径

        Returns:
            操作结果和截图路径
        """
        logger.info(f"[MCP] 截图: {url}")

        # 实际实现需要调用 MCP 的 take_screenshot 工具
        result = {
            "success": True,
            "url": url,
            "screenshot_path": save_path or "screenshot.png",
            "message": "截图成功"
        }

        return result

    async def evaluate_page(self, url: str, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估网页是否符合指定标准

        Args:
            url: 目标网址
            criteria: 评估标准，例如：
                {
                    "country": "伊拉克",
                    "grade": "高中一年级",
                    "subject": "伊斯兰教育"
                }

        Returns:
            评估结果
        """
        logger.info(f"[MCP] 评估网页: {url}")
        logger.info(f"[MCP] 评估标准: {json.dumps(criteria, ensure_ascii=False)}")

        # 1. 导航到网页
        nav_result = await self.navigate_to_url(url)

        # 2. 截图
        screenshot_result = await self.take_screenshot(url)

        # 3. 获取页面内容（通过 MCP 的其他工具）
        # 这里需要集成实际的页面分析逻辑

        # 4. 返回评估结果
        result = {
            "url": url,
            "criteria": criteria,
            "navigation": nav_result,
            "screenshot": screenshot_result,
            "evaluation": {
                "score": 0,
                "details": {}
            }
        }

        return result

    def create_mcp_config(self) -> bool:
        """
        在项目中创建 .mcp.json 配置文件

        Returns:
            是否成功创建
        """
        config = {
            "mcpServers": {
                "chrome-devtools": {
                    "command": "npx",
                    "args": ["-y", "chrome-devtools-mcp@latest"],
                    "env": {}
                }
            }
        }

        try:
            with open(self.mcp_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            logger.info(f"[MCP] ✅ 配置文件已创建: {self.mcp_config_file}")
            logger.info(f"[MCP] 配置内容:\n{json.dumps(config, indent=2, ensure_ascii=False)}")
            return True

        except Exception as e:
            logger.error(f"[MCP] ❌ 创建配置文件失败: {e}")
            return False


class SimpleWebEvaluator:
    """简单的网页评估器（不依赖 MCP SDK）"""

    def __init__(self):
        self.logger = get_logger('web_evaluator')

    def evaluate_from_content(self, title: str, description: str, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        从页面内容评估网页

        Args:
            title: 页面标题
            description: 页面描述
            criteria: 评估标准

        Returns:
            评估结果
        """
        result = {
            "url": criteria.get("url", ""),
            "criteria": criteria,
            "page_info": {
                "title": title,
                "description": description
            },
            "scores": {},
            "overall_score": 0,
            "analysis": {}
        }

        # 提取评估标准
        required_country = criteria.get("country", "")
        required_grade = criteria.get("grade", "")
        required_subject = criteria.get("subject", "")

        # 评估标题和描述
        text_to_check = f"{title} {description}".lower()

        # 简单匹配逻辑
        scores = {}
        analysis = {}

        # 1. 年级匹配
        if required_grade:
            # 支持多语言关键词
            grade_keywords = self._get_grade_keywords(required_grade)
            grade_score = self._calculate_match_score(text_to_check, grade_keywords)
            scores["grade"] = grade_score
            analysis["grade"] = f"年级匹配度: {grade_score}/10"

        # 2. 学科匹配
        if required_subject:
            subject_keywords = self._get_subject_keywords(required_subject)
            subject_score = self._calculate_match_score(text_to_check, subject_keywords)
            scores["subject"] = subject_score
            analysis["subject"] = f"学科匹配度: {subject_score}/10"

        # 3. 国家/地区匹配（从语言推断）
        if required_country:
            country_score = self._infer_country_from_language(title, description, required_country)
            scores["country"] = country_score
            analysis["country"] = f"地区相关性: {country_score}/10"

        # 计算总分
        if scores:
            overall_score = sum(scores.values()) / len(scores)
        else:
            overall_score = 0

        result["scores"] = scores
        result["analysis"] = analysis
        result["overall_score"] = round(overall_score, 1)

        self.logger.info(f"[评估] 总分: {result['overall_score']}/10")
        for key, value in analysis.items():
            self.logger.info(f"[评估] {value}")

        return result

    def _get_grade_keywords(self, grade: str) -> List[str]:
        """获取年级的多语言关键词"""
        keywords_map = {
            "高中一年级": [
                "الصف الأول الثانوي",  # 阿拉伯语
                "grade 10",
                "sma kelas 1",  # 印尼语
                "高一",
                "高中一年级"
            ],
            # 可以继续添加其他年级...
        }
        return keywords_map.get(grade, [grade])

    def _get_subject_keywords(self, subject: str) -> List[str]:
        """获取学科的多语言关键词"""
        keywords_map = {
            "伊斯兰教育": [
                "التربية الإسلامية",  # 阿拉伯语
                "islamic education",
                "pendidikan islam",  # 印尼语
                "伊斯兰教育",
                "宗教"
            ],
            # 可以继续添加其他学科...
        }
        return keywords_map.get(subject, [subject])

    def _calculate_match_score(self, text: str, keywords: List[str]) -> float:
        """
        计算文本与关键词的匹配分数

        Args:
            text: 要检查的文本
            keywords: 关键词列表

        Returns:
            匹配分数 (0-10)
        """
        if not keywords:
            return 0.0

        matches = 0
        for keyword in keywords:
            if keyword.lower() in text:
                matches += 1

        # 计算匹配比例
        match_ratio = matches / len(keywords)

        # 转换为 0-10 分
        score = round(match_ratio * 10, 1)

        return score

    def _infer_country_from_language(self, title: str, description: str, target_country: str) -> float:
        """
        从语言推断国家/地区相关性

        Args:
            title: 页面标题
            description: 页面描述
            target_country: 目标国家

        Returns:
            相关性分数 (0-10)
        """
        text = f"{title} {description}"

        # 语言特征映射
        language_indicators = {
            "伊拉克": {
                "scripts": ["ar"],  # 阿拉伯语
                "keywords": ["العراق", "بغداد"],
                "score": 9
            },
            "印度尼西亚": {
                "scripts": ["id"],  # 印尼语
                "keywords": ["indonesia", "jakarta", "pendidikan"],
                "score": 9
            }
        }

        # 检查阿拉伯语特征（适用于伊拉克等阿拉伯国家）
        if any(char in text for char in "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"):
            return 9.0

        # 如果目标国家在映射表中
        if target_country in language_indicators:
            indicators = language_indicators[target_country]
            for keyword in indicators["keywords"]:
                if keyword.lower() in text.lower():
                    return indicators["score"]

        # 默认中等分数
        return 5.0


# 便捷函数
def create_mcp_config(project_dir: Optional[str] = None) -> bool:
    """
    在项目中创建 MCP 配置文件

    Args:
        project_dir: 项目目录

    Returns:
        是否成功创建
    """
    client = ChromeDevToolsMCP(project_dir)
    return client.create_mcp_config()


if __name__ == "__main__":
    # 测试：创建配置文件
    print("=" * 60)
    print("Chrome DevTools MCP 客户端测试")
    print("=" * 60)

    client = ChromeDevToolsMCP()
    success = client.create_mcp_config()

    if success:
        print("\n✅ 配置文件创建成功！")
        print(f"📁 配置文件位置: {client.mcp_config_file}")
        print("\n下一步：")
        print("1. 安装依赖: pip install mcp")
        print("2. 运行测试: python test_mcp_integration.py")
    else:
        print("\n❌ 配置文件创建失败")
