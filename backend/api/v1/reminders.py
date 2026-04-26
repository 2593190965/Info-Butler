from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user_id
from backend.core.database import get_db
from backend.services.reminder_service import get_due_soon_actions, get_overdue_actions, get_reminder_summary

router = APIRouter()


@router.get("/summary")
async def reminder_summary(
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    result = await get_reminder_summary(db=db, user_id=uid)
    return result


@router.get("/due-soon")
async def due_soon(
    days: int = 3,
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    result = await get_due_soon_actions(db=db, user_id=uid, days=days)
    return {"items": result}


@router.get("/overdue")
async def overdue(
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    result = await get_overdue_actions(db=db, user_id=uid)
    return {"items": result}
