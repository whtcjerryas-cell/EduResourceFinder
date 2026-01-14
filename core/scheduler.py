#!/usr/bin/env python3
"""
定时任务调度器
使用APScheduler管理定时任务，支持自动更新、健康检查等
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import threading

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger_utils import get_logger

logger = get_logger('scheduler')


@dataclass
class ScheduledTask:
    """定时任务"""
    task_id: str
    name: str
    description: str
    trigger_type: str  # 'interval' or 'cron'
    trigger_params: Dict
    job_func: Callable
    enabled: bool = True
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    run_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None


class TaskScheduler:
    """任务调度器"""

    def __init__(self):
        """初始化任务调度器"""
        self.scheduler = BackgroundScheduler()
        self.tasks: Dict[str, ScheduledTask] = {}
        self.lock = threading.Lock()

        # 监听任务事件
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )

        logger.info("✅ 任务调度器初始化完成")

    def _job_executed_listener(self, event):
        """任务执行监听器"""
        if event.exception:
            # 任务执行出错
            job_id = event.job_id
            if job_id in self.tasks:
                with self.lock:
                    task = self.tasks[job_id]
                    task.error_count += 1
                    task.last_error = str(event.exception)
                    task.last_run = datetime.now().isoformat()

                logger.error(f"❌ 任务执行失败 [{task.name}]: {event.exception}")
        else:
            # 任务执行成功
            job_id = event.job_id
            if job_id in self.tasks:
                with self.lock:
                    task = self.tasks[job_id]
                    task.run_count += 1
                    task.last_run = datetime.now().isoformat()
                    task.last_error = None

                logger.info(f"✅ 任务执行成功 [{task.name}], 累计执行: {task.run_count}次")

    def add_interval_task(
        self,
        task_id: str,
        name: str,
        job_func: Callable,
        interval_seconds: int,
        description: str = "",
        enabled: bool = True
    ) -> ScheduledTask:
        """
        添加间隔任务

        Args:
            task_id: 任务ID
            name: 任务名称
            job_func: 任务函数
            interval_seconds: 间隔秒数
            description: 任务描述
            enabled: 是否启用

        Returns:
            创建的任务对象
        """
        with self.lock:
            if task_id in self.tasks:
                logger.warning(f"任务ID已存在: {task_id}")
                return self.tasks[task_id]

            # 创建任务对象
            task = ScheduledTask(
                task_id=task_id,
                name=name,
                description=description,
                trigger_type='interval',
                trigger_params={'seconds': interval_seconds},
                job_func=job_func,
                enabled=enabled
            )

            # 添加到调度器
            if enabled:
                job = self.scheduler.add_job(
                    job_func,
                    trigger=IntervalTrigger(seconds=interval_seconds),
                    id=task_id,
                    name=name,
                    replace_existing=True
                )

                # 更新下次运行时间
                task.next_run = job.next_run_time.isoformat() if job.next_run_time else None

            self.tasks[task_id] = task

            logger.info(f"✅ 添加间隔任务: {name} (间隔: {interval_seconds}秒)")

            return task

    def add_cron_task(
        self,
        task_id: str,
        name: str,
        job_func: Callable,
        cron_expr: str,
        description: str = "",
        enabled: bool = True
    ) -> ScheduledTask:
        """
        添加Cron任务

        Args:
            task_id: 任务ID
            name: 任务名称
            job_func: 任务函数
            cron_expr: Cron表达式 (分 时 日 月 周)
            description: 任务描述
            enabled: 是否启用

        Returns:
            创建的任务对象
        """
        with self.lock:
            if task_id in self.tasks:
                logger.warning(f"任务ID已存在: {task_id}")
                return self.tasks[task_id]

            # 解析Cron表达式
            parts = cron_expr.split()
            if len(parts) != 5:
                raise ValueError(f"无效的Cron表达式: {cron_expr}")

            minute, hour, day, month, day_of_week = parts

            # 创建任务对象
            task = ScheduledTask(
                task_id=task_id,
                name=name,
                description=description,
                trigger_type='cron',
                trigger_params={
                    'minute': minute,
                    'hour': hour,
                    'day': day,
                    'month': month,
                    'day_of_week': day_of_week
                },
                job_func=job_func,
                enabled=enabled
            )

            # 添加到调度器
            if enabled:
                job = self.scheduler.add_job(
                    job_func,
                    trigger=CronTrigger(
                        minute=minute,
                        hour=hour,
                        day=day,
                        month=month,
                        day_of_week=day_of_week
                    ),
                    id=task_id,
                    name=name,
                    replace_existing=True
                )

                # 更新下次运行时间
                task.next_run = job.next_run_time.isoformat() if job.next_run_time else None

            self.tasks[task_id] = task

            logger.info(f"✅ 添加Cron任务: {name} (Cron: {cron_expr})")

            return task

    def remove_task(self, task_id: str):
        """
        移除任务

        Args:
            task_id: 任务ID
        """
        with self.lock:
            if task_id not in self.tasks:
                logger.warning(f"任务不存在: {task_id}")
                return

            # 从调度器移除
            try:
                self.scheduler.remove_job(task_id)
            except Exception as e:
                logger.warning(f"移除任务失败: {str(e)}")

            # 从字典移除
            task = self.tasks.pop(task_id)
            logger.info(f"✅ 移除任务: {task.name}")

    def enable_task(self, task_id: str):
        """
        启用任务

        Args:
            task_id: 任务ID
        """
        with self.lock:
            if task_id not in self.tasks:
                logger.warning(f"任务不存在: {task_id}")
                return

            task = self.tasks[task_id]

            if task.enabled:
                logger.warning(f"任务已启用: {task.name}")
                return

            # 恢复任务
            try:
                if task.trigger_type == 'interval':
                    job = self.scheduler.add_job(
                        task.job_func,
                        trigger=IntervalTrigger(**task.trigger_params),
                        id=task_id,
                        name=task.name,
                        replace_existing=True
                    )
                else:  # cron
                    job = self.scheduler.add_job(
                        task.job_func,
                        trigger=CronTrigger(**task.trigger_params),
                        id=task_id,
                        name=task.name,
                        replace_existing=True
                    )

                task.enabled = True
                task.next_run = job.next_run_time.isoformat() if job.next_run_time else None

                logger.info(f"✅ 启用任务: {task.name}")

            except Exception as e:
                logger.error(f"启用任务失败: {str(e)}")

    def disable_task(self, task_id: str):
        """
        禁用任务

        Args:
            task_id: 任务ID
        """
        with self.lock:
            if task_id not in self.tasks:
                logger.warning(f"任务不存在: {task_id}")
                return

            task = self.tasks[task_id]

            if not task.enabled:
                logger.warning(f"任务已禁用: {task.name}")
                return

            # 暂停任务
            try:
                self.scheduler.pause_job(task_id)
                task.enabled = False
                task.next_run = None

                logger.info(f"✅ 禁用任务: {task.name}")

            except Exception as e:
                logger.error(f"禁用任务失败: {str(e)}")

    def run_task_now(self, task_id: str):
        """
        立即运行任务

        Args:
            task_id: 任务ID
        """
        with self.lock:
            if task_id not in self.tasks:
                logger.warning(f"任务不存在: {task_id}")
                return

            task = self.tasks[task_id]

            try:
                # 在新线程中执行任务
                import threading
                thread = threading.Thread(target=task.job_func)
                thread.start()

                logger.info(f"✅ 手动运行任务: {task.name}")

            except Exception as e:
                logger.error(f"运行任务失败: {str(e)}")

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态字典
        """
        with self.lock:
            if task_id not in self.tasks:
                return None

            task = self.tasks[task_id]

            return {
                'task_id': task.task_id,
                'name': task.name,
                'description': task.description,
                'trigger_type': task.trigger_type,
                'trigger_params': task.trigger_params,
                'enabled': task.enabled,
                'last_run': task.last_run,
                'next_run': task.next_run,
                'run_count': task.run_count,
                'error_count': task.error_count,
                'last_error': task.last_error
            }

    def get_all_tasks_status(self) -> List[Dict]:
        """
        获取所有任务状态

        Returns:
            任务状态列表
        """
        with self.lock:
            return [
                self.get_task_status(task_id)
                for task_id in self.tasks.keys()
            ]

    def start(self):
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("✅ 任务调度器已启动")

    def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("⏹️ 任务调度器已停止")

    def is_running(self) -> bool:
        """检查调度器是否运行中"""
        return self.scheduler.running


