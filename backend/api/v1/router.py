from fastapi import APIRouter

from backend.api.v1.actions import router as actions_router
from backend.api.v1.digest import router as digest_router
from backend.api.v1.review import router as review_router
from backend.api.v1.tags import router as tags_router

api_router = APIRouter()
api_router.include_router(digest_router, prefix="/digest", tags=["Digest"])
api_router.include_router(actions_router, prefix="/actions", tags=["Actions"])
api_router.include_router(tags_router, prefix="/tags", tags=["Tags"])
api_router.include_router(review_router, prefix="/review", tags=["Review"])
