from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user_id
from backend.core.database import get_db
from backend.schemas.action_item import (
    ActionItemResponse,
    ActionItemUpdate,
    BatchActionAddTags,
    BatchActionDelete,
    BatchActionPriorityUpdate,
    BatchActionUpdate,
    PaginatedActions,
)
from backend.services.action_service import (
    batch_add_tags_to_actions,
    batch_delete_actions,
    batch_update_actions,
    batch_update_priority,
    get_action_by_id,
    list_actions,
    update_action,
)

router = APIRouter()


@router.get("", response_model=PaginatedActions)
async def action_list(
    status: str | None = Query(None, pattern="^(pending|done|ignored)$"),
    priority: str | None = Query(None, pattern="^(high|medium|low)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    result = await list_actions(
        db=db,
        user_id=uid,
        page=page,
        page_size=page_size,
        status=status,
        priority=priority,
    )

    items = []
    for ai in result["items"]:
        tag_names = [t.name for t in ai.tags] if hasattr(ai, "tags") and ai.tags else []
        info_summary = ai.info.summary if ai.info else None
        items.append(
            ActionItemResponse(
                id=ai.id,
                info_id=ai.info_id,
                content=ai.content,
                status=ai.status,
                priority=ai.priority,
                due_date=ai.due_date.isoformat() if ai.due_date else None,
                tags=tag_names,
                info_summary=info_summary,
                created_at=ai.created_at.isoformat() if ai.created_at else "",
            )
        )

    return PaginatedActions(
        items=items,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.patch("/batch", response_model=dict)
async def batch_update(
    body: BatchActionUpdate,
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    count = await batch_update_actions(db=db, user_id=uid, ids=body.ids, status=body.status)
    return {"updated_count": count}


@router.patch("/{action_id}", response_model=ActionItemResponse)
async def update_action_item(
    action_id: int,
    body: ActionItemUpdate,
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    action_item = await get_action_by_id(db, action_id, uid)
    if not action_item:
        raise HTTPException(status_code=404, detail="Action item not found")

    updated = await update_action(
        db=db,
        action_item=action_item,
        content=body.content,
        status=body.status,
        priority=body.priority,
        due_date=body.due_date,
    )

    tag_names = [t.name for t in updated.tags] if hasattr(updated, "tags") and updated.tags else []
    info_summary = updated.info.summary if updated.info else None
    return ActionItemResponse(
        id=updated.id,
        info_id=updated.info_id,
        content=updated.content,
        status=updated.status,
        priority=updated.priority,
        due_date=updated.due_date.isoformat() if updated.due_date else None,
        tags=tag_names,
        info_summary=info_summary,
        created_at=updated.created_at.isoformat() if updated.created_at else "",
    )


@router.delete("/batch")
async def batch_delete(
    body: BatchActionDelete,
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    """批量删除行动项"""
    count = await batch_delete_actions(db, uid, body.ids)
    return {"deleted_count": count}


@router.patch("/batch/priority")
async def batch_priority_update(
    body: BatchActionPriorityUpdate,
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    """批量更新行动项优先级"""
    count = await batch_update_priority(db, uid, body.ids, body.priority)
    return {"updated_count": count}


@router.post("/batch/tags")
async def batch_add_tags_endpoint(
    body: BatchActionAddTags,
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    """批量为行动项添加标签"""
    count = await batch_add_tags_to_actions(db, uid, body.ids, body.tag_ids)
    return {"updated_count": count}
