"""飞书账号绑定 API"""

import asyncio
import logging
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user_id
from backend.core.database import get_db
from backend.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

BINDING_CODE_BYTES = 8
BINDING_CODE_LENGTH = BINDING_CODE_BYTES * 2
BINDING_CODE_TTL_SECONDS = 300

_binding_codes: dict[str, dict] = {}
_binding_lock = asyncio.Lock()


class BindingCodeResponse(BaseModel):
    binding_code: str
    expires_in: int  # 秒
    instructions: str


class BindingStatusResponse(BaseModel):
    has_linked: bool
    feishu_open_id: str | None = None
    linked_at: str | None = None


@router.post("/generate-binding-code", response_model=BindingCodeResponse)
async def generate_binding_code(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    生成飞书账号绑定码

    用户需要：
    1. 在前端获取绑定码
    2. 在飞书中@机器人发送绑定码
    3. 系统自动完成绑定
    """
    # 检查是否已绑定
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.feishu_open_id:
        raise HTTPException(status_code=400, detail="已绑定飞书账号，如需重新绑定请先解绑")

    # 生成绑定码
    binding_code = secrets.token_hex(BINDING_CODE_BYTES).upper()

    # 存储绑定码（5分钟有效）
    expires_at = datetime.now(UTC) + timedelta(seconds=BINDING_CODE_TTL_SECONDS)
    _binding_codes[binding_code] = {
        "user_id": user_id,
        "expires_at": expires_at,
    }

    _cleanup_expired_codes()

    instructions = (
        f"请在飞书中@机器人发送以下绑定码：\n"
        f"`绑定 {binding_code}`\n\n"
        f"绑定码 5 分钟内有效，请尽快完成绑定。"
    )

    return BindingCodeResponse(
        binding_code=binding_code,
        expires_in=BINDING_CODE_TTL_SECONDS,
        instructions=instructions,
    )


async def bind_feishu_by_code(db: AsyncSession, binding_code: str, feishu_open_id: str) -> dict:
    """
    通过绑定码绑定飞书账号（服务内部调用，非 HTTP 端点）

    Args:
        db: 数据库会话
        binding_code: 绑定码
        feishu_open_id: 飞书用户 open_id

    Returns:
        {"success": bool, "message": str}
    """
    async with _binding_lock:
        if binding_code not in _binding_codes:
            return {"success": False, "message": "无效的绑定码"}

        code_info = _binding_codes[binding_code]

        if datetime.now(UTC) > code_info["expires_at"]:
            del _binding_codes[binding_code]
            return {"success": False, "message": "绑定码已过期"}

        user_id = code_info["user_id"]

        try:
            result = await db.execute(
                update(User).where(User.id == user_id).values(feishu_open_id=feishu_open_id)
            )
            await db.commit()
        except IntegrityError:
            await db.rollback()
            return {"success": False, "message": "该飞书账号已被其他用户绑定"}

        # 绑定成功后立即删除绑定码
        del _binding_codes[binding_code]

        logger.info(f"Successfully bound feishu_open_id {feishu_open_id[:6]}... to user {user_id}")
        return {"success": True, "message": "绑定成功", "user_id": user_id}


@router.get("/status", response_model=BindingStatusResponse)
async def get_binding_status(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """查询飞书账号绑定状态"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return BindingStatusResponse(
        has_linked=user.has_linked_feishu(),
        feishu_open_id=user.feishu_open_id,
        linked_at=None,
    )


@router.post("/unbind")
async def unbind_feishu_account(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """解绑飞书账号"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if not user.feishu_open_id:
        raise HTTPException(status_code=400, detail="未绑定飞书账号")

    # 解绑
    user.feishu_open_id = None
    await db.commit()

    logger.info(f"Unbound feishu account for user {user_id}")

    return {"message": "解绑成功"}


def _cleanup_expired_codes():
    """清理过期的绑定码"""
    now = datetime.now(UTC)
    expired_codes = [code for code, info in _binding_codes.items() if now > info["expires_at"]]
    for code in expired_codes:
        del _binding_codes[code]
