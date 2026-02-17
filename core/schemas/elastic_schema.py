from typing import Literal

from pydantic import BaseModel


class MethodSearchSchema(BaseModel):
    search_tab: Literal['teachers', 'groups', 'disciplines']
    search_phrase: str

