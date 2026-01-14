#!/usr/bin/env python3
"""
生成智能评分测试用例

生成100个测试用例，涵盖：
- 伊拉克（30个）：阿拉伯语、1-12年级、数学/科学/物理
- 中国（30个）：中文、1-12年级、数学/语文/英语/物理
- 印尼（25个）：印尼语、1-12年级、Matematika/IPA/Bahasa
- 美国（15个）：英语、K-12、Math/Science/Physics
"""
import json
from pathlib import Path
from typing import List, Dict, Any

# ============== 年级和学科表达 ==============

# 伊拉克阿拉伯语表达
IRAQ_GRADES = {
    1: "الصف الأول",
    2: "الصف الثاني",
    3: "الصف الثالث",
    4: "الصف الرابع",
    5: "الصف الخامس",
    6: "الصف السادس",
    7: "الصف السابع",
    8: "الصف الثامن",
    9: "الصف التاسع",
    10: "الصف العاشر",
    11: "الصف الحادي عشر",
    12: "الصف الثاني عشر",
}

IRAQ_SUBJECTS = {
    "数学": "الرياضيات",
    "科学": "العلوم",
    "物理": "الفيزياء",
}

# 中国中文表达
CHINA_GRADES = {
    1: "一年级", 2: "二年级", 3: "三年级", 4: "四年级",
    5: "五年级", 6: "六年级",
    7: "初一", 8: "初二", 9: "初三",
    10: "高一", 11: "高二", 12: "高三",
}

CHINA_SUBJECTS = {
    "数学": "数学",
    "语文": "语文",
    "英语": "英语",
    "物理": "物理",
}

# 印尼印尼语表达
INDONESIA_GRADES = {
    1: "Kelas 1", 2: "Kelas 2", 3: "Kelas 3", 4: "Kelas 4",
    5: "Kelas 5", 6: "Kelas 6",
    7: "Kelas 7", 8: "Kelas 8", 9: "Kelas 9",
    10: "Kelas 10", 11: "Kelas 11", 12: "Kelas 12",
}

INDONESIA_SUBJECTS = {
    "数学": "Matematika",
    "科学": "IPA",
    "语言": "Bahasa Indonesia",
}

# 美国英语表达
USA_GRADES = {
    1: "Grade 1", 2: "Grade 2", 3: "Grade 3", 4: "Grade 4",
    5: "Grade 5", 6: "Grade 6", 7: "Grade 7", 8: "Grade 8",
    9: "Grade 9", 10: "Grade 10", 11: "Grade 11", 12: "Grade 12",
}

USA_SUBJECTS = {
    "数学": "Mathematics",
    "科学": "Science",
    "物理": "Physics",
}

# ============== 测试用例生成函数 ==============

def generate_iraq_test_cases(count: int = 30) -> List[Dict[str, Any]]:
    """生成伊拉克测试用例（阿拉伯语）"""
    test_cases = []

    grade_nums = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    subjects = ["数学", "科学", "物理"]

    case_id = 1
    for grade_num in grade_nums[:10]:  # 前10个年级
        for subject in subjects:
            if case_id > count:
                break

            grade_arabic = IRAQ_GRADES[grade_num]
            grade_chinese = f"{grade_num}年级"
            subject_arabic = IRAQ_SUBJECTS[subject]

            # 构建测试用例
            test_case = {
                "id": f"IQ-{case_id:03d}",
                "target": {
                    "country": "IQ",
                    "country_code": "IQ",
                    "grade": grade_chinese,
                    "grade_variants": [grade_arabic, f"Grade {grade_num}", f"Kelas {grade_num}"],
                    "subject": subject,
                    "subject_variants": [subject_arabic, subject, "Mathematics"],
                },
                "search_results": [
                    # 1. 完全匹配（阿拉伯语）
                    {
                        "id": 1,
                        "title": f"{subject_arabic} للصف {grade_arabic.replace('الصف', '').strip()} الشامل",
                        "url": f"https://youtube.com/playlist?list=IQ{case_id}a",
                        "snippet": f"شرح كامل لمادة {subject_arabic} للصف {grade_arabic}",
                        "expected": {
                            "score": 9.5,
                            "identified_grade": grade_arabic,
                            "identified_subject": subject_arabic,
                            "grade_match": True,
                            "subject_match": True,
                            "score_range": [9.0, 10.0],
                        }
                    },
                    # 2. 年级不符（阿拉伯语）
                    {
                        "id": 2,
                        "title": f"{subject_arabic} للصف {IRAQ_GRADES[min(grade_num + 1, 12)].replace('الصف', '').strip()} المرحلة",
                        "url": f"https://youtube.com/playlist?list=IQ{case_id}b",
                        "snippet": f"شرح منهج {subject_arabic}",
                        "expected": {
                            "score": 4.0,
                            "identified_grade": IRAQ_GRADES[min(grade_num + 1, 12)],
                            "identified_subject": subject_arabic,
                            "grade_match": False,
                            "subject_match": True,
                            "score_range": [3.0, 5.0],
                            "reason": f"年级不符（{min(grade_num + 1, 12)}年级，目标{grade_num}年级）"
                        }
                    },
                    # 3. 学科不符（阿拉伯语）
                    {
                        "id": 3,
                        "title": f"{IRAQ_SUBJECTS['科学'] if subject != '科学' else IRAQ_SUBJECTS['数学']} للصف {grade_arabic.replace('الصف', '').strip()}",
                        "url": f"https://youtube.com/playlist?list=IQ{case_id}c",
                        "snippet": f"شرح منهج العلوم",
                        "expected": {
                            "score": 4.0,
                            "identified_grade": grade_arabic,
                            "identified_subject": IRAQ_SUBJECTS['科学'] if subject != '科学' else IRAQ_SUBJECTS['数学'],
                            "grade_match": True,
                            "subject_match": False,
                            "score_range": [3.0, 5.0],
                            "reason": f"学科不符（{'科学' if subject != '科学' else '数学'}，目标{subject}）"
                        }
                    },
                    # 4. 部分匹配（英语）
                    {
                        "id": 4,
                        "title": f"Grade {grade_num} {USA_SUBJECTS[subject]} Complete Course",
                        "url": f"https://youtube.com/playlist?list=IQ{case_id}d",
                        "snippet": f"Complete {subject.lower()} course for grade {grade_num}",
                        "expected": {
                            "score": 8.0,
                            "identified_grade": f"Grade {grade_num}",
                            "identified_subject": USA_SUBJECTS[subject],
                            "grade_match": True,
                            "subject_match": True,
                            "score_range": [7.5, 8.5],
                        }
                    },
                ]
            }

            test_cases.append(test_case)
            case_id += 1

        if case_id > count:
            break

    return test_cases


