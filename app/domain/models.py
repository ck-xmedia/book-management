from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class Book(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    author: str
    isbn: Optional[str] = None
    published_year: Optional[int] = None
    genres: List[str] = Field(default_factory=list)
    total_copies: int = 1
    available_copies: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("title", "author")
    @classmethod
    def non_empty(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("must not be empty")
        return v

    @field_validator("published_year")
    @classmethod
    def check_year(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        if v < 1000 or v > datetime.utcnow().year + 1:
            raise ValueError("published_year out of range")
        return v

    @field_validator("available_copies")
    @classmethod
    def copies_le_total(cls, v: int, info):
        total = info.data.get("total_copies", 1)
        if v > total:
            raise ValueError("available_copies cannot exceed total_copies")
        return v
