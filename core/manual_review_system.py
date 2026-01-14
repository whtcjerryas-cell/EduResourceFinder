#!/usr/bin/env python3
"""
人工审核系统 - 管理国家配置的审核流程
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


# ============================================================================
# 数据模型
# ============================================================================

class ReviewStatus(str, Enum):
    """审核状态"""
    PENDING = "pending"          # 待审核
    APPROVED = "approved"        # 已通过
    REJECTED = "rejected"        # 已拒绝
    CHANGES_REQUESTED = "changes_requested"  # 需要修改


class ReviewRequest(BaseModel):
    """审核请求"""
    review_id: str = Field(description="审核ID")
    country_code: str = Field(description="国家代码")
    country_name: str = Field(description="国家名称")
    submitter: str = Field(description="提交人")
    submitted_at: str = Field(description="提交时间")
    status: ReviewStatus = Field(description="审核状态", default=ReviewStatus.PENDING)

    # 审核内容
    changes: Dict[str, Any] = Field(description="变更内容")
    reason: str = Field(description="提交原因", default="")

    # 审核结果
    reviewer: Optional[str] = Field(description="审核人", default=None)
    reviewed_at: Optional[str] = Field(description="审核时间", default=None)
    review_comments: Optional[str] = Field(description="审核意见", default=None)


class ReviewStatistics(BaseModel):
    """审核统计"""
    total_reviews: int = Field(description="总审核数")
    pending_reviews: int = Field(description="待审核数")
    approved_reviews: int = Field(description="已通过数")
    rejected_reviews: int = Field(description="已拒绝数")
    changes_requested_reviews: int = Field(description="需修改数")


# ============================================================================
# 人工审核系统
# ============================================================================

class ManualReviewSystem:
    """人工审核系统"""

    def __init__(self, data_file: str = "data/config/review_requests.json"):
        """
        初始化审核系统

        Args:
            data_file: 审核请求数据文件路径
        """
        self.data_file = data_file
        self._ensure_data_file()

    def _ensure_data_file(self):
        """确保数据文件存在"""
        if not os.path.exists(self.data_file):
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            self._write_data({})

    def _read_data(self) -> Dict[str, Any]:
        """读取审核数据"""
        try:
            if not os.path.exists(self.data_file):
                return {}

            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[⚠️ 警告] 读取审核数据失败: {str(e)}")
            return {}

    def _write_data(self, data: Dict[str, Any]):
        """写入审核数据"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise ValueError(f"写入审核数据失败: {str(e)}")

    def submit_for_review(
        self,
        country_code: str,
        country_name: str,
        changes: Dict[str, Any],
        submitter: str,
        reason: str = ""
    ) -> str:
        """
        提交配置供人工审核

        Args:
            country_code: 国家代码
            country_name: 国家名称
            changes: 变更内容
            submitter: 提交人
            reason: 提交原因

        Returns:
            审核ID
        """
        # 生成审核ID
        review_id = str(uuid.uuid4())[:8]

        # 创建审核请求
        review_request = ReviewRequest(
            review_id=review_id,
            country_code=country_code,
            country_name=country_name,
            submitter=submitter,
            submitted_at=datetime.now().isoformat(),
            status=ReviewStatus.PENDING,
            changes=changes,
            reason=reason
        )

        # 保存到数据文件
        data = self._read_data()
        data[review_id] = review_request.model_dump()
        self._write_data(data)

        print(f"[✅ 成功] 已提交审核请求: {review_id}")
        print(f"   国家: {country_name} ({country_code})")
        print(f"   提交人: {submitter}")

        return review_id

    def get_review_request(self, review_id: str) -> Optional[ReviewRequest]:
        """
        获取审核请求

        Args:
            review_id: 审核ID

        Returns:
            ReviewRequest对象，如果不存在则返回None
        """
        data = self._read_data()

        if review_id not in data:
            return None

        try:
            return ReviewRequest(**data[review_id])
        except Exception as e:
            print(f"[⚠️ 警告] 解析审核请求失败 ({review_id}): {str(e)}")
            return None

    def list_review_requests(
        self,
        status: Optional[ReviewStatus] = None,
        country_code: Optional[str] = None
    ) -> List[ReviewRequest]:
        """
        列出审核请求

        Args:
            status: 按状态筛选（可选）
            country_code: 按国家代码筛选（可选）

        Returns:
            审核请求列表
        """
        data = self._read_data()
        requests = []

        for review_data in data.values():
            try:
                review = ReviewRequest(**review_data)

                # 应用筛选条件
                if status and review.status != status:
                    continue
                if country_code and review.country_code != country_code:
                    continue

                requests.append(review)
            except Exception as e:
                print(f"[⚠️ 警告] 跳过无效的审核请求: {str(e)}")
                continue

        # 按提交时间倒序排序
        requests.sort(key=lambda r: r.submitted_at, reverse=True)
        return requests

    def approve_review(
        self,
        review_id: str,
        reviewer: str,
        comments: str = ""
    ) -> bool:
        """
        审核通过

        Args:
            review_id: 审核ID
            reviewer: 审核人
            comments: 审核意见

        Returns:
            是否成功
        """
        data = self._read_data()

        if review_id not in data:
            print(f"[❌ 错误] 审核请求不存在: {review_id}")
            return False

        # 更新状态
        data[review_id]['status'] = ReviewStatus.APPROVED.value
        data[review_id]['reviewer'] = reviewer
        data[review_id]['reviewed_at'] = datetime.now().isoformat()
        data[review_id]['review_comments'] = comments

        self._write_data(data)

        print(f"[✅ 成功] 审核通过: {review_id}")
        print(f"   审核人: {reviewer}")
        if comments:
            print(f"   意见: {comments}")

        return True

    def reject_review(
        self,
        review_id: str,
        reviewer: str,
        reason: str
    ) -> bool:
        """
        审核拒绝

        Args:
            review_id: 审核ID
            reviewer: 审核人
            reason: 拒绝原因

        Returns:
            是否成功
        """
        data = self._read_data()

        if review_id not in data:
            print(f"[❌ 错误] 审核请求不存在: {review_id}")
            return False

        # 更新状态
        data[review_id]['status'] = ReviewStatus.REJECTED.value
        data[review_id]['reviewer'] = reviewer
        data[review_id]['reviewed_at'] = datetime.now().isoformat()
        data[review_id]['review_comments'] = reason

        self._write_data(data)

        print(f"[✅ 成功] 审核拒绝: {review_id}")
        print(f"   审核人: {reviewer}")
        print(f"   原因: {reason}")

        return True

    def request_changes(
        self,
        review_id: str,
        reviewer: str,
        comments: str
    ) -> bool:
        """
        请求修改

        Args:
            review_id: 审核ID
            reviewer: 审核人
            comments: 修改意见

        Returns:
            是否成功
        """
        data = self._read_data()

        if review_id not in data:
            print(f"[❌ 错误] 审核请求不存在: {review_id}")
            return False

        # 更新状态
        data[review_id]['status'] = ReviewStatus.CHANGES_REQUESTED.value
        data[review_id]['reviewer'] = reviewer
        data[review_id]['reviewed_at'] = datetime.now().isoformat()
        data[review_id]['review_comments'] = comments

        self._write_data(data)

        print(f"[✅ 成功] 请求修改: {review_id}")
        print(f"   审核人: {reviewer}")
        print(f"   意见: {comments}")

        return True

    def get_statistics(self) -> ReviewStatistics:
        """
        获取审核统计信息

        Returns:
            ReviewStatistics对象
        """
        data = self._read_data()

        stats = ReviewStatistics(
            total_reviews=len(data),
            pending_reviews=0,
            approved_reviews=0,
            rejected_reviews=0,
            changes_requested_reviews=0
        )

        for review_data in data.values():
            status = review_data.get('status', ReviewStatus.PENDING.value)
            if status == ReviewStatus.PENDING.value:
                stats.pending_reviews += 1
            elif status == ReviewStatus.APPROVED.value:
                stats.approved_reviews += 1
            elif status == ReviewStatus.REJECTED.value:
                stats.rejected_reviews += 1
            elif status == ReviewStatus.CHANGES_REQUESTED.value:
                stats.changes_requested_reviews += 1

        return stats

    def delete_review_request(self, review_id: str) -> bool:
        """
        删除审核请求

        Args:
            review_id: 审核ID

        Returns:
            是否成功
        """
        data = self._read_data()

        if review_id not in data:
            return False

        del data[review_id]
        self._write_data(data)

        print(f"[✅ 成功] 已删除审核请求: {review_id}")
        return True


