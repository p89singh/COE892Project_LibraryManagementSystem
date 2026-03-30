from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import asyncio

app = FastAPI(title="Notification Service")
notification_queue = None


@app.on_event("startup")
async def startup():
    global notification_queue
    notification_queue = asyncio.Queue()
    asyncio.create_task(process_notifications())


class NotificationRequest(BaseModel):
    user_id: int
    message: str


@app.post("/notify")
async def send_notification(request: NotificationRequest):
    await notification_queue.put(request)
    return {"status": "queued"}


async def process_notifications():
    while True:
        notification = await notification_queue.get()
        print(f"[NOTIFICATION] User {notification.user_id}: {notification.message}")
        await asyncio.sleep(0.1)
        notification_queue.task_done()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)