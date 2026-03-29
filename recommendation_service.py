from fastapi import FastAPI
import asyncpg
import redis.asyncio as aioredis
import aio_pika
import uvicorn
import json
import os
from collections import Counter

app = FastAPI(title="Recommendation Service")

PG_DSN     = os.getenv("PG_DSN",     "postgresql://user:password@localhost:5432/library")
REDIS_URL  = os.getenv("REDIS_URL",  "redis://localhost:6379")
RABBIT_URL = os.getenv("RABBIT_URL", "amqp://guest:guest@localhost/")

db_pool      = None
redis_client = None


@app.on_event("startup")
async def startup():
    global db_pool, redis_client
    db_pool      = await asyncpg.create_pool(PG_DSN)
    redis_client = await aioredis.from_url(REDIS_URL, decode_responses=True)

    # Start the RabbitMQ consumer in the background
    asyncio.get_event_loop().create_task(consume_events())


@app.on_event("shutdown")
async def shutdown():
    await db_pool.close()
    await redis_client.close()


import asyncio


async def consume_events():
    rabbit_conn = await aio_pika.connect_robust(RABBIT_URL)
    channel     = await rabbit_conn.channel()
    await channel.set_qos(prefetch_count=10)
    queue = await channel.declare_queue("recommendations", durable=True)

    async def handle(message: aio_pika.IncomingMessage):
        async with message.process():
            event = json.loads(message.body.decode())
            if event.get("event") == "update_profile":
                await update_user_profile(
                    event["user_id"],
                    event.get("genre"),
                    event.get("media")
                )

    print("[Recommendation Service] Listening for events...")
    await queue.consume(handle)
    await asyncio.Future()  # run forever


async def update_user_profile(user_id: int, genre: str, media: str):
    """
    Increment genre and media counters in Redis for this user.
    Keys: user_profile:{user_id}:genres  and  user_profile:{user_id}:media
    Stored as Redis hashes: field=genre/media, value=count
    """
    if genre:
        await redis_client.hincrby(f"user_profile:{user_id}:genres", genre, 1)
    if media:
        await redis_client.hincrby(f"user_profile:{user_id}:media",  media,  1)


def score_item(item: dict, genre_prefs: dict, media_prefs: dict) -> float:
    """
    Score a catalog item based on how well it matches the user's
    genre and media preferences.
    Genre match is weighted 2x relative to media match.
    """
    genre_score = int(genre_prefs.get(item["genre"],      0)) * 2
    media_score = int(media_prefs.get(item["media_type"], 0)) * 1
    return genre_score + media_score


@app.get("/recommend/{user_id}")
async def get_recommendations(user_id: int, top_n: int = 5):
    # Load preference profile from Redis
    genre_prefs = await redis_client.hgetall(f"user_profile:{user_id}:genres")
    media_prefs = await redis_client.hgetall(f"user_profile:{user_id}:media")

    # Cold start: if no profile yet, fall back to borrow history from Postgres
    if not genre_prefs:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT genre, media_type FROM borrow_history WHERE user_id=$1", user_id
            )
        genre_prefs = dict(Counter(r["genre"]      for r in rows if r["genre"]))
        media_prefs = dict(Counter(r["media_type"] for r in rows if r["media_type"]))

    # Fetch available items the user has NOT already borrowed
    async with db_pool.acquire() as conn:
        already_borrowed = await conn.fetch(
            "SELECT DISTINCT item_id FROM borrow_history WHERE user_id=$1", user_id
        )
        borrowed_ids = {r["item_id"] for r in already_borrowed}

        candidates = await conn.fetch(
            "SELECT item_id, title, author, genre, media_type FROM inventory WHERE available=TRUE"
        )

    # Score and rank
    scored = []
    for item in candidates:
        if item["item_id"] in borrowed_ids:
            continue
        s = score_item(dict(item), genre_prefs, media_prefs)
        scored.append({**dict(item), "score": s})

    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[:top_n]

    # Summarise the preference profile for transparency
    profile_summary = {
        "genre_preferences": {k: int(v) for k, v in genre_prefs.items()},
        "media_preferences": {k: int(v) for k, v in media_prefs.items()},
    }

    return {
        "user_id":      user_id,
        "profile":      profile_summary,
        "recommended":  top
    }


@app.get("/analytics/{user_id}")
async def get_analytics(user_id: int):
    """
    Returns a breakdown of the user's borrowing history
    by genre and media type, with counts and percentages.
    """
    async with db_pool.acquire() as conn:
        genre_rows = await conn.fetch(
            """SELECT genre, COUNT(*) AS count
               FROM borrow_history
               WHERE user_id=$1 AND genre IS NOT NULL
               GROUP BY genre ORDER BY count DESC""",
            user_id
        )
        media_rows = await conn.fetch(
            """SELECT media_type, COUNT(*) AS count
               FROM borrow_history
               WHERE user_id=$1 AND media_type IS NOT NULL
               GROUP BY media_type ORDER BY count DESC""",
            user_id
        )
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM borrow_history WHERE user_id=$1", user_id
        )

    def with_pct(rows):
        return [
            {
                "label":      r["genre"] if "genre" in r.keys() else r["media_type"],
                "count":      r["count"],
                "percentage": round(r["count"] / total * 100, 1) if total else 0
            }
            for r in rows
        ]

    return {
        "user_id":       user_id,
        "total_borrows": total,
        "by_genre":      with_pct(genre_rows),
        "by_media":      with_pct(media_rows),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)