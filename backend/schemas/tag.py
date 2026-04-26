from pydantic import BaseModel, Field


class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)


class TagUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)


class TagResponse(BaseModel):
    id: int
    name: str
    info_count: int = 0
    action_count: int = 0

    model_config = {"from_attributes": True}


class BatchTagDelete(BaseModel):
    ids: list[int] = Field(..., min_length=1, description="要删除的标签 ID 列表")


class MergeTagsRequest(BaseModel):
    source_ids: list[int] = Field(..., min_length=1, description="源标签 ID 列表（将被合并）")
    target_id: int = Field(..., description="目标标签 ID（将保留）")


class TagRename(BaseModel):
    id: int
    new_name: str = Field(..., min_length=1, max_length=50)


class BatchTagRenameRequest(BaseModel):
    renames: list[TagRename] = Field(..., min_length=1, description="批量重命名列表")


class PaginatedTags(BaseModel):
    items: list[TagResponse]
    total: int
