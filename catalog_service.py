from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import asyncpg
import uvicorn

app = FastAPI(title="Catalog Service")

DB_DSN = "postgresql://postgres:postgres@postgres:5432/catalog_db"
db_pool = None


class CatalogItemCreate(BaseModel):
    title: str
    author: str
    genre: str | None = None
    media_type: str
    isbn: str | None = None
    publication_year: int | None = None
    description: str | None = None
    total_copies: int = 1


class CatalogItemUpdate(BaseModel):
    title: str
    author: str
    genre: str | None = None
    media_type: str
    isbn: str | None = None
    publication_year: int | None = None
    description: str | None = None
    total_copies: int = 1


@app.on_event("startup")
async def startup() -> None:
    global db_pool
    db_pool = await asyncpg.create_pool(dsn=DB_DSN)


@app.on_event("shutdown")
async def shutdown() -> None:
    if db_pool:
        await db_pool.close()


@app.get("/items")
async def get_items(q: str = Query(default="")):
    async with db_pool.acquire() as conn:
        if q.strip():
            rows = await conn.fetch(
                """
                SELECT id, title, author, genre, media_type, isbn, publication_year, description, total_copies, created_at
                FROM items
                WHERE title ILIKE $1
                   OR author ILIKE $1
                   OR genre ILIKE $1
                ORDER BY id
                """,
                f"%{q}%",
            )
        else:
            rows = await conn.fetch(
                """
                SELECT id, title, author, genre, media_type, isbn, publication_year, description, total_copies, created_at
                FROM items
                ORDER BY id
                """
            )

    return [dict(row) for row in rows]


@app.get("/items/{item_id}")
async def get_item(item_id: int):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, title, author, genre, media_type, isbn, publication_year, description, total_copies, created_at
            FROM items
            WHERE id = $1
            """,
            item_id,
        )

    if not row:
        raise HTTPException(status_code=404, detail="Item not found.")

    return dict(row)


@app.post("/items")
async def create_item(item: CatalogItemCreate):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO items (
                title, author, genre, media_type, isbn, publication_year, description, total_copies
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id, title, author, genre, media_type, isbn, publication_year, description, total_copies, created_at
            """,
            item.title,
            item.author,
            item.genre,
            item.media_type,
            item.isbn,
            item.publication_year,
            item.description,
            item.total_copies,
        )

    return dict(row)


@app.put("/items/{item_id}")
async def update_item(item_id: int, item: CatalogItemUpdate):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE items
            SET title = $1,
                author = $2,
                genre = $3,
                media_type = $4,
                isbn = $5,
                publication_year = $6,
                description = $7,
                total_copies = $8
            WHERE id = $9
            RETURNING id, title, author, genre, media_type, isbn, publication_year, description, total_copies, created_at
            """,
            item.title,
            item.author,
            item.genre,
            item.media_type,
            item.isbn,
            item.publication_year,
            item.description,
            item.total_copies,
            item_id,
        )

    if not row:
        raise HTTPException(status_code=404, detail="Item not found.")

    return dict(row)


@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    async with db_pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM items WHERE id = $1",
            item_id,
        )

    if result.endswith("0"):
        raise HTTPException(status_code=404, detail="Item not found.")

    return {"status": "success", "message": f"Item {item_id} deleted successfully."}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)