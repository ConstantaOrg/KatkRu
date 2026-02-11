from pydantic import BaseModel
from typing import List

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

"Для бульк вставки"
class BulkCardsSchema(BaseModel):
    ttable_id: int
    group_names: list[str]
    lessons: List[CardLessonPayload]

"Для бульк удаления"
class DelCardsSchema(BaseModel):
    card_ids: list[int]