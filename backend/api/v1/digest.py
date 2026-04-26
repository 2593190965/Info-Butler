import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user_id
from backend.core.config import settings
from backend.core.database import get_db
from backend.schemas.digest import (
    BatchAddTagsRequest,
    BatchDeleteRequest,
    BatchStatusUpdateRequest,
    DigestAccepted,
    DigestCreate,
    DigestListResponse,
    DigestResponse,
    PaginatedDigests,
)
from backend.services.digest_service import (
    batch_add_tags,
    batch_delete_digests,
    batch_update_status,
    create_raw_info,
    get_digest_by_task_id,
    list_digests,
    process_digest_sync,
)
from backend.workers.arq_client import enqueue_digest

router = APIRouter()

_SAFE_URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)


@router.post("", status_code=202, response_model=DigestAccepted)
async def create_digest(
    body: DigestCreate,
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    raw_info = await create_raw_info(
        db=db,
        source_type=body.source_type,
        content=body.content,
        user_id=uid,
        title=body.title,
    )

    if raw_info.source_type == "url" and not raw_info.source_url:
        url = body.content.strip()
        if not _SAFE_URL_PATTERN.match(url):
            raise HTTPException(status_code=400, detail="URL 必须以 http:// 或 https:// 开头")
        raw_info.source_url = url
        await db.commit()

    if settings.app_env == "production":
        await enqueue_digest(
            raw_info.task_id,
            generate_actions=body.generate_actions,
            generate_tags=body.generate_tags,
        )
    else:
        try:
            await process_digest_sync(
                db, raw_info, generate_actions=body.generate_actions, generate_tags=body.generate_tags
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Processing failed: {e}")

    return DigestAccepted(task_id=raw_info.task_id, status="processing")


@router.get("/{task_id}", response_model=DigestResponse)
async def get_digest(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    raw_info = await get_digest_by_task_id(db, task_id, uid)
    if not raw_info:
        raise HTTPException(status_code=404, detail="Task not found")

    tag_names = [t.name for t in raw_info.tags] if raw_info.tags else []

    action_items_data = []
    for ai in raw_info.action_items:
        action_items_data.append(
            {
                "id": ai.id,
                "content": ai.content,
                "status": ai.status,
                "priority": ai.priority,
            }
        )

    return DigestResponse(
        id=raw_info.id,
        task_id=raw_info.task_id,
        source_type=raw_info.source_type,
        source_url=raw_info.source_url,
        title=raw_info.title,
        summary=raw_info.summary,
        status=raw_info.status,
        tags=tag_names,
        action_items=action_items_data,
        created_at=raw_info.created_at.isoformat() if raw_info.created_at else "",
    )


@router.get("/{task_id}/related")
async def get_related_digests(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    raw_info = await get_digest_by_task_id(db, task_id, uid)
    if not raw_info:
        raise HTTPException(status_code=404, detail="Task not found")

    tag_names = [t.name for t in raw_info.tags] if raw_info.tags else []
    result = await list_digests(
        db=db,
        user_id=uid,
        page=1,
        page_size=5,
        status="done",
        tags=tag_names if tag_names else None,
        exclude_id=raw_info.id,
    )

    items = []
    for info in result["items"]:
        tag_list = [t.name for t in info.tags] if info.tags else []
        items.append(
            DigestListResponse(
                id=info.id,
                task_id=info.task_id,
                title=info.title,
                summary=info.summary,
                status=info.status,
                tags=tag_list,
                action_count=len(info.action_items) if info.action_items else 0,
                pending_action_count=(
                    sum(1 for a in info.action_items if a.status == "pending") if info.action_items else 0
                ),
                created_at=info.created_at.isoformat() if info.created_at else "",
            )
        )

    return PaginatedDigests(
        items=items,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.get("", response_model=PaginatedDigests)
async def digest_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    keyword: str | None = None,
    tags: str | None = None,
    exclude_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    tag_list = tags.split(",") if tags else None
    result = await list_digests(
        db=db,
        user_id=uid,
        page=page,
        page_size=page_size,
        status=status,
        keyword=keyword,
        tags=tag_list,
        exclude_id=exclude_id,
    )

    items = []
    for info in result["items"]:
        tag_names = [t.name for t in info.tags] if info.tags else []
        items.append(
            DigestListResponse(
                id=info.id,
                task_id=info.task_id,
                title=info.title,
                summary=info.summary,
                status=info.status,
                tags=tag_names,
                action_count=len(info.action_items) if info.action_items else 0,
                pending_action_count=(
                    sum(1 for a in info.action_items if a.status == "pending") if info.action_items else 0
                ),
                created_at=info.created_at.isoformat() if info.created_at else "",
            )
        )

    return PaginatedDigests(
        items=items,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.delete("/batch")
async def batch_delete(
    body: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    """批量删除知识卡片"""
    count = await batch_delete_digests(db, uid, body.ids)
    return {"deleted_count": count}


@router.patch("/batch/status")
async def batch_status_update(
    body: BatchStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    """批量更新知识卡片状态"""
    count = await batch_update_status(db, uid, body.ids, body.status)
    return {"updated_count": count}


@router.post("/batch/tags")
async def batch_add_tags_endpoint(
    body: BatchAddTagsRequest,
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    """批量为知识卡片添加标签"""
    count = await batch_add_tags(db, uid, body.ids, body.tag_ids)
    return {"updated_count": count}