def generate_china_test_cases(count: int = 30) -> List[Dict[str, Any]]:
    """生成中国测试用例（中文）"""
    test_cases = []

    grade_nums = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    subjects = ["数学", "语文", "英语", "物理"]

    case_id = 1
    for grade_num in grade_nums[:8]:  # 前8个年级
        for subject in subjects:
            if case_id > count:
                break

            grade_chinese = CHINA_GRADES[grade_num]
            subject_chinese = CHINA_SUBJECTS[subject]

            # 构建测试用例
            test_case = {
                "id": f"CN-{case_id:03d}",
                "target": {
                    "country": "CN",
                    "country_code": "CN",
                    "grade": grade_chinese,
                    "grade_variants": [grade_chinese, f"Grade {grade_num}", f"{grade_num}年级"],
                    "subject": subject,
                    "subject_variants": [subject_chinese, subject, "Mathematics" if subject == "数学" else subject],
                },
                "search_results": [
                    # 1. 完全匹配（中文）
                    {
                        "id": 1,
                        "title": f"{grade_chinese}{subject_chinese}上册全册讲解",
                        "url": f"https://www.bilibili.com/video/BV{case_id}a",
                        "snippet": f"完整讲解{grade_chinese}{subject_chinese}上册所有知识点",
                        "expected": {
                            "score": 9.5,
                            "identified_grade": grade_chinese,
                            "identified_subject": subject_chinese,
                            "grade_match": True,
                            "subject_match": True,
                            "score_range": [9.0, 10.0],
                        }
                    },
                    # 2. 年级不符（中文）
                    {
                        "id": 2,
                        "title": f"{CHINA_GRADES[min(grade_num + 1, 12)]}{subject_chinese}重点复习",
                        "url": f"https://www.bilibili.com/video/BV{case_id}b",
                        "snippet": f"{CHINA_GRADES[min(grade_num + 1, 12)]}{subject_chinese}期末复习指南",
                        "expected": {
                            "score": 4.5,
                            "identified_grade": CHINA_GRADES[min(grade_num + 1, 12)],
                            "identified_subject": subject_chinese,
                            "grade_match": False,
                            "subject_match": True,
                            "score_range": [4.0, 5.0],
                            "reason": f"年级不符（{CHINA_GRADES[min(grade_num + 1, 12)]}，目标{grade_chinese}）"
                        }
                    },
                    # 3. 学科不符（中文）
                    {
                        "id": 3,
                        "title": f"{grade_chinese}{'语文' if subject != '语文' else '数学'}精品课程",
                        "url": f"https://www.bilibili.com/video/BV{case_id}c",
                        "snippet": f"{grade_chinese}{'语文' if subject != '语文' else '数学'}详细讲解",
                        "expected": {
                            "score": 4.0,
                            "identified_grade": grade_chinese,
                            "identified_subject": '语文' if subject != '语文' else '数学',
                            "grade_match": True,
                            "subject_match": False,
                            "score_range": [3.0, 5.0],
                            "reason": f"学科不符（{'语文' if subject != '语文' else '数学'}，目标{subject}）"
                        }
                    },
                    # 4. 部分匹配（英语）
                    {
                        "id": 4,
                        "title": f"Grade {grade_num} {subject} (Chinese Curriculum)",
                        "url": f"https://www.youtube.com/playlist?list=CN{case_id}d",
                        "snippet": f"Grade {grade_num} {subject} following Chinese curriculum",
                        "expected": {
                            "score": 8.5,
                            "identified_grade": f"Grade {grade_num}",
                            "identified_subject": subject,
                            "grade_match": True,
                            "subject_match": True,
                            "score_range": [8.0, 9.0],
                        }
                    },
                ]
            }

            test_cases.append(test_case)
            case_id += 1

        if case_id > count:
            break

    return test_cases


