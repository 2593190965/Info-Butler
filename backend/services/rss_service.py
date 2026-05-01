import hashlib
import logging
from datetime import datetime

import feedparser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.rss_subscription import RssSubscription

logger = logging.getLogger(__name__)


async def list_subscriptions(db: AsyncSession, user_id: int) -> list[RssSubscription]:
    result = await db.execute(
        select(RssSubscription).where(RssSubscription.user_id == user_id).order_by(RssSubscription.created_at.desc())
    )
    return list(result.scalars().all())


async def create_subscription(
    db: AsyncSession,
    user_id: int,
    name: str,
    url: str,
    fetch_interval: int = 3600,
) -> RssSubscription:
    sub = RssSubscription(
        user_id=user_id,
        name=name,
        url=url,
        fetch_interval=fetch_interval,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


async def update_subscription(
    db: AsyncSession,
    user_id: int,
    sub_id: int,
    name: str | None = None,
    url: str | None = None,
    fetch_interval: int | None = None,
    enabled: bool | None = None,
) -> RssSubscription | None:
    result = await db.execute(
        select(RssSubscription).where(
            RssSubscription.id == sub_id,
            RssSubscription.user_id == user_id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return None

    if name is not None:
        sub.name = name
    if url is not None:
        sub.url = url
    if fetch_interval is not None:
        sub.fetch_interval = fetch_interval
    if enabled is not None:
        sub.enabled = 1 if enabled else 0

    await db.commit()
    await db.refresh(sub)
    return sub


async def delete_subscription(db: AsyncSession, user_id: int, sub_id: int) -> bool:
    result = await db.execute(
        select(RssSubscription).where(
            RssSubscription.id == sub_id,
            RssSubscription.user_id == user_id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return False
    await db.delete(sub)
    await db.commit()
    return True


def parse_feed(url: str) -> list[dict]:
    try:
        feed = feedparser.parse(url)
        if not feed.entries:
            logger.warning(f"No entries found for RSS feed: {url}")
            return []

        articles = []
        for entry in feed.entries:
            link = entry.get("link", "")
            title = entry.get("title", "")
            content = ""
            if "content" in entry:
                content = "\n".join(c.get("value", "") for c in entry.content)
            elif "summary" in entry:
                content = entry.summary

            article_hash = hashlib.md5(f"{link}{title}".encode()).hexdigest()

            articles.append(
                {
                    "title": title,
                    "content": content,
                    "url": link,
                    "published": entry.get("published", ""),
                    "hash": article_hash,
                }
            )
        return articles
    except Exception as e:
        logger.error(f"Failed to parse RSS feed {url}: {e}")
        return []


async def fetch_and_process(
    db: AsyncSession,
    sub: RssSubscription,
) -> dict:
    articles = parse_feed(sub.url)
    if not articles:
        sub.last_fetch_status = "failed"
        sub.last_fetch_at = datetime.now()
        await db.commit()
        return {"fetched": 0, "new": 0, "errors": 0}

    sub.last_fetch_at = datetime.now()
    sub.last_fetch_status = "success"
    sub.article_count += len(articles)

    new_count = 0
    error_count = 0

    for article in articles:
        try:
            from backend.services.digest_service import create_raw_info, process_digest_sync

            raw_info = await create_raw_info(
                db=db,
                source_type="url",
                content=article["url"] if article["url"] else article["content"],
                user_id=sub.user_id,
                title=article["title"] or sub.name,
            )
            await process_digest_sync(db, raw_info)
            new_count += 1
        except Exception as e:
            logger.error(f"Failed to process article {article['title']}: {e}")
            error_count += 1

    await db.commit()
    return {"fetched": len(articles), "new": new_count, "errors": error_count}
