#!/usr/bin/env python3
"""
职业教育搜索引擎 - 专门用于职业教育资源的搜索
支持按技能领域、目标受众、技能水平等进行搜索
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import json
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

try:
    from search_engine_v2 import SearchEngineV2
except ImportError:
    SearchEngineV2 = None
    print("[⚠️ 警告] search_engine_v2不可用，部分功能可能受限")


# ============================================================================
# 数据模型
# ============================================================================

class VocationalSearchRequest(BaseModel):
    """职业教育搜索请求"""
    # 基本信息
    country: str = Field(description="国家代码（如：ID）")
    query: str = Field(description="搜索查询（关键词或主题）")

    # 技能领域信息
    skill_area: Optional[str] = Field(description="技能领域代码（如：IT, LANG, BIZ）", default=None)
    program_code: Optional[str] = Field(description="课程代码（如：IT-BASIC, LANG-EN-BEG）", default=None)

    # 筛选条件
    target_audience: Optional[str] = Field(description="目标受众（如：beginner, professional）", default=None)
    level: Optional[str] = Field(description="技能水平（如：beginner, intermediate, advanced）", default=None)
    provider: Optional[str] = Field(description="培训提供商（如：Ruangguru, EF）", default=None)
    max_duration: Optional[int] = Field(description="最大培训时长（月）", default=None)
    max_price: Optional[int] = Field(description="最高价格（千印尼盾）", default=None)

    # 搜索选项
    max_results: int = Field(description="最大结果数", default=10)


class VocationalConfig(BaseModel):
    """职业教育配置"""
    country_code: str
    country_name: str
    country_name_zh: str
    education_levels: Dict[str, Any]


# ============================================================================
# 职业教育搜索引擎
# ============================================================================

class VocationalSearchEngine:
    """职业教育资源搜索引擎"""

    def __init__(self, config_file: str = "data/config/indonesia_vocational.json"):
        """
        初始化职业教育搜索引擎

        Args:
            config_file: 职业教育配置文件路径
        """
        self.config_file = config_file
        self.config = self._load_config()
        self.base_engine = SearchEngineV2() if SearchEngineV2 else None

    def _load_config(self) -> Optional[VocationalConfig]:
        """加载职业教育配置"""
        try:
            if not os.path.exists(self.config_file):
                print(f"[⚠️ 警告] 职业教育配置文件不存在: {self.config_file}")
                return None

            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return VocationalConfig(**data)
        except Exception as e:
            print(f"[⚠️ 警告] 加载职业教育配置失败: {str(e)}")
            return None

    def _get_skill_area(self, area_code: str) -> Optional[Dict[str, Any]]:
        """获取指定技能领域的信息"""
        if not self.config:
            return None

        skill_areas = self.config.education_levels.get("vocational", {}).get("skill_areas", [])

        for area in skill_areas:
            if area.get("area_code") == area_code:
                return area

        return None

    def _get_program(self, area_code: str, program_code: str) -> Optional[Dict[str, Any]]:
        """获取指定课程的信息"""
        area = self._get_skill_area(area_code)
        if not area:
            return None

        programs = area.get("programs", [])
        for program in programs:
            if program.get("program_code") == program_code:
                return program

        return None

    def _generate_search_query(self, request: VocationalSearchRequest) -> str:
        """
        生成职业教育的搜索查询

        策略：
        1. 如果指定了技能领域，使用领域名称
        2. 如果指定了课程，使用课程名称
        3. 如果指定了技能，使用技能名称
        4. 组合用户提供的查询词
        """
        query_parts = []

        # 添加技能领域上下文
        if request.skill_area:
            area = self._get_skill_area(request.skill_area)
            if area:
                # 使用三语名称
                for name_key in ["local_name", "english_name", "zh_name"]:
                    name = area.get(name_key, "")
                    if name:
                        query_parts.append(name)
                        break

        # 添加课程上下文
        if request.program_code and request.skill_area:
            program = self._get_program(request.skill_area, request.program_code)
            if program:
                for name_key in ["local_name", "english_name", "zh_name"]:
                    name = program.get(name_key, "")
                    if name:
                        query_parts.append(name)
                        break

        # 添加用户查询
        if request.query:
            query_parts.append(request.query)

        # 组合查询
        if query_parts:
            combined_query = " ".join(query_parts)
        else:
            combined_query = request.query

        return combined_query.strip()

    def _get_context_info(self, request: VocationalSearchRequest) -> Dict[str, Any]:
        """获取搜索上下文信息"""
        context = {
            "country": request.country,
            "country_name": "",
            "skill_area": None,
            "program": None,
            "filters": {}
        }

        # 获取国家名称
        if self.config:
            context["country_name"] = self.config.country_name_zh

        # 获取技能领域信息
        if request.skill_area:
            area = self._get_skill_area(request.skill_area)
            if area:
                context["skill_area"] = {
                    "code": area.get("area_code"),
                    "local_name": area.get("local_name"),
                    "zh_name": area.get("zh_name"),
                    "english_name": area.get("english_name"),
                    "icon": area.get("icon"),
                    "program_count": len(area.get("programs", []))
                }

        # 获取课程信息
        if request.program_code and request.skill_area:
            program = self._get_program(request.skill_area, request.program_code)
            if program:
                context["program"] = {
                    "code": program.get("program_code"),
                    "local_name": program.get("local_name"),
                    "zh_name": program.get("zh_name"),
                    "english_name": program.get("english_name"),
                    "provider": program.get("provider"),
                    "duration": program.get("duration"),
                    "target_audience": program.get("target_audience"),
                    "certification": program.get("certification"),
                    "price_range": program.get("price_range")
                }

                # 添加筛选条件到上下文
                context["filters"]["target_audience"] = program.get("target_audience", [])
                context["filters"]["prerequisites"] = program.get("prerequisites", [])

        # 添加其他筛选条件
        if request.target_audience:
            context["filters"]["target_audience_selected"] = request.target_audience
        if request.level:
            context["filters"]["level"] = request.level
        if request.provider:
            context["filters"]["provider"] = request.provider

        return context

    def search(self, request: VocationalSearchRequest) -> Dict[str, Any]:
        """
        执行职业教育资源搜索

        Args:
            request: 职业教育搜索请求

        Returns:
            搜索结果，包含：
            - success: 是否成功
            - context: 搜索上下文（技能领域、课程信息、筛选条件）
            - query: 实际使用的搜索词
            - results: 搜索结果列表
            - total_results: 总结果数
        """
        print(f"\n{'='*80}")
        print(f"🛠️  职业教育资源搜索")
        print(f"{'='*80}")

        # 生成搜索查询
        search_query = self._generate_search_query(request)
        print(f"\n[搜索查询] {search_query}")

        # 获取上下文信息
        context = self._get_context_info(request)

        # 打印搜索上下文
        if context.get("skill_area"):
            area = context['skill_area']
            print(f"[技能领域] {area['icon']} {area['zh_name']}")

        if context.get("program"):
            prog = context['program']
            print(f"[课程] {prog['zh_name']}")
            print(f"[提供商] {prog['provider']}")
            print(f"[时长] {prog['duration']}")
            print(f"[认证] {prog['certification']}")

        # 执行搜索
        print(f"\n[执行搜索]...")
        try:
            if SearchEngineV2 is None or self.base_engine is None:
                # 如果基础引擎不可用，返回上下文信息
                print(f"[⚠️ 警告] 基础搜索引擎不可用，返回上下文信息")

                return {
                    "success": True,
                    "context": context,
                    "vocational_search_query": search_query,
                    "results": [],
                    "total_results": 0,
                    "message": "基础搜索引擎不可用，仅返回上下文信息"
                }

            # 这里可以集成实际的搜索引擎调用
            # 目前先返回模拟结果
            print(f"[⚠️ 注意] 职业教育搜索功能待完善，返回上下文信息")

            return {
                "success": True,
                "context": context,
                "vocational_search_query": search_query,
                "results": [],
                "total_results": 0,
                "message": "职业教育搜索功能开发中"
            }

        except Exception as e:
            print(f"[❌ 错误] 搜索失败: {str(e)}")
            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "error": str(e),
                "context": context,
                "query": search_query,
                "results": [],
                "total_results": 0
            }

    def get_available_skill_areas(self, country_code: str) -> List[Dict[str, Any]]:
        """
        获取指定国家的所有技能领域列表

        Args:
            country_code: 国家代码

        Returns:
            技能领域列表
        """
        if not self.config or self.config.country_code != country_code:
            return []

        skill_areas = self.config.education_levels.get("vocational", {}).get("skill_areas", [])

        return [
            {
                "code": area.get("area_code"),
                "local_name": area.get("local_name"),
                "zh_name": area.get("zh_name"),
                "english_name": area.get("english_name"),
                "icon": area.get("icon"),
                "program_count": len(area.get("programs", []))
            }
            for area in skill_areas
        ]

    def get_available_programs(
        self,
        country_code: str,
        skill_area: str,
        target_audience: Optional[str] = None,
        max_duration: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取指定技能领域的课程列表

        Args:
            country_code: 国家代码
            skill_area: 技能领域代码
            target_audience: 目标受众（可选）
            max_duration: 最大培训时长（月，可选）

        Returns:
            课程列表
        """
        if not self.config or self.config.country_code != country_code:
            return []

        area = self._get_skill_area(skill_area)
        if not area:
            return []

        programs = area.get("programs", [])

        # 应用筛选条件
        if target_audience:
            programs = [
                p for p in programs
                if target_audience in p.get("target_audience", [])
            ]

        if max_duration:
            programs = [
                p for p in programs
                if self._parse_duration(p.get("duration", "")) <= max_duration
            ]

        return [
            {
                "code": program.get("program_code"),
                "local_name": program.get("local_name"),
                "zh_name": program.get("zh_name"),
                "english_name": program.get("english_name"),
                "provider": program.get("provider"),
                "duration": program.get("duration"),
                "target_audience": program.get("target_audience"),
                "skill_count": len(program.get("skills", [])),
                "certification": program.get("certification"),
                "price_range": program.get("price_range")
            }
            for program in programs
        ]

    def get_program_skills(
        self,
        country_code: str,
        skill_area: str,
        program_code: str
    ) -> List[Dict[str, Any]]:
        """
        获取指定课程的技能列表

        Args:
            country_code: 国家代码
            skill_area: 技能领域代码
            program_code: 课程代码

        Returns:
            技能列表
        """
        if not self.config or self.config.country_code != country_code:
            return []

        program = self._get_program(skill_area, program_code)
        if not program:
            return []

        skills = program.get("skills", [])

        return [
            {
                "code": skill.get("skill_code"),
                "local_name": skill.get("local_name"),
                "zh_name": skill.get("zh_name"),
                "english_name": skill.get("english_name"),
                "level": skill.get("level"),
                "description": skill.get("description")
            }
            for skill in skills
        ]

    def _parse_duration(self, duration_str: str) -> int:
        """解析时长字符串，返回月数"""
        try:
            # 提取数字
            import re
            numbers = re.findall(r'\d+', duration_str)
            if numbers:
                return int(numbers[0])
        except:
            pass
        return 999  # 默认返回一个大数字


