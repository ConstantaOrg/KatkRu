import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class CreateTtableSchema(BaseModel):
    date: datetime.date | None
    type: Literal['standard', 'replacements']
    @field_validator('date', mode='after')
    @classmethod
    def actual_date(cls, v):
        """"""
        "Актуальна ли назначенная дата для расписания, Если это не standard type"
        if isinstance(v, datetime.date) and datetime.datetime.now().date() <= v:
            return v
        raise ValueError('Введите актуальную дату для расписания')

class StdTtableSchema(BaseModel):
    ttable_id: int

class StdTtableLoadSchema(StdTtableSchema):
    week_day: int = Field(le=6, gt=0)

class ExtCardStateSchema(BaseModel):
    card_hist_id: int


class SnapshotTtableSchema(BaseModel):
    ttable_id: int