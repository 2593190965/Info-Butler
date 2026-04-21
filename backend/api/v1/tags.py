from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.core.database import get_db
from backend.schemas.tag import PaginatedTags, TagCreate, TagResponse, TagUpdate
from backend.services.tag_service import (
    create_tag,
    delete_tag,
    get_tag_by_id,
    list_tags,
    update_tag,
)

router = APIRouter()


@router.get("", response_model=PaginatedTags)
async def tag_list(
    keyword: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    result = await list_tags(db=db, keyword=keyword, page=page, page_size=page_size)
    return PaginatedTags(items=result["items"], total=result["total"])


@router.post("", response_model=TagResponse, status_code=201)
async def tag_create(
    body: TagCreate,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    tag = await create_tag(db=db, name=body.name)
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
    _user: str = Depends(get_current_user),
):
    tag = await get_tag_by_id(db, tag_id)
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
    _user: str = Depends(get_current_user),
):
    deleted = await delete_tag(db=db, tag_id=tag_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"deleted": True}
