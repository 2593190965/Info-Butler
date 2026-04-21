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
    on_job_failure = "on_job_failure"
    on_job_success = "on_job_success"

    @staticmethod
    async def on_job_failure(ctx, job_id, exc):
        logger.error(f"Job {job_id} failed: {exc}")

    @staticmethod
    async def on_job_success(ctx, job_id, result):
        logger.info(f"Job {job_id} completed: {result}")
