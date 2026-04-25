import logging
import re
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.action_item import ActionItem
from backend.models.raw_info import RawInfo

logger = logging.getLogger(__name__)

WEEK_START_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


async def get_weekly_review(
    db: AsyncSession,
    user_id: int,
    week_start: str | None = None,
) -> dict:
    if week_start:
        if not WEEK_START_PATTERN.match(week_start):
            from backend.core.exceptions import ValidationError

            raise ValidationError("week_start 格式无效，应为 YYYY-MM-DD")
        try:
            start = date.fromisoformat(week_start)
        except ValueError as e:
            from backend.core.exceptions import ValidationError

            raise ValidationError(f"week_start 日期无效: {e}")
    else:
        today = date.today()
        start = today - timedelta(days=today.weekday())

    end = start + timedelta(days=6)
    start_dt = datetime.combine(start, datetime.min.time(), tzinfo=UTC)
    end_dt = datetime.combine(end + timedelta(days=1), datetime.min.time(), tzinfo=UTC)

    new_info_result = await db.execute(
        select(func.count())
        .select_from(RawInfo)
        .where(RawInfo.user_id == user_id)
        .where(RawInfo.created_at >= start_dt)
        .where(RawInfo.created_at < end_dt)
        .where(RawInfo.status == "done")
    )
    new_info_count = new_info_result.scalar() or 0

    new_action_result = await db.execute(
        select(func.count())
        .select_from(ActionItem)
        .where(ActionItem.user_id == user_id)
        .where(ActionItem.created_at >= start_dt)
        .where(ActionItem.created_at < end_dt)
    )
    new_action_count = new_action_result.scalar() or 0

    done_action_result = await db.execute(
        select(func.count())
        .select_from(ActionItem)
        .where(ActionItem.user_id == user_id)
        .where(ActionItem.updated_at >= start_dt)
        .where(ActionItem.updated_at < end_dt)
        .where(ActionItem.status == "done")
    )
    done_action_count = done_action_result.scalar() or 0

    ignored_action_result = await db.execute(
        select(func.count())
        .select_from(ActionItem)
        .where(ActionItem.user_id == user_id)
        .where(ActionItem.updated_at >= start_dt)
        .where(ActionItem.updated_at < end_dt)
        .where(ActionItem.status == "ignored")
    )
    ignored_action_count = ignored_action_result.scalar() or 0

    completion_rate = round(done_action_count / max(new_action_count, 1), 2)

    pending_actions_query = (
        select(ActionItem)
        .where(ActionItem.user_id == user_id)
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
