from pydantic import BaseModel, Field


class BatchItem(BaseModel):
    source_type: str = Field(..., pattern="^(text|url)$")
    content: str = Field(..., min_length=1)
    title: str | None = None
    generate_actions: bool = Field(default=True, description="是否生成行动项")
    generate_tags: bool = Field(default=True, description="是否生成标签")


class BatchImportRequest(BaseModel):
    items: list[BatchItem] = Field(..., min_length=1, max_length=20)
    generate_actions: bool = Field(default=True, description="批量默认：是否生成行动项")
    generate_tags: bool = Field(default=True, description="批量默认：是否生成标签")


class BatchImportResponse(BaseModel):
    accepted: int
    task_ids: list[str]
    message: str


class TaskStatusResponse(BaseModel):
    total_submitted: int
    pending: int
    done: int
    failed: int
    recent_tasks: list[dict]
