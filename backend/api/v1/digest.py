from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.core.database import get_db
from backend.schemas.digest import (
    DigestAccepted,
    DigestCreate,
    DigestListResponse,
    DigestResponse,
    PaginatedDigests,
)
from backend.services.digest_service import (
    create_raw_info,
    get_digest_by_task_id,
    list_digests,
    process_digest_sync,
)

router = APIRouter()


@router.post("", status_code=202, response_model=DigestAccepted)
async def create_digest(
    body: DigestCreate,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    raw_info = await create_raw_info(
        db=db,
        source_type=body.source_type,
        content=body.content,
        title=body.title,
    )

    if raw_info.source_type == "url" and not raw_info.source_url:
        raw_info.source_url = body.content
        await db.commit()

    try:
        await process_digest_sync(db, raw_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")

    return DigestAccepted(task_id=raw_info.task_id, status="done")


@router.get("/{task_id}", response_model=DigestResponse)
async def get_digest(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    raw_info = await get_digest_by_task_id(db, task_id)
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


@router.get("", response_model=PaginatedDigests)
async def digest_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    keyword: str | None = None,
    tags: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    tag_list = tags.split(",") if tags else None
    result = await list_digests(
        db=db,
        page=page,
        page_size=page_size,
        status=status,
        keyword=keyword,
        tags=tag_list,
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
