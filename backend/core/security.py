from fastapi import Header, HTTPException

from backend.core.config import settings


async def verify_api_key(x_api_key: str = Header(default=None)) -> str:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key
