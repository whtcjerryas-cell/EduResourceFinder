#!/usr/bin/env python3
"""
从印度尼西亚数学学科 K12 教学大纲 PDF 中提取知识点
使用 AI Builders 的 gemini-2.5-pro 模型进行提取和检查
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
                timeout=300,  # 增加超时时间
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
            
            self.pdf_text = "\n".join(text_parts)
            print(f"✅ PDF 读取完成，共 {len(reader.pages)} 页")
            return self.pdf_text
        except Exception as e:
            raise ValueError(f"读取 PDF 文件失败: {str(e)}")
    
    def extract_knowledge_points(self) -> Dict[str, Any]:
        """
        提取知识点（使用大模型1）
        
        Returns:
            提取的知识点 JSON 数据
        """
        if not self.pdf_text:
            self.read_pdf()
        
        print("\n🤖 正在使用 gemini-2.5-pro 提取知识点...")
        
        system_prompt = """你是一位专业的教育内容分析专家，擅长从教学大纲中提取结构化知识点。
你的任务是仔细分析教学大纲内容，提取出所有知识点，并按照要求的 JSON 格式输出。"""
        
        user_prompt = f"""请仔细分析以下印度尼西亚数学学科 K12 教学大纲的内容，提取出所有知识点。

要求：
1. 提取所有年级（Kelas 1-12）的知识点
2. 每个知识点需要包含以下字段：
   - 国家：固定为"印度尼西亚"或"Indonesia"
   - 学科：固定为"数学"或"Matematika"
   - 年级：如"Kelas 1"、"Kelas 2"等，或对应的数字年级
   - 知识点：用印尼语或英语描述的知识点名称
   - 知识点中文：对应的中文翻译
   - 教学目标：该知识点的教学目标描述（中文）

3. 输出格式必须是有效的 JSON 数组，每个元素是一个知识点对象
4. 确保 JSON 格式完全正确，可以被 Python json.loads() 解析
5. 尽量提取完整，不要遗漏重要知识点

教学大纲内容（由于内容较长，这里是前60000字符，请尽可能提取所有年级的知识点）：
{self.pdf_text[:60000]}

请直接输出 JSON 数组，不要包含任何其他文字说明。格式示例：
[
  {{
    "国家": "印度尼西亚",
    "学科": "数学",
    "年级": "Kelas 1",
    "知识点": "Bilangan",
    "知识点中文": "数字",
    "教学目标": "学生能够认识和理解数字1-20"
  }},
  ...
]"""
        
        try:
            response_text = self.client.call_gemini(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=16000,
                temperature=0.3
            )
            
            # 尝试从响应中提取 JSON
            json_text = self._extract_json_from_response(response_text)
            
            # 解析 JSON
            try:
                knowledge_points = json.loads(json_text)
                print(f"✅ 成功提取 {len(knowledge_points)} 个知识点")
                return knowledge_points
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON 解析失败: {str(e)}")
                print(f"响应内容前500字符: {response_text[:500]}")
                raise ValueError(f"JSON 解析失败: {str(e)}")
                
        except Exception as e:
            raise ValueError(f"知识点提取失败: {str(e)}")
    
    def _extract_json_from_response(self, response_text: str) -> str:
        """从响应文本中提取 JSON 部分"""
        # 首先尝试查找代码块中的 JSON
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, response_text, re.DOTALL)
        if match:
            return match.group(1)
        
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
        
        # 如果还是没找到，返回原文本
        return response_text
    
    def check_json_quality(self, knowledge_points: List[Dict[str, Any]], 
                          iteration: int = 1) -> Dict[str, Any]:
        """
        检查 JSON 质量（使用大模型2）
        
        Args:
            knowledge_points: 待检查的知识点列表
            iteration: 当前迭代次数
        
        Returns:
            包含检查结果和修正后数据的字典
        """
        print(f"\n🔍 第 {iteration} 次检查 JSON 质量...")
        
        system_prompt = """你是一位专业的数据质量检查专家，擅长检查 JSON 数据的完整性和正确性。
你的任务是仔细检查知识点 JSON 数据，找出问题并提供修正建议。"""
        
        knowledge_points_json = json.dumps(knowledge_points, ensure_ascii=False, indent=2)
        
        user_prompt = f"""请仔细检查以下知识点 JSON 数据，找出以下问题：
1. JSON 格式是否正确（能否被解析）
2. 必填字段是否完整（国家、学科、年级、知识点、知识点中文、教学目标）
3. 数据是否合理（年级格式、知识点描述是否清晰）
4. 是否有重复或遗漏的知识点
5. 中文翻译是否准确

知识点数据：
{knowledge_points_json[:40000]}  # 限制长度

重要：请只输出 JSON 格式的检查结果，不要包含任何其他文字说明。格式如下：
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

如果发现问题，请在 corrected_data 中提供修正后的数据。如果数据质量良好，has_issues 设为 false，corrected_data 保持原样。请直接输出 JSON，不要有任何前缀或后缀文字。"""
        
        try:
            response_text = self.client.call_gemini(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=16000,
                temperature=0.2
            )
            
            # 提取 JSON
            json_text = self._extract_json_from_response(response_text)
            
            try:
                check_result = json.loads(json_text)
                
                if check_result.get("has_issues", False):
                    issues = check_result.get("issues", [])
                    print(f"⚠️ 发现 {len(issues)} 个问题：")
                    for issue in issues[:5]:  # 只显示前5个
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
                print(f"响应内容前500字符: {response_text[:500]}")
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
    # PDF 文件路径
    pdf_file = "/Users/shmiwanghao8/Desktop/education/EduResourceFinder/5. Final Panduan Mata Pelajaran Matematika_12_09_2025_Revisi 3.pdf"
    
    # 检查文件是否存在
    if not os.path.exists(pdf_file):
        print(f"❌ 错误: PDF 文件不存在: {pdf_file}")
        return
    
    try:
        # 创建提取器
        extractor = SyllabusExtractor(pdf_file)
        
        # 提取并验证知识点
        result = extractor.extract_with_validation(max_iterations=2)
        
        # 保存结果
        output_file = "syllabus_knowledge_points.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 提取完成！")
        print(f"📊 统计信息：")
        print(f"   - 知识点总数: {result['metadata']['total_knowledge_points']}")
        print(f"   - 检查迭代次数: {result['metadata']['check_iterations']}")
        print(f"   - 发现问题数: {len(result['issues'])}")
        print(f"   - 输出文件: {output_file}")
        
        if result['issues']:
            print(f"\n⚠️ 发现的问题（需要人工确认）：")
            for i, issue in enumerate(result['issues'], 1):
                print(f"   {i}. {issue}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