def generate_indonesia_test_cases(count: int = 25) -> List[Dict[str, Any]]:
    """生成印尼测试用例（印尼语）"""
    test_cases = []

    grade_nums = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    subjects = ["数学", "科学", "语言"]

    case_id = 1
    for grade_num in grade_nums[:9]:  # 前9个年级
        for subject in subjects:
            if case_id > count:
                break

            grade_indonesian = INDONESIA_GRADES[grade_num]
            subject_indonesian = INDONESIA_SUBJECTS[subject]

            # 构建测试用例
            test_case = {
                "id": f"ID-{case_id:03d}",
                "target": {
                    "country": "ID",
                    "country_code": "ID",
                    "grade": f"{grade_num}年级",
                    "grade_variants": [grade_indonesian, f"Grade {grade_num}", f"{grade_num}年级"],
                    "subject": subject,
                    "subject_variants": [subject_indonesian, subject, "Mathematics" if subject == "数学" else subject],
                },
                "search_results": [
                    # 1. 完全匹配（印尼语）
                    {
                        "id": 1,
                        "title": f"{subject_indonesian} {grade_indonesian} - Lengkap",
                        "url": f"https://youtube.com/playlist?list=ID{case_id}a",
                        "snippet": f"Video pembelajaran {subject_indonesian} untuk {grade_indonesian}",
                        "expected": {
                            "score": 9.5,
                            "identified_grade": grade_indonesian,
                            "identified_subject": subject_indonesian,
                            "grade_match": True,
                            "subject_match": True,
                            "score_range": [9.0, 10.0],
                        }
                    },
                    # 2. 年级不符（印尼语）
                    {
                        "id": 2,
                        "title": f"{subject_indonesian} {INDONESIA_GRADES[min(grade_num + 1, 12)]} Playlist",
                        "url": f"https://youtube.com/playlist?list=ID{case_id}b",
                        "snippet": f"Kumpulan video {subject_indonesian}",
                        "expected": {
                            "score": 4.0,
                            "identified_grade": INDONESIA_GRADES[min(grade_num + 1, 12)],
                            "identified_subject": subject_indonesian,
                            "grade_match": False,
                            "subject_match": True,
                            "score_range": [3.0, 5.0],
                            "reason": f"年级不符（{min(grade_num + 1, 12)}年级，目标{grade_num}年级）"
                        }
                    },
                    # 3. 学科不符（印尼语）
                    {
                        "id": 3,
                        "title": f"{INDONESIA_SUBJECTS['语言'] if subject != '语言' else INDONESIA_SUBJECTS['数学']} {grade_indonesian}",
                        "url": f"https://youtube.com/playlist?list=ID{case_id}c",
                        "snippet": f"Pembelajaran lengkap",
                        "expected": {
                            "score": 4.0,
                            "identified_grade": grade_indonesian,
                            "identified_subject": INDONESIA_SUBJECTS['语言'] if subject != '语言' else INDONESIA_SUBJECTS['数学'],
                            "grade_match": True,
                            "subject_match": False,
                            "score_range": [3.0, 5.0],
                            "reason": f"学科不符（{'语言' if subject != '语言' else '数学'}，目标{subject}）"
                        }
                    },
                    # 4. 部分匹配（英语）
                    {
                        "id": 4,
                        "title": f"{subject} Grade {grade_num} Indonesia Curriculum",
                        "url": f"https://youtube.com/playlist?list=ID{case_id}d",
                        "snippet": f"{subject} for Grade {grade_num} following Indonesian curriculum",
                        "expected": {
                            "score": 8.0,
                            "identified_grade": f"Grade {grade_num}",
                            "identified_subject": subject,
                            "grade_match": True,
                            "subject_match": True,
                            "score_range": [7.5, 8.5],
                        }
                    },
                ]
            }

            test_cases.append(test_case)
            case_id += 1

        if case_id > count:
            break

    return test_cases


