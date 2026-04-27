import asyncio
import logging
import sys
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi.middleware.cors import CORSMiddleware

from backend.api.v1.router import api_router
from backend.core.base import Base
from backend.core.config import settings
from backend.core.database import engine
from backend.core.exceptions import AppError
from backend.core.middleware import RateLimitMiddleware, SecurityHeadersMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from backend.workers.arq_client import close_arq_pool, get_arq_pool

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        await get_arq_pool()
    except Exception as e:
        logger.warning(f"Failed to connect to Redis/ARQ pool: {e}. Background tasks will not be available.")

    yield

    await close_arq_pool()
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    logger.error(f"AppError: {exc.detail}")
    return JSONResponse(
        status_code=exc.code,
        content={"code": exc.code, "data": None, "message": exc.detail},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"code": 500, "data": None, "message": "Internal server error"},
    )


@app.get("/health")
async def health_check():
    from backend.core.database import async_session
    from backend.services.digest_service import cleanup_stuck_processing

    try:
        async with async_session() as db:
            cleaned = await cleanup_stuck_processing(db)
    except Exception as e:
        logger.warning(f"Health check cleanup failed: {e}")
        cleaned = 0

    return {"status": "ok", "app": settings.app_name, "cleaned_stuck": cleaned}
