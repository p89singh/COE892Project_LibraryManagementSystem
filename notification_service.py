import asyncio
import asyncpg
import aio_pika
import json
import os
from datetime import date, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

PG_DSN     = os.getenv("PG_DSN",     "postgresql://user:password@localhost:5432/library")
RABBIT_URL = os.getenv("RABBIT_URL", "amqp://guest:guest@localhost/")

db_pool = None


def send_notification(user_id: int, message: str):
    """
    Replace this with your actual notification delivery:
    e.g. send email via SMTP, SMS via Twilio, push notification, etc.
    """
    print(f"[NOTIFICATION] User {user_id}: {message}")


async def handle_borrow_event(message: aio_pika.IncomingMessage):
    async with message.process():
        event = json.loads(message.body.decode())

        if event.get("event") == "item_borrowed":
            user_id  = event["user_id"]
            title    = event["title"]
            due_date = event["due_date"]
            send_notification(
                user_id,
                f"You have borrowed '{title}'. It is due on {due_date}."
            )


async def check_due_soon():
    """
    Scheduled job: runs daily to find items due within 3 days
    and notify the borrowing user.
    """
    if db_pool is None:
        return
    warning_date = date.today() + timedelta(days=3)
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT i.borrowed_by AS user_id, i.title, i.due_date
               FROM inventory i
               WHERE i.available = FALSE
                 AND i.due_date <= $1
                 AND i.due_date >= $2""",
            warning_date, date.today()
        )
    for row in rows:
        days_left = (row["due_date"] - date.today()).days
        send_notification(
            row["user_id"],
            f"Reminder: '{row['title']}' is due in {days_left} day(s) (on {row['due_date']})."
        )


async def main():
    global db_pool
    db_pool = await asyncpg.create_pool(PG_DSN)

    # Daily due-date check — runs at 9:00 AM
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_due_soon, "cron", hour=9, minute=0)
    scheduler.start()

    # RabbitMQ consumer
    rabbit_conn = await aio_pika.connect_robust(RABBIT_URL)
    channel     = await rabbit_conn.channel()
    await channel.set_qos(prefetch_count=10)
    queue = await channel.declare_queue("notifications", durable=True)

    print("[Notification Service] Listening for events...")
    await queue.consume(handle_borrow_event)

    try:
        await asyncio.Future()  # run forever
    finally:
        await rabbit_conn.close()
        await db_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
