from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user_id
from backend.core.database import get_db
from backend.schemas.tag import (
    BatchTagDelete,
    BatchTagRenameRequest,
    MergeTagsRequest,
    PaginatedTags,
    TagCreate,
    TagResponse,
    TagUpdate,
)
from backend.services.tag_service import (
    batch_delete_tags,
    batch_rename_tags,
    create_tag,
    delete_tag,
    get_tag_by_id,
    list_tags,
    merge_tags,
    update_tag,
)

router = APIRouter()


@router.get("", response_model=PaginatedTags)
async def tag_list(
    keyword: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    result = await list_tags(db=db, user_id=uid, keyword=keyword, page=page, page_size=page_size)
    return PaginatedTags(items=result["items"], total=result["total"])


@router.post("", response_model=TagResponse, status_code=201)
async def tag_create(
    body: TagCreate,
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    tag = await create_tag(db=db, name=body.name, user_id=uid)
    return TagResponse(
        id=tag.id,
        name=tag.name,
        info_count=0,
        action_count=0,
    )


@router.put("/{tag_id}", response_model=TagResponse)
async def tag_update(
    tag_id: int,
    body: TagUpdate,
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    tag = await get_tag_by_id(db, tag_id, uid)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    updated = await update_tag(db=db, tag=tag, name=body.name)
    return TagResponse(
        id=updated.id,
        name=updated.name,
        info_count=0,
        action_count=0,
    )


@router.delete("/{tag_id}")
async def tag_delete(
    tag_id: int,
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    deleted = await delete_tag(db=db, tag_id=tag_id, user_id=uid)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"deleted": True}


@router.delete("/batch")
async def batch_delete(
    body: BatchTagDelete,
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    """批量删除标签"""
    count = await batch_delete_tags(db, uid, body.ids)
    return {"deleted_count": count}


@router.post("/merge")
async def merge_tags_endpoint(
    body: MergeTagsRequest,
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    """合并标签"""
    count = await merge_tags(db, uid, body.source_ids, body.target_id)
    return {"merged_count": count}


@router.patch("/batch/rename")
async def batch_rename(
    body: BatchTagRenameRequest,
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    """批量重命名标签"""
    count = await batch_rename_tags(db, uid, [item.model_dump() for item in body.renames])
    return {"renamed_count": count}
