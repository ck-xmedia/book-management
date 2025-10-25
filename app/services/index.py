from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass
class Indexer:
    by_author: Dict[str, List[str]]
    by_genre: Dict[str, List[str]]
    by_year: Dict[int, List[str]]

    @staticmethod
    def build(books: Dict[str, dict]) -> "Indexer":
        by_author: Dict[str, List[str]] = {}
        by_genre: Dict[str, List[str]] = {}
        by_year: Dict[int, List[str]] = {}
        for bid, b in books.items():
            author = (b.get("author") or "").strip().lower()
            if author:
                by_author.setdefault(author, []).append(bid)
            for g in b.get("genres", []) or []:
                gk = (g or "").strip().lower()
                if gk:
                    by_genre.setdefault(gk, []).append(bid)
            year = b.get("published_year")
            if isinstance(year, int):
                by_year.setdefault(year, []).append(bid)
        return Indexer(by_author=by_author, by_genre=by_genre, by_year=by_year)

    def query(
        self,
        books: Dict[str, dict],
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
        # Candidate set via indices
        candidates: Iterable[str] = books.keys()
        if author:
            candidates = set(self.by_author.get(author.strip().lower(), []))
        if genre:
            gset = set(self.by_genre.get(genre.strip().lower(), []))
            candidates = set(candidates) & gset
        if year is not None:
            yset = set(self.by_year.get(year, []))
            candidates = set(candidates) & yset

        # Materialize
        items = [books[bid] for bid in candidates]

        # Filters
        if q:
            ql = q.strip().lower()
            items = [b for b in items if ql in (b.get("title", "").lower() + " " + b.get("author", "").lower())]
        if available is not None:
            if available:
                items = [b for b in items if (b.get("available_copies", 0) or 0) > 0]
            else:
                items = [b for b in items if (b.get("available_copies", 0) or 0) <= 0]

        # Sort
        reverse = order == "desc"
        key_funcs = {
            "title": lambda b: (b.get("title") or "").lower(),
            "author": lambda b: (b.get("author") or "").lower(),
            "year": lambda b: b.get("published_year") or 0,
            "created_at": lambda b: b.get("created_at") or "",
        }
        key_fn = key_funcs.get(sort, key_funcs["created_at"])
        items.sort(key=key_fn, reverse=reverse)

        total = len(items)
        items = items[offset : offset + limit]
        return items, total