# ============================================================================
# 单例模式
# ============================================================================

_task_scheduler_instance = None
_scheduler_lock = threading.Lock()


def get_task_scheduler() -> TaskScheduler:
    """获取任务调度器单例"""
    global _task_scheduler_instance
    with _scheduler_lock:
        if _task_scheduler_instance is None:
            _task_scheduler_instance = TaskScheduler()
            # 自动启动
            _task_scheduler_instance.start()
        return _task_scheduler_instance


# ============================================================================
# 预定义任务
# ============================================================================

def setup_default_tasks():
    """设置默认任务"""
    from resource_updater import ResourceUpdater

    scheduler = get_task_scheduler()
    updater = ResourceUpdater()

    # 添加每日资源更新任务（凌晨2点执行）
    scheduler.add_cron_task(
        task_id='daily_resource_update',
        name='每日资源更新',
        job_func=updater.update_all_resources,
        cron_expr='0 2 * * *',  # 每天凌晨2点
        description='自动更新所有国家的教育资源'
    )

    # 添加每周健康检查任务（每周一上午9点）
    from health_checker import get_health_checker
    checker = get_health_checker()

    def weekly_health_check():
        results = checker.run_all_checks()
        # 保存报告
        report = checker.generate_health_report(results)
        report_file = f"health_check_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'reports',
            report_file
        )
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"✅ 健康检查报告已保存: {report_path}")

    scheduler.add_cron_task(
        task_id='weekly_health_check',
        name='每周健康检查',
        job_func=weekly_health_check,
        cron_expr='0 9 * * 1',  # 每周一上午9点
        description='每周系统健康检查并生成报告'
    )

    # 添加每5分钟心跳任务
    def heartbeat():
        logger.debug(f"💓 调度器心跳 - {datetime.now().isoformat()}")

    scheduler.add_interval_task(
        task_id='heartbeat',
        name='调度器心跳',
        job_func=heartbeat,
        interval_seconds=300,  # 5分钟
        description='定期检查调度器运行状态'
    )

    logger.info("✅ 默认任务设置完成")


