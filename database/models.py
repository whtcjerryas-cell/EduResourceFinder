#!/usr/bin/env python3
"""
数据库模型定义
用于存储评估结果、搜索历史、优化指标等
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# 基类
Base = declarative_base()


# ============================================================================
# 数据库模型
# ============================================================================

class Evaluation(Base):
    """视频评估结果表"""
    __tablename__ = 'evaluations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_url = Column(String(500), unique=True, nullable=False, index=True)

    # 上下文信息
    country = Column(String(10))
    grade = Column(String(50))
    subject = Column(String(100))
    knowledge_point_id = Column(String(100))

    # 评估分数
    overall_score = Column(Float)
    visual_quality = Column(Float)
    relevance = Column(Float)
    pedagogy = Column(Float)
    metadata_score = Column(Float)

    # 多模态数据路径
    video_path = Column(String(500))
    frames_dir = Column(String(500))
    audio_path = Column(String(500))
    transcript = Column(Text)  # 字幕文本

    # 视频元数据
    duration = Column(Integer)  # 秒
    view_count = Column(Integer)
    upload_date = Column(String(20))
    channel = Column(String(200))

    # 状态
    status = Column(String(20))  # 'approved' or 'rejected'
    reject_reason = Column(String(500))

    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Evaluation(url={self.video_url}, score={self.overall_score}, status={self.status})>"


class SearchHistory(Base):
    """搜索历史表"""
    __tablename__ = 'search_history'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 搜索参数
    country = Column(String(10))
    grade = Column(String(50))
    subject = Column(String(100))
    query = Column(String(500))
    search_engine = Column(String(50))

    # 效果指标
    result_count = Column(Integer)
    avg_score = Column(Float)
    success_rate = Column(Float)

    # 成本
    api_calls = Column(Integer)
    tokens_used = Column(Integer)
    estimated_cost = Column(Float)

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, index=True)

    def __repr__(self):
        return f"<Search(query={self.query}, results={self.result_count})>"


class OptimizationMetrics(Base):
    """优化指标表"""
    __tablename__ = 'optimization_metrics'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 指标类型
    metric_type = Column(String(100), index=True)  # 'search_performance', 'evaluation_quality', etc.
    metric_name = Column(String(100))
    metric_value = Column(Float)

    # 策略信息
    strategy_version = Column(String(50))
    context = Column(Text)  # JSON 格式的上下文信息

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, index=True)

    def __repr__(self):
        return f"<Metric(type={self.metric_type}, name={self.metric_name}, value={self.metric_value})>"


class ABTest(Base):
    """A/B测试表"""
    __tablename__ = 'ab_tests'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 测试信息
    test_name = Column(String(200))
    strategy_a = Column(String(100))
    strategy_b = Column(String(100))

    # 测试结果
    metric_a = Column(Float)
    metric_b = Column(Float)
    is_significant = Column(Boolean)
    winner = Column(String(10))
    improvement = Column(Float)  # 百分比

    # 时间戳
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<ABTest(name={self.test_name}, winner={self.winner})>"


class TaskRecord(Base):
    """任务执行记录表"""
    __tablename__ = 'task_records'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 任务信息
    task_type = Column(String(50))  # 'search', 'download', 'evaluate', etc.
    task_id = Column(String(100), unique=True)

    # 任务参数
    country = Column(String(10))
    grade = Column(String(50))
    subject = Column(String(100))
    target_url = Column(String(500))

    # 执行状态
    status = Column(String(20))  # 'pending', 'running', 'success', 'failed'
    retry_count = Column(Integer, default=0)

    # 执行结果
    result = Column(Text)  # JSON 格式的结果
    error_message = Column(Text)

    # 执行时间
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, index=True)

    def __repr__(self):
        return f"<TaskRecord(type={self.task_type}, status={self.status}, url={self.target_url})>"


# ============================================================================
# 数据库管理
# ============================================================================

class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: str = None):
        """
        初始化数据库管理器

        Args:
            db_path: 数据库文件路径，默认为 data/education.db
        """
        if db_path is None:
            # 确保目录存在
            db_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, 'education.db')

        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # 创建所有表
        Base.metadata.create_all(self.engine)

        print(f"[✅ 数据库] 初始化成功: {db_path}")

    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()

    def drop_all_tables(self):
        """删除所有表（谨慎使用）"""
        Base.metadata.drop_all(self.engine)
        print("[⚠️ 数据库] 所有表已删除")

    def recreate_tables(self):
        """重建所有表"""
        self.drop_all_tables()
        Base.metadata.create_all(self.engine)
        print("[✅ 数据库] 所有表已重建")


# ============================================================================
# 便捷函数
# ============================================================================

# 全局数据库管理器实例
_db_manager = None


def get_db_manager(db_path: str = None) -> DatabaseManager:
    """获取数据库管理器单例"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path)
    return _db_manager


if __name__ == "__main__":
    # 测试代码
    db = get_db_manager()

    # 创建一些测试数据
    session = db.get_session()

    # 测试评估记录
    eval1 = Evaluation(
        video_url="https://www.youtube.com/watch?v=test1",
        country="ID",
        grade="Kelas 8",
        subject="Matematika",
        overall_score=8.5,
        visual_quality=9.0,
        relevance=8.0,
        pedagogy=8.5,
        status="approved"
    )
    session.add(eval1)

    # 测试搜索历史
    search1 = SearchHistory(
        country="ID",
        grade="Kelas 8",
        subject="Matematika",
        query="matematika kelas 8",
        search_engine="google",
        result_count=10,
        avg_score=7.5
    )
    session.add(search1)

    session.commit()

    # 查询数据
    evaluations = session.query(Evaluation).all()
    print(f"\n✅ 评估记录数: {len(evaluations)}")
    for eval in evaluations:
        print(f"  - {eval.video_url}: {eval.overall_score}")

    searches = session.query(SearchHistory).all()
    print(f"\n✅ 搜索记录数: {len(searches)}")
    for search in searches:
        print(f"  - {search.query}: {search.result_count}个结果")

    print("\n✅ 数据库测试完成！")
