from pydantic import BaseModel


class TeachersUpdateSchema(BaseModel):
    set_as_active: list[int] | None = None
    set_as_deprecated: list[int] | None = None

class TeachersAddSchema(BaseModel):
    fio: str

class TeacherFilterSchema(BaseModel):
    is_active: bool | None = None
