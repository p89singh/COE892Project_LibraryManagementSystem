from fastapi import FastAPI
from pydantic import BaseModel
import asyncpg
import uvicorn

app = FastAPI(title="Recommendation Service")

CATALOG_DB_DSN = "postgresql://postgres:postgres@postgres:5432/catalog_db"

catalog_pool = None


class BorrowRecordRequest(BaseModel):
    user_id: int
    item_id: int


@app.on_event("startup")
async def startup() -> None:
    global catalog_pool
    catalog_pool = await asyncpg.create_pool(dsn=CATALOG_DB_DSN)


@app.on_event("shutdown")
async def shutdown() -> None:
    if catalog_pool:
        await catalog_pool.close()


@app.post("/record-borrow")
async def record_borrow(data: BorrowRecordRequest):
    return {
        "status": "success",
        "message": f"Borrow event recorded for user {data.user_id}, item {data.item_id}"
    }


@app.get("/recommend/{user_id}")
async def recommend(user_id: int):
    async with catalog_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, title, author, genre, media_type, isbn, publication_year, description, total_copies, created_at
            FROM items
            ORDER BY id
            LIMIT 5
            """
        )

    return [dict(row) for row in rows]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)