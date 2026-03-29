from fastapi import FastAPI, HTTPException
import asyncpg
import uvicorn
import os

app = FastAPI(title="User Service")

PG_DSN = os.getenv("PG_DSN", "postgresql://user:password@localhost:5432/library")

db_pool = None


@app.on_event("startup")
async def startup():
    global db_pool
    db_pool = await asyncpg.create_pool(PG_DSN)
    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     SERIAL PRIMARY KEY,
                name        TEXT NOT NULL,
                email       TEXT UNIQUE NOT NULL
            );
        """)
        count = await conn.fetchval("SELECT COUNT(*) FROM users")
        if count == 0:
            await conn.executemany(
                "INSERT INTO users (name, email) VALUES ($1, $2)",
                [
                    ("Alice Smith",  "alice@example.com"),
                    ("Bob Jones",    "bob@example.com"),
                    ("Carol White",  "carol@example.com"),
                ]
            )


@app.on_event("shutdown")
async def shutdown():
    await db_pool.close()


@app.get("/profile/{user_id}")
async def get_profile(user_id: int):
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE user_id=$1", user_id
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        borrowed_items = await conn.fetch(
            """SELECT i.item_id AS id, i.title, i.due_date
               FROM inventory i
               WHERE i.borrowed_by=$1 AND i.available=FALSE""",
            user_id
        )
        history = await conn.fetch(
            """SELECT h.item_id, i.title, h.borrow_date, h.return_date, h.genre, h.media_type
               FROM borrow_history h
               JOIN inventory i ON h.item_id = i.item_id
               WHERE h.user_id=$1
               ORDER BY h.borrow_date DESC""",
            user_id
        )

    return {
        "user_id":        user["user_id"],
        "name":           user["name"],
        "email":          user["email"],
        "borrowed_items": [dict(r) for r in borrowed_items],
        "history":        [dict(r) for r in history]
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)