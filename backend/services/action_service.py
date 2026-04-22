from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.action_item import ActionItem


async def list_actions(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    priority: str | None = None,
):
    query = select(ActionItem).where(ActionItem.user_id == user_id)

    if status:
        query = query.where(ActionItem.status == status)
    if priority:
        query = query.where(ActionItem.priority == priority)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    query = (
        query.order_by(ActionItem.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .options(selectinload(ActionItem.tags), selectinload(ActionItem.info))
    )
    result = await db.execute(query)
    items = result.scalars().all()

    return {"items": items, "total": total, "page": page, "page_size": page_size}


async def get_action_by_id(db: AsyncSession, action_id: int, user_id: int) -> ActionItem | None:
    result = await db.execute(
        select(ActionItem)
        .where(ActionItem.id == action_id, ActionItem.user_id == user_id)
        .options(selectinload(ActionItem.tags), selectinload(ActionItem.info))
    )
    return result.scalar_one_or_none()


async def update_action(
    db: AsyncSession,
    action_item: ActionItem,
    status: str | None = None,
    priority: str | None = None,
    due_date: str | None = None,
) -> ActionItem:
    if status is not None:
        action_item.status = status
    if priority is not None:
        action_item.priority = priority
    if due_date is not None:
        from datetime import date

        action_item.due_date = date.fromisoformat(due_date)

    await db.commit()
    await db.refresh(action_item)
    return action_item


async def batch_update_actions(
    db: AsyncSession,
    user_id: int,
    ids: list[int],
    status: str,
) -> int:
    stmt = (
        update(ActionItem)
        .where(ActionItem.id.in_(ids), ActionItem.user_id == user_id)
        .values(status=status)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount
