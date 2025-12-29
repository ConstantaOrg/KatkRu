import datetime
from typing import Literal

from pydantic import BaseModel, Field


class BaseTtableSchema(BaseModel):
    building_id: int

class CreateTtableSchema(BaseTtableSchema):
    date: datetime.date | None
    type: Literal['standard', 'replacements']

class StdTtableSchema(BaseTtableSchema):
    week_day: int = Field(le=6, gt=0)
    ttable_id: int
    user_id: int

class ExtCardStateSchema(BaseModel):
    card_hist_id: int