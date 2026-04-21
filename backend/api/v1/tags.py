from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.core.database import get_db
from backend.services.tag_service import list_tags

router = APIRouter()


@router.get("", response_model=dict)
async def tag_list(
    keyword: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    result = await list_tags(db=db, keyword=keyword)
    return {"code": 0, "data": {"items": result["items"]}, "message": "ok"}
