"""
验证工具 - 验证年级匹配和URL质量

遵循 agent-native 原则：
- 原子工具：只负责验证判断，不编码业务逻辑
- 丰富输出：返回完整验证信息供Agent决策
- 可配置：通过配置文件定义规则
"""

import re
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
from logger_utils import get_logger
from .config_tools import read_country_config

logger = get_logger('validation_tools')


async def validate_grade_match(
    target_grade: str,
    identified_grade: str,
    country_code: str
) -> Dict[str, Any]:
    """
    验证年级是否匹配

    Args:
        target_grade: 目标年级（可以是年级ID、中文名、本地名）
        identified_grade: 识别出的年级（同上）
        country_code: 国家代码

    Returns:
        {
            "success": True/False,
            "data": {
                "match": True/False,
                "target_grade_id": "1",
                "identified_grade_id": "6",
                "confidence": "high",
                "reason": "年级匹配" / "年级不匹配"
            },
            "text": "年级匹配：一年级 (Kelas 1)"
        }

    示例：
        >>> result = await validate_grade_match("一年级", "Kelas 1", "ID")
        >>> print(result['data'])
        {'match': True, 'target_grade_id': '1', 'identified_grade_id': '1', 'confidence': 'high', 'reason': '年级匹配'}

        >>> result = await validate_grade_match("Kelas 1", "Kelas 6", "ID")
        >>> print(result['data'])
        {'match': False, 'target_grade_id': '1', 'identified_grade_id': '6', 'confidence': 'high', 'reason': '年级不匹配'}
    """
    try:
        # 1. 读取国家配置
        config_result = await read_country_config(country_code)

        if not config_result["success"]:
            return {
                "success": False,
                "data": None,
                "text": f"无法读取配置：{config_result.get('error', '未知错误')}"
            }

        config = config_result["data"]
        grades = config.get("grades", [])

        # 2. 创建查找映射（支持ID、中文名、本地名查找）
        grade_lookup = {}
        for grade in grades:
            grade_id = grade["grade_id"]
            grade_lookup[grade_id] = grade
            grade_lookup[grade["zh_name"]] = grade
            grade_lookup[grade["local_name"]] = grade
            # 也支持英文名查找
            if "en_name" in grade:
                grade_lookup[grade["en_name"]] = grade

        # 3. 查找目标年级和识别年级
        target_grade_info = grade_lookup.get(target_grade)
        identified_grade_info = grade_lookup.get(identified_grade)

        if not target_grade_info:
            return {
                "success": False,
                "data": None,
                "text": f"无法识别目标年级：{target_grade}，可用年级：{', '.join([g['zh_name'] for g in grades[:5]])}..."
            }

        if not identified_grade_info:
            return {
                "success": False,
                "data": None,
                "text": f"无法识别年级：{identified_grade}，可用年级：{', '.join([g['zh_name'] for g in grades[:5]])}..."
            }

        # 4. 比较年级ID（最可靠的匹配方式）
        target_grade_id = target_grade_info["grade_id"]
        identified_grade_id = identified_grade_info["grade_id"]

        is_match = target_grade_id == identified_grade_id

        if is_match:
            return {
                "success": True,
                "data": {
                    "match": True,
                    "target_grade_id": target_grade_id,
                    "identified_grade_id": identified_grade_id,
                    "target_grade_name": target_grade_info["zh_name"],
                    "identified_grade_name": identified_grade_info["zh_name"],
                    "target_grade_local": target_grade_info["local_name"],
                    "identified_grade_local": identified_grade_info["local_name"],
                    "confidence": "high",
                    "reason": "年级匹配"
                },
                "text": f"年级匹配：{target_grade_info['zh_name']} ({target_grade_info['local_name']})"
            }
        else:
            return {
                "success": True,
                "data": {
                    "match": False,
                    "target_grade_id": target_grade_id,
                    "identified_grade_id": identified_grade_id,
                    "target_grade_name": target_grade_info["zh_name"],
                    "identified_grade_name": identified_grade_info["zh_name"],
                    "target_grade_local": target_grade_info["local_name"],
                    "identified_grade_local": identified_grade_info["local_name"],
                    "confidence": "high",
                    "reason": "年级不匹配"
                },
                "text": f"年级不匹配：目标{target_grade_info['zh_name']} ({target_grade_info['local_name']})，标题{identified_grade_info['zh_name']} ({identified_grade_info['local_name']})"
            }

    except Exception as e:
        logger.error(f"验证年级匹配失败：{str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": None,
            "text": f"验证失败：{str(e)}"
        }


