#!/usr/bin/env python3
"""
代理工具模块

提供统一的代理禁用功能，解决代码重复问题。
"""

import os
import logging

logger = logging.getLogger(__name__)


def disable_proxy() -> int:
    """
    强制禁用所有代理设置

    确保公司内部API可以正常访问，避免请求被WAF拦截。

    Returns:
        int: 禁用的代理环境变量数量

    Examples:
        >>> from core.proxy_utils import disable_proxy
        >>> disable_proxy()
        ✅ 已清除 3 个代理环境变量
        3
    """
    proxy_vars = [
        "HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
        "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy"
    ]

    disabled_count = 0
    for var in proxy_vars:
        if var in os.environ:
            del os.environ[var]
            disabled_count += 1
            logger.debug(f"已清除代理环境变量: {var}")

    # 也设置为空，防止代码中读取
    os.environ["HTTP_PROXY"] = ""
    os.environ["HTTPS_PROXY"] = ""
    os.environ["http_proxy"] = ""
    os.environ["https_proxy"] = ""

    if disabled_count > 0:
        logger.info(f"✅ 已清除 {disabled_count} 个代理环境变量")

    return disabled_count


def get_proxy_status() -> dict:
    """
    获取当前代理环境变量状态

    Returns:
        dict: 包含所有代理环境变量及其值的字典

    Examples:
        >>> from core.proxy_utils import get_proxy_status
        >>> get_proxy_status()
        {'HTTP_PROXY': '', 'HTTPS_PROXY': '', 'http_proxy': '', ...}
    """
    proxy_vars = [
        "HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
        "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy"
    ]

    status = {}
    for var in proxy_vars:
        status[var] = os.environ.get(var, '')

    return status


# 模块导入时自动禁用代理（保持向后兼容）
disable_proxy()


if __name__ == "__main__":
    print("=" * 60)
    print("代理工具模块测试")
    print("=" * 60)

    # 测试1: 禁用代理
    print("\n测试1 - 禁用代理:")
    count = disable_proxy()
    print(f"  禁用了 {count} 个代理环境变量")

    # 测试2: 获取代理状态
    print("\n测试2 - 代理状态:")
    status = get_proxy_status()
    for key, value in status.items():
        print(f"  {key}: '{value}'")

    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)
