from fastapi import Depends

from backend.core.security import verify_api_key


async def get_current_user(api_key: str = Depends(verify_api_key)) -> str:
    return api_key
