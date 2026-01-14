#!/usr/bin/env python3
"""
大学搜索引擎 - 专门用于大学教育资源的搜索
支持按大学、学院、专业、课程进行搜索
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
    from search_engine_v2 import SearchEngineV2, UniversitySearchRequest as V2UniRequest
except ImportError:
    # 如果search_engine_v2不可用，使用占位符
    SearchEngineV2 = None
    V2UniRequest = None
    print("[⚠️ 警告] search_engine_v2不可用，部分功能可能受限")


# ============================================================================
# 数据模型
# ============================================================================

class UniversitySearchRequest(BaseModel):
    """大学教育搜索请求"""
    # 基本信息
    country: str = Field(description="国家代码（如：ID）")
    query: str = Field(description="搜索查询（关键词或主题）")

    # 大学信息
    university_code: Optional[str] = Field(description="大学代码（如：UI, ITB）", default=None)
    faculty_code: Optional[str] = Field(description="学院代码（如：FIK, FT）", default=None)
    major_code: Optional[str] = Field(description="专业代码（如：TI-SKRI, TE-SKRI）", default=None)

    # 课程信息
    subject_code: Optional[str] = Field(description="课程代码（如：CS101）", default=None)
    subject_name: Optional[str] = Field(description="课程名称", default=None)
    year: Optional[int] = Field(description="学年（1-4）", default=None)
    semester: Optional[int] = Field(description="学期（1-2）", default=None)

    # 搜索选项
    max_results: int = Field(description="最大结果数", default=10)
    domains: List[str] = Field(description="域名白名单", default_factory=list)


class UniversityConfig(BaseModel):
    """大学配置"""
    country_code: str
    country_name: str
    country_name_zh: str
    education_levels: Dict[str, Any]


# ============================================================================
# 大学搜索引擎
# ============================================================================

class UniversitySearchEngine:
    """大学教育资源搜索引擎"""

    def __init__(self, config_file: str = "data/config/indonesia_universities.json"):
        """
        初始化大学搜索引擎

        Args:
            config_file: 大学配置文件路径
        """
        self.config_file = config_file
        self.config = self._load_config()
        self.base_engine = SearchEngineV2() if SearchEngineV2 else None

    def _load_config(self) -> Optional[UniversityConfig]:
        """加载大学配置"""
        try:
            if not os.path.exists(self.config_file):
                print(f"[⚠️ 警告] 大学配置文件不存在: {self.config_file}")
                return None

            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return UniversityConfig(**data)
        except Exception as e:
            print(f"[⚠️ 警告] 加载大学配置失败: {str(e)}")
            return None

    def _get_university_info(self, university_code: str) -> Optional[Dict[str, Any]]:
        """获取指定大学的信息"""
        if not self.config:
            return None

        universities = self.config.education_levels.get("university", {}).get("undergraduate", {}).get("universities", [])

        for uni in universities:
            if uni.get("university_code") == university_code:
                return uni

        return None

    def _get_faculty_info(self, university_code: str, faculty_code: str) -> Optional[Dict[str, Any]]:
        """获取指定学院的信息"""
        uni = self._get_university_info(university_code)
        if not uni:
            return None

        faculties = uni.get("faculties", [])
        for faculty in faculties:
            if faculty.get("faculty_code") == faculty_code:
                return faculty

        return None

    def _get_major_info(self, university_code: str, faculty_code: str, major_code: str) -> Optional[Dict[str, Any]]:
        """获取指定专业信息"""
        faculty = self._get_faculty_info(university_code, faculty_code)
        if not faculty:
            return None

        majors = faculty.get("majors", [])
        for major in majors:
            if major.get("major_code") == major_code:
                return major

        return None

    def _get_subjects_for_major(
        self,
        university_code: str,
        faculty_code: str,
        major_code: str,
        year: Optional[int] = None,
        semester: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取专业的课程列表"""
        major = self._get_major_info(university_code, faculty_code, major_code)
        if not major:
            return []

        subjects = major.get("subjects", [])

        # 按学年/学期筛选
        if year is not None:
            subjects = [s for s in subjects if s.get("year") == year]

        if semester is not None:
            subjects = [s for s in subjects if s.get("semester") == semester]

        return subjects

    def _generate_search_query(self, request: UniversitySearchRequest) -> str:
        """
        生成大学级别的搜索查询

        策略：
        1. 如果指定了课程名称，使用课程名称（本地/英文/中文）
        2. 如果指定了专业，使用专业名称 + 课程关键词
        3. 如果指定了学院，使用学院名称 + 课程关键词
        4. 如果只指定了大学，使用大学名称 + 课程关键词
        """
        query_parts = []

        # 构建上下文信息
        context_parts = []

        if request.subject_code:
            # 如果指定了课程代码，获取课程信息
            subject_info = None
            if request.university_code and request.faculty_code and request.major_code:
                subjects = self._get_subjects_for_major(
                    request.university_code,
                    request.faculty_code,
                    request.major_code,
                    request.year,
                    request.semester
                )
                for subj in subjects:
                    if subj.get("subject_code") == request.subject_code:
                        subject_info = subj
                        break

            if subject_info:
                # 使用课程的三语名称
                names = [
                    subject_info.get("local_name", ""),
                    subject_info.get("english_name", ""),
                    subject_info.get("zh_name", "")
                ]
                # 使用第一个非空名称
                for name in names:
                    if name:
                        query_parts.append(name)
                        break
            else:
                # 如果找不到课程信息，使用课程代码
                query_parts.append(request.subject_code)

        # 添加专业上下文
        if request.major_code and request.faculty_code and request.university_code:
            major = self._get_major_info(request.university_code, request.faculty_code, request.major_code)
            if major:
                major_names = [
                    major.get("local_name", ""),
                    major.get("english_name", ""),
                    major.get("zh_name", "")
                ]
                for name in major_names:
                    if name:
                        context_parts.append(name)
                        break

        # 添加学院上下文
        if request.faculty_code and request.university_code:
            faculty = self._get_faculty_info(request.university_code, request.faculty_code)
            if faculty:
                faculty_names = [
                    faculty.get("local_name", ""),
                    faculty.get("english_name", ""),
                    faculty.get("zh_name", "")
                ]
                for name in faculty_names:
                    if name:
                        context_parts.append(name)
                        break

        # 添加大学上下文
        if request.university_code:
            uni = self._get_university_info(request.university_code)
            if uni:
                uni_names = [
                    uni.get("local_name", ""),
                    uni.get("english_name", ""),
                    uni.get("zh_name", "")
                ]
                for name in uni_names:
                    if name:
                        context_parts.append(name)
                        break

        # 如果没有添加任何查询词，使用用户提供的query
        if not query_parts and request.query:
            query_parts.append(request.query)

        # 组合查询：上下词 + 主要查询词
        # 这样可以更精确地搜索到相关资源
        if context_parts and query_parts:
            # 上下文在前，查询词在后
            combined_query = " ".join(context_parts) + " " + " ".join(query_parts)
        elif context_parts:
            combined_query = " ".join(context_parts)
            if request.query:
                combined_query += " " + request.query
        elif query_parts:
            combined_query = " ".join(query_parts)
        else:
            combined_query = request.query

        return combined_query.strip()

    def _get_context_info(self, request: UniversitySearchRequest) -> Dict[str, Any]:
        """获取搜索上下文信息（用于返回给前端）"""
        context = {
            "country": request.country,
            "country_name": "",
            "university": None,
            "faculty": None,
            "major": None,
            "subject": None
        }

        # 获取国家名称
        if self.config:
            context["country_name"] = self.config.country_name_zh

        # 获取大学信息
        if request.university_code:
            uni = self._get_university_info(request.university_code)
            if uni:
                context["university"] = {
                    "code": uni.get("university_code"),
                    "local_name": uni.get("local_name"),
                    "zh_name": uni.get("zh_name"),
                    "english_name": uni.get("english_name")
                }

        # 获取学院信息
        if request.faculty_code and request.university_code:
            faculty = self._get_faculty_info(request.university_code, request.faculty_code)
            if faculty:
                context["faculty"] = {
                    "code": faculty.get("faculty_code"),
                    "local_name": faculty.get("local_name"),
                    "zh_name": faculty.get("zh_name"),
                    "english_name": faculty.get("english_name")
                }

        # 获取专业信息
        if request.major_code and request.faculty_code and request.university_code:
            major = self._get_major_info(request.university_code, request.faculty_code, request.major_code)
            if major:
                context["major"] = {
                    "code": major.get("major_code"),
                    "local_name": major.get("local_name"),
                    "zh_name": major.get("zh_name"),
                    "english_name": major.get("english_name"),
                    "degree": major.get("degree")
                }

        # 获取课程信息
        if request.subject_code and request.major_code and request.faculty_code and request.university_code:
            subjects = self._get_subjects_for_major(
                request.university_code,
                request.faculty_code,
                request.major_code,
                request.year,
                request.semester
            )
            for subj in subjects:
                if subj.get("subject_code") == request.subject_code:
                    context["subject"] = {
                        "code": subj.get("subject_code"),
                        "local_name": subj.get("local_name"),
                        "zh_name": subj.get("zh_name"),
                        "english_name": subj.get("english_name"),
                        "year": subj.get("year"),
                        "semester": subj.get("semester"),
                        "credits": subj.get("credits")
                    }
                    break

        return context

    def search(self, request: UniversitySearchRequest) -> Dict[str, Any]:
        """
        执行大学教育资源搜索

        Args:
            request: 大学搜索请求

        Returns:
            搜索结果，包含：
            - success: 是否成功
            - context: 搜索上下文（大学、学院、专业、课程信息）
            - query: 实际使用的搜索词
            - results: 搜索结果列表
            - total_results: 总结果数
        """
        print(f"\n{'='*80}")
        print(f"🎓 大学教育资源搜索")
        print(f"{'='*80}")

        # 生成搜索查询
        search_query = self._generate_search_query(request)
        print(f"\n[搜索查询] {search_query}")

        # 获取上下文信息
        context = self._get_context_info(request)

        # 打印搜索上下文
        if context.get("university"):
            print(f"[大学] {context['university']['zh_name']}")
        if context.get("faculty"):
            print(f"[学院] {context['faculty']['zh_name']}")
        if context.get("major"):
            print(f"[专业] {context['major']['zh_name']} ({context['major']['degree']})")
        if context.get("subject"):
            subj = context['subject']
            print(f"[课程] {subj['zh_name']} (第{subj['year']}学年 第{subj['semester']}学期)")

        # 构建基础搜索引擎请求
        # 注意：这里我们复用SearchEngineV2，但使用自定义的查询词
        if V2UniRequest is None:
            # 如果V2UniRequest不可用，直接返回上下文信息
            print(f"[⚠️ 警告] V2UniRequest不可用，返回上下文信息")

            return {
                "success": True,
                "context": context,
                "university_search_query": search_query,
                "results": [],
                "total_results": 0,
                "message": "V2UniRequest不可用，仅返回上下文信息"
            }

        base_request = V2UniRequest(
            country=request.country,
            query=search_query,
            education_level="university",  # 指定为大学层级
            domains=request.domains if request.domains else None,
            max_results=request.max_results
        )

        # 执行搜索
        print(f"\n[执行搜索]...")
        try:
            if SearchEngineV2 is None or self.base_engine is None:
                # 如果基础引擎不可用，返回模拟结果
                print(f"[⚠️ 警告] 基础搜索引擎不可用，返回上下文信息")

                return {
                    "success": True,
                    "context": context,
                    "university_search_query": search_query,
                    "results": [],
                    "total_results": 0,
                    "message": "基础搜索引擎不可用，仅返回上下文信息"
                }

            results = self.base_engine.search_university(base_request)

            # 添加大学教育的上下文信息
            results["context"] = context
            results["university_search_query"] = search_query

            print(f"\n[搜索完成] 找到 {results.get('total_results', 0)} 个结果")
            print(f"{'='*80}\n")

            return results

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

    def get_available_universities(self, country_code: str) -> List[Dict[str, Any]]:
        """
        获取指定国家的所有大学列表

        Args:
            country_code: 国家代码

        Returns:
            大学列表
        """
        if not self.config or self.config.country_code != country_code:
            return []

        universities = self.config.education_levels.get("university", {}).get("undergraduate", {}).get("universities", [])

        return [
            {
                "code": uni.get("university_code"),
                "local_name": uni.get("local_name"),
                "zh_name": uni.get("zh_name"),
                "english_name": uni.get("english_name"),
                "location": uni.get("location"),
                "website": uni.get("website"),
                "faculty_count": len(uni.get("faculties", []))
            }
            for uni in universities
        ]

    def get_available_faculties(self, country_code: str, university_code: str) -> List[Dict[str, Any]]:
        """
        获取指定大学的所有学院列表

        Args:
            country_code: 国家代码
            university_code: 大学代码

        Returns:
            学院列表
        """
        if not self.config or self.config.country_code != country_code:
            return []

        uni = self._get_university_info(university_code)
        if not uni:
            return []

        faculties = uni.get("faculties", [])

        return [
            {
                "code": faculty.get("faculty_code"),
                "local_name": faculty.get("local_name"),
                "zh_name": faculty.get("zh_name"),
                "english_name": faculty.get("english_name"),
                "major_count": len(faculty.get("majors", []))
            }
            for faculty in faculties
        ]

    def get_available_majors(
        self,
        country_code: str,
        university_code: str,
        faculty_code: str
    ) -> List[Dict[str, Any]]:
        """
        获取指定学院的所有专业列表

        Args:
            country_code: 国家代码
            university_code: 大学代码
            faculty_code: 学院代码

        Returns:
            专业列表
        """
        if not self.config or self.config.country_code != country_code:
            return []

        faculty = self._get_faculty_info(university_code, faculty_code)
        if not faculty:
            return []

        majors = faculty.get("majors", [])

        return [
            {
                "code": major.get("major_code"),
                "local_name": major.get("local_name"),
                "zh_name": major.get("zh_name"),
                "english_name": major.get("english_name"),
                "degree": major.get("degree"),
                "subject_count": len(major.get("subjects", []))
            }
            for major in majors
        ]

    def get_available_subjects(
        self,
        country_code: str,
        university_code: str,
        faculty_code: str,
        major_code: str,
        year: Optional[int] = None,
        semester: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取指定专业的课程列表

        Args:
            country_code: 国家代码
            university_code: 大学代码
            faculty_code: 学院代码
            major_code: 专业代码
            year: 学年（可选）
            semester: 学期（可选）

        Returns:
            课程列表
        """
        if not self.config or self.config.country_code != country_code:
            return []

        subjects = self._get_subjects_for_major(
            university_code,
            faculty_code,
            major_code,
            year,
            semester
        )

        return [
            {
                "code": subj.get("subject_code"),
                "local_name": subj.get("local_name"),
                "zh_name": subj.get("zh_name"),
                "english_name": subj.get("english_name"),
                "year": subj.get("year"),
                "semester": subj.get("semester"),
                "credits": subj.get("credits")
            }
            for subj in subjects
        ]


# ============================================================================
# 辅助函数
# ============================================================================

def get_university_search_engine() -> UniversitySearchEngine:
    """获取大学搜索引擎实例"""
    return UniversitySearchEngine()


if __name__ == "__main__":
    # 测试代码
    import sys

    print("="*80)
    print("大学搜索引擎测试")
    print("="*80)

    engine = UniversitySearchEngine()

    # 测试1: 获取大学列表
    print("\n[测试1] 获取大学列表")
    universities = engine.get_available_universities("ID")
    print(f"找到 {len(universities)} 所大学:")
    for uni in universities:
        print(f"  - {uni['zh_name']} ({uni['code']}): {uni['faculty_count']}个学院")

    # 测试2: 获取学院列表
    print("\n[测试2] 获取UI的学院列表")
    faculties = engine.get_available_faculties("ID", "UI")
    print(f"找到 {len(faculties)} 个学院:")
    for faculty in faculties:
        print(f"  - {faculty['zh_name']} ({faculty['code']}): {faculty['major_count']}个专业")

    # 测试3: 获取专业列表
    print("\n[测试3] 获取FIK的专业列表")
    majors = engine.get_available_majors("ID", "UI", "FIK")
    print(f"找到 {len(majors)} 个专业:")
    for major in majors:
        print(f"  - {major['zh_name']} ({major['code']}): {major['degree']}, {major['subject_count']}门课程")

    # 测试4: 获取课程列表
    print("\n[测试4] 获取TI-SKRI的课程列表")
    subjects = engine.get_available_subjects("ID", "UI", "FIK", "TI-SKRI")
    print(f"找到 {len(subjects)} 门课程:")
    for subj in subjects:
        print(f"  - {subj['zh_name']} ({subj['code']}): 第{subj['year']}学年, {subj['credits']}学分")

    # 测试5: 执行搜索
    print("\n[测试5] 搜索算法课程")
    search_request = UniversitySearchRequest(
        country="ID",
        query="Algoritma",
        university_code="UI",
        faculty_code="FIK",
        major_code="TI-SKRI",
        subject_code="CS101",
        max_results=5
    )

    results = engine.search(search_request)
    print(f"\n搜索结果: {results.get('success')}")
    print(f"查询词: {results.get('university_search_query')}")
    print(f"结果数: {results.get('total_results', 0)}")
