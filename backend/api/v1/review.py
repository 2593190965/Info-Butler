from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.core.database import get_db
from backend.services.review_service import get_weekly_review

router = APIRouter()


@router.get("/weekly")
async def weekly_review(
    week_start: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    result = await get_weekly_review(db=db, week_start=week_start)
    return result
