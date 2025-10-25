from typing import Optional
from fastapi import Query


def pagination_params(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: str = Query("created_at"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
):
    return {"limit": limit, "offset": offset, "sort": sort, "order": order}
