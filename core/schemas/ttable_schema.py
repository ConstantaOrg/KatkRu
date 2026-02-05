from datetime import datetime, date

from pydantic import Field, BaseModel


class ScheduleFilterSchema(BaseModel):
    group: str | list[str] | None = None
    date_field: date = Field(datetime.now().date(), alias="date")

class PreAcceptTimetableSchema(BaseModel):
    ttable_id: int

class CommitTtableVersionSchema(BaseModel):
    pending_ver_id: int
    target_ver_id: int
