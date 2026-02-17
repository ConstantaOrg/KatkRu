from pydantic import BaseModel


class GroupUpdateSchema(BaseModel):
    set_as_active: list[int] | None = None
    set_as_deprecated: list[int] | None = None

class GroupAddSchema(BaseModel):
    group_name: str

class GroupFilterSchema(BaseModel):
    is_active: bool | None = None
