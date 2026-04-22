import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.clients.dify_client import dify_client
from backend.clients.feishu_client import feishu_client
from backend.clients.scraper_client import scraper_client
from backend.models.action_item import ActionItem
from backend.models.raw_info import RawInfo
from backend.models.tag import Tag, action_tags_table, info_tags_table

logger = logging.getLogger(__name__)


async def create_raw_info(
    db: AsyncSession,
    source_type: str,
    content: str,
    user_id: int,
    title: str | None = None,
) -> RawInfo:
    raw_info = RawInfo(
        user_id=user_id,
        source_type=source_type,
        raw_text=content,
        title=title,
        status="processing",
    )
    db.add(raw_info)
    await db.commit()
    await db.refresh(raw_info)
    return raw_info


async def process_digest_sync(db: AsyncSession, raw_info: RawInfo) -> None:
    text = raw_info.raw_text
    uid = raw_info.user_id

    logger.info(f"Processing task {raw_info.task_id}: type={raw_info.source_type}, url={raw_info.source_url}")

    if raw_info.source_type == "url" and raw_info.source_url:
        try:
            result = await scraper_client.fetch_url(raw_info.source_url)
            text = result["text"] or text
            logger.info(f"URL fetched for {raw_info.task_id}: title={result['title'][:50]}, text_len={len(text)}")
            if result["title"]:
                raw_info.title = result["title"]
            await db.commit()
        except Exception as e:
            raw_info.status = "failed"
            raw_info.error_msg = f"URL fetch failed: {e}"
            await db.commit()
            logger.error(f"URL fetch failed for task {raw_info.task_id}: {e}")
            return

    try:
        dify_result = await dify_client.run_workflow(text, raw_info.source_type)

        validated = dify_client.validate_response(dify_result)
        if not validated:
            raw_info.status = "parse_error"
            raw_info.dify_raw_response = dify_result
            raw_info.error_msg = "Dify response validation failed"
            await db.commit()
            return

        raw_info.summary = validated.summary
        raw_info.status = "done"

        tag_ids = []
        for tag_name in validated.tags:
            existing = await db.execute(select(Tag).where(Tag.name == tag_name, Tag.user_id == uid).limit(1))
            tag_obj = existing.scalar_one_or_none()
            if not tag_obj:
                tag_obj = Tag(user_id=uid, name=tag_name)
                db.add(tag_obj)
                await db.flush()
            tag_ids.append(tag_obj.id)

        await db.execute(info_tags_table.delete().where(info_tags_table.c.info_id == raw_info.id))
        for tid in tag_ids:
            await db.execute(info_tags_table.insert().values(info_id=raw_info.id, tag_id=tid))

        for action_data in validated.action_items:
            action_item = ActionItem(
                user_id=uid,
                info_id=raw_info.id,
                content=action_data.content,
                priority=action_data.priority,
                status="pending",
            )
            db.add(action_item)
            await db.flush()

            for tid in tag_ids:
                await db.execute(action_tags_table.insert().values(action_id=action_item.id, tag_id=tid))

        await db.commit()

        action_items_list = [{"content": a.content, "priority": a.priority} for a in validated.action_items]
        tag_names = validated.tags

        await feishu_client.send_digest_summary(
            title=raw_info.title or "",
            summary=validated.summary,
            tags=tag_names,
            action_items=action_items_list,
            status="done",
        )

    except ValueError as e:
        raw_info.status = "failed"
        raw_info.error_msg = str(e)
        await db.commit()
        logger.error(f"Dify call failed for task {raw_info.task_id}: {e}")
        await feishu_client.send_digest_summary(
            title=raw_info.title or "",
            summary="",
            tags=[],
            action_items=[],
            status="failed",
        )
    except Exception as e:
        raw_info.status = "failed"
        raw_info.error_msg = f"Unexpected error: {e}"
        await db.commit()
        logger.error(f"Unexpected error processing task {raw_info.task_id}: {e}")
        await feishu_client.send_digest_summary(
            title=raw_info.title or "",
            summary="",
            tags=[],
            action_items=[],
            status="failed",
        )


async def get_digest_by_task_id(db: AsyncSession, task_id: str, user_id: int | None = None) -> RawInfo | None:
    query = select(RawInfo).where(RawInfo.task_id == task_id)
    if user_id is not None:
        query = query.where(RawInfo.user_id == user_id)
    result = await db.execute(query.options(selectinload(RawInfo.tags), selectinload(RawInfo.action_items)))
    return result.scalar_one_or_none()


async def list_digests(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    keyword: str | None = None,
    tags: list[str] | None = None,
):
    query = select(RawInfo).where(RawInfo.user_id == user_id)

    if status:
        query = query.where(RawInfo.status == status)

    if keyword:
        like_pattern = f"%{keyword}%"
        query = query.where((RawInfo.summary.ilike(like_pattern)) | (RawInfo.raw_text.ilike(like_pattern)))

    if tags:
        tag_names = [t for t in tags if t]
        if tag_names:
            subq = (
                select(info_tags_table.c.info_id)
                .join(Tag, info_tags_table.c.tag_id == Tag.id)
                .where(Tag.name.in_(tag_names), Tag.user_id == user_id)
            )
            query = query.where(RawInfo.id.in_(subq))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    query = (
        query.order_by(RawInfo.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .options(selectinload(RawInfo.tags), selectinload(RawInfo.action_items))
    )
    result = await db.execute(query)
    items = result.scalars().all()

    return {"items": items, "total": total, "page": page, "page_size": page_size}
