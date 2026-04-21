import json
import logging

import httpx

from backend.core.config import settings

logger = logging.getLogger(__name__)


class FeishuClient:
    def __init__(self):
        self.webhook_url = settings.feishu_webhook_url or ""
        self.client = httpx.AsyncClient(timeout=10.0)

    async def send_text(self, text: str) -> bool:
        if not self.webhook_url:
            logger.debug("Feishu webhook URL not configured, skipping")
            return False

        payload = {
            "msg_type": "text",
            "content": json.dumps({"text": text}, ensure_ascii=False),
        }

        try:
            resp = await self.client.post(self.webhook_url, json=payload)
            data = resp.json()
            if data.get("code") == 0:
                logger.info("Feishu message sent successfully")
                return True
            else:
                logger.error(f"Feishu API error: {data}")
                return False
        except Exception as e:
            logger.error(f"Feishu send failed: {e}")
            return False

    async def send_digest_summary(
        self,
        title: str,
        summary: str,
        tags: list[str],
        action_items: list[dict],
        status: str = "done",
    ):
        if not self.webhook_url:
            return False

        if status != "done":
            await self.send_text(f"⚠️ 信息处理失败\n标题: {title}\n状态: {status}")
            return True

        tag_str = " ".join(f"#{t}" for t in tags) if tags else ""

        lines = [
            f"📋 **{title}**" if title else "📋 **新信息处理完成**",
            "",
            f"> {summary}",
            "",
        ]

        if tag_str:
            lines.append(tag_str)

        if action_items:
            lines.append("")
            lines.append("**行动项:**")
            for i, item in enumerate(action_items[:5], 1):
                priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(item.get("priority", ""), "⚪")
                lines.append(f"{i}. {priority_icon} {item.get('content', '')}")

        await self.send_text("\n".join(lines))

    async def close(self):
        await self.client.aclose()


feishu_client = FeishuClient()
