#!/usr/bin/env python3
"""
批量将 print 语句迁移到 logger 的脚本
"""
import re
from pathlib import Path

def migrate_prints_to_logger(file_path: str):
    """
    批量替换 print 语句为 logger 调用
    """
    file_path = Path(file_path)
    content = file_path.read_text(encoding='utf-8')
    original_content = content

    # 1. 替换 ERROR 级别日志（包含 "❌ 错误"）
    content = re.sub(
        r'print\(f"\[❌ 错误\]([^"]+)"\)',
        r'logger.error(f"\1")',
        content
    )

    # 2. 替换 WARNING 级别日志（包含 "⚠️ 警告"）
    content = re.sub(
        r'print\(f"\[⚠️ 警告\]([^"]+)"\)',
        r'logger.warning(f"\1")',
        content
    )

    # 3. 替换 WARNING 级别日志（仅包含 "⚠️"）
    content = re.sub(
        r'print\(f"\[⚠️\]([^"]+)"\)',
        r'logger.warning(f"\1")',
        content
    )

    # 4. 替换 INFO 级别日志（包含 "✅"）
    content = re.sub(
        r'print\("\[✅\]([^"]+)"\)',
        r'logger.info("\1")',
        content
    )
    content = re.sub(
        r'print\(f"\[✅([^"]+)"\)',
        r'logger.info(f"\1")',
        content
    )

    # 5. 替换初始化成功的 INFO 日志
    content = re.sub(
        r'print\(f"\[✅\]([^"]+)初始化成功"\)',
        r'logger.info("\1客户端初始化成功")',
        content
    )

    # 6. 替换 DEBUG 级别日志（输入/输出）
    content = re.sub(
        r'print\(f"\[📤 输入\]([^"]+)"\)',
        r'logger.debug(f"\1")',
        content
    )
    content = re.sub(
        r'print\(f"\[📥 响应\]([^"]+)"\)',
        r'logger.debug(f"\1")',
        content
    )

    # 7. 替换分隔线（保留但简化）
    content = re.sub(
        r'print\(f"\\n\[\'\*\'\*80\]"\)',
        r'logger.debug("="*80)',
        content
    )
    content = re.sub(
        r'print\(f"\[\'\*\'\*80\]"\)',
        r'logger.debug("="*80)',
        content
    )

    # 8. 替换 API 调用开始的 INFO 日志
    content = re.sub(
        r'print\(f"\[🏢 公司内部API\]([^"]+)"\)',
        r'logger.info(f"公司内部API\1")',
        content
    )
    content = re.sub(
        r'print\(f"\[🌐 AI Builders API\]([^"]+)"\)',
        r'logger.info(f"AI Builders API\1")',
        content
    )

    # 9. 替换搜索相关的 INFO 日志
    content = re.sub(
        r'print\(f"\[🔍 搜索\]([^"]+)"\)',
        r'logger.info(f"搜索\1")',
        content
    )

    # 10. 替换建议和提示
    content = re.sub(
        r'print\(f"\[💡 [^]]+\]([^"]+)"\)',
        r'logger.info(f"\1")',
        content
    )

    # 如果内容有变化，写回文件
    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        print(f"✅ 已更新文件: {file_path}")
        return True
    else:
        print(f"ℹ️  文件无需更改: {file_path}")
        return False

if __name__ == "__main__":
    migrate_prints_to_logger("llm_client.py")
