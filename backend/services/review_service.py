import logging
import re
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.action_item import ActionItem
from backend.models.raw_info import RawInfo
from backend.models.tag import Tag, info_tags_table

logger = logging.getLogger(__name__)

WEEK_START_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


async def get_monthly_trends(
    db: AsyncSession,
    user_id: int,
    days: int = 30,
) -> dict:
    """获取近 N 天的趋势数据"""
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)
    start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=UTC)
    end_dt = datetime.combine(end_date + timedelta(days=1), datetime.min.time(), tzinfo=UTC)

    # 每日新增信息数
    daily_info_query = (
        select(
            func.date(RawInfo.created_at).label("date"),
            func.count().label("count"),
        )
        .where(RawInfo.user_id == user_id)
        .where(RawInfo.created_at >= start_dt)
        .where(RawInfo.created_at < end_dt)
        .where(RawInfo.status == "done")
        .group_by(func.date(RawInfo.created_at))
        .order_by(func.date(RawInfo.created_at))
    )
    daily_info_result = await db.execute(daily_info_query)
    daily_info_data = {}
    for row in daily_info_result:
        d = row.date if isinstance(row.date, date) else date.fromisoformat(str(row.date))
        daily_info_data[d] = row.count

    # 每日完成行动项数
    daily_done_query = (
        select(
            func.date(ActionItem.updated_at).label("date"),
            func.count().label("count"),
        )
        .where(ActionItem.user_id == user_id)
        .where(ActionItem.updated_at >= start_dt)
        .where(ActionItem.updated_at < end_dt)
        .where(ActionItem.status == "done")
        .group_by(func.date(ActionItem.updated_at))
        .order_by(func.date(ActionItem.updated_at))
    )
    daily_done_result = await db.execute(daily_done_query)
    daily_done_data = {}
    for row in daily_done_result:
        d = row.date if isinstance(row.date, date) else date.fromisoformat(str(row.date))
        daily_done_data[d] = row.count

    # 构造完整的日期序列
    date_list = []
    info_counts = []
    done_counts = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date.isoformat())
        info_counts.append(daily_info_data.get(current_date, 0))
        done_counts.append(daily_done_data.get(current_date, 0))
        current_date += timedelta(days=1)

    # 标签分布 Top 10
    tag_dist_query = (
        select(Tag.name, func.count(info_tags_table.c.info_id).label("count"))
        .join(info_tags_table, Tag.id == info_tags_table.c.tag_id)
        .where(Tag.user_id == user_id)
        .group_by(Tag.id)
        .order_by(func.count(info_tags_table.c.info_id).desc())
        .limit(10)
    )
    tag_dist_result = await db.execute(tag_dist_query)
    tag_distribution = [
        {"name": row.name, "value": row.count} for row in tag_dist_result
    ]

    return {
        "dates": date_list,
        "info_counts": info_counts,
        "done_counts": done_counts,
        "tag_distribution": tag_distribution,
    }


async def get_global_stats(
    db: AsyncSession,
    user_id: int,
) -> dict:
    """获取全局统计数据"""
    # 总卡片数
    total_info_result = await db.execute(
        select(func.count())
        .select_from(RawInfo)
        .where(RawInfo.user_id == user_id)
        .where(RawInfo.status == "done")
    )
    total_info = total_info_result.scalar() or 0

    # 总行动项数
    total_actions_result = await db.execute(
        select(func.count())
        .select_from(ActionItem)
        .where(ActionItem.user_id == user_id)
    )
    total_actions = total_actions_result.scalar() or 0

    # 已完成行动项数
    done_actions_result = await db.execute(
        select(func.count())
        .select_from(ActionItem)
        .where(ActionItem.user_id == user_id)
        .where(ActionItem.status == "done")
    )
    done_actions = done_actions_result.scalar() or 0

    # 待办行动项数
    pending_actions_result = await db.execute(
        select(func.count())
        .select_from(ActionItem)
        .where(ActionItem.user_id == user_id)
        .where(ActionItem.status == "pending")
    )
    pending_actions = pending_actions_result.scalar() or 0

    # 整体完成率
    completion_rate = round(done_actions / max(total_actions, 1), 2)

    # 最活跃标签 (使用次数最多)
    active_tag_query = (
        select(Tag.name, func.count(info_tags_table.c.info_id).label("count"))
        .join(info_tags_table, Tag.id == info_tags_table.c.tag_id)
        .where(Tag.user_id == user_id)
        .group_by(Tag.id)
        .order_by(func.count(info_tags_table.c.info_id).desc())
        .limit(1)
    )
    active_tag_result = await db.execute(active_tag_query)
    active_tag_row = active_tag_result.first()
    most_active_tag = active_tag_row.name if active_tag_row else None

    return {
        "total_info": total_info,
        "total_actions": total_actions,
        "done_actions": done_actions,
        "pending_actions": pending_actions,
        "completion_rate": completion_rate,
        "most_active_tag": most_active_tag,
    }


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
