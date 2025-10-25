import pytest

from app.main import create_app


@pytest.mark.asyncio
async def test_update_validation(client):
    # Create
    r = await client.post("/api/v1/books", json={"title": "A", "author": "B", "total_copies": 1})
    assert r.status_code == 201
    book = r.json()
    bid = book["id"]

    # Invalid: available > total
    r = await client.put(f"/api/v1/books/{bid}", json={"available_copies": 5})
    assert r.status_code == 400
