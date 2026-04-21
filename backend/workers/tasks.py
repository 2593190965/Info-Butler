import logging

from arq.connections import RedisSettings

logger = logging.getLogger(__name__)


async def process_digest(ctx, task_id: str):
    from backend.core.database import async_session
    from backend.services.digest_service import get_digest_by_task_id, process_digest_sync

    async with async_session() as db:
        raw_info = await get_digest_by_task_id(db, task_id)
        if not raw_info:
            logger.error(f"Task {task_id} not found")
            return {"status": "error", "reason": "not_found"}

        await process_digest_sync(db, raw_info)
        return {"status": "done", "info_id": raw_info.id}


class WorkerSettings:
    functions = [process_digest]
    redis_settings = RedisSettings(
        host="127.0.0.1",
        port=6379,
        database=0,
    )
