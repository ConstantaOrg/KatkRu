from datetime import datetime, date, timedelta

from pydantic import Field, BaseModel, field_validator, ValidationError


class ScheduleFilterSchema(BaseModel):
    building_id: int = Field(ge=1, le=3)
    group: str | list[str] | None = None
    date_start: date = datetime.now().date()
    date_end: date | None = None

    @field_validator('date_end', mode='after')
    @classmethod
    def date_start_validator(cls, v, info):
        if v is None:
            return v

        data = info.data
        if v < data['date_start']:
            raise ValueError("date_end не может быть раньше date_start")

        if timedelta(days=14) < (v - data['date_start']):
            raise ValueError('Выберите диапазон дат в пределах 14 дней')

        return v
