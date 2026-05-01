import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.services.digest_service import create_raw_info, process_digest_sync

router = APIRouter()
logger = logging.getLogger(__name__)


class FeishuEvent(BaseModel):
    challenge: str | None = None
    token: str | None = None
    type: str | None = None


@router.post("/feishu")
async def feishu_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.json()

    if "challenge" in body:
        return {"challenge": body["challenge"]}

    event = body.get("event", {})
    message = event.get("message", {})
    message_type = message.get("message_type", "")
    content = message.get("content", "{}")

    import json

    try:
        content_data = json.loads(content)
    except json.JSONDecodeError:
        return {"code": 1, "msg": "Invalid message content"}

    text = content_data.get("text", "").strip()
    if not text:
        return {"code": 0, "msg": "Empty message"}

    mentions = content_data.get("mentions", [])
    for mention in mentions:
        text = text.replace(mention.get("key", ""), "")
    text = text.strip()

    if not text:
        return {"code": 0, "msg": "No content after removing mentions"}

    source_type = "url" if text.startswith("http") else "text"

    try:
        raw_info = await create_raw_info(
            db=db,
            source_type=source_type,
            content=text,
            user_id=1,
            title="飞书消息",
        )
        await process_digest_sync(db, raw_info)

        reply_text = f"✅ 处理完成\n\n摘要: {raw_info.summary or '无'}"
        if raw_info.action_items:
            reply_text += "\n\n行动项:"
            for item in raw_info.action_items[:3]:
                reply_text += f"\n- {item.content}"
        if raw_info.tags:
            tag_names = [t.name for t in raw_info.tags]
            reply_text += f"\n\n标签: {' '.join(tag_names)}"

        return {"code": 0, "msg": "success", "reply": reply_text}
    except Exception as e:
        logger.error(f"Feishu webhook processing failed: {e}")
        return {"code": 1, "msg": f"Processing failed: {str(e)}"}
