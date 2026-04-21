from pydantic import BaseModel, Field


class ActionItemCreate(BaseModel):
    content: str = Field(..., min_length=2, max_length=500)
    priority: str | None = Field(None, pattern="^(high|medium|low)$")
    due_date: str | None = None


class ActionItemUpdate(BaseModel):
    status: str | None = Field(None, pattern="^(pending|done|ignored)$")
    priority: str | None = Field(None, pattern="^(high|medium|low)$")
    due_date: str | None = None


class ActionItemResponse(BaseModel):
    id: int
    info_id: int
    content: str
    status: str
    priority: str
    due_date: str | None
    tags: list[str] = []
    info_summary: str | None = None
    created_at: str

    model_config = {"from_attributes": True}


class BatchActionUpdate(BaseModel):
    ids: list[int]
    status: str = Field(..., pattern="^(pending|done|ignored)$")


class PaginatedActions(BaseModel):
    items: list[ActionItemResponse]
    total: int
    page: int
    page_size: int