# ============================================================================
# 命令行接口
# ============================================================================

if __name__ == "__main__":
    import argparse
    import time

    parser = argparse.ArgumentParser(description='任务调度器管理')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有任务')
    parser.add_argument('--start', action='store_true', help='启动调度器')
    parser.add_argument('--setup', action='store_true', help='设置默认任务')
    parser.add_argument('--run', '-r', help='立即运行指定任务')
    parser.add_argument('--enable', '-e', help='启用指定任务')
    parser.add_argument('--disable', '-d', help='禁用指定任务')

    args = parser.parse_args()

    # 获取调度器
    scheduler = get_task_scheduler()

    if args.setup:
        # 设置默认任务
        setup_default_tasks()
        print("✅ 默认任务设置完成")

    if args.list:
        # 列出所有任务
        print("\n" + "=" * 80)
        print("📋 任务列表")
        print("=" * 80)

        tasks = scheduler.get_all_tasks_status()

        if not tasks:
            print("暂无任务")
        else:
            for task in tasks:
                print(f"\n📌 {task['name']} ({task['task_id']})")
                print(f"   描述: {task['description']}")
                print(f"   状态: {'✅ 启用' if task['enabled'] else '❌ 禁用'}")
                print(f"   类型: {task['trigger_type']}")
                print(f"   参数: {task['trigger_params']}")
                print(f"   上次运行: {task['last_run'] or '未运行'}")
                print(f"   下次运行: {task['next_run'] or '未计划'}")
                print(f"   运行次数: {task['run_count']}")
                print(f"   错误次数: {task['error_count']}")

                if task['last_error']:
                    print(f"   最后错误: {task['last_error']}")

        print("\n" + "=" * 80)

    if args.run:
        # 立即运行任务
        scheduler.run_task_now(args.run)
        print(f"✅ 已触发任务: {args.run}")

    if args.enable:
        # 启用任务
        scheduler.enable_task(args.enable)
        print(f"✅ 已启用任务: {args.enable}")

    if args.disable:
        # 禁用任务
        scheduler.disable_task(args.disable)
        print(f"✅ 已禁用任务: {args.disable}")

    if args.start or (not args.list and not args.run and not args.enable and not args.disable and not args.setup):
        # 启动调度器（保持运行）
        print("\n" + "=" * 80)
        print("🚀 任务调度器正在运行...")
        print("=" * 80)
        print("按 Ctrl+C 停止")
        print("=" * 80 + "\n")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⏹️ 正在停止调度器...")
            scheduler.stop()
            print("✅ 调度器已停止")
