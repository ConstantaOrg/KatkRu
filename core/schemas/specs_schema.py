from typing import Literal

from pydantic import BaseModel, Field


class SpecsPaginSchema(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=6, ge=0)


class ExtSpecialitySchema(BaseModel):
    id: int


class BaseSpecSearchSchema(SpecsPaginSchema):
    search_term: str

class AutocompleteSearchSchema(BaseSpecSearchSchema):
    search_mode: Literal["auto"]

class DeepSearchSchema(BaseSpecSearchSchema):
    search_mode: Literal["deep"]