from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.action_item import ActionItem
from backend.models.raw_info import RawInfo


async def get_weekly_review(
    db: AsyncSession,
    week_start: str | None = None,
) -> dict:
    if week_start:
        start = date.fromisoformat(week_start)
    else:
        today = date.today()
        start = today - timedelta(days=today.weekday())

    end = start + timedelta(days=6)

    new_info_result = await db.execute(
        select(func.count())
        .select_from(RawInfo)
        .where(RawInfo.created_at >= start)
        .where(RawInfo.created_at <= end)
        .where(RawInfo.status == "done")
    )
    new_info_count = new_info_result.scalar() or 0

    new_action_result = await db.execute(
        select(func.count())
        .select_from(ActionItem)
        .where(ActionItem.created_at >= start)
        .where(ActionItem.created_at <= end)
    )
    new_action_count = new_action_result.scalar() or 0

    done_action_result = await db.execute(
        select(func.count())
        .select_from(ActionItem)
        .where(ActionItem.updated_at >= start)
        .where(ActionItem.updated_at <= end)
        .where(ActionItem.status == "done")
    )
    done_action_count = done_action_result.scalar() or 0

    ignored_action_result = await db.execute(
        select(func.count())
        .select_from(ActionItem)
        .where(ActionItem.updated_at >= start)
        .where(ActionItem.updated_at <= end)
        .where(ActionItem.status == "ignored")
    )
    ignored_action_count = ignored_action_result.scalar() or 0

    completion_rate = round(done_action_count / max(new_action_count, 1), 2)

    pending_actions_query = (
        select(ActionItem)
        .where(ActionItem.status == "pending")
        .order_by(ActionItem.priority.desc(), ActionItem.created_at.asc())
        .limit(5)
    )
    pending_actions = (await db.execute(pending_actions_query)).scalars().all()

    return {
        "week_start": start.isoformat(),
        "week_end": end.isoformat(),
        "new_info_count": new_info_count,
        "new_action_count": new_action_count,
        "done_action_count": done_action_count,
        "ignored_action_count": ignored_action_count,
        "completion_rate": completion_rate,
        "top_tags": [],
        "pending_actions": [
            {
                "id": a.id,
                "content": a.content,
                "priority": a.priority,
            }
            for a in pending_actions
        ],
    }
