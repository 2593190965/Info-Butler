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


async def batch_delete_tags(db: AsyncSession, user_id: int, ids: list[int]) -> int:
    """批量删除标签"""
    # 验证所有标签都属于当前用户
    valid_result = await db.execute(select(Tag.id).where(Tag.id.in_(ids), Tag.user_id == user_id))
    valid_ids = [row[0] for row in valid_result.fetchall()]

    if not valid_ids:
        return 0

    # 删除关联
    await db.execute(info_tags_table.delete().where(info_tags_table.c.tag_id.in_(valid_ids)))
    await db.execute(action_tags_table.delete().where(action_tags_table.c.tag_id.in_(valid_ids)))

    # 删除标签
    result = await db.execute(Tag.__table__.delete().where(Tag.id.in_(valid_ids)))
    await db.commit()

    return result.rowcount


async def merge_tags(
    db: AsyncSession, user_id: int, source_ids: list[int], target_id: int
) -> int:
    """合并标签（将源标签的关联全部迁移到目标标签）"""
    # 验证目标标签存在且属于当前用户
    target_tag = await get_tag_by_id(db, target_id, user_id)
    if not target_tag:
        return 0

    # 验证源标签都属于当前用户，排除目标标签
    valid_source_result = await db.execute(
        select(Tag.id).where(
            Tag.id.in_(source_ids),
            Tag.user_id == user_id,
            Tag.id != target_id,
        )
    )
    valid_source_ids = [row[0] for row in valid_source_result.fetchall()]

    if not valid_source_ids:
        return 0

    # 迁移 info_tags 关联
    from sqlalchemy.dialects.mysql import insert as mysql_insert

    # 查询所有源标签关联的信息
    info_assoc_result = await db.execute(
        select(info_tags_table.c.info_id, info_tags_table.c.tag_id)
        .where(info_tags_table.c.tag_id.in_(valid_source_ids))
    )
    info_assocs = info_assoc_result.fetchall()

    # 为每个信息添加目标标签（使用 ON DUPLICATE KEY UPDATE 避免重复）
    for info_id, _ in info_assocs:
        stmt = mysql_insert(info_tags_table).values(info_id=info_id, tag_id=target_id)
        stmt = stmt.on_duplicate_key_update(info_id=stmt.inserted.info_id)
        await db.execute(stmt)

    # 迁移 action_tags 关联
    action_assoc_result = await db.execute(
        select(action_tags_table.c.action_id, action_tags_table.c.tag_id)
        .where(action_tags_table.c.tag_id.in_(valid_source_ids))
    )
    action_assocs = action_assoc_result.fetchall()

    for action_id, _ in action_assocs:
        stmt = mysql_insert(action_tags_table).values(action_id=action_id, tag_id=target_id)
        stmt = stmt.on_duplicate_key_update(action_id=stmt.inserted.action_id)
        await db.execute(stmt)

    # 删除源标签的关联
    await db.execute(info_tags_table.delete().where(info_tags_table.c.tag_id.in_(valid_source_ids)))
    await db.execute(action_tags_table.delete().where(action_tags_table.c.tag_id.in_(valid_source_ids)))

    # 删除源标签
    await db.execute(Tag.__table__.delete().where(Tag.id.in_(valid_source_ids)))
    await db.commit()

    return len(valid_source_ids)


async def batch_rename_tags(
    db: AsyncSession, user_id: int, renames: list[dict]
) -> int:
    """批量重命名标签"""
    count = 0
    for item in renames:
        tag_id = item["id"]
        new_name = item["new_name"]

        tag = await get_tag_by_id(db, tag_id, user_id)
        if tag:
            tag.name = new_name
            count += 1

    await db.commit()
    return count
