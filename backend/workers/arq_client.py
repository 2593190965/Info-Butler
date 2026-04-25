import logging

from arq import create_pool
from arq.connections import RedisSettings

from backend.core.config import settings

logger = logging.getLogger(__name__)

_arq_pool = None


async def get_arq_pool():
    global _arq_pool
    if _arq_pool is None:
        _arq_pool = await create_pool(
            RedisSettings(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password or None,
                database=settings.redis_db,
            )
        )
    return _arq_pool


async def close_arq_pool():
    global _arq_pool
    if _arq_pool is not None:
        await _arq_pool.close()
        _arq_pool = None


async def enqueue_digest(
    task_id: str,
    generate_actions: bool = True,
    generate_tags: bool = True,
) -> str:
    pool = await get_arq_pool()
    job = await pool.enqueue_job(
        "process_digest",
        task_id,
        generate_actions,
        generate_tags,
    )
    logger.info(f"Enqueued digest task: {task_id}, job_id: {job.job_id}")
    return job.job_id
