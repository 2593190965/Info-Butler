from fastapi import Depends, HTTPException

from backend.core.security import get_current_user


async def get_current_user_info(user: dict = Depends(get_current_user)) -> dict:
    return user


async def get_current_user_id(user: dict = Depends(get_current_user)) -> int:
    if user.get("type") == "api_key":
        return 1
    sub = user.get("sub")
    if not sub or not str(sub).isdigit():
        raise HTTPException(status_code=401, detail="Invalid user identity")
    return int(sub)
