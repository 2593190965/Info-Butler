import logging
import re

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user_id
from backend.core.config import settings
from backend.core.database import get_db
from backend.models.raw_info import RawInfo
from backend.schemas.batch import BatchImportRequest, BatchImportResponse, TaskStatusResponse
from backend.services.digest_service import create_raw_info, process_digest_sync
from backend.workers.arq_client import enqueue_digest

logger = logging.getLogger(__name__)
router = APIRouter()

_SAFE_URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)


@router.post("/batch", response_model=BatchImportResponse, status_code=202)
async def batch_import(
    body: BatchImportRequest,
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    task_ids = []
    errors = []

    for i, item in enumerate(body.items):
        raw_info = await create_raw_info(
            db=db,
            source_type=item.source_type,
            content=item.content,
            user_id=uid,
            title=item.title,
        )
        if raw_info.source_type == "url" and not raw_info.source_url:
            url = item.content.strip()
            if _SAFE_URL_PATTERN.match(url):
                raw_info.source_url = url
            else:
                raw_info.source_url = None
                raw_info.status = "failed"
                raw_info.error_msg = "URL 必须以 http:// 或 https:// 开头"
            await db.commit()

        if settings.app_env == "production":
            try:
                _job_id = await enqueue_digest(raw_info.task_id)
            except Exception as e:
                logger.error(f"Failed to enqueue task {raw_info.task_id}: {e}")
                raw_info.status = "failed"
                raw_info.error_msg = f"Enqueue failed: {e}"
                await db.commit()
                errors.append({"index": i, "task_id": raw_info.task_id, "error": str(e)})
        else:
            try:
                await process_digest_sync(db, raw_info)
            except Exception as e:
                logger.error(f"Failed to process task {raw_info.task_id}: {e}")
                errors.append({"index": i, "task_id": raw_info.task_id, "error": str(e)})

        task_ids.append(raw_info.task_id)

    message = f"Submitted {len(task_ids)} items for processing"
    if errors:
        message += f", {len(errors)} failed"

    return BatchImportResponse(
        accepted=len(task_ids),
        task_ids=task_ids,
        message=message,
    )


@router.get("/status", response_model=TaskStatusResponse)
async def task_status(db: AsyncSession = Depends(get_db), uid: int = Depends(get_current_user_id)):
    total_result = await db.execute(select(func.count(RawInfo.id)).where(RawInfo.user_id == uid))
    total_submitted = total_result.scalar() or 0

    pending_result = await db.execute(
        select(func.count(RawInfo.id)).where(RawInfo.user_id == uid).where(RawInfo.status == "processing")
    )
    pending = pending_result.scalar() or 0

    done_result = await db.execute(
        select(func.count(RawInfo.id)).where(RawInfo.user_id == uid).where(RawInfo.status == "done")
    )
    done = done_result.scalar() or 0

    failed_result = await db.execute(
        select(func.count(RawInfo.id))
        .where(RawInfo.user_id == uid)
        .where(RawInfo.status.in_(["failed", "parse_error"]))
    )
    failed = failed_result.scalar() or 0

    recent_query = select(RawInfo).where(RawInfo.user_id == uid).order_by(RawInfo.created_at.desc()).limit(10)
    recent_result = await db.execute(recent_query)
    recent_items = recent_result.scalars().all()

    recent_tasks = [
        {
            "task_id": item.task_id,
            "title": item.title,
            "status": item.status,
            "source_type": item.source_type,
            "created_at": item.created_at.isoformat() if item.created_at else "",
        }
        for item in recent_items
    ]

    return TaskStatusResponse(
        total_submitted=total_submitted,
        pending=pending,
        done=done,
        failed=failed,
        recent_tasks=recent_tasks,
    )
