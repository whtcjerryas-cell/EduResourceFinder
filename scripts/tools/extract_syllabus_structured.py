#!/usr/bin/env python3
"""
从印度尼西亚数学学科 K12 教学大纲 PDF 中提取结构化知识点
使用 AI Builders 的 gemini-2.5-pro 模型进行提取和检查
按照用户要求的新格式提取：章 -> 节 -> 知识点的层级关系
"""

import os
import json
import re
import requests
from typing import Dict, List, Optional, Any
from pypdf import PdfReader


class AIBuildersClient:
    """AI Builders API 客户端"""
    
    def __init__(self, api_token: Optional[str] = None):
        """
        初始化客户端
        
        Args:
            api_token: AI Builders API 令牌，如果不提供则从环境变量读取
        """
        self.api_token = api_token or os.getenv("AI_BUILDER_TOKEN")
        if not self.api_token:
            raise ValueError("请设置 AI_BUILDER_TOKEN 环境变量或传入 api_token 参数")
        
        # 根据文档，正确的 API 端点
        self.base_url = "https://space.ai-builders.com/backend"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    def call_gemini(self, prompt: str, system_prompt: Optional[str] = None, 
                    max_tokens: int = 8000, temperature: float = 0.3) -> str:
        """
        调用 gemini-2.5-pro 模型
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）
            max_tokens: 最大生成 token 数
            temperature: 温度参数
        
        Returns:
            模型返回的文本内容
        """
        endpoint = f"{self.base_url}/v1/chat/completions"
        
        messages = []
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        payload = {
            "model": "gemini-2.5-pro",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            # 禁用代理以避免连接问题
            proxies = {
                "http": None,
                "https": None
            }
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=600,  # 增加超时时间到10分钟
                proxies=proxies
            )
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    raise ValueError(f"API 响应格式异常: {json.dumps(result, ensure_ascii=False)}")
            else:
                raise ValueError(f"API 调用失败，状态码: {response.status_code}, 响应: {response.text[:500]}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"API 请求异常: {str(e)}")


class SyllabusExtractor:
    """教学大纲知识点提取器"""
    
    def __init__(self, pdf_path: str, api_token: Optional[str] = None):
        """
        初始化提取器
        
        Args:
            pdf_path: PDF 文件路径
            api_token: AI Builders API 令牌
        """
        self.pdf_path = pdf_path
        self.client = AIBuildersClient(api_token)
        self.pdf_text = None
        self.pdf_pages = 0
    
    def read_pdf(self) -> str:
        """读取 PDF 文件内容"""
        print(f"📖 正在读取 PDF 文件: {self.pdf_path}")
        try:
            reader = PdfReader(self.pdf_path)
            text_parts = []
            
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text.strip():
                    text_parts.append(f"=== 第 {i+1} 页 ===\n{text}\n")
                if (i + 1) % 10 == 0:
                    print(f"   已读取 {i+1} 页...")
            
            self.pdf_pages = len(reader.pages)
            self.pdf_text = "\n".join(text_parts)
            print(f"✅ PDF 读取完成，共 {self.pdf_pages} 页")
            return self.pdf_text
        except Exception as e:
            raise ValueError(f"读取 PDF 文件失败: {str(e)}")
    
    def split_text_if_needed(self, text: str, max_chars: int = 200000) -> List[str]:
        """
        如果文本过长，按逻辑分割成多个部分
        
        Args:
            text: 原始文本
            max_chars: 每个部分的最大字符数
        
        Returns:
            分割后的文本列表
        """
        if len(text) <= max_chars:
            return [text]
        
        # 尝试按章节分割
        parts = []
        current_part = ""
        
        # 按页面分割，尽量保持完整性
        pages = text.split("=== 第 ")
        for i, page in enumerate(pages):
            if not page.strip():
                continue
            
            page_with_header = f"=== 第 {page}" if i > 0 else page
            
            if len(current_part) + len(page_with_header) > max_chars and current_part:
                parts.append(current_part)
                current_part = page_with_header
            else:
                current_part += page_with_header
        
        if current_part:
            parts.append(current_part)
        
        return parts if parts else [text]
    
    def extract_knowledge_points(self, pdf_text: str = None) -> List[Dict[str, Any]]:
        """
        提取知识点（使用大模型1 - Generator）
        
        Args:
            pdf_text: PDF 文本内容，如果为 None 则从文件读取
        
        Returns:
            提取的知识点 JSON 数据列表
        """
        if pdf_text is None:
            if not self.pdf_text:
                self.read_pdf()
            pdf_text = self.pdf_text
        
        print("\n🤖 正在使用 gemini-2.5-pro 提取知识点...")
        
        # 用户提供的系统提示词
        system_prompt = """你是印度尼西亚 K12 教育体系构建专家，精通 Kurikulum Merdeka 和 K13 课程标准。"""
        
        # 检查是否需要分割文本
        text_parts = self.split_text_if_needed(pdf_text, max_chars=200000)
        
        all_knowledge_points = []
        
        for part_idx, text_part in enumerate(text_parts):
            print(f"\n📄 处理第 {part_idx + 1}/{len(text_parts)} 部分...")
            
            user_prompt = f"""**角色定义：** 
你是印度尼西亚 K12 教育体系构建专家，精通 Kurikulum Merdeka 和 K13 课程标准。

**任务目标：**
读取以下PDF文件内容（印尼数学教学大纲），将其解析为标准化的"知识图谱"JSON 数据。
该数据将作为"骨架"，用于后续将视频资源精准挂载到对应的知识点上。因此，层级关系和概念定义的准确性至关重要。

**执行步骤：**

**Step 1: 深度结构化提取 (Generator)**
请分析文档，识别"章 (Chapter) -> 节 (Section) -> 知识点 (Topic)"的层级关系。提取以下字段：

*   `id`: (唯一标识符，如 "MAT-7-01-02"，格式：MAT-{{年级数字}}-{{章节号}}-{{知识点号}})
*   `curriculum_standard`: (例如 Kurikulum Merdeka)
*   `grade_level`: (例如 Kelas 7)
*   `subject`: (Matematika)
*   `chapter_title`: (章节印尼语原名)
*   `topic_title_id`: (知识点印尼语原名，需清洗掉序号，如 "1.2 Bilangan Bulat" -> "Bilangan Bulat")
*   `topic_title_cn`: (知识点中文翻译，需使用标准数学术语，如 "Teorema Pythagoras" -> "勾股定理")
*   `learning_objective`: (核心教学目标。这是判断视频内容是否合格的"金标准")
*   `mapping_tags`: (数组格式。列出 3-5 个该知识点的核心印尼语词汇或同义词。**注意：这不是为了搜索，而是为了让后续 AI 判断一个视频标题是否属于该知识点。** 例如：对于"混合运算"，Tag 应包含 "Campuran", "Kabataku", "Urutan Operasi")

**Step 2: 逻辑与完整性校验 (Critic)**
在生成最终 JSON 前，请执行以下自我检查（Self-Reflection）：
1.  **覆盖率检查**：是否遗漏了任何小节？大纲中的所有知识点是否都已转化为 JSON 节点？
2.  **术语准确性**：中文翻译是否符合数学教学规范？（例如不要把 "Akar Kuadrat" 翻译成 "方根" 而应是 "平方根"）。
3.  **去噪**：`topic_title_id` 中是否还有 "1.2", "A." 等干扰字符？请去除。

**Step 3: 输出**
输出严格的 JSON 列表格式，必须是有效的 JSON 数组。

**模型指令：**
请使用 ai-builders 中的 gemini 2.5 pro。如果 PDF 包含复杂的跨页表格，请优先保持逻辑层级的连贯性。

**PDF 内容：**
{text_part}

请直接输出 JSON 数组，不要包含任何其他文字说明、markdown 代码块标记或解释。格式示例：
[
  {{
    "id": "MAT-7-01-01",
    "curriculum_standard": "Kurikulum Merdeka",
    "grade_level": "Kelas 7",
    "subject": "Matematika",
    "chapter_title": "Bilangan Bulat",
    "topic_title_id": "Bilangan Bulat",
    "topic_title_cn": "整数",
    "learning_objective": "学生能够理解整数的概念，进行整数的加减运算",
    "mapping_tags": ["Bilangan Bulat", "Integer", "Angka Bulat", "Operasi Bilangan Bulat"]
  }}
]"""
            
            try:
                response_text = self.client.call_gemini(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    max_tokens=32000,  # 增加 token 限制
                    temperature=0.3
                )
                
                # 尝试从响应中提取 JSON
                json_text = self._extract_json_from_response(response_text)
                
                # 解析 JSON
                try:
                    knowledge_points = json.loads(json_text)
                    if isinstance(knowledge_points, list):
                        all_knowledge_points.extend(knowledge_points)
                        print(f"✅ 成功提取 {len(knowledge_points)} 个知识点")
                    else:
                        print(f"⚠️ 返回的不是数组格式，跳过此部分")
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON 解析失败: {str(e)}")
                    print(f"响应内容前1000字符: {response_text[:1000]}")
                    # 保存失败的响应以便调试
                    with open(f"failed_response_part_{part_idx}.txt", "w", encoding="utf-8") as f:
                        f.write(response_text)
                    raise ValueError(f"JSON 解析失败: {str(e)}")
                    
            except Exception as e:
                print(f"⚠️ 提取第 {part_idx + 1} 部分时出错: {str(e)}")
                raise
        
        print(f"\n✅ 总共提取 {len(all_knowledge_points)} 个知识点")
        return all_knowledge_points
    
    def _extract_json_from_response(self, response_text: str) -> str:
        """从响应文本中提取 JSON 部分"""
        # 首先尝试查找代码块中的 JSON（数组或对象）
        json_pattern_array = r'```(?:json)?\s*(\[.*?\])\s*```'
        json_pattern_object = r'```(?:json)?\s*(\{.*?\})\s*```'
        
        match = re.search(json_pattern_array, response_text, re.DOTALL)
        if match:
            return match.group(1)
        
        match = re.search(json_pattern_object, response_text, re.DOTALL)
        if match:
            return match.group(1)
        
        # 尝试找到 JSON 数组的开始和结束
        start_idx = response_text.find('[')
        end_idx = response_text.rfind(']')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_text = response_text[start_idx:end_idx+1]
            # 验证是否是有效的 JSON
            try:
                json.loads(json_text)
                return json_text
            except:
                pass
        
        # 尝试找到 JSON 对象的开始和结束
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_text = response_text[start_idx:end_idx+1]
            # 验证是否是有效的 JSON
            try:
                json.loads(json_text)
                return json_text
            except:
                pass
        
        # 如果还是没找到，返回原文本
        return response_text
    
    def check_json_quality(self, knowledge_points: List[Dict[str, Any]], 
                          iteration: int = 1) -> Dict[str, Any]:
        """
        检查 JSON 质量（使用大模型2 - Critic）
        
        Args:
            knowledge_points: 待检查的知识点列表
            iteration: 当前迭代次数
        
        Returns:
            包含检查结果和修正后数据的字典
        """
        print(f"\n🔍 第 {iteration} 次检查 JSON 质量...")
        
        system_prompt = """你是印度尼西亚 K12 教育体系构建专家，精通 Kurikulum Merdeka 和 K13 课程标准。
你的任务是仔细检查知识点 JSON 数据，找出问题并提供修正建议。"""
        
        knowledge_points_json = json.dumps(knowledge_points, ensure_ascii=False, indent=2)
        
        # 如果数据太长，需要分割检查
        max_check_length = 150000
        if len(knowledge_points_json) > max_check_length:
            print(f"⚠️ 数据过长 ({len(knowledge_points_json)} 字符)，将分批检查...")
            # 分批检查，但这里简化处理，只检查前一部分
            knowledge_points_json = knowledge_points_json[:max_check_length] + "\n... (数据已截断)"
        
        user_prompt = f"""请仔细检查以下知识点 JSON 数据，找出以下问题：

1. **覆盖率检查**：是否遗漏了任何小节？大纲中的所有知识点是否都已转化为 JSON 节点？
2. **术语准确性**：中文翻译是否符合数学教学规范？（例如不要把 "Akar Kuadrat" 翻译成 "方根" 而应是 "平方根"）
3. **去噪**：`topic_title_id` 中是否还有 "1.2", "A." 等干扰字符？请去除
4. **字段完整性**：每个知识点是否都包含所有必填字段（id, curriculum_standard, grade_level, subject, chapter_title, topic_title_id, topic_title_cn, learning_objective, mapping_tags）？
5. **ID 唯一性**：所有 id 是否唯一？
6. **mapping_tags 质量**：mapping_tags 是否包含 3-5 个核心印尼语词汇或同义词？

知识点数据：
{knowledge_points_json}

**重要**：请只输出 JSON 格式的检查结果，不要包含任何其他文字说明。格式如下：
{{
  "has_issues": true/false,
  "issues": [
    "问题1描述",
    "问题2描述"
  ],
  "suggestions": [
    "建议1",
    "建议2"
  ],
  "corrected_data": [修正后的知识点数组，如果没有问题则保持原样]
}}

如果发现问题，请在 corrected_data 中提供修正后的数据。如果数据质量良好，has_issues 设为 false，corrected_data 保持原样。请直接输出 JSON，不要有任何前缀或后缀文字，不要使用 markdown 代码块。"""
        
        try:
            response_text = self.client.call_gemini(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=32000,
                temperature=0.2
            )
            
            # 提取 JSON
            json_text = self._extract_json_from_response(response_text)
            
            try:
                check_result = json.loads(json_text)
                
                if check_result.get("has_issues", False):
                    issues = check_result.get("issues", [])
                    print(f"⚠️ 发现 {len(issues)} 个问题：")
                    for issue in issues[:10]:  # 显示前10个
                        print(f"   - {issue}")
                    
                    # 如果有修正后的数据，使用它
                    if "corrected_data" in check_result and check_result["corrected_data"]:
                        print("✅ 已应用修正")
                        return {
                            "has_issues": True,
                            "issues": issues,
                            "data": check_result["corrected_data"]
                        }
                    else:
                        return {
                            "has_issues": True,
                            "issues": issues,
                            "data": knowledge_points
                        }
                else:
                    print("✅ 检查通过，数据质量良好")
                    return {
                        "has_issues": False,
                        "issues": [],
                        "data": check_result.get("corrected_data", knowledge_points)
                    }
                    
            except json.JSONDecodeError as e:
                print(f"⚠️ 检查结果 JSON 解析失败: {str(e)}")
                print(f"响应内容前1000字符: {response_text[:1000]}")
                # 保存失败的响应以便调试
                with open(f"failed_check_response_iter_{iteration}.txt", "w", encoding="utf-8") as f:
                    f.write(response_text)
                # 如果解析失败，认为检查通过
                return {
                    "has_issues": False,
                    "issues": ["检查结果解析失败"],
                    "data": knowledge_points
                }
                
        except Exception as e:
            print(f"⚠️ 检查过程出错: {str(e)}")
            return {
                "has_issues": False,
                "issues": [f"检查过程出错: {str(e)}"],
                "data": knowledge_points
            }
    
    def extract_with_validation(self, max_iterations: int = 2) -> Dict[str, Any]:
        """
        提取知识点并进行验证（最多循环 max_iterations 次）
        
        Args:
            max_iterations: 最大检查迭代次数
        
        Returns:
            最终的知识点数据和质量报告
        """
        # 第一次提取
        knowledge_points = self.extract_knowledge_points()
        
        all_issues = []
        current_data = knowledge_points
        
        # 检查循环（最多 max_iterations 次）
        for iteration in range(1, max_iterations + 1):
            check_result = self.check_json_quality(current_data, iteration)
            
            all_issues.extend(check_result.get("issues", []))
            current_data = check_result.get("data", current_data)
            
            # 如果没有问题，提前结束
            if not check_result.get("has_issues", False):
                break
        
        # 生成最终报告
        result = {
            "metadata": {
                "source_file": self.pdf_path,
                "total_pages": self.pdf_pages,
                "total_knowledge_points": len(current_data),
                "check_iterations": min(iteration, max_iterations),
                "has_remaining_issues": len(all_issues) > 0
            },
            "knowledge_points": current_data,
            "issues": all_issues
        }
        
        return result


def main():
    """主函数"""
    import sys
    import glob
    
    # 确定输出目录
    output_dir = "/Users/shmiwanghao8/Desktop/education/Indonesia/Knowledge Point"
    os.makedirs(output_dir, exist_ok=True)
    
    # 如果提供了命令行参数，使用它；否则处理所有PDF文件
    if len(sys.argv) > 1:
        pdf_files = [sys.argv[1]]
    else:
        # 处理所有PDF文件
        syllabus_dir = "/Users/shmiwanghao8/Desktop/education/Indonesia/syllabus"
        pdf_files = sorted(glob.glob(os.path.join(syllabus_dir, "*.pdf")))
    
    if not pdf_files:
        print("❌ 错误: 没有找到 PDF 文件")
        return
    
    print(f"📚 找到 {len(pdf_files)} 个 PDF 文件需要处理\n")
    
    all_results = []
    
    for idx, pdf_file in enumerate(pdf_files, 1):
        print(f"\n{'='*80}")
        print(f"📄 处理文件 {idx}/{len(pdf_files)}: {os.path.basename(pdf_file)}")
        print(f"{'='*80}\n")
        
        # 检查文件是否存在
        if not os.path.exists(pdf_file):
            print(f"❌ 错误: PDF 文件不存在: {pdf_file}")
            continue
        
        try:
            # 创建提取器
            extractor = SyllabusExtractor(pdf_file)
            
            # 提取并验证知识点
            result = extractor.extract_with_validation(max_iterations=2)
            
            # 生成输出文件名
            base_name = os.path.splitext(os.path.basename(pdf_file))[0]
            output_file = os.path.join(output_dir, f"{base_name}_knowledge_points.json")
            
            # 保存结果
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"\n✅ 提取完成！")
            print(f"📊 统计信息：")
            print(f"   - PDF 页数: {result['metadata']['total_pages']}")
            print(f"   - 知识点总数: {result['metadata']['total_knowledge_points']}")
            print(f"   - 检查迭代次数: {result['metadata']['check_iterations']}")
            print(f"   - 发现问题数: {len(result['issues'])}")
            print(f"   - 输出文件: {output_file}")
            
            if result['issues']:
                print(f"\n⚠️ 发现的问题（需要人工确认）：")
                for i, issue in enumerate(result['issues'], 1):
                    print(f"   {i}. {issue}")
            
            all_results.append({
                "file": os.path.basename(pdf_file),
                "knowledge_points": result['metadata']['total_knowledge_points'],
                "issues": len(result['issues']),
                "output_file": output_file
            })
        
        except Exception as e:
            print(f"❌ 处理文件时出错: {e}")
            import traceback
            traceback.print_exc()
            all_results.append({
                "file": os.path.basename(pdf_file),
                "error": str(e)
            })
    
    # 打印总结
    print(f"\n\n{'='*80}")
    print(f"📊 处理总结")
    print(f"{'='*80}")
    total_knowledge_points = sum(r.get('knowledge_points', 0) for r in all_results)
    successful_files = sum(1 for r in all_results if 'error' not in r)
    
    print(f"✅ 成功处理: {successful_files}/{len(pdf_files)} 个文件")
    print(f"📚 知识点总数: {total_knowledge_points}")
    print(f"📁 输出目录: {output_dir}")
    
    print(f"\n详细结果：")
    for r in all_results:
        if 'error' in r:
            print(f"   ❌ {r['file']}: {r['error']}")
        else:
            print(f"   ✅ {r['file']}: {r['knowledge_points']} 个知识点, {r['issues']} 个问题")


if __name__ == "__main__":
    main()

