from typing import Annotated

from fastapi import Depends
from pydantic import BaseModel, Field


class PagenSchema(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=10, ge=1)

PagenDep = Annotated[PagenSchema, Depends(PagenSchema)]
