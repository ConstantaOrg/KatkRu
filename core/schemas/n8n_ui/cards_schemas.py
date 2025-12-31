from pydantic import BaseModel
from typing import List, Optional

"Наполнение карточки"
class CardLessonPayload(BaseModel):
    position: int
    discipline_id: int
    teacher_id: int
    aud: str
    is_force: bool = False

"Карточка на сохранение"
class SaveCardSchema(BaseModel):
    card_hist_id: int
    ttable_id: int
    lessons: List[CardLessonPayload]


"Схема для смены статусов групп"
class GroupUpdateSchema(BaseModel):
    set_as_active: list[int] | None = None
    set_as_deprecated: list[int] | None = None

class GroupAddSchema(BaseModel):
    group_name: str
    building_id: int
