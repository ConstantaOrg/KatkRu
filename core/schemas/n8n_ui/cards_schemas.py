from pydantic import BaseModel
from typing import List

class CardLessonPayload(BaseModel):
    position: int
    discipline_id: int
    teacher_id: int
    aud: str

class SaveCardSchema(BaseModel):
    card_hist_id: int
    ttable_id: int  # sched_ver_id
    lessons: List[CardLessonPayload]
