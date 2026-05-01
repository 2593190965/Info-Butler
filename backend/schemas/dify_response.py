from pydantic import BaseModel, Field


class ActionItemOutput(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)
    priority: str = Field(default="medium", pattern="^(high|medium|low)$")


class DifyResponse(BaseModel):
    summary: str = Field(default="")
    action_items: list[ActionItemOutput] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
