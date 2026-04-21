import logging

logger = logging.getLogger(__name__)


async def process_digest(ctx, task_id: str):
    from backend.core.database import async_session
    from backend.services.digest_service import get_digest_by_task_id, process_digest_sync

    logger.info(f"Processing digest task: {task_id}")

    try:
        async with async_session() as db:
            raw_info = await get_digest_by_task_id(db, task_id)
            if not raw_info:
                logger.error(f"Task {task_id} not found")
                return {"status": "error", "reason": "not_found"}

            await process_digest_sync(db, raw_info)
            logger.info(f"Task {task_id} processed successfully")
            return {"status": "done", "info_id": raw_info.id}
    except Exception as e:
        logger.exception(f"Task {task_id} failed: {e}")
        raise
