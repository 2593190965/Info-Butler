from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user_id
from backend.core.database import get_db
from backend.models.rss_subscription import RssSubscription
from backend.services import rss_service

router = APIRouter()


class RssCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    url: str = Field(..., min_length=1, max_length=2048)
    fetch_interval: int = Field(default=3600, ge=300, le=86400)


class RssUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    url: str | None = Field(None, min_length=1, max_length=2048)
    fetch_interval: int | None = Field(None, ge=300, le=86400)
    enabled: bool | None = None


class RssResponse(BaseModel):
    id: int
    name: str
    url: str
    fetch_interval: int
    last_fetch_at: str | None
    last_fetch_status: str | None
    article_count: int
    enabled: bool
    created_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=list[RssResponse])
async def list_rss(
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    subs = await rss_service.list_subscriptions(db, uid)
    return [
        RssResponse(
            id=s.id,
            name=s.name,
            url=s.url,
            fetch_interval=s.fetch_interval,
            last_fetch_at=s.last_fetch_at.isoformat() if s.last_fetch_at else None,
            last_fetch_status=s.last_fetch_status,
            article_count=s.article_count,
            enabled=bool(s.enabled),
            created_at=s.created_at.isoformat(),
        )
        for s in subs
    ]


@router.post("", response_model=RssResponse, status_code=201)
async def create_rss(
    body: RssCreate,
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    sub = await rss_service.create_subscription(db, uid, body.name, body.url, body.fetch_interval)
    return RssResponse(
        id=sub.id,
        name=sub.name,
        url=sub.url,
        fetch_interval=sub.fetch_interval,
        last_fetch_at=None,
        last_fetch_status=None,
        article_count=0,
        enabled=True,
        created_at=sub.created_at.isoformat(),
    )


@router.put("/{sub_id}", response_model=RssResponse)
async def update_rss(
    sub_id: int,
    body: RssUpdate,
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    sub = await rss_service.update_subscription(db, uid, sub_id, body.name, body.url, body.fetch_interval, body.enabled)
    if not sub:
        raise HTTPException(status_code=404, detail="RSS subscription not found")
    return RssResponse(
        id=sub.id,
        name=sub.name,
        url=sub.url,
        fetch_interval=sub.fetch_interval,
        last_fetch_at=sub.last_fetch_at.isoformat() if sub.last_fetch_at else None,
        last_fetch_status=sub.last_fetch_status,
        article_count=sub.article_count,
        enabled=bool(sub.enabled),
        created_at=sub.created_at.isoformat(),
    )


@router.delete("/{sub_id}")
async def delete_rss(
    sub_id: int,
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    deleted = await rss_service.delete_subscription(db, uid, sub_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="RSS subscription not found")
    return {"message": "Deleted"}


@router.post("/{sub_id}/fetch")
async def fetch_rss(
    sub_id: int,
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    result = await db.execute(
        select(RssSubscription).where(
            RssSubscription.id == sub_id,
            RssSubscription.user_id == uid,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="RSS subscription not found")

    fetch_result = await rss_service.fetch_and_process(db, sub, None)
    return fetch_result
