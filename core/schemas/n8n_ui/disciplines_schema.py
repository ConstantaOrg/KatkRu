from pydantic import BaseModel


class DisciplineUpdateSchema(BaseModel):
    set_as_active: list[int] | None = None
    set_as_deprecated: list[int] | None = None

class DisciplineAddSchema(BaseModel):
    title: str
