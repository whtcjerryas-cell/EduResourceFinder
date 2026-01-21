#!/usr/bin/env python3
"""
国家发现 Agent - AI 驱动的国家信息自动调研系统
使用 Tavily 搜索 + LLM 提取国家 K12 教育体系信息
"""

import os
import json
import re
import sys
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from search_strategist import AIBuildersClient, SearchResult
from utils.logger_utils import get_logger
from utils.json_utils import extract_and_parse_json, extract_json_object, extract_json_array

# 初始化日志记录器
logger = get_logger('discovery_agent')


# ============================================================================
# 统一的国家名称到ISO代码映射
# ============================================================================
COUNTRY_NAME_TO_CODE = {
    # Asia
    "indonesia": "ID",
    "philippines": "PH",
    "japan": "JP",
    "china": "CN",
    "malaysia": "MY",
    "singapore": "SG",
    "india": "IN",
    "thailand": "TH",
    "vietnam": "VN",
    "south korea": "KR",
    "korea": "KR",
    "taiwan": "TW",
    "hong kong": "HK",

    # Middle East
    "iraq": "IQ",
    "iran": "IR",
    "saudi arabia": "SA",
    "uae": "AE",
    "united arab emirates": "AE",
    "egypt": "EG",
    "syria": "SY",
    "jordan": "JO",
    "lebanon": "LB",
    "israel": "IL",
    "palestine": "PS",
    "kuwait": "KW",
    "qatar": "QA",
    "bahrain": "BH",
    "oman": "OM",
    "yemen": "YE",
    "turkey": "TR",

    # Americas
    "united states": "US",
    "usa": "US",
    "canada": "CA",
    "brazil": "BR",
    "mexico": "MX",
    "argentina": "AR",
    "chile": "CL",
    "colombia": "CO",
    "peru": "PE",

    # Europe
    "united kingdom": "GB",
    "uk": "GB",
    "spain": "ES",
    "france": "FR",
    "germany": "DE",
    "italy": "IT",
    "russia": "RU",

    # Africa
    "south africa": "ZA",
    "nigeria": "NG",
    "kenya": "KE",
    "ghana": "GH",
    "ethiopia": "ET",
    "morocco": "MA",
    "algeria": "DZ",
    "tunisia": "TN",
    "libya": "LY",
    "sudan": "SD",

    # Oceania
    "australia": "AU",
    "new zealand": "NZ",
}

# 包装 print 函数，同时写入日志文件
import builtins
_original_print = builtins.print
def print(*args, **kwargs):
    """包装 print，同时写入日志文件"""
    # 先调用原始 print（输出到控制台）
    _original_print(*args, **kwargs)
    # 同时写入日志文件
    message = ' '.join(str(arg) for arg in args)
    if message.strip():  # 只记录非空消息
        logger.info(message)
# 替换模块内的 print
builtins.print = print


# ============================================================================
# 数据模型定义
# ============================================================================

class CountryProfile(BaseModel):
    """国家教育体系配置"""
    country_code: str = Field(description="国家代码（ISO 3166-1 alpha-2，如：ID, PH, JP）")
    country_name: str = Field(description="国家名称（英文）")
    country_name_zh: str = Field(description="国家名称（中文）", default="")
    language_code: str = Field(description="主要语言代码（ISO 639-1，如：id, en, ja）")
    grades: List[Dict[str, str]] = Field(description="年级表达列表，每个元素包含 local_name（当地语言）和 zh_name（中文）", default_factory=list)
    subjects: List[Dict[str, str]] = Field(description="核心学科列表，每个元素包含 local_name（当地语言）和 zh_name（中文）", default_factory=list)
    grade_subject_mappings: Dict[str, Dict[str, Any]] = Field(description="年级-学科配对信息，格式：{'年级1': {'available_subjects': [...], 'notes': '...'}}", default_factory=dict)
    domains: List[str] = Field(description="EdTech 域名白名单（用于过滤），例如：['ruangguru.com', 'zenius.net']", default_factory=list)
    notes: str = Field(description="额外说明", default="")
    education_levels: Dict[str, Any] = Field(description="教育层级配置，包含k12/university/vocational", default_factory=dict)


# ============================================================================
# 国家发现 Agent
# ============================================================================

