import json
import logging
import time
from typing import Any

import httpx

from backend.core.config import settings

logger = logging.getLogger(__name__)


class FeishuClient:
    def __init__(self):
        self.webhook_url = settings.feishu_webhook_url or ""
        self.app_id = settings.feishu_app_id
        self.app_secret = settings.feishu_app_secret
        self.client = httpx.AsyncClient(timeout=10.0)

        # Token 缓存
        self._tenant_access_token: str | None = None
        self._token_expire_time: float = 0

    async def get_tenant_access_token(self) -> str | None:
        """获取 tenant_access_token，自动缓存和刷新"""
        # 检查缓存是否有效（提前5分钟刷新）
        if self._tenant_access_token and time.time() < self._token_expire_time - 300:
            return self._tenant_access_token

        if not self.app_id or not self.app_secret:
            logger.error(
                "Feishu APP_ID or APP_SECRET not configured! "
                "Please follow FEISHU_SETUP_GUIDE.md to configure these values."
            )
            return None

        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = {"app_id": self.app_id, "app_secret": self.app_secret}

        try:
            resp = await self.client.post(url, json=payload)
            data = resp.json()

            if data.get("code") == 0:
                self._tenant_access_token = data.get("tenant_access_token")
                expire = data.get("expire", 7200)
                self._token_expire_time = time.time() + expire
                logger.info("Feishu tenant_access_token obtained successfully")
                return self._tenant_access_token
            else:
                logger.error(f"Failed to get tenant_access_token: {data}")
                return None
        except Exception as e:
            logger.error(f"Error getting tenant_access_token: {e}")
            return None

    async def send_message(self, open_id: str, msg_type: str, content: dict[str, Any]) -> bool:
        """发送消息给指定用户"""
        token = await self.get_tenant_access_token()
        if not token:
            logger.error("Cannot send message: no tenant_access_token")
            return False

        url = "https://open.feishu.cn/open-apis/im/v1/messages"
        params = {"receive_id_type": "open_id"}
        payload = {"receive_id": open_id, "msg_type": msg_type, "content": json.dumps(content, ensure_ascii=False)}
        headers = {"Authorization": f"Bearer {token}"}

        try:
            resp = await self.client.post(url, params=params, json=payload, headers=headers)
            data = resp.json()
            if data.get("code") == 0:
                logger.info(f"Message sent to {open_id} successfully")
                return True
            else:
                logger.error(f"Failed to send message: {data}")
                return False
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    async def reply_message(self, message_id: str, msg_type: str, content: dict[str, Any]) -> bool:
        """回复消息"""
        token = await self.get_tenant_access_token()
        if not token:
            logger.error("Cannot reply message: no tenant_access_token")
            return False

        url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply"
        payload = {"msg_type": msg_type, "content": json.dumps(content, ensure_ascii=False)}
        headers = {"Authorization": f"Bearer {token}"}

        try:
            resp = await self.client.post(url, json=payload, headers=headers)
            data = resp.json()
            if data.get("code") == 0:
                logger.info(f"Replied to message {message_id} successfully")
                return True
            else:
                logger.error(f"Failed to reply message: {data}")
                return False
        except Exception as e:
            logger.error(f"Error replying message: {e}")
            return False

    async def get_user_info(self, open_id: str) -> dict[str, Any] | None:
        """获取用户信息"""
        token = await self.get_tenant_access_token()
        if not token:
            logger.error("Cannot get user info: no tenant_access_token")
            return None

        url = f"https://open.feishu.cn/open-apis/user/v3/{open_id}"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            resp = await self.client.get(url, headers=headers)
            data = resp.json()
            if data.get("code") == 0:
                return data.get("data", {}).get("user")
            else:
                logger.error(f"Failed to get user info: {data}")
                return None
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None

    async def send_text(self, text: str) -> bool:
        """通过 Webhook 发送文本消息（兼容旧逻辑）"""
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
                logger.info("Feishu message sent successfully via webhook")
                return True
            else:
                logger.error(f"Feishu webhook API error: {data}")
                return False
        except Exception as e:
            logger.error(f"Feishu webhook send failed: {e}")
            return False

    async def send_notification(self, open_id: str, text: str) -> bool:
        """
        发送通知消息给用户

        优先使用应用 API 发送，失败时回退到 Webhook
        """
        # 优先使用应用 API 发送
        if self.app_id and self.app_secret:
            success = await self.send_message(open_id, "text", {"text": text})
            if success:
                return True
            logger.warning("App API send failed, falling back to webhook")

        # 回退到 Webhook
        if self.webhook_url:
            return await self.send_text(text)

        logger.warning("No way to send notification: both app API and webhook unavailable")
        return False

    async def send_digest_summary(
        self,
        title: str,
        summary: str,
        tags: list[str],
        action_items: list[dict],
        status: str = "done",
        open_id: str | None = None,
    ):
        # 构建消息文本
        if status != "done":
            text = f"⚠️ 信息处理失败\n标题: {title}\n状态: {status}"
            if open_id:
                return await self.send_notification(open_id, text)
            return await self.send_text(text)

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

        text = "\n".join(lines)

        if open_id:
            return await self.send_notification(open_id, text)
        return await self.send_text(text)

    async def close(self):
        await self.client.aclose()


feishu_client = FeishuClient()
