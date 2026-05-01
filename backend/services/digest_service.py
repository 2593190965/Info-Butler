import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.dialects.mysql import insert as mysql_insert
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


async def process_digest_sync(
    db: AsyncSession,
    raw_info: RawInfo,
    generate_actions: bool = True,
    generate_tags: bool = True,
) -> None:
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
            await db.delete(raw_info)
            await db.commit()
            return

        raw_info.summary = validated.summary
        raw_info.status = "done"

        tag_ids = []
        if generate_tags and validated.tags:
            for tag_name in validated.tags:
                stmt = mysql_insert(Tag).values(user_id=uid, name=tag_name)
                stmt = stmt.on_duplicate_key_update(id=stmt.inserted.id)
                result = await db.execute(stmt)
                tag_id = result.inserted_primary_key[0]
                if tag_id is None:
                    existing = await db.execute(select(Tag.id).where(Tag.name == tag_name, Tag.user_id == uid).limit(1))
                    tag_id = existing.scalar_one()
                tag_ids.append(tag_id)

            await db.execute(info_tags_table.delete().where(info_tags_table.c.info_id == raw_info.id))
            for tid in tag_ids:
                await db.execute(info_tags_table.insert().values(info_id=raw_info.id, tag_id=tid))

        if generate_actions and validated.action_items:
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
        await db.rollback()
        await db.delete(raw_info)
        await db.commit()
        logger.error(f"Dify call failed for task {raw_info.task_id}: {e}")
    except Exception as e:
        await db.rollback()
        await db.delete(raw_info)
        await db.commit()
        logger.error(f"Unexpected error processing task {raw_info.task_id}: {e}")


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
    exclude_id: int | None = None,
):
    query = select(RawInfo).where(RawInfo.user_id == user_id)

    if status:
        query = query.where(RawInfo.status == status)

    if keyword:
        from sqlalchemy import text

        safe_keyword = keyword.replace("'", "''").replace('"', '""')
        count_sql = text(
            "SELECT COUNT(*) FROM raw_infos WHERE user_id = :uid "
            "AND MATCH(raw_text, summary, title) AGAINST(:kw IN BOOLEAN MODE)"
        )
        count_result = await db.execute(count_sql, {"uid": user_id, "kw": safe_keyword})
        total = count_result.scalar() or 0

        offset = (page - 1) * page_size
        search_sql = text(
            "SELECT id FROM raw_infos WHERE user_id = :uid "
            "AND MATCH(raw_text, summary, title) AGAINST(:kw IN BOOLEAN MODE) "
            "ORDER BY MATCH(raw_text, summary, title) AGAINST(:kw IN BOOLEAN MODE) DESC "
            "LIMIT :limit OFFSET :offset"
        )
        search_result = await db.execute(
            search_sql,
            {
                "uid": user_id,
                "kw": safe_keyword,
                "limit": page_size,
                "offset": offset,
            },
        )
        info_ids = [row[0] for row in search_result]

        if info_ids:
            query = (
                select(RawInfo)
                .where(RawInfo.id.in_(info_ids))
                .options(selectinload(RawInfo.tags), selectinload(RawInfo.action_items))
            )
            result = await db.execute(query)
            items = result.scalars().all()
            items.sort(key=lambda x: info_ids.index(x.id))
        else:
            items = []

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    if tags:
        tag_names = [t for t in tags if t]
        if tag_names:
            subq = (
                select(info_tags_table.c.info_id)
                .join(Tag, info_tags_table.c.tag_id == Tag.id)
                .where(Tag.name.in_(tag_names), Tag.user_id == user_id)
            )
            query = query.where(RawInfo.id.in_(subq))

    if exclude_id is not None:
        query = query.where(RawInfo.id != exclude_id)

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


STUCK_PROCESSING_TIMEOUT_MINUTES = 30


async def cleanup_stuck_processing(db: AsyncSession) -> int:
    cutoff = datetime.now(UTC) - timedelta(minutes=STUCK_PROCESSING_TIMEOUT_MINUTES)
    result = await db.execute(
        update(RawInfo)
        .where(RawInfo.status == "processing", RawInfo.created_at < cutoff)
        .values(status="failed", error_msg="Processing timed out")
    )
    await db.commit()
    count = result.rowcount
    if count > 0:
        logger.warning(f"Cleaned up {count} stuck-in-processing records")
    return count


async def batch_delete_digests(db: AsyncSession, user_id: int, ids: list[int]) -> int:
    """批量删除知识卡片（级联删除关联的行动项和标签关联）"""
    # 验证所有 ID 都属于当前用户
    result = await db.execute(select(RawInfo.id).where(RawInfo.id.in_(ids), RawInfo.user_id == user_id))
    valid_ids = [row[0] for row in result.fetchall()]

    if not valid_ids:
        return 0

    # 删除关联的行动项标签
    action_ids_result = await db.execute(select(ActionItem.id).where(ActionItem.info_id.in_(valid_ids)))
    action_ids = [row[0] for row in action_ids_result.fetchall()]

    if action_ids:
        await db.execute(action_tags_table.delete().where(action_tags_table.c.action_id.in_(action_ids)))
        await db.execute(ActionItem.__table__.delete().where(ActionItem.id.in_(action_ids)))

    # 删除知识卡片标签关联
    await db.execute(info_tags_table.delete().where(info_tags_table.c.info_id.in_(valid_ids)))

    # 删除知识卡片
    result = await db.execute(RawInfo.__table__.delete().where(RawInfo.id.in_(valid_ids)))
    await db.commit()

    count = result.rowcount
    logger.info(f"Batch deleted {count} digests for user {user_id}")
    return count


async def batch_update_status(db: AsyncSession, user_id: int, ids: list[int], status: str) -> int:
    """批量更新知识卡片状态"""
    result = await db.execute(
        update(RawInfo).where(RawInfo.id.in_(ids), RawInfo.user_id == user_id).values(status=status)
    )
    await db.commit()

    count = result.rowcount
    logger.info(f"Batch updated status to '{status}' for {count} digests")
    return count


async def batch_add_tags(db: AsyncSession, user_id: int, ids: list[int], tag_ids: list[int]) -> int:
    """批量为知识卡片添加标签"""
    # 验证所有知识卡片和标签都属于当前用户
    valid_info_result = await db.execute(select(RawInfo.id).where(RawInfo.id.in_(ids), RawInfo.user_id == user_id))
    valid_info_ids = [row[0] for row in valid_info_result.fetchall()]

    valid_tag_result = await db.execute(select(Tag.id).where(Tag.id.in_(tag_ids), Tag.user_id == user_id))
    valid_tag_ids = [row[0] for row in valid_tag_result.fetchall()]

    if not valid_info_ids or not valid_tag_ids:
        return 0

    # 批量插入标签关联（使用 ON DUPLICATE KEY UPDATE 避免重复）
    for info_id in valid_info_ids:
        for tag_id in valid_tag_ids:
            stmt = mysql_insert(info_tags_table).values(info_id=info_id, tag_id=tag_id)
            stmt = stmt.on_duplicate_key_update(info_id=stmt.inserted.info_id)
            await db.execute(stmt)

    await db.commit()
    logger.info(f"Batch added {len(valid_tag_ids)} tags to {len(valid_info_ids)} digests")
    return len(valid_info_ids)
