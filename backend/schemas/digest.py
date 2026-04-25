from pydantic import BaseModel, Field


class DigestCreate(BaseModel):
    source_type: str = Field(default="text", pattern="^(text|url|voice)$")
    content: str = Field(..., min_length=1, max_length=50000)
    title: str | None = Field(None, max_length=500)
    generate_actions: bool = Field(default=True, description="是否生成行动项")
    generate_tags: bool = Field(default=True, description="是否生成标签")


class DigestResponse(BaseModel):
    id: int
    task_id: str
    source_type: str
    source_url: str | None
    title: str | None
    summary: str | None
    status: str
    tags: list[str] = []
    action_items: list[dict] = []
    created_at: str

    model_config = {"from_attributes": True}


class DigestListResponse(BaseModel):
    id: int
    task_id: str
    title: str | None
    summary: str | None
    status: str
    tags: list[str] = []
    action_count: int = 0
    pending_action_count: int = 0
    created_at: str

    model_config = {"from_attributes": True}


class DigestAccepted(BaseModel):
    task_id: str
    status: str = "processing"


class PaginatedDigests(BaseModel):
    items: list[DigestListResponse]
    total: int
    page: int
    page_size: int
