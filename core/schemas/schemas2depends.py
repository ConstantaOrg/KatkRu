from typing import Annotated

from fastapi import Depends
from pydantic import BaseModel, Field


class PagenSchema(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=10, gt=offset)

PagenDep = Annotated[PagenSchema, Depends(PagenSchema)]
