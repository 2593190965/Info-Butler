import hashlib
import json
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.database import get_db
from backend.services.feishu_bot_service import feishu_bot_service

router = APIRouter()
logger = logging.getLogger(__name__)

_processed_messages: dict[str, float] = {}
_DEDUP_TTL_SECONDS = 300


def _is_duplicate_message(message_id: str) -> bool:
    """基于 message_id 去重，防止飞书重推导致重复处理"""
    import time

    now = time.time()
    expired = [k for k, v in _processed_messages.items() if now - v > _DEDUP_TTL_SECONDS]
    for k in expired:
        del _processed_messages[k]

    if message_id in _processed_messages:
        return True
    _processed_messages[message_id] = now
    return False


def _decrypt_feishu_data(encrypt: str, key: str) -> str:
    """解密飞书加密数据（AES-256-CBC）"""
    import base64

    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    key_bytes = hashlib.sha256(key.encode()).digest()
    encrypt_bytes = base64.b64decode(encrypt)
    iv = encrypt_bytes[:16]
    cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv))
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(encrypt_bytes[16:]) + decryptor.finalize()
    # 去除 PKCS7 填充
    pad_len = decrypted[-1]
    decrypted = decrypted[:-pad_len]
    return decrypted.decode("utf-8")


class FeishuEvent(BaseModel):
    challenge: str | None = None
    token: str | None = None
    type: str | None = None
    event: dict | None = None


@router.post("/feishu")
async def feishu_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_lark_signature: str | None = Header(None),
    x_lark_request_timestamp: str | None = Header(None),
    x_lark_request_nonce: str | None = Header(None),
):
    """
    飞书事件回调处理

    支持的事件：
    - url_verification: 验证回调地址
    - im.message.receive_v1: 接收消息
    """
    try:
        raw_body = await request.body()
        body_str = raw_body.decode("utf-8")

        # 记录所有收到的请求（用于调试）
        logger.info(f"Received feishu request, length={len(body_str)}, has_encrypt={'encrypt' in body_str}, has_signature={x_lark_signature is not None}")

        body = json.loads(body_str)

        # 如果配置了 Encrypt Key 且数据有 encrypt 字段，需要解密
        if "encrypt" in body:
            if settings.feishu_encrypt_key:
                try:
                    decrypted_str = _decrypt_feishu_data(body["encrypt"], settings.feishu_encrypt_key)
                    body = json.loads(decrypted_str)
                    logger.info(f"Decrypted feishu event: {body.get('type', 'unknown')}")
                except Exception as decrypt_err:
                    logger.error(f"Failed to decrypt feishu data: {decrypt_err}", exc_info=True)
                    return {"code": 1, "msg": "Decryption failed"}
            else:
                logger.error("Received encrypted data but no ENCRYPT_KEY configured")
                return {"code": 1, "msg": "No encrypt key"}

        logger.info(f"Received feishu event: {body.get('type', 'unknown')}")

        # 1. URL 验证
        if body.get("type") == "url_verification":
            token = body.get("token")
            if settings.feishu_verification_token and token != settings.feishu_verification_token:
                logger.warning("Invalid verification token")
                return {"code": 1, "msg": "Invalid token"}

            challenge = body.get("challenge")
            logger.info("URL verification successful")
            return {"challenge": challenge}

        # 2. 签名验证（用解密前的原始 body 计算）
        if settings.feishu_encrypt_key and x_lark_signature and x_lark_request_timestamp:
            sign_base = f"{x_lark_request_timestamp}\n{x_lark_request_nonce}\n{body_str}\n"
            computed_sig = hashlib.sha256(
                (sign_base + settings.feishu_encrypt_key).encode()
            ).hexdigest()
            if computed_sig != x_lark_signature:
                logger.warning(f"Invalid signature, computed={computed_sig[:16]}... received={x_lark_signature[:16]}...")
                return {"code": 1, "msg": "Invalid signature"}

        # 3. 处理消息事件
        if body.get("type") == "event" or body.get("header", {}).get("event_type") == "im.message.receive_v1":
            return await handle_message_event(db, body)

        # 4. 其他事件类型
        logger.warning(f"Unhandled event type: {body.get('type')}")
        return {"code": 0, "msg": "Event type not handled"}

    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return {"code": 1, "msg": "Invalid JSON"}
    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        return {"code": 1, "msg": "Internal error"}


