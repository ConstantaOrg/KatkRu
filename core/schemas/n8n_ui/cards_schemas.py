from pydantic import BaseModel
from typing import List

"Наполнение карточки"
class CardLessonPayload(BaseModel):
    position: int
    discipline_id: int
    teacher_id: int
    aud: str
    week_day: int | None
    is_force: bool = False

"Карточка на сохранение"
class SaveCardSchema(BaseModel):
    card_hist_id: int
    ttable_id: int
    week_day: int | None
    lessons: List[CardLessonPayload]

"Для бульк вставки"
class BulkCardsSchema(BaseModel):
    ttable_id: int
    week_day: int | None
    group_names: list[str]
    lessons: List[CardLessonPayload]

"Для бульк удаления"
class DelCardsSchema(BaseModel):
    card_ids: list[int]
    ttable_id: int

class EditCardSchema(BaseModel):
    card_hist_id: int
    ttable_id: int