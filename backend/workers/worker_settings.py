import logging

from arq.connections import RedisSettings

from backend.core.config import settings

logger = logging.getLogger("arq.worker")


class WorkerSettings:
    functions = ["backend.workers.tasks.process_digest"]
    redis_settings = RedisSettings(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password or None,
        database=settings.redis_db,
        retry_on_timeout=True,
        socket_connect_timeout=10,
        socket_timeout=30,
    )
    max_jobs = 100
    job_timeout = 300
    max_tries = 3
    keep_cron_jobs = True

    @staticmethod
    async def on_job_failure(ctx, job_id, exc):
        logger.error(f"Job {job_id} failed: {exc}")
        try:
            from sqlalchemy import select, update

            from backend.core.database import async_session
            from backend.models.raw_info import RawInfo

            task_id = None
            if ctx:
                args = ctx.get("args", [])
                task_id = args[0] if args else None
            if not task_id:
                return

            async with async_session() as db:
                result = await db.execute(select(RawInfo.id).where(RawInfo.task_id == task_id))
                if result.scalar_one_or_none():
                    await db.execute(
                        update(RawInfo)
                        .where(RawInfo.task_id == task_id)
                        .values(status="failed", error_msg=f"ARQ job failed: {exc}")
                    )
                    await db.commit()
                    logger.info(f"Updated task {task_id} status to failed")
        except Exception as e:
            logger.error(f"Failed to update task status on job failure: {e}")

    @staticmethod
    async def on_job_success(ctx, job_id, result):
        logger.info(f"Job {job_id} completed: {result}")
