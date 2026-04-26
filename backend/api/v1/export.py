import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user_id
from backend.core.database import get_db
from backend.services.export_service import export_actions, export_digests

router = APIRouter()


@router.get("/digests")
async def export_digests_api(
    format: str = Query("markdown", pattern="^(markdown|json|csv)$"),
    status: str | None = Query(None, pattern="^(processing|done|failed|parse_error)$"),
    tags: list[str] = Query(default=[]),
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    content, media_type, filename = await export_digests(
        db=db,
        user_id=uid,
        fmt=format,
        status=status,
        tags=tags if tags else None,
    )

    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/actions")
async def export_actions_api(
    format: str = Query("csv", pattern="^(csv|json)$"),
    status: str | None = Query(None, pattern="^(pending|done|ignored)$"),
    priority: str | None = Query(None, pattern="^(high|medium|low)$"),
    db: AsyncSession = Depends(get_db),
    uid: int = Depends(get_current_user_id),
):
    content, media_type, filename = await export_actions(
        db=db,
        user_id=uid,
        fmt=format,
        status=status,
        priority=priority,
    )

    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
