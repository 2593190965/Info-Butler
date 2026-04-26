from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.action_item import ActionItem
from backend.models.tag import Tag, action_tags_table


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


async def batch_delete_actions(db: AsyncSession, user_id: int, ids: list[int]) -> int:
    """批量删除行动项"""
    # 删除关联的标签
    await db.execute(action_tags_table.delete().where(action_tags_table.c.action_id.in_(ids)))

    # 删除行动项
    result = await db.execute(
        ActionItem.__table__.delete().where(ActionItem.id.in_(ids), ActionItem.user_id == user_id)
    )
    await db.commit()
    return result.rowcount


async def batch_update_priority(db: AsyncSession, user_id: int, ids: list[int], priority: str) -> int:
    """批量更新行动项优先级"""
    result = await db.execute(
        update(ActionItem)
        .where(ActionItem.id.in_(ids), ActionItem.user_id == user_id)
        .values(priority=priority)
    )
    await db.commit()
    return result.rowcount


async def batch_add_tags_to_actions(
    db: AsyncSession, user_id: int, action_ids: list[int], tag_ids: list[int]
) -> int:
    """批量为行动项添加标签"""
    # 验证所有行动项和标签都属于当前用户
    valid_action_result = await db.execute(
        select(ActionItem.id).where(ActionItem.id.in_(action_ids), ActionItem.user_id == user_id)
    )
    valid_action_ids = [row[0] for row in valid_action_result.fetchall()]

    valid_tag_result = await db.execute(
        select(Tag.id).where(Tag.id.in_(tag_ids), Tag.user_id == user_id)
    )
    valid_tag_ids = [row[0] for row in valid_tag_result.fetchall()]

    if not valid_action_ids or not valid_tag_ids:
        return 0

    # 批量插入标签关联
    from sqlalchemy.dialects.mysql import insert as mysql_insert

    for action_id in valid_action_ids:
        for tag_id in valid_tag_ids:
            stmt = mysql_insert(action_tags_table).values(action_id=action_id, tag_id=tag_id)
            stmt = stmt.on_duplicate_key_update(action_id=stmt.inserted.action_id)
            await db.execute(stmt)

    await db.commit()
    return len(valid_action_ids)
