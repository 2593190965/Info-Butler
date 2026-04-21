from pydantic import BaseModel


class TagResponse(BaseModel):
    id: int
    name: str
    info_count: int = 0
    action_count: int = 0

    model_config = {"from_attributes": True}
