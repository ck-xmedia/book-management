from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class BookCreate(BaseModel):
    title: str
    author: str
    isbn: Optional[str] = None
    published_year: Optional[int] = None
    genres: List[str] = Field(default_factory=list)
    total_copies: int = 1

    @field_validator("title", "author")
    @classmethod
    def non_empty(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("must not be empty")
        return v


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    published_year: Optional[int] = None
    genres: Optional[List[str]] = None
    total_copies: Optional[int] = None
    available_copies: Optional[int] = None

    @field_validator("title", "author")
    @classmethod
    def non_empty_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("must not be empty")
        return v


class BookOut(BaseModel):
    id: UUID
    title: str
    author: str
    isbn: Optional[str]
    published_year: Optional[int]
    genres: List[str]
    total_copies: int
    available_copies: int
    created_at: datetime
    updated_at: datetime


class PaginatedBooks(BaseModel):
    items: List[BookOut]
    total: int
    limit: int
    offset: int
