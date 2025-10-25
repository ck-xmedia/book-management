from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi import Request, status

from app.api.deps import pagination_params
from app.domain.schemas import BookCreate, BookOut, BookUpdate, PaginatedBooks

router = APIRouter(prefix="/books", tags=["books"])


def get_service(request: Request):
    return request.app.state.books_service


@router.get("", response_model=PaginatedBooks)
async def list_books(
    request: Request,
    q: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    genre: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    available: Optional[bool] = Query(None),
    page=Depends(pagination_params),
):
    svc = get_service(request)
    items, total = await svc.list_books(
        q=q,
        author=author,
        genre=genre,
        year=year,
        available=available,
        sort=page["sort"],
        order=page["order"],
        limit=page["limit"],
        offset=page["offset"],
    )
    return {"items": items, "total": total, **page}


@router.post("", response_model=BookOut, status_code=status.HTTP_201_CREATED)
async def create_book(request: Request, payload: BookCreate):
    svc = get_service(request)
    return await svc.create_book(payload)


@router.get("/{book_id}", response_model=BookOut)
async def get_book(request: Request, book_id: UUID):
    svc = get_service(request)
    return await svc.get_book(book_id)


@router.put("/{book_id}", response_model=BookOut)
async def update_book(request: Request, book_id: UUID, payload: BookUpdate):
    svc = get_service(request)
    return await svc.update_book(book_id, payload)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(request: Request, book_id: UUID):
    svc = get_service(request)
    await svc.delete_book(book_id)
    return None
