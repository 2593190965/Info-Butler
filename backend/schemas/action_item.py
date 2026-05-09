from pydantic import BaseModel, Field


class ActionItemCreate(BaseModel):
    content: str = Field(..., min_length=2, max_length=500)
    priority: str | None = Field(None, pattern="^(high|medium|low)$")
    due_date: str | None = None


class ActionItemUpdate(BaseModel):
    content: str | None = Field(None, min_length=2, max_length=500)
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
    ids: list[int] = Field(..., min_length=1, max_length=100)
    status: str = Field(..., pattern="^(pending|done|ignored)$")


class BatchActionDelete(BaseModel):
    ids: list[int] = Field(..., min_length=1, description="要删除的行动项 ID 列表")


class BatchActionPriorityUpdate(BaseModel):
    ids: list[int] = Field(..., min_length=1, description="要更新的行动项 ID 列表")
    priority: str = Field(..., pattern="^(high|medium|low)$", description="目标优先级")


class BatchActionAddTags(BaseModel):
    ids: list[int] = Field(..., min_length=1, description="要添加标签的行动项 ID 列表")
    tag_ids: list[int] = Field(..., min_length=1, description="要添加的标签 ID 列表")


class PaginatedActions(BaseModel):
    items: list[ActionItemResponse]
    total: int
    page: int
    page_size: int
