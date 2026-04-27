import re

from pydantic import BaseModel, EmailStr, Field, model_validator


def validate_password_strength(value: str) -> str:
    if len(value) < 8:
        raise ValueError("密码长度至少为8位")
    if not re.search(r"[A-Z]", value):
        raise ValueError("密码需包含至少一个大写字母")
    if not re.search(r"[a-z]", value):
        raise ValueError("密码需包含至少一个小写字母")
    if not re.search(r"[0-9]", value):
        raise ValueError("密码需包含至少一个数字")
    return value


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @model_validator(mode="after")
    def check_password_strength(self):
        validate_password_strength(self.password)
        return self


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool

    model_config = {"from_attributes": True}
