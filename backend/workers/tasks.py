import logging

from sqlalchemy import update

logger = logging.getLogger(__name__)


async def process_digest(ctx, task_id: str, generate_actions: bool = True, generate_tags: bool = True):
    from backend.core.database import async_session
    from backend.models.raw_info import RawInfo
    from backend.services.digest_service import get_digest_by_task_id, process_digest_sync

    logger.info(f"Processing digest task: {task_id}, actions={generate_actions}, tags={generate_tags}")

    async with async_session() as db:
        raw_info = await get_digest_by_task_id(db, task_id)
        if not raw_info:
            logger.error(f"Task {task_id} not found")
            return {"status": "error", "reason": "not_found"}

        if raw_info.status == "done":
            logger.info(f"Task {task_id} already done, skipping")
            return {"status": "skipped", "reason": "already_done"}

        try:
            await process_digest_sync(
                db, raw_info, generate_actions=generate_actions, generate_tags=generate_tags
            )
            logger.info(f"Task {task_id} processed successfully")
            return {"status": "done", "info_id": raw_info.id}
        except Exception as e:
            logger.exception(f"Task {task_id} failed: {e}")
            try:
                await db.rollback()
                await db.execute(
                    update(RawInfo)
                    .where(RawInfo.task_id == task_id)
                    .values(status="failed", error_msg=f"Worker error: {e}")
                )
                await db.commit()
            except Exception as commit_err:
                logger.error(f"Failed to update status for task {task_id}: {commit_err}")
            raise
