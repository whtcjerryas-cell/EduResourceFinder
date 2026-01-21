#!/usr/bin/env python3
"""
批量修复 logger_utils 导入路径

将所有的 "from utils.logger_utils import" 替换为 "from utils.logger_utils import"
"""
import re
from pathlib import Path


def fix_logger_import(file_path: Path) -> bool:
    """
    修复单个文件中的 logger_utils 导入

    Args:
        file_path: 文件路径

    Returns:
        True 如果文件被修改，False 否则
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content

        # 替换 "from utils.logger_utils import" 为 "from utils.logger_utils import"
        content = re.sub(
            r'from utils.logger_utils import',
            r'from utils.logger_utils import',
            content
        )

        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"❌ 处理文件失败 {file_path}: {e}")
        return False


def main():
    """批量修复所有 Python 文件"""
    project_root = Path.cwd()

    print("="*80)
    print("批量修复 logger_utils 导入路径")
    print("="*80)

    # 查找所有包含 "from utils.logger_utils import" 的 Python 文件
    fixed_count = 0
    total_count = 0

    for py_file in project_root.rglob("*.py"):
        try:
            content = py_file.read_text(encoding='utf-8')
            if 'from utils.logger_utils import' in content:
                total_count += 1
                if fix_logger_import(py_file):
                    fixed_count += 1
                    print(f"✅ 修复: {py_file.relative_to(project_root)}")
        except Exception as e:
            # 忽略无法读取的文件
            pass

    print("\n" + "="*80)
    print("修复总结")
    print("="*80)
    print(f"找到需要修复的文件: {total_count}")
    print(f"成功修复: {fixed_count}")
    print(f"无需修复: {total_count - fixed_count}")

    if fixed_count == total_count:
        print("\n🎉 所有文件已成功修复！")
        return 0
    else:
        print(f"\n⚠️  有 {total_count - fixed_count} 个文件未修复")
        return 1


if __name__ == "__main__":
    exit(main())
