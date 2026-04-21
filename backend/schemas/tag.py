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


class PaginatedTags(BaseModel):
    items: list[TagResponse]
    total: int