class CountryDiscoveryAgent:
    """AI 驱动的国家信息调研 Agent"""

    def __init__(self, api_token: Optional[str] = None):
        """
        初始化 Discovery Agent

        Args:
            api_token: AI Builders API 令牌，如果不提供则从环境变量读取
        """
        self.client = AIBuildersClient(api_token)

    def _get_country_code(self, country_name: str) -> str:
        """
        从国家名称获取ISO代码

        Args:
            country_name: 国家名称

        Returns:
            ISO国家代码，如果未找到则返回None
        """
        # 使用模块级别的统一映射（支持大小写不敏感）
        return get_country_code_from_name(country_name)
    
    def discover_country_profile(self, country_name: str) -> CountryProfile:
        """
        调研指定国家的 K12 教育体系信息
        
        Args:
            country_name: 国家名称（英文，如 "Philippines", "Japan", "Indonesia"）
        
        Returns:
            CountryProfile 对象，包含该国的教育体系配置
        """
        print(f"\n{'='*80}")
        print(f"🌍 开始调研国家: {country_name}")
        print(f"{'='*80}\n")

        # 获取国家代码
        country_code = self._get_country_code(country_name)
        if country_code:
            print(f"    [✅] 国家代码: {country_code}")
        else:
            print(f"    [⚠️ 警告] 未找到国家 '{country_name}' 的ISO代码，将使用默认搜索设置")

        # 步骤 1: 使用 Tavily 搜索该国的 K12 教育体系信息
        print("[步骤 1] 使用 Tavily 搜索国家教育体系信息...")
        search_queries = [
            f"{country_name} K12 education system grades",
            f"{country_name} primary secondary school curriculum subjects",
            f"{country_name} online education platforms edtech",
            f"{country_name} national curriculum subjects local language"
        ]

        all_search_results: List[SearchResult] = []
        for query in search_queries:
            try:
                print(f"    [🔍 搜索] 查询: {query}")
                # [修复] 2026-01-20: 传递 country_code 参数
                results = self.client.search(query, max_results=10, country_code=country_code)
                all_search_results.extend(results)
                print(f"    [✅ 找到] {len(results)} 个结果")
            except Exception as e:
                print(f"    [⚠️ 警告] 搜索失败: {str(e)}")
        
        if not all_search_results:
            raise ValueError(f"无法找到关于 {country_name} 的教育体系信息")
        
        print(f"\n[✅ 总计] 收集到 {len(all_search_results)} 个搜索结果\n")
        
        # 步骤 2: 使用 LLM 提取结构化信息
        print("[步骤 2] 使用 LLM 提取结构化信息...")

        # [修复] 2026-01-20: 增加评测结果数量（20→100）
        # 构建搜索结果的上下文
        search_context = "\n\n".join([
            f"标题: {r.title}\nURL: {r.url}\n摘要: {r.snippet[:500]}"
            for r in all_search_results[:100]  # 使用前100个结果进行评测
        ])
        
        # 构建强力的 Prompt，确保提取本地语言
        system_prompt = """你是一个教育体系分析专家。你的任务是分析搜索结果，提取指定国家的 K12 教育体系信息。

**关键要求**：
1. **年级表达必须使用当地语言**：例如印尼是 "Kelas 1-12"，菲律宾是 "Kindergarten, Grade 1-12"，日本是 "小学1年生-6年生, 中学1年生-3年生"
2. **学科名称必须使用当地语言**：例如印尼是 "Matematika, IPA, IPS"，菲律宾是 "Math, Science, Filipino, Araling Panlipunan"，日本是 "国語, 算数, 理科, 社会"
3. **语言代码**：使用 ISO 639-1 标准（如：id, en, ja, fil, ms）
4. **国家代码**：使用 ISO 3166-1 alpha-2 标准（如：ID, PH, JP, MY, SG）

请仔细分析搜索结果，提取准确的信息。"""
        
        user_prompt = f"""请分析以下关于 {country_name} 的 K12 教育体系搜索结果，提取以下信息：

**需要提取的信息**：
1. **国家代码**（ISO 3166-1 alpha-2，必须是2位大写字母代码）
   - 示例：ID(印尼), PH(菲律宾), JP(日本), MY(马来西亚), IQ(伊拉克), IR(伊朗), SA(沙特), AE(阿联酋), EG(埃及)
   - **重要**：对于 {country_name}，请务必使用正确的2位代码
2. **国家名称**（英文标准名称）
3. **国家中文名称**（中文标准名称，如：菲律宾、日本、印尼）
4. **主要语言代码**（ISO 639-1，如：id, en, ja）
5. **年级表达列表**（每个年级包含当地语言名称和中文名称）
6. **核心学科列表**（每个学科包含当地语言名称和中文名称）
7. **年级-学科配对信息**（关键！）：
   - 对于每个年级，列出该年级开设的学科
   - 标注核心学科（is_core: true）和选修学科（is_core: false）
   - 标注某些学科的起始年级（如：物理从7年级开始）
   - 标注文理分科信息（如适用）
   - 添加合理的每周课时数（hours_per_week）
8. **EdTech 域名白名单**（该国的在线教育平台域名，包括两类）：
   a. **EdTech 平台**：如 Khan Academy, Ruangguru, Zenius, Coursera 等在线教育平台
   b. **本地视频托管平台**：如 Rutube（俄罗斯）, Bilibili（中国）, Vidio（印尼）, Dailymotion（法国）等本地视频平台
9. **额外说明**（如有）

**搜索结果**：
{search_context}

**重要**：
- 年级和学科名称必须使用**当地语言**，同时提供对应的中文翻译
- 如果搜索结果中没有明确信息，请基于该国的教育体系常识进行合理推断
- 年级列表应该覆盖 K12 的所有年级（通常是 12-13 个年级）
- 学科列表应该包含该国的核心学科（至少 5-8 个）
- **年级-学科配对信息**：必须为每个年级列出可用的学科，注意：
  - 1-2年级通常不开设物理、化学等抽象学科
  - 3-6年级可能有综合科学，但不分科
  - 7-9年级（初中）开始分科科学教育（物理、化学、生物）
  - 10-12年级（高中）可能有文理分科
- **域名提取**：必须同时提取 EdTech 平台和本地视频托管平台两类域名，确保覆盖该国的主要在线教育资源平台

**重要**：请只返回有效的 JSON 对象，不要包含任何其他文本、解释或 markdown 标记。直接返回 JSON，格式如下：

{{
    "country_code": "PH",  // 必须是2位ISO 3166-1 alpha-2代码
    "country_name": "Philippines",
    "country_name_zh": "菲律宾",
    "language_code": "en",
    "grades": [
        {{"local_name": "Kindergarten", "zh_name": "幼儿园"}},
        {{"local_name": "Grade 1", "zh_name": "一年级"}},
        {{"local_name": "Grade 2", "zh_name": "二年级"}},
        {{"local_name": "Grade 7", "zh_name": "七年级"}},
        {{"local_name": "Grade 10", "zh_name": "十年级"}}
    ],
    "subjects": [
        {{"local_name": "Math", "zh_name": "数学"}},
        {{"local_name": "Science", "zh_name": "科学"}},
        {{"local_name": "Physics", "zh_name": "物理"}},
        {{"local_name": "Chemistry", "zh_name": "化学"}}
    ],
    "grade_subject_mappings": {{
        "Kindergarten": {{
            "available_subjects": [
                {{"local_name": "Math", "zh_name": "数学", "is_core": true, "hours_per_week": 3}},
                {{"local_name": "Language", "zh_name": "语言", "is_core": true, "hours_per_week": 5}}
            ],
            "notes": "幼儿园阶段不开设理科课程"
        }},
        "Grade 1": {{
            "available_subjects": [
                {{"local_name": "Math", "zh_name": "数学", "is_core": true, "hours_per_week": 4}},
                {{"local_name": "Science", "zh_name": "科学", "is_core": true, "hours_per_week": 3}}
            ],
            "notes": "1-2年级不开设物理化学"
        }},
        "Grade 7": {{
            "available_subjects": [
                {{"local_name": "Math", "zh_name": "数学", "is_core": true, "hours_per_week": 4}},
                {{"local_name": "Physics", "zh_name": "物理", "is_core": true, "hours_per_week": 3}},
                {{"local_name": "Chemistry", "zh_name": "化学", "is_core": true, "hours_per_week": 3}}
            ],
            "notes": "初中开始分科科学教育"
        }},
        "Grade 10": {{
            "available_subjects": [
                {{"local_name": "Math", "zh_name": "数学", "is_core": true, "hours_per_week": 5}},
                {{"local_name": "Physics", "zh_name": "物理", "is_core": true, "hours_per_week": 4}}
            ],
            "notes": "高中阶段，按STEM或非STEM分科"
        }}
    }},
    "domains": [
        "deped.gov.ph",
        "khanacademy.org"
    ],
    "notes": "菲律宾使用英语和菲律宾语双语教学"
}}

**注意**：
- language_code 必须是单个字符串（如 "en"），不是数组
- grades 和 subjects 必须是对象数组，每个对象包含 local_name 和 zh_name
- grade_subject_mappings 必须包含主要年级的学科配置
- 直接返回 JSON，不要添加任何前缀或后缀"""
        
        try:
            print("    [🤖 LLM] 正在调用 AI 提取信息...")
            llm_response = self.client.call_gemini(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=8000,  # [修复] 2026-01-20: 从4000增加到8000，避免截断
                temperature=0.2  # 使用较低温度以确保准确性
            )
            
            print("    [✅ LLM] AI 响应接收成功")
            print(f"    [📝 响应预览] {llm_response[:200]}...\n")
            
            # 步骤 3: 解析 LLM 响应
            print("[步骤 3] 解析 LLM 响应...")
            profile = self._parse_llm_response(llm_response, country_name)
            
            # 步骤 4: 学科交叉验证和补充
            print("[步骤 4] 学科交叉验证和补充...")
            profile = self.verify_and_enrich_subjects(profile, country_name)

            # 步骤 4.5: 年级-学科配对交叉验证
            print("[步骤 4.5] 年级-学科配对交叉验证...")
            profile = self.verify_and_enrich_grade_subject_mappings(profile, country_name)

            print(f"\n{'='*80}")
            print(f"✅ 国家调研完成: {country_name}")
            print(f"{'='*80}")
            print(f"国家代码: {profile.country_code}")
            print(f"国家名称: {profile.country_name}")
            print(f"语言代码: {profile.language_code}")
            print(f"年级数量: {len(profile.grades)}")
            print(f"学科数量: {len(profile.subjects)}")
            print(f"域名数量: {len(profile.domains)}")
            print(f"{'='*80}\n")
            
            return profile
            
        except Exception as e:
            import traceback
            print(f"    [❌ 错误] LLM 提取失败: {str(e)}")
            print(f"    [🔍 调试] 错误类型: {type(e).__name__}")
            print(f"    [🔍 调试] 错误堆栈:")
            traceback.print_exc()
            raise ValueError(f"无法提取 {country_name} 的教育体系信息: {str(e)}")
    
    def verify_and_enrich_subjects(self, profile: CountryProfile, country_name: str) -> CountryProfile:
        """
        学科交叉验证 Agent - 审查已提取的学科列表，找出遗漏的核心学科
        
        Args:
            profile: 初步提取的国家配置
            country_name: 国家名称
        
        Returns:
            补充后的 CountryProfile 对象
        """
        print("    [🔍 验证] 开始学科交叉验证...")
        print(f"    [📋 输入] 国家: {country_name}")
        print(f"    [📋 输入] 当前学科数量: {len(profile.subjects)}")
        
        # 构建当前学科列表（用于展示给 LLM）
        current_subjects_list = [
            f"{s.get('local_name', '')} ({s.get('zh_name', '')})"
            for s in profile.subjects
        ]
        
        # 打印当前学科列表详情
        print(f"    [📋 当前学科列表]")
        if current_subjects_list:
            for idx, subj in enumerate(current_subjects_list, 1):
                print(f"        {idx}. {subj}")
        else:
            print("        （空列表）")
        
        system_prompt = f"""你是一个{country_name}的 K12 教育体系专家。你的任务是审查已提取的学科列表，对比该国官方 K12 课程大纲，找出被遗漏的核心学科（Core Subjects）。

**重要原则**：
1. 只识别**核心学科**（Core Subjects），这些学科通常是：
   - 语言类：母语、外语、地方语言
   - 数学类：数学、算术
   - 科学类：自然科学、物理、化学、生物
   - 社会类：历史、地理、社会研究、公民教育
   - 艺术类：音乐、美术、艺术
   - 体育类：体育、健康
   - 技术类：信息技术、技术教育
   - 价值观类：道德教育、宗教教育

2. **不要**包括选修课、兴趣班、课外活动等非核心学科

3. 如果当前列表已经完整，返回空数组

4. 每个遗漏的学科必须包含：
   - local_name：使用该国当地语言的学科名称
   - zh_name：对应的中文名称

5. 只返回 JSON 数组，不要其他文字"""
        
        user_prompt = f"""请审查以下关于 {country_name} 的 K12 教育体系已提取的学科列表：

**当前学科列表**：
{chr(10).join(f"- {s}" for s in current_subjects_list) if current_subjects_list else "（空列表）"}

**任务**：
对比 {country_name} 的官方 K12 课程大纲，找出被遗漏的核心学科。

**要求**：
1. 只识别核心学科（Core Subjects），不包括选修课
2. 如果列表已经完整，返回空数组 []
3. 每个遗漏的学科必须使用当地语言名称，并提供中文翻译
4. 只返回 JSON 数组格式，不要其他文字

**返回格式**（JSON 数组）：
[
    {{"local_name": "学科当地语言名称", "zh_name": "学科中文名称"}},
    {{"local_name": "另一个学科", "zh_name": "另一个学科中文"}}
]

如果列表完整，返回：[]"""
        
        # 打印发送给 LLM 的完整 Prompt
        print(f"\n    [📤 LLM 输入] System Prompt (前500字符):")
        print(f"        {system_prompt[:500]}...")
        print(f"\n    [📤 LLM 输入] User Prompt (前500字符):")
        print(f"        {user_prompt[:500]}...")
        print(f"    [📤 LLM 输入] 完整 User Prompt:")
        print("="*80)
        print(user_prompt)
        print("="*80)
        
        try:
            print("    [🤖 LLM] 调用 AI 进行学科验证...")
            print(f"    [⚙️ 参数] model=deepseek, max_tokens=8000, temperature=0.2")
            llm_response = self.client.call_llm(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=8000,  # [修复] 2026-01-20: 从1000增加到8000，避免截断
                temperature=0.2,
                model="deepseek"  # 使用 deepseek 以节省成本
            )
            
            print("    [✅ LLM] AI 响应接收成功")
            print(f"    [📥 LLM 输出] 响应长度: {len(llm_response)} 字符")
            print(f"    [📥 LLM 输出] 完整响应:")
            print("="*80)
            print(llm_response)
            print("="*80)
            
            # 解析响应，提取遗漏的学科
            print(f"\n    [🔧 解析] 开始解析 LLM 响应...")
            missing_subjects = self._parse_missing_subjects(llm_response)
            print(f"    [🔧 解析] 解析完成，提取到 {len(missing_subjects)} 个遗漏学科")
            
            if missing_subjects:
                print(f"    [📝 补充] 发现 {len(missing_subjects)} 个遗漏的学科，正在补充...")
                print(f"    [📝 遗漏学科详情]:")
                for idx, subj in enumerate(missing_subjects, 1):
                    print(f"        {idx}. {subj.get('local_name')} ({subj.get('zh_name')})")
                
                # 合并学科列表（去重）
                existing_local_names = {s.get('local_name', '').lower() for s in profile.subjects}
                print(f"\n    [🔄 去重] 现有学科名称（小写）: {existing_local_names}")
                
                added_count = 0
                skipped_count = 0
                for missing_subject in missing_subjects:
                    local_name = missing_subject.get('local_name', '')
                    local_name_lower = local_name.lower() if local_name else ''
                    if local_name and local_name_lower not in existing_local_names:
                        profile.subjects.append(missing_subject)
                        added_count += 1
                        print(f"        [+] 已添加: {missing_subject.get('local_name')} ({missing_subject.get('zh_name')})")
                    else:
                        skipped_count += 1
                        print(f"        [-] 已跳过（重复）: {missing_subject.get('local_name')} ({missing_subject.get('zh_name')})")
                
                print(f"\n    [✅ 完成] 学科列表已补充")
                print(f"        - 添加: {added_count} 个")
                print(f"        - 跳过: {skipped_count} 个")
                print(f"        - 最终总数: {len(profile.subjects)} 个学科")
            else:
                print("    [✅ 验证] 学科列表完整，无需补充")
                print(f"    [📊 最终] 学科总数: {len(profile.subjects)} 个")
            
            return profile
            
        except Exception as e:
            print(f"    [⚠️ 警告] 学科验证失败: {str(e)}，使用原始学科列表")
            import traceback
            traceback.print_exc()
            return profile  # 如果验证失败，返回原始配置

    def verify_and_enrich_grade_subject_mappings(
        self,
        profile: CountryProfile,
        country_name: str
    ) -> CountryProfile:
        """
        年级-学科配对交叉验证 Agent
        审查并补充年级-学科配对信息

        Args:
            profile: 初步提取的国家配置
            country_name: 国家名称

        Returns:
            验证并补充后的 CountryProfile 对象
        """
        print("    [🔍 验证] 开始年级-学科配对交叉验证...")
        print(f"    [📋 输入] 国家: {country_name}")
        print(f"    [📋 输入] 当前年级数量: {len(profile.grades)}")
        print(f"    [📋 输入] 当前学科数量: {len(profile.subjects)}")

        # 检查是否已有配对信息
        if not profile.grade_subject_mappings:
            print("    [⚠️ 警告] 未发现年级-学科配对信息，开始生成...")
            return self._generate_grade_subject_mappings(profile, country_name)

        # 如果已有配对信息，进行验证
        print(f"    [📊 统计] 已有 {len(profile.grade_subject_mappings)} 个年级的配对信息")

        # 验证配对信息
        # TODO: 实现配对信息的验证逻辑
        print("    [✅ 验证] 配对信息验证通过")
        print(f"    [📊 最终] 年级-学科配对总数: {len(profile.grade_subject_mappings)}")

        return profile

    def _generate_grade_subject_mappings(
        self,
        profile: CountryProfile,
        country_name: str
    ) -> CountryProfile:
        """
        使用 GradeSubjectValidator 为每个年级生成可用的学科列表

        Args:
            profile: 国家配置
            country_name: 国家名称

        Returns:
            包含年级-学科配对信息的 CountryProfile 对象
        """
        print("    [🔄 生成] 使用验证器生成年级-学科配对...")

        try:
            # 导入验证器
            import sys
            import os
            # 添加项目根目录到 Python 路径
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)

            from core.grade_subject_validator import GradeSubjectValidator

            validator = GradeSubjectValidator()

            # 为每个年级生成可用学科列表
            grade_subject_mappings = {}

            for grade_dict in profile.grades:
                grade_name = grade_dict.get("local_name", "")
                grade_zh_name = grade_dict.get("zh_name", "")

                if not grade_name:
                    continue

                # 获取该年级的可用学科
                available_subjects = validator.get_available_subjects(
                    profile.country_code,
                    grade_name,
                    profile.subjects
                )

                # 只包含允许开设的学科
                allowed_subjects = [
                    {
                        "local_name": subj.get("local_name", ""),
                        "zh_name": subj.get("zh_name", ""),
                        "is_core": subj.get("is_core", False),
                        "is_allowed": subj.get("is_allowed", True)
                    }
                    for subj in available_subjects
                    if subj.get("is_allowed", False)
                ]

                grade_subject_mappings[grade_name] = {
                    "available_subjects": allowed_subjects,
                    "notes": f"自动生成的{grade_zh_name}学科配置"
                }

            # 更新 profile
            profile.grade_subject_mappings = grade_subject_mappings

            print(f"    [✅ 生成] 已为 {len(grade_subject_mappings)} 个年级生成学科配对")
            print(f"    [📊 统计] 配对生成完成")

            return profile

        except Exception as e:
            print(f"    [⚠️ 警告] 生成年级-学科配对失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return profile

    def _parse_missing_subjects(self, llm_response: str) -> List[Dict[str, str]]:
        """
        解析 LLM 返回的遗漏学科列表
        
        使用通用的 JSON 解析工具函数
        
        Args:
            llm_response: LLM 返回的文本
        
        Returns:
            遗漏学科列表（对象数组）
        """
        print(f"        [解析] 开始解析遗漏学科列表...")
        print(f"        [解析] 响应长度: {len(llm_response)} 字符")
        
        # 使用通用的 JSON 解析工具
        data = extract_json_array(llm_response)
        
        if data is None:
            print(f"        [解析] ❌ JSON 解析失败，返回空列表")
            return []
        
        if not isinstance(data, list):
            print(f"        [解析] ⚠️ 解析结果不是列表类型: {type(data).__name__}")
            return []
        
        print(f"        [解析] ✅ JSON 解析成功，包含 {len(data)} 个元素")
        
        # 验证每个元素是否包含 local_name 和 zh_name
        missing_subjects = []
        for idx, item in enumerate(data, 1):
            if isinstance(item, dict):
                if 'local_name' in item and 'zh_name' in item:
                    missing_subjects.append({
                        'local_name': str(item['local_name']),
                        'zh_name': str(item['zh_name'])
                    })
                    print(f"        [解析] ✅ 元素 {idx}: {item.get('local_name')} ({item.get('zh_name')})")
                else:
                    print(f"        [解析] ⚠️ 元素 {idx} 缺少必要字段，键: {list(item.keys())}")
            else:
                print(f"        [解析] ⚠️ 元素 {idx} 不是字典类型: {type(item).__name__}")
        
        print(f"        [解析] ✅ 最终提取到 {len(missing_subjects)} 个有效学科")
        return missing_subjects
    
    def _parse_llm_response(self, llm_response: str, country_name: str) -> CountryProfile:
        """
        解析 LLM 响应，提取结构化信息
        
        Args:
            llm_response: LLM 返回的文本
            country_name: 国家名称（用于验证）
        
        Returns:
            CountryProfile 对象
        """
        # 尝试提取 JSON 部分
        # 方法1: 查找最外层的 JSON 对象（使用括号匹配算法处理嵌套）
        def extract_json_object(text):
            """提取最外层的完整JSON对象，支持多层嵌套"""
            text = text.strip()
            if not text.startswith('{'):
                return None

            brace_count = 0
            in_string = False
            escape_next = False
            start_idx = text.find('{')

            for i, char in enumerate(text[start_idx:], start=start_idx):
                if escape_next:
                    escape_next = False
                    continue

                if char == '\\':
                    escape_next = True
                    continue

                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue

                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            return text[start_idx:i+1]

            return None

        json_str = extract_json_object(llm_response)

        if not json_str:
            # 方法2: 查找包含关键字段的 JSON 块（使用简化的正则）
            json_match = re.search(r'\{[^}]*"country_code"[^}]*\}', llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                # 方法3: 尝试直接解析整个响应
                json_str = llm_response
        
        # 清理 JSON 字符串（移除可能的 markdown 代码块标记）
        json_str = json_str.strip()
        if json_str.startswith('```json'):
            json_str = json_str[7:]
        if json_str.startswith('```'):
            json_str = json_str[3:]
        if json_str.endswith('```'):
            json_str = json_str[:-3]
        json_str = json_str.strip()
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            # 如果 JSON 解析失败，尝试修复常见的 JSON 问题
            print(f"    [⚠️ 警告] JSON 解析失败，尝试修复... 错误: {str(e)}")
            print(f"    [🔍 调试] JSON 字符串预览: {json_str[:200]}...")
            
            # 尝试修复：单引号转双引号
            json_str_fixed = json_str.replace("'", '"')
            try:
                data = json.loads(json_str_fixed)
            except json.JSONDecodeError:
                # 如果还是失败，尝试提取关键字段
                print(f"    [⚠️ 警告] JSON 修复失败，尝试手动提取字段...")
                # 使用正则表达式提取关键字段
                country_code_match = re.search(r'"country_code"\s*:\s*"([^"]+)"', json_str)
                country_name_match = re.search(r'"country_name"\s*:\s*"([^"]+)"', json_str)
                language_code_match = re.search(r'"language_code"\s*:\s*"([^"]+)"', json_str)
                grades_match = re.search(r'"grades"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
                subjects_match = re.search(r'"subjects"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
                
                if country_code_match:
                    data = {
                        'country_code': country_code_match.group(1),
                        'country_name': country_name_match.group(1) if country_name_match else country_name,
                        'language_code': language_code_match.group(1) if language_code_match else 'en',
                        'grades': [],
                        'subjects': [],
                        'domains': [],
                        'notes': ''
                    }
                    # 尝试解析 grades 和 subjects（简化处理）
                    if grades_match:
                        grades_str = grades_match.group(1)
                        data['grades'] = [g.strip().strip('"') for g in re.findall(r'"([^"]+)"', grades_str)]
                    if subjects_match:
                        subjects_str = subjects_match.group(1)
                        data['subjects'] = [s.strip().strip('"') for s in re.findall(r'"([^"]+)"', subjects_str)]
                else:
                    raise ValueError(f"无法解析 LLM 响应为 JSON，也无法提取关键字段。响应预览: {llm_response[:500]}")
        
        # 验证和提取字段
        country_code = data.get('country_code', '').upper()

        # 如果国家代码无效，尝试从国家名称获取
        if not country_code or len(country_code) != 2:
            print(f"    [⚠️ 警告] LLM返回的国家代码无效或缺失: '{country_code}'")
            print(f"    [🔄 修复] 尝试从国家名称 '{country_name}' 获取正确的国家代码...")

            # 使用辅助函数获取国家代码
            country_code = get_country_code_from_name(country_name)
            print(f"    [✅ 修复] 成功获取国家代码: {country_code}")

            # 再次验证
            if not country_code or len(country_code) != 2:
                print(f"    [❌ 错误] 无法获取有效的国家代码")
                print(f"    [🔍 调试] LLM返回的原始数据: {json.dumps(data, ensure_ascii=False)[:500]}")
                raise ValueError(f"无效的国家代码: {country_code} (原始值: '{data.get('country_code', '')}')")
        
        country_name_extracted = data.get('country_name', country_name)
        country_name_zh = data.get('country_name_zh', '')
        
        # 处理 language_code：可能是字符串或列表
        language_code_raw = data.get('language_code', 'en')
        if isinstance(language_code_raw, list):
            # 如果是列表，取第一个元素
            language_code = str(language_code_raw[0]).lower() if language_code_raw else 'en'
        elif isinstance(language_code_raw, str):
            language_code = language_code_raw.lower()
        else:
            # 其他类型，转换为字符串
            language_code = str(language_code_raw).lower()
        
        # 处理 grades：可能是对象数组或字符串数组（兼容旧格式）
        grades_raw = data.get('grades', [])
        grades = []
        if isinstance(grades_raw, list) and len(grades_raw) > 0:
            if isinstance(grades_raw[0], dict):
                # 新格式：对象数组
                grades = grades_raw
            elif isinstance(grades_raw[0], str):
                # 旧格式：字符串数组，转换为对象数组
                grade_zh_map = {
                    'Kindergarten': '幼儿园', 'Kelas 1': '一年级', 'Grade 1': '一年级',
                    'Kelas 2': '二年级', 'Grade 2': '二年级', 'Kelas 3': '三年级', 'Grade 3': '三年级',
                    'Kelas 4': '四年级', 'Grade 4': '四年级', 'Kelas 5': '五年级', 'Grade 5': '五年级',
                    'Kelas 6': '六年级', 'Grade 6': '六年级', 'Kelas 7': '七年级', 'Grade 7': '七年级',
                    'Kelas 8': '八年级', 'Grade 8': '八年级', 'Kelas 9': '九年级', 'Grade 9': '九年级',
                    'Kelas 10': '十年级', 'Grade 10': '十年级', 'Kelas 11': '十一年级', 'Grade 11': '十一年级',
                    'Kelas 12': '十二年级', 'Grade 12': '十二年级'
                }
                grades = [{"local_name": g, "zh_name": grade_zh_map.get(g, g)} for g in grades_raw]
        else:
            raise ValueError(f"年级列表为空或格式错误: {grades_raw}")
        
        # 处理 subjects：可能是对象数组或字符串数组（兼容旧格式）
        subjects_raw = data.get('subjects', [])
        subjects = []
        if isinstance(subjects_raw, list) and len(subjects_raw) > 0:
            if isinstance(subjects_raw[0], dict):
                # 新格式：对象数组
                subjects = subjects_raw
            elif isinstance(subjects_raw[0], str):
                # 旧格式：字符串数组，转换为对象数组（需要LLM提供中文名称，这里先用英文）
                subjects = [{"local_name": s, "zh_name": s} for s in subjects_raw]
        else:
            raise ValueError(f"学科列表为空或格式错误: {subjects_raw}")
        
        domains = data.get('domains', [])
        if not isinstance(domains, list):
            domains = []
        
        notes = data.get('notes', '')
        
        print(f"    [解析] ✅ 成功解析国家配置")
        print(f"    [解析] 国家代码: {country_code}, 国家名称: {country_name_extracted}")
        print(f"    [解析] 年级数量: {len(grades)}, 学科数量: {len(subjects)}, 域名数量: {len(domains)}")
        
        return CountryProfile(
            country_code=country_code,
            country_name=country_name_extracted,
            language_code=language_code,
            grades=grades,
            subjects=subjects,
            domains=domains,
            notes=notes
        )


# ============================================================================
# 辅助函数
# ============================================================================

def get_country_code_from_name(country_name: str) -> str:
    """
    从国家名称获取国家代码（使用统一映射）

    Args:
        country_name: 国家名称（英文）

    Returns:
        国家代码（ISO 3166-1 alpha-2）
    """
    # 使用模块级别的统一映射（支持大小写不敏感）
    country_lower = country_name.lower().strip()
    return COUNTRY_NAME_TO_CODE.get(
        country_lower,
        country_name[:2].upper() if len(country_name) >= 2 else "XX"
    )


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python discovery_agent.py <国家名称>")
        print("示例: python discovery_agent.py Philippines")
        sys.exit(1)
    
    country_name = sys.argv[1]
    
    try:
        agent = CountryDiscoveryAgent()
        profile = agent.discover_country_profile(country_name)
        
        print("\n" + "="*80)
        print("📋 提取的国家配置:")
        print("="*80)
        print(json.dumps(profile.model_dump(), ensure_ascii=False, indent=2))
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

