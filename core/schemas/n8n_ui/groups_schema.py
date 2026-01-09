from pydantic import BaseModel


class GroupUpdateSchema(BaseModel):
    set_as_active: list[int] | None = None
    set_as_deprecated: list[int] | None = None

class GroupAddSchema(BaseModel):
    group_name: str
    building_id: int
