import csv
import io
import json
import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.action_item import ActionItem
from backend.models.raw_info import RawInfo
from backend.models.tag import Tag

logger = logging.getLogger(__name__)


def _build_markdown(data: list[dict]) -> str:
    lines = ["# 知识卡片导出\n", f"> 导出时间: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}\n"]
    for item in data:
        lines.append(f"## {item.get('title', '无标题')}\n")
        lines.append(f"**状态:** {item.get('status', 'unknown')}  ")
        lines.append(f"**来源:** {item.get('source_type', 'text')}\n")
        if item.get("tags"):
            lines.append(f"**标签:** {', '.join(item['tags'])}\n")
        lines.append(f"\n{item.get('summary', '无摘要')}\n")
        if item.get("action_items"):
            lines.append("\n**行动项:**\n")
            for a in item["action_items"]:
                lines.append(f"- [{a.get('priority', '?')}] {a.get('content', '')}\n")
        lines.append("\n---\n")
    return "\n".join(lines)


def _build_json(data: list[dict]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _build_csv(data: list[dict]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "标题", "摘要", "状态", "标签", "来源类型", "创建时间"])
    for item in data:
        tags = ", ".join(item.get("tags", []))
        writer.writerow(
            [
                item.get("id", ""),
                item.get("title", ""),
                item.get("summary", ""),
                item.get("status", ""),
                tags,
                item.get("source_type", ""),
                item.get("created_at", ""),
            ]
        )
    return output.getvalue()


def _build_actions_csv(data: list[dict]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "内容", "状态", "优先级", "标签", "关联卡片摘要", "创建时间"])
    for item in data:
        tags = ", ".join(item.get("tags", []))
        writer.writerow(
            [
                item.get("id", ""),
                item.get("content", ""),
                item.get("status", ""),
                item.get("priority", ""),
                tags,
                item.get("info_summary", ""),
                item.get("created_at", ""),
            ]
        )
    return output.getvalue()


async def export_digests(
    db: AsyncSession,
    user_id: int,
    fmt: str = "markdown",
    status: str | None = None,
    tags: list[str] | None = None,
) -> tuple[str, str, str]:
    query = select(RawInfo).where(RawInfo.user_id == user_id)
    if status:
        query = query.where(RawInfo.status == status)
    if tags:
        tag_names = [t for t in tags if t]
        if tag_names:
            from backend.models.tag import info_tags_table

            subq = (
                select(info_tags_table.c.info_id)
                .join(Tag, info_tags_table.c.tag_id == Tag.id)
                .where(Tag.name.in_(tag_names), Tag.user_id == user_id)
            )
            query = query.where(RawInfo.id.in_(subq))

    result = await db.execute(query.options(selectinload(RawInfo.tags), selectinload(RawInfo.action_items)))
    items = result.scalars().all()

    data = []
    for ri in items:
        tag_names = [t.name for t in ri.tags] if ri.tags else []
        action_items = []
        if ri.action_items:
            action_items = [{"content": a.content, "priority": a.priority, "status": a.status} for a in ri.action_items]
        data.append(
            {
                "id": ri.id,
                "title": ri.title or "",
                "summary": ri.summary or "",
                "status": ri.status,
                "source_type": ri.source_type,
                "tags": tag_names,
                "action_items": action_items,
                "created_at": ri.created_at.isoformat() if ri.created_at else "",
            }
        )

    if fmt == "json":
        content = _build_json(data)
        media_type = "application/json"
        filename = f"digests_{user_id}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
    elif fmt == "csv":
        content = _build_csv(data)
        media_type = "text/csv; charset=utf-8"
        filename = f"digests_{user_id}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.csv"
    else:
        content = _build_markdown(data)
        media_type = "text/markdown; charset=utf-8"
        filename = f"digests_{user_id}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.md"

    return content, media_type, filename


async def export_actions(
    db: AsyncSession,
    user_id: int,
    fmt: str = "csv",
    status: str | None = None,
    priority: str | None = None,
) -> tuple[str, str, str]:
    query = select(ActionItem).where(ActionItem.user_id == user_id)
    if status:
        query = query.where(ActionItem.status == status)
    if priority:
        query = query.where(ActionItem.priority == priority)

    result = await db.execute(query.options(selectinload(ActionItem.tags), selectinload(ActionItem.info)))
    items = result.scalars().all()

    data = []
    for ai in items:
        tag_names = [t.name for t in ai.tags] if ai.tags else []
        data.append(
            {
                "id": ai.id,
                "content": ai.content,
                "status": ai.status,
                "priority": ai.priority,
                "tags": tag_names,
                "info_summary": ai.info.summary if ai.info else "",
                "created_at": ai.created_at.isoformat() if ai.created_at else "",
            }
        )

    if fmt == "json":
        content = _build_json(data)
        media_type = "application/json"
        filename = f"actions_{user_id}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
    else:
        content = _build_actions_csv(data)
        media_type = "text/csv; charset=utf-8"
        filename = f"actions_{user_id}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.csv"

    return content, media_type, filename