# ============================================================================
# 辅助函数
# ============================================================================

def get_review_system() -> ManualReviewSystem:
    """获取全局审核系统实例"""
    return ManualReviewSystem()


if __name__ == "__main__":
    # 测试代码
    import sys

    review_system = ManualReviewSystem()

    # 测试：提交审核请求
    print("\n" + "="*80)
    print("测试：提交审核请求")
    print("="*80)

    changes = {
        "grade_subject_mappings": {
            "Kelas 1": {
                "available_subjects": [
                    {"local_name": "Matematika", "is_core": True}
                ]
            }
        }
    }

    review_id = review_system.submit_for_review(
        country_code="ID",
        country_name="Indonesia",
        changes=changes,
        submitter="system",
        reason="自动生成的年级-学科配对数据"
    )

    # 测试：获取审核请求
    print("\n" + "="*80)
    print("测试：获取审核请求")
    print("="*80)

    review = review_system.get_review_request(review_id)
    if review:
        print(f"审核ID: {review.review_id}")
        print(f"国家: {review.country_name}")
        print(f"状态: {review.status}")
        print(f"提交时间: {review.submitted_at}")

    # 测试：列出所有待审核请求
    print("\n" + "="*80)
    print("测试：列出待审核请求")
    print("="*80)

    pending_reviews = review_system.list_review_requests(status=ReviewStatus.PENDING)
    print(f"待审核数量: {len(pending_reviews)}")

    # 测试：审核通过
    print("\n" + "="*80)
    print("测试：审核通过")
    print("="*80)

    review_system.approve_review(
        review_id=review_id,
        reviewer="admin",
        comments="数据准确，审核通过"
    )

    # 测试：获取统计信息
    print("\n" + "="*80)
    print("测试：获取统计信息")
    print("="*80)

    stats = review_system.get_statistics()
    print(f"总审核数: {stats.total_reviews}")
    print(f"待审核数: {stats.pending_reviews}")
    print(f"已通过数: {stats.approved_reviews}")
    print(f"已拒绝数: {stats.rejected_reviews}")
    print(f"需修改数: {stats.changes_requested_reviews}")
