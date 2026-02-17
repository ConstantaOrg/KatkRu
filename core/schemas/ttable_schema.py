from datetime import datetime, date
from typing import Literal

from pydantic import Field, BaseModel


class ScheduleFilterSchema(BaseModel):
    group: str | list[str] | None = None
    date_field: date = Field(datetime.now().date(), alias="date")

class PreAcceptTimetableSchema(BaseModel):
    ttable_id: int

class CommitTtableVersionSchema(BaseModel):
    pending_ver_id: int
    target_ver_id: int


class TtableVersionsGetSchema(BaseModel):
    type: Literal["standard", "replacements"] | None = None
    status_id: int | None = None
    schedule_date: date | None = None
    is_commited: bool | None = None
    date_sort: Literal["asc", "desc"] = "desc"