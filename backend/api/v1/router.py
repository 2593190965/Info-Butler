from fastapi import APIRouter

from backend.api.v1.actions import router as actions_router
from backend.api.v1.auth import router as auth_router
from backend.api.v1.digest import router as digest_router
from backend.api.v1.export import router as export_router
from backend.api.v1.feishu_binding import router as feishu_binding_router
from backend.api.v1.reminders import router as reminders_router
from backend.api.v1.review import router as review_router
from backend.api.v1.rss import router as rss_router
from backend.api.v1.tags import router as tags_router
from backend.api.v1.tasks import router as tasks_router
from backend.api.v1.webhook import router as webhook_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(digest_router, prefix="/digest", tags=["Digest"])
api_router.include_router(actions_router, prefix="/actions", tags=["Actions"])
api_router.include_router(tags_router, prefix="/tags", tags=["Tags"])
api_router.include_router(review_router, prefix="/review", tags=["Review"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(export_router, prefix="/export", tags=["Export"])
api_router.include_router(reminders_router, prefix="/reminders", tags=["Reminders"])
api_router.include_router(rss_router, prefix="/rss", tags=["RSS"])
api_router.include_router(webhook_router, prefix="/webhook", tags=["Webhook"])
api_router.include_router(feishu_binding_router, prefix="/feishu", tags=["Feishu Binding"])
