from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tag import Tag, info_tags_table


async def list_tags(
    db: AsyncSession,
    keyword: str | None = None,
):
    query = select(Tag)

    if keyword:
        query = query.where(Tag.name.ilike(f"%{keyword}%"))

    result = await db.execute(query)
    tags = result.scalars().all()

    items = []
    for tag in tags:
        count_query = select(func.count()).select_from(info_tags_table).where(info_tags_table.c.tag_id == tag.id)
        info_count = (await db.execute(count_query)).scalar() or 0
        items.append(
            {
                "id": tag.id,
                "name": tag.name,
                "info_count": info_count,
                "action_count": 0,
            }
        )

    return {"items": items}
