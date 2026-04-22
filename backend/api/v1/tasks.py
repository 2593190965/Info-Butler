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

router = APIRouter()


@router.post("/batch", response_model=BatchImportResponse, status_code=202)
async def batch_import(
    body: BatchImportRequest,
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    task_ids = []

    for item in body.items:
        raw_info = await create_raw_info(
            db=db,
            source_type=item.source_type,
            content=item.content,
            user_id=uid,
            title=item.title,
        )
        if raw_info.source_type == "url" and not raw_info.source_url:
            raw_info.source_url = item.content
            await db.commit()

        if settings.app_env == "production":
            _job_id = await enqueue_digest(raw_info.task_id)
        else:
            try:
                await process_digest_sync(db, raw_info)
            except Exception:
                pass

        task_ids.append(raw_info.task_id)

    return BatchImportResponse(
        accepted=len(task_ids),
        task_ids=task_ids,
        message=f"Successfully submitted {len(task_ids)} items for processing",
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
