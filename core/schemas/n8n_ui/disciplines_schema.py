from pydantic import BaseModel


class DisciplineUpdateSchema(BaseModel):
    set_as_active: list[int] | None = None
    set_as_deprecated: list[int] | None = None

class DisciplineAddSchema(BaseModel):
    title: str


class DisciplineFilterSchema(BaseModel):
    is_active: bool | None = None
    group_name: str | None = None


class Group2DisciplineSchema(BaseModel):
    discipline_id: int
    group_name: str