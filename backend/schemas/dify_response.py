from pydantic import BaseModel, Field


class ActionItemOutput(BaseModel):
    content: str = Field(..., min_length=2, max_length=500)
    priority: str = Field(..., pattern="^(high|medium|low)$")


class DifyResponse(BaseModel):
    summary: str = Field(..., min_length=1, max_length=200)
    action_items: list[ActionItemOutput] = Field(..., min_length=1, max_length=10)
    tags: list[str] = Field(..., min_length=3, max_length=5)
