import datetime
from typing import Literal

from pydantic import BaseModel, Field


class BaseTtableSchema(BaseModel):
    building_id: int

class CreateTtableSchema(BaseTtableSchema):
    date: datetime.date | None
    type: Literal['standard', 'replacements']

class StdTtableSchema(BaseTtableSchema):
    ttable_id: int

class StdTtableLoadSchema(StdTtableSchema):
    week_day: int = Field(le=6, gt=0)

class ExtCardStateSchema(BaseModel):
    card_hist_id: int


class SnapshotTtableSchema(BaseModel):
    ttable_id: int