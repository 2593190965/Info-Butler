from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user_id
from backend.core.database import get_db
from backend.services.review_service import get_weekly_review

router = APIRouter()


@router.get("/weekly")
async def weekly_review(
    week_start: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    result = await get_weekly_review(db=db, user_id=uid, week_start=week_start)
    return result
