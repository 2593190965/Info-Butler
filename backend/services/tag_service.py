from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tag import Tag, action_tags_table, info_tags_table


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


async def list_tags(
    db: AsyncSession,
    user_id: int,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 50,
):
    query = select(Tag).where(Tag.user_id == user_id)

    if keyword:
        query = query.where(Tag.name.ilike(f"%{_escape_like(keyword)}%", escape="\\"))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    query = query.order_by(Tag.name).offset(offset).limit(page_size)
    result = await db.execute(query)
    tags = result.scalars().all()

    if not tags:
        return {"items": [], "total": total}

    tag_ids = [tag.id for tag in tags]

    info_counts_q = (
        select(info_tags_table.c.tag_id, func.count().label("cnt"))
        .where(info_tags_table.c.tag_id.in_(tag_ids))
        .group_by(info_tags_table.c.tag_id)
    )
    info_counts_rows = (await db.execute(info_counts_q)).all()
    info_counts = {row.tag_id: row.cnt for row in info_counts_rows}

    action_counts_q = (
        select(action_tags_table.c.tag_id, func.count().label("cnt"))
        .where(action_tags_table.c.tag_id.in_(tag_ids))
        .group_by(action_tags_table.c.tag_id)
    )
    action_counts_rows = (await db.execute(action_counts_q)).all()
    action_counts = {row.tag_id: row.cnt for row in action_counts_rows}

    items = [
        {
            "id": tag.id,
            "name": tag.name,
            "info_count": info_counts.get(tag.id, 0),
            "action_count": action_counts.get(tag.id, 0),
        }
        for tag in tags
    ]

    return {"items": items, "total": total}


async def get_tag_by_id(db: AsyncSession, tag_id: int, user_id: int) -> Tag | None:
    result = await db.execute(select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id))
    return result.scalar_one_or_none()


async def get_tag_by_name(db: AsyncSession, name: str, user_id: int) -> Tag | None:
    result = await db.execute(select(Tag).where(Tag.name == name, Tag.user_id == user_id))
    return result.scalar_one_or_none()


async def create_tag(db: AsyncSession, name: str, user_id: int) -> Tag:
    existing = await get_tag_by_name(db, name, user_id)
    if existing:
        return existing
    tag = Tag(user_id=user_id, name=name)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


async def update_tag(db: AsyncSession, tag: Tag, name: str) -> Tag:
    tag.name = name
    await db.commit()
    await db.refresh(tag)
    return tag


async def delete_tag(db: AsyncSession, tag_id: int, user_id: int) -> bool:
    tag = await get_tag_by_id(db, tag_id, user_id)
    if not tag:
        return False
    await db.execute(info_tags_table.delete().where(info_tags_table.c.tag_id == tag_id))
    await db.execute(action_tags_table.delete().where(action_tags_table.c.tag_id == tag_id))
    await db.delete(tag)
    await db.commit()
    return True