# ============================================================================
# 辅助函数
# ============================================================================

def get_vocational_search_engine() -> VocationalSearchEngine:
    """获取职业教育搜索引擎实例"""
    return VocationalSearchEngine()


if __name__ == "__main__":
    # 测试代码
    print("="*80)
    print("职业教育搜索引擎测试")
    print("="*80)

    engine = VocationalSearchEngine()

    # 测试1: 获取技能领域列表
    print("\n[测试1] 获取技能领域列表")
    skill_areas = engine.get_available_skill_areas("ID")
    print(f"找到 {len(skill_areas)} 个技能领域:")
    for area in skill_areas:
        print(f"  - {area['icon']} {area['zh_name']} ({area['code']}): {area['program_count']}个课程")

    # 测试2: 获取IT领域的课程列表
    print("\n[测试2] 获取IT领域的课程列表")
    programs = engine.get_available_programs("ID", "IT")
    print(f"找到 {len(programs)} 个课程:")
    for prog in programs:
        print(f"  - {prog['zh_name']} ({prog['code']}): {prog['provider']}, {prog['duration']}, {prog['skill_count']}个技能")

    # 测试3: 获取初学者课程
    print("\n[测试3] 获取IT领域的初学者课程")
    beginner_programs = engine.get_available_programs("ID", "IT", target_audience="beginner")
    print(f"找到 {len(beginner_programs)} 个初学者课程:")
    for prog in beginner_programs:
        print(f"  - {prog['zh_name']}: {prog['duration']}")

    # 测试4: 获取课程的技能列表
    print("\n[测试4] 获取IT-BASIC的技能列表")
    skills = engine.get_program_skills("ID", "IT", "IT-BASIC")
    print(f"找到 {len(skills)} 个技能:")
    for skill in skills:
        print(f"  - {skill['zh_name']} ({skill['english_name']}): {skill['level']}")

    # 测试5: 执行搜索
    print("\n[测试5] 搜索Python编程课程")
    search_request = VocationalSearchRequest(
        country="ID",
        query="Python",
        skill_area="IT",
        program_code="IT-DATA",
        target_audience="advanced",
        max_results=5
    )

    results = engine.search(search_request)
    print(f"\n搜索结果: {results.get('success')}")
    print(f"查询词: {results.get('vocational_search_query')}")
    print(f"结果数: {results.get('total_results', 0)}")
