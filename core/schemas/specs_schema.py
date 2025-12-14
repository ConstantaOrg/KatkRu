from pydantic import BaseModel, Field


class SpecsPaginSchema(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=0)


class ExtSpecialitySchema(BaseModel):
    id: int