async def handle_message_event(db: AsyncSession, body: dict) -> dict:
    """
    处理消息事件

    Args:
        db: 数据库会话
        body: 事件请求体

    Returns:
        响应字典
    """
    event = body.get("event", {})
    message = event.get("message", {})
    chat = event.get("chat", {})

    # 提取消息信息
    message_id = message.get("message_id")
    message_type = message.get("message_type")
    chat_type = chat.get("chat_type", "p2p")  # p2p=私聊, group=群聊
    sender = event.get("sender", {})
    sender_id = sender.get("sender_id", {})
    open_id = sender_id.get("open_id")

    if not open_id:
        logger.warning("No open_id in message event")
        return {"code": 1, "msg": "No sender open_id"}

    # 消息去重：飞书可能重推同一事件
    if message_id and _is_duplicate_message(message_id):
        logger.info(f"Duplicate message {message_id}, skipping")
        return {"code": 0, "msg": "duplicate"}

    # 解析消息内容 - 支持多种消息类型
    content_str = message.get("content", "{}")
    try:
        content_data = json.loads(content_str)
    except json.JSONDecodeError:
        logger.error(f"Invalid message content JSON: {content_str}")
        return {"code": 1, "msg": "Invalid message content"}

    text = ""

    if message_type == "text":
        text = content_data.get("text", "").strip()
    elif message_type == "interactive":
        # 群聊中 @机器人 可能触发 interactive 类型
        # 尝试从不同字段提取文本
        action = content_data.get("action", {})
        if action:
            text = action.get("display", {}).get("text", "")
        if not text:
            text = content_data.get("display", {}).get("text", "")
        if not text:
            # interactive 消息可能包含 button 等元素，提取 label
            elements = content_data.get("elements", [])
            for elem in elements:
                if elem.get("tag") == "div":
                    text_elem = elem.get("text", {})
                    text = text_elem.get("content", "")
                    if text:
                        break
        text = text.strip()
    elif message_type == "post":
        # 富文本消息
        content_list = content_data.get("content", [])
        for line in content_list:
            for item in line:
                if item.get("tag") == "text":
                    text += item.get("text", "")
                elif item.get("tag") == "at":
                    # 跳过 @ 标记，只保留后面的文本
                    pass
        text = text.strip()

    if not text:
        logger.info(f"Empty or unsupported message type: {message_type}, content: {content_str[:200]}")
        return {"code": 0, "msg": "Empty or unsupported message"}

    # 移除 @机器人 的标记（飞书在 text 中用 @_user_1 这样的占位符）
    mentions = content_data.get("mentions", [])
    for mention in mentions:
        mention_key = mention.get("key", "")
        mention_name = mention.get("name", "")
        if mention_key:
            # 替换 @标记 为空，或替换为 @名字
            text = text.replace(mention_key, "").strip()

    # 额外清理：移除 @机器人名称 后的空格
    text = text.strip()

    if not text:
        logger.info("No content after removing mentions")
        return {"code": 0, "msg": "No content"}

    logger.info(f"Processing message from {open_id[:6]}... in {chat_type}: {text[:50]}...")

    # 调用飞书机器人服务处理消息
    try:
        chat_id = chat.get("chat_id")
        await feishu_bot_service.handle_message(
            db=db,
            open_id=open_id,
            message_id=message_id,
            text=text,
            chat_id=chat_id,
        )
        return {"code": 0, "msg": "success"}
    except Exception as e:
        logger.error(f"Failed to handle message: {e}", exc_info=True)
        return {"code": 1, "msg": "Processing failed"}
