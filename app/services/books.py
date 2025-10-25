from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from app.domain.models import Book
from app.domain.schemas import BookCreate, BookUpdate
from app.services.storage.json_store import JsonStore
from app.services.index import Indexer


class NotFoundError(Exception):
    pass


class BooksService:
    def __init__(self, store: JsonStore) -> None:
        self.store = store

    async def _load(self) -> Tuple[int, Dict[str, dict]]:
        total, books = await self.store.list_books()
        return total, books

    async def list_books(
        self,
        *,
        q: Optional[str] = None,
        author: Optional[str] = None,
        genre: Optional[str] = None,
        year: Optional[int] = None,
        available: Optional[bool] = None,
        sort: str = "created_at",
        order: str = "asc",
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[dict], int]:
        _, books = await self._load()
        index = Indexer.build(books)
        items, total = index.query(
            books,
            q=q,
            author=author,
            genre=genre,
            year=year,
            available=available,
            sort=sort,
            order=order,
            limit=limit,
            offset=offset,
        )
        return items, total

    async def create_book(self, payload: BookCreate) -> dict:
        now = datetime.utcnow()
        book = Book(
            title=payload.title,
            author=payload.author,
            isbn=payload.isbn,
            published_year=payload.published_year,
            genres=payload.genres or [],
            total_copies=payload.total_copies or 1,
            available_copies=payload.total_copies or 1,
            created_at=now,
            updated_at=now,
        )
        data = book.model_dump()
        await self.store.upsert_book(str(book.id), data)
        return data

    async def get_book(self, book_id: UUID) -> dict:
        b = await self.store.get_book(str(book_id))
        if not b:
            raise NotFoundError("book not found")
        return b

    async def update_book(self, book_id: UUID, payload: BookUpdate) -> dict:
        current = await self.store.get_book(str(book_id))
        if not current:
            raise NotFoundError("book not found")
        # Merge
        updated = {**current}
        data = payload.model_dump(exclude_unset=True)
        updated.update(data)
        # Validation: available_copies <= total_copies
        total = updated.get("total_copies", 1)
        avail = updated.get("available_copies", total)
        if avail > total:
            raise ValueError("available_copies cannot exceed total_copies")
        updated["updated_at"] = datetime.utcnow().isoformat()
        await self.store.upsert_book(str(book_id), updated)
        return updated

    async def delete_book(self, book_id: UUID) -> None:
        ok = await self.store.delete_book(str(book_id))
        if not ok:
            raise NotFoundError("book not found")