async def validate_url_quality(url: str, title: str = "") -> Dict[str, Any]:
    """
    验证URL来源质量

    Args:
        url: 资源URL
        title: 资源标题（可选，用于辅助判断）

    Returns:
        {
            "success": True/False,
            "data": {
                "quality": "high" / "medium" / "low",
                "reason": "trusted_platform" / "unknown_domain" / "social_media",
                "filter": True/False,
                "score_adjustment": 1.5 / -8.0
            },
            "text": "推荐：来源是YouTube" / "不推荐：来源是社交媒体"
        }

    示例：
        >>> result = await validate_url_quality("https://www.youtube.com/watch?v=xxx", "Math Tutorial")
        >>> print(result['data'])
        {'quality': 'high', 'reason': 'trusted_platform', 'filter': False, 'score_adjustment': 1.5}

        >>> result = await validate_url_quality("https://www.facebook.com/posts/xxx", "Video")
        >>> print(result['data'])
        {'quality': 'low', 'reason': 'social_media', 'filter': True, 'score_adjustment': -8.0}
    """
    try:
        logger.debug(f"[🔍 URL验证开始] URL={url[:80]}..., 标题={title[:50] if title else 'N/A'}")

        if not url:
            logger.warning(f"[❌ URL验证] URL为空")
            return {
                "success": False,
                "data": None,
                "text": "URL为空"
            }

        # 1. 解析URL获取域名
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # 移除 www. 前缀
            if domain.startswith("www."):
                domain = domain[4:]

            logger.debug(f"[✅ URL解析] 域名={domain}")

        except Exception as e:
            logger.error(f"[❌ URL解析失败] {str(e)}")
            return {
                "success": False,
                "data": None,
                "text": f"URL解析失败：{str(e)}"
            }

        # 2. 黑名单检查（社交媒体、非教育内容）
        blacklist = [
            # 社交媒体
            'facebook.com', 'fb.com', 'fb.watch',
            'instagram.com', 'instagr.am',
            'twitter.com', 'x.com',
            'tiktok.com',
            'twitch.tv',
            'vk.com',
            'telegram.org', 't.me',
            'whatsapp.com',

            # 短链接服务
            'bit.ly', 'bitly.com',
            'tinyurl.com',
            'short.link',
            'goo.gl',

            # 非教育内容（电商、游戏等）
            'amazon.com', 'amazon.co.', 'amazon.cn',
            'ebay.com', 'ebay.co.',
            'aliexpress.com',
            'taobao.com', 'tmall.com',
            'steam.com',
            'epicgames.com',
        ]

        logger.debug(f"[🔍 黑名单检查] 检查域名 {domain} 是否在黑名单中...")

        for blacklist_domain in blacklist:
            if blacklist_domain in domain:
                logger.warning(f"[❌ 黑名单匹配] 域名 {domain} 匹配黑名单规则: {blacklist_domain}")
                return {
                    "success": True,
                    "data": {
                        "quality": "low",
                        "reason": "blacklist",
                        "domain": domain,
                        "filter": True,
                        "score_adjustment": -8.0,
                        "matched_rule": blacklist_domain
                    },
                    "text": f"不推荐：来源在黑名单中 ({domain} - {blacklist_domain})"
                }

        logger.debug(f"[✅ 黑名单检查] 域名 {domain} 不在黑名单中")

        # 3. 信任列表检查（教育平台）
        trusted = [
            'youtube.com', 'youtu.be', 'youtube-nocookie.com',
            'vimeo.com',
            'drive.google.com', 'docs.google.com',
            'slideshare.net',
            'scribd.com',
            'academia.edu',
            'researchgate.net',
            'teachertube.com',
            'khanacademy.org',
            'coursera.org',
            'edx.org',
            'udemy.com',
            'skillshare.com',
        ]

        logger.debug(f"[🔍 信任列表检查] 检查域名 {domain} 是否在信任列表中...")

        for trusted_domain in trusted:
            if trusted_domain in domain:
                logger.info(f"[✅ 信任列表匹配] 域名 {domain} 匹配信任规则: {trusted_domain}")

                # YouTube额外检查
                if 'youtube' in domain:
                    # YouTube播放列表加分
                    if 'playlist' in url.lower():
                        logger.info(f"[🎬 YouTube播放列表] {url[:80]}...")
                        return {
                            "success": True,
                            "data": {
                                "quality": "high",
                                "reason": "youtube_playlist",
                                "domain": domain,
                                "filter": False,
                                "score_adjustment": 2.0,
                                "matched_rule": trusted_domain
                            },
                            "text": f"强烈推荐：来源是YouTube播放列表 ({domain})"
                        }
                    # 单个YouTube视频
                    logger.info(f"[🎬 YouTube视频] {url[:80]}...")
                    return {
                        "success": True,
                        "data": {
                            "quality": "high",
                            "reason": "trusted_platform",
                            "domain": domain,
                            "filter": False,
                            "score_adjustment": 1.5,
                            "matched_rule": trusted_domain
                        },
                        "text": f"推荐：来源是YouTube ({domain})"
                    }

                # 其他信任平台
                logger.info(f"[✅ 可信平台] 域名 {domain} 是可信教育平台")
                return {
                    "success": True,
                    "data": {
                        "quality": "high",
                        "reason": "trusted_platform",
                        "domain": domain,
                        "filter": False,
                        "score_adjustment": 1.0,
                        "matched_rule": trusted_domain
                    },
                    "text": f"推荐：来源是可信平台 ({domain})"
                }

        logger.debug(f"[❌ 信任列表检查] 域名 {domain} 不在信任列表中")

        # 4. 基于标题的补充判断（如果有标题）
        if title:
            title_lower = title.lower()
            logger.debug(f"[🔍 标题关键词检查] 检查标题是否包含明显无关内容...")

            # ✅ 新增：明显无关内容检查（优先级最高，必须在spam_keywords之前）
            irrelevant_categories = {
                'automotive': ['rivian', 'tesla', 'ford', 'bmw', 'mercedes', 'toyota', 'honda',
                              'car', 'automotive', 'vehicle', 'truck', 'suv'],
                'music': ['drum', 'drums', 'guitar', 'piano', 'violin', 'instrument',
                         'music library', 'audio', 'band', 'orchestra'],
                'gaming': ['game', 'gaming', 'gameplay', 'streamer', 'twitch', 'steam',
                          'esport', 'console', 'playstation', 'xbox'],
                'shopping': ['shop', 'store', 'buy', 'purchase', 'price', 'sale', 'discount'],
                'news_general': ['news', 'breaking news', 'latest updates', 'rumors', 'gossip'],
            }

            # 检查是否包含无关内容关键词
            for category, keywords in irrelevant_categories.items():
                matched_keywords = [kw for kw in keywords if kw in title_lower]
                if matched_keywords:
                    logger.warning(f"[❌ 明显无关内容] 标题包含 {category} 关键词: {matched_keywords}")
                    return {
                        "success": True,
                        "data": {
                            "quality": "low",
                            "reason": f"irrelevant_content_{category}",
                            "domain": domain,
                            "filter": True,  # ✅ 应该过滤
                            "score_adjustment": -10.0,
                            "matched_keywords": matched_keywords,
                            "category": category
                        },
                        "text": f"不推荐：明显无关内容（{category}）: {', '.join(matched_keywords)}"
                    }

            # 游戏、电商关键词（原有逻辑）
            spam_keywords = [
                'hack', 'cheat', 'mod',
                'crack', 'patch',
                'casino', 'betting', 'gambling'
            ]

            spam_count = sum(1 for kw in spam_keywords if kw in title_lower)
            if spam_count >= 2:
                matched_keywords = [kw for kw in spam_keywords if kw in title_lower]
                logger.warning(f"[❌ 垃圾关键词] 标题包含 {spam_count} 个垃圾关键词: {matched_keywords}")
                return {
                    "success": True,
                    "data": {
                        "quality": "low",
                        "reason": "spam_keywords",
                        "domain": domain,
                        "filter": True,
                        "score_adjustment": -6.0,
                        "matched_keywords": matched_keywords
                    },
                    "text": f"不推荐：标题包含垃圾内容关键词 ({domain})"
                }

        # 5. 未知域名（需要进一步判断）
        logger.info(f"[❓ 未知域名] 域名 {domain} 不在黑名单或信任列表中，质量评级: medium")
        return {
            "success": True,
            "data": {
                "quality": "medium",
                "reason": "unknown_domain",
                "domain": domain,
                "filter": False,
                "score_adjustment": 0.0,
                "matched_rule": None
            },
            "text": f"来源未知：{domain}，需要进一步判断内容质量"
        }

    except Exception as e:
        logger.error(f"验证URL质量失败：{str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": None,
            "text": f"验证失败：{str(e)}"
        }
