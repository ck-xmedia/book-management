import pytest


@pytest.mark.asyncio
async def test_crud_flow(client):
    # Create
    payload = {"title": "The Hobbit", "author": "J.R.R. Tolkien", "genres": ["fantasy"], "total_copies": 3}
    r = await client.post("/api/v1/books", json=payload)
    assert r.status_code == 201, r.text
    book = r.json()
    book_id = book["id"]

    # Get
    r = await client.get(f"/api/v1/books/{book_id}")
    assert r.status_code == 200
    assert r.json()["title"] == "The Hobbit"

    # List
    r = await client.get("/api/v1/books", params={"q": "hobbit", "limit": 10, "offset": 0})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert any(item["id"] == book_id for item in data["items"])

    # Update
    r = await client.put(f"/api/v1/books/{book_id}", json={"available_copies": 2})
    assert r.status_code == 200
    assert r.json()["available_copies"] == 2

    # Delete
    r = await client.delete(f"/api/v1/books/{book_id}")
    assert r.status_code == 204

    # Not found after delete
    r = await client.get(f"/api/v1/books/{book_id}")
    assert r.status_code == 404
