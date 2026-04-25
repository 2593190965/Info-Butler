from fastapi import Depends, HTTPException

from backend.core.security import get_current_user


async def get_current_user_info(user: dict = Depends(get_current_user)) -> dict:
    return user


async def get_current_user_id(user: dict = Depends(get_current_user)) -> int:
    if user.get("type") == "api_key":
        api_key_user_id = _resolve_api_key_user(user.get("sub"))
        if api_key_user_id is None:
            raise HTTPException(status_code=401, detail="API key not associated with a user")
        return api_key_user_id
    sub = user.get("sub")
    if not sub or not str(sub).isdigit():
        raise HTTPException(status_code=401, detail="Invalid user identity")
    return int(sub)


def _resolve_api_key_user(api_key_sub: str | None) -> int | None:
    from backend.core.config import settings

    api_user_id = getattr(settings, "api_key_user_id", None)
    if api_user_id is not None:
        try:
            return int(api_user_id)
        except (ValueError, TypeError):
            pass
    return 1