def generate_usa_test_cases(count: int = 15) -> List[Dict[str, Any]]:
    """生成美国测试用例（英语）"""
    test_cases = []

    grade_nums = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    subjects = ["数学", "科学", "物理"]

    case_id = 1
    for grade_num in grade_nums[:5]:  # 前5个年级
        for subject in subjects:
            if case_id > count:
                break

            grade_english = USA_GRADES[grade_num]
            subject_english = USA_SUBJECTS[subject]

            # 构建测试用例
            test_case = {
                "id": f"US-{case_id:03d}",
                "target": {
                    "country": "US",
                    "country_code": "US",
                    "grade": f"Grade {grade_num}",
                    "grade_variants": [grade_english, f"{grade_num}年级"],
                    "subject": subject,
                    "subject_variants": [subject_english, subject],
                },
                "search_results": [
                    # 1. 完全匹配（英语）
                    {
                        "id": 1,
                        "title": f"{subject_english} - Grade {grade_num} Complete Course",
                        "url": f"https://www.youtube.com/playlist?list=US{case_id}a",
                        "snippet": f"Complete {subject_english} curriculum for Grade {grade_num}",
                        "expected": {
                            "score": 9.5,
                            "identified_grade": grade_english,
                            "identified_subject": subject_english,
                            "grade_match": True,
                            "subject_match": True,
                            "score_range": [9.0, 10.0],
                        }
                    },
                    # 2. 年级不符（英语）
                    {
                        "id": 2,
                        "title": f"{subject_english} - Grade {min(grade_num + 1, 12)} Full Course",
                        "url": f"https://www.youtube.com/playlist?list=US{case_id}b",
                        "snippet": f"Full {subject_english} course",
                        "expected": {
                            "score": 4.0,
                            "identified_grade": f"Grade {min(grade_num + 1, 12)}",
                            "identified_subject": subject_english,
                            "grade_match": False,
                            "subject_match": True,
                            "score_range": [3.0, 5.0],
                            "reason": f"年级不符（Grade {min(grade_num + 1, 12)}，目标Grade {grade_num}）"
                        }
                    },
                    # 3. 学科不符（英语）
                    {
                        "id": 3,
                        "title": f"{USA_SUBJECTS['科学'] if subject != '科学' else USA_SUBJECTS['数学']} - Grade {grade_num}",
                        "url": f"https://www.youtube.com/playlist?list=US{case_id}c",
                        "snippet": f"Complete course",
                        "expected": {
                            "score": 4.0,
                            "identified_grade": grade_english,
                            "identified_subject": USA_SUBJECTS['科学'] if subject != '科学' else USA_SUBJECTS['数学'],
                            "grade_match": True,
                            "subject_match": False,
                            "score_range": [3.0, 5.0],
                            "reason": f"学科不符（{'科学' if subject != '科学' else '数学'}，目标{subject}）"
                        }
                    },
                    # 4. 部分匹配（简化）
                    {
                        "id": 4,
                        "title": f"{subject} Grade {grade_num} Lessons",
                        "url": f"https://www.youtube.com/playlist?list=US{case_id}d",
                        "snippet": f"{subject} lessons for grade {grade_num}",
                        "expected": {
                            "score": 8.5,
                            "identified_grade": f"Grade {grade_num}",
                            "identified_subject": subject,
                            "grade_match": True,
                            "subject_match": True,
                            "score_range": [8.0, 9.0],
                        }
                    },
                ]
            }

            test_cases.append(test_case)
            case_id += 1

        if case_id > count:
            break

    return test_cases


# ============== 主函数 ==============

def main():
    """主函数：生成所有测试用例"""
    print("🔬 开始生成A/B测试用例...")

    # 生成各国的测试用例
    print("\n📊 生成伊拉克测试用例（30个）...")
    iraq_cases = generate_iraq_test_cases(30)
    print(f"  ✅ 已生成 {len(iraq_cases)} 个伊拉克测试用例")

    print("\n📊 生成中国测试用例（30个）...")
    china_cases = generate_china_test_cases(30)
    print(f"  ✅ 已生成 {len(china_cases)} 个中国测试用例")

    print("\n📊 生成印尼测试用例（25个）...")
    indonesia_cases = generate_indonesia_test_cases(25)
    print(f"  ✅ 已生成 {len(indonesia_cases)} 个印尼测试用例")

    print("\n📊 生成美国测试用例（15个）...")
    usa_cases = generate_usa_test_cases(15)
    print(f"  ✅ 已生成 {len(usa_cases)} 个美国测试用例")

    # 合并所有测试用例
    all_test_cases = {
        "test_cases": iraq_cases + china_cases + indonesia_cases + usa_cases
    }

    total = len(all_test_cases["test_cases"])
    print(f"\n📊 测试用例汇总:")
    print(f"  - 伊拉克: {len(iraq_cases)} 个")
    print(f"  - 中国: {len(china_cases)} 个")
    print(f"  - 印尼: {len(indonesia_cases)} 个")
    print(f"  - 美国: {len(usa_cases)} 个")
    print(f"  - 总计: {total} 个")

    # 保存到文件
    output_path = Path("/Users/shmiwanghao8/Desktop/education/Indonesia/tests/ab_testing/test_data/test_cases_scoring.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_test_cases, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 测试用例已保存到:")
    print(f"   {output_path}")

    # 验证文件
    with open(output_path, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
        assert len(loaded_data["test_cases"]) == total, "测试用例数量不匹配！"
        print(f"\n✅ 文件验证成功！")

    return total


if __name__ == "__main__":
    main()
