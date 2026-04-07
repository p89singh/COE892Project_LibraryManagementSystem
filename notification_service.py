from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Notification Service")


class NotificationRequest(BaseModel):
    user_id: int
    message: str


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/notify")
async def notify(data: NotificationRequest):
    return {
        "status": "success",
        "message": f"Notification accepted for user {data.user_id}",
        "payload": {
            "user_id": data.user_id,
            "message": data.message
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)