from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import uvicorn
import asyncpg
import redis.asyncio as aioredis
import aio_pika
import json
import os
from datetime import date, timedelta

app = FastAPI(title="Circulation Engine")

# --- Connection config (update these) ---
PG_DSN     = os.getenv("PG_DSN",      "postgresql://user:password@localhost:5432/library")
REDIS_URL  = os.getenv("REDIS_URL",   "redis://localhost:6379")
RABBIT_URL = os.getenv("RABBIT_URL",  "amqp://guest:guest@localhost/")

# --- Globals ---
db_pool       = None
redis_client  = None
rabbit_conn   = None
rabbit_channel= None

@app.on_event("startup")
async def startup():
    global db_pool, redis_client, rabbit_conn, rabbit_channel

    # PostgreSQL
    db_pool = await asyncpg.create_pool(PG_DSN)
    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                item_id     SERIAL PRIMARY KEY,
                title       TEXT NOT NULL,
                author      TEXT,
                genre       TEXT,
                media_type  TEXT,
                available   BOOLEAN DEFAULT TRUE,
                borrowed_by INT DEFAULT NULL,
                due_date    DATE DEFAULT NULL
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS borrow_history (
                id          SERIAL PRIMARY KEY,
                user_id     INT NOT NULL,
                item_id     INT NOT NULL,
                borrow_date DATE NOT NULL,
                return_date DATE DEFAULT NULL,
                genre       TEXT,
                media_type  TEXT
            );
        """)
        # Seed some items if table is empty (replace with your real catalog)
        count = await conn.fetchval("SELECT COUNT(*) FROM inventory")
        if count == 0:
            await conn.executemany(
                "INSERT INTO inventory (title, author, genre, media_type) VALUES ($1,$2,$3,$4)",
                [
                    ("Database System Concepts", "Silberschatz", "Technology", "Book"),
                    ("RabbitMQ in Action",        "Videla",       "Technology", "Book"),
                    ("Dune",                      "Herbert",      "Fiction",    "Book"),
                    ("Sapiens",                   "Harari",       "History",    "Book"),
                    ("The Great Gatsby",          "Fitzgerald",   "Fiction",    "Book"),
                ]
            )

    # Redis
    redis_client = await aioredis.from_url(REDIS_URL, decode_responses=True)

    # RabbitMQ
    rabbit_conn    = await aio_pika.connect_robust(RABBIT_URL)
    rabbit_channel = await rabbit_conn.channel()
    await rabbit_channel.declare_queue("notifications",    durable=True)
    await rabbit_channel.declare_queue("recommendations",  durable=True)


@app.on_event("shutdown")
async def shutdown():
    await db_pool.close()
    await redis_client.close()
    await rabbit_conn.close()


class BorrowRequest(BaseModel):
    user_id: int
    item_id: int


async def publish(queue_name: str, payload: dict):
    """Fire-and-forget publish to a RabbitMQ queue."""
    await rabbit_channel.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps(payload).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        ),
        routing_key=queue_name
    )


@app.post("/borrow")
async def process_borrow(request: BorrowRequest):
    # Use Redis lock to prevent race conditions (replaces asyncio.Lock)
    lock_key = f"lock:item:{request.item_id}"
    lock = redis_client.lock(lock_key, timeout=10)

    async with lock:
        async with db_pool.acquire() as conn:
            item = await conn.fetchrow(
                "SELECT * FROM inventory WHERE item_id = $1", request.item_id
            )
            if not item:
                raise HTTPException(status_code=404, detail="Item not found.")
            if not item["available"]:
                raise HTTPException(status_code=409, detail=f"Item {request.item_id} is already checked out.")

            borrow_date = date.today()
            due_date    = borrow_date + timedelta(days=14)  # 2-week loan period

            await conn.execute(
                """UPDATE inventory
                   SET available=FALSE, borrowed_by=$1, due_date=$2
                   WHERE item_id=$3""",
                request.user_id, due_date, request.item_id
            )
            await conn.execute(
                """INSERT INTO borrow_history (user_id, item_id, borrow_date, genre, media_type)
                   VALUES ($1, $2, $3, $4, $5)""",
                request.user_id, request.item_id, borrow_date,
                item["genre"], item["media_type"]
            )

    # Publish events asynchronously — does NOT block the borrow response
    await publish("notifications", {
        "event":    "item_borrowed",
        "user_id":  request.user_id,
        "item_id":  request.item_id,
        "title":    item["title"],
        "due_date": str(due_date)
    })
    await publish("recommendations", {
        "event":    "update_profile",
        "user_id":  request.user_id,
        "genre":    item["genre"],
        "media":    item["media_type"]
    })

    return {
        "status":   "success",
        "message":  f"Item '{item['title']}' checked out to user {request.user_id}",
        "due_date": str(due_date)
    }


@app.post("/return")
async def process_return(request: BorrowRequest):
    lock_key = f"lock:item:{request.item_id}"
    lock = redis_client.lock(lock_key, timeout=10)

    async with lock:
        async with db_pool.acquire() as conn:
            item = await conn.fetchrow(
                "SELECT * FROM inventory WHERE item_id=$1", request.item_id
            )
            if not item:
                raise HTTPException(status_code=404, detail="Item not found.")
            if item["borrowed_by"] != request.user_id:
                raise HTTPException(status_code=403, detail="This item was not borrowed by this user.")

            await conn.execute(
                """UPDATE inventory
                   SET available=TRUE, borrowed_by=NULL, due_date=NULL
                   WHERE item_id=$1""",
                request.item_id
            )
            await conn.execute(
                """UPDATE borrow_history SET return_date=$1
                   WHERE user_id=$2 AND item_id=$3 AND return_date IS NULL""",
                date.today(), request.user_id, request.item_id
            )

    return {"status": "success", "message": f"Item {request.item_id} returned."}


@app.get("/items")
async def list_items(q: str = ""):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT item_id AS id, title, author, genre, media_type, available
               FROM inventory
               WHERE title ILIKE $1 OR author ILIKE $1 OR genre ILIKE $1""",
            f"%{q}%"
        )
    return [dict(r) for r in rows]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
