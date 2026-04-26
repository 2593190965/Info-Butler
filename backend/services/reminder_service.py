import logging
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.action_item import ActionItem
from backend.models.user import User

logger = logging.getLogger(__name__)


async def get_due_soon_actions(
    db: AsyncSession,
    user_id: int,
    days: int = 3,
) -> list[dict]:
    """获取即将到期的行动项"""
    today = date.today()
    deadline = today + timedelta(days=days)

    result = await db.execute(
        select(ActionItem)
        .where(ActionItem.user_id == user_id)
        .where(ActionItem.status == "pending")
        .where(ActionItem.due_date.isnot(None))
        .where(ActionItem.due_date <= deadline)
        .where(ActionItem.due_date >= today)
        .order_by(ActionItem.due_date.asc(), ActionItem.priority.desc())
        .options(selectinload(ActionItem.info))
    )
    items = result.scalars().all()

    return [
        {
            "id": a.id,
            "content": a.content,
            "priority": a.priority,
            "due_date": a.due_date.isoformat() if a.due_date else None,
            "days_left": (a.due_date - today).days if a.due_date else None,
            "info_summary": a.info.summary if a.info else None,
        }
        for a in items
    ]


async def get_overdue_actions(
    db: AsyncSession,
    user_id: int,
) -> list[dict]:
    """获取已逾期的行动项"""
    today = date.today()

    result = await db.execute(
        select(ActionItem)
        .where(ActionItem.user_id == user_id)
        .where(ActionItem.status == "pending")
        .where(ActionItem.due_date.isnot(None))
        .where(ActionItem.due_date < today)
        .order_by(ActionItem.due_date.asc(), ActionItem.priority.desc())
        .options(selectinload(ActionItem.info))
    )
    items = result.scalars().all()

    return [
        {
            "id": a.id,
            "content": a.content,
            "priority": a.priority,
            "due_date": a.due_date.isoformat() if a.due_date else None,
            "days_overdue": (today - a.due_date).days if a.due_date else None,
            "info_summary": a.info.summary if a.info else None,
        }
        for a in items
    ]


async def get_reminder_summary(
    db: AsyncSession,
    user_id: int,
) -> dict:
    """获取提醒汇总"""
    due_soon = await get_due_soon_actions(db, user_id, days=3)
    overdue = await get_overdue_actions(db, user_id)

    return {
        "due_soon_count": len(due_soon),
        "overdue_count": len(overdue),
        "due_soon": due_soon,
        "overdue": overdue,
    }
