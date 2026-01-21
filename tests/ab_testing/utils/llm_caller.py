#!/usr/bin/env python3
"""
LLM调用工具（带监控）

用于A/B测试，跟踪LLM调用的性能和成本指标
"""
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logger_utils import get_logger

logger = get_logger('llm_caller')


class LLMCaller:
    """LLM调用工具（带监控）"""

    def __init__(self):
        """初始化LLM调用器"""
        from llm_client import get_llm_client
        self.llm_client = get_llm_client()
        self.call_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_time": 0,
            "total_tokens": 0,
            "total_cost": 0,
        }

    def call_llm(
        self,
        prompt: str,
        model: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        timeout: int = 30,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        调用LLM（带监控）

        Args:
            prompt: 提示词
            model: 模型名称
            max_tokens: 最大token数
            temperature: 温度参数
            timeout: 超时时间（秒）
            metadata: 元数据

        Returns:
            {
                "response": str,
                "success": bool,
                "time": float,
                "tokens": int,
                "cost": float,
                "error": str (如果失败),
            }
        """
        start_time = time.time()
        self.call_stats["total_calls"] += 1

        result = {
            "model": model,
            "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
            "metadata": metadata or {},
        }

        try:
            # 调用LLM
            response = self.llm_client.call_llm(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                model=model
            )

            # 计算耗时
            elapsed_time = time.time() - start_time

            # 更新统计信息
            self.call_stats["successful_calls"] += 1
            self.call_stats["total_time"] += elapsed_time

            result.update({
                "response": response,
                "success": True,
                "time": elapsed_time,
                "tokens": None,  # TODO: 从LLM响应中提取token数
                "cost": None,    # TODO: 根据token数计算成本
                "error": None,
            })

            logger.info(f"✅ LLM调用成功 ({model}): {elapsed_time:.2f}秒")

        except Exception as e:
            elapsed_time = time.time() - start_time

            # 更新统计信息
            self.call_stats["failed_calls"] += 1
            self.call_stats["total_time"] += elapsed_time

            result.update({
                "response": None,
                "success": False,
                "time": elapsed_time,
                "error": str(e),
            })

            logger.error(f"❌ LLM调用失败 ({model}): {str(e)}")

        return result

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.call_stats.copy()

        if stats["total_calls"] > 0:
            stats["average_time"] = stats["total_time"] / stats["total_calls"]
            stats["success_rate"] = stats["successful_calls"] / stats["total_calls"]
        else:
            stats["average_time"] = 0
            stats["success_rate"] = 0

        return stats

    def reset_statistics(self):
        """重置统计信息"""
        self.call_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_time": 0,
            "total_tokens": 0,
            "total_cost": 0,
        }

    def print_statistics(self):
        """打印统计信息"""
        stats = self.get_statistics()

        logger.info("\n" + "="*80)
        logger.info("📊 LLM调用统计")
        logger.info("="*80)
        logger.info(f"  总调用次数: {stats['total_calls']}")
        logger.info(f"  成功次数: {stats['successful_calls']}")
        logger.info(f"  失败次数: {stats['failed_calls']}")
        logger.info(f"  成功率: {stats['success_rate']:.2%}")
        logger.info(f"  总耗时: {stats['total_time']:.2f}秒")
        logger.info(f"  平均耗时: {stats['average_time']:.2f}秒")
        logger.info("="*80 + "\n")
