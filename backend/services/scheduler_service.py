"""定时任务调度服务"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backend.workers.tasks import send_due_reminders, send_overdue_reminders, send_scheduled_reminders

logger = logging.getLogger(__name__)


class SchedulerService:
    """定时任务调度服务"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

    def setup_jobs(self):
        """设置定时任务"""
        # 每天 9:00 发送截止提醒
        self.scheduler.add_job(
            send_due_reminders,
            "cron",
            hour=9,
            minute=0,
            id="send_due_reminders",
            replace_existing=True,
        )
        logger.info("Scheduled job: send_due_reminders at 9:00 daily")

        # 每天 14:00 发送逾期提醒
        self.scheduler.add_job(
            send_overdue_reminders,
            "cron",
            hour=14,
            minute=0,
            id="send_overdue_reminders",
            replace_existing=True,
        )
        logger.info("Scheduled job: send_overdue_reminders at 14:00 daily")

        # 每分钟检查精确时间提醒
        self.scheduler.add_job(
            send_scheduled_reminders,
            "cron",
            minute="*",
            id="send_scheduled_reminders",
            replace_existing=True,
        )
        logger.info("Scheduled job: send_scheduled_reminders every minute")

    def start(self):
        """启动调度器"""
        try:
            self.setup_jobs()
            self.scheduler.start()
            logger.info("Scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}", exc_info=True)
            raise

    def shutdown(self):
        """关闭调度器"""
        try:
            self.scheduler.shutdown()
            logger.info("Scheduler shutdown successfully")
        except Exception as e:
            logger.error(f"Error shutting down scheduler: {e}")


scheduler_service = SchedulerService()
