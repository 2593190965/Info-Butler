from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user_id
from backend.core.database import get_db
from backend.services.review_service import get_global_stats, get_monthly_trends, get_weekly_review

router = APIRouter()


@router.get("/weekly")
async def weekly_review(
    week_start: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    result = await get_weekly_review(db=db, user_id=uid, week_start=week_start)
    return result


@router.get("/monthly")
async def monthly_trends(
    days: int = Query(30, ge=7, le=90, description="统计天数 (7-90)"),
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    result = await get_monthly_trends(db=db, user_id=uid, days=days)
    return result


@router.get("/stats")
async def global_stats(
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    result = await get_global_stats(db=db, user_id=uid)
    return result
