from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import uvicorn

app = FastAPI(title="Recommendation Service")

CATALOG_URL = "http://localhost:8001/items"
borrow_history = {}


class BorrowEvent(BaseModel):
    user_id: int
    item_id: int


@app.post("/record-borrow")
async def record_borrow(event: BorrowEvent):
    history = borrow_history.setdefault(event.user_id, [])
    history.append(event.item_id)
    return {"status": "recorded"}


@app.get("/recommend/{user_id}")
async def recommend(user_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(CATALOG_URL, timeout=5.0)

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Catalog service unavailable.")

    items = response.json()
    borrowed_ids = set(borrow_history.get(user_id, []))

    borrowed_genres = set()
    for item in items:
        if item["id"] in borrowed_ids:
            borrowed_genres.add(item.get("genre"))

    recommendations = []
    for item in items:
        if item["id"] in borrowed_ids:
            continue
        if borrowed_genres and item.get("genre") in borrowed_genres:
            recommendations.append(item)

    if not recommendations:
        recommendations = [item for item in items if item["id"] not in borrowed_ids][:5]

    return recommendations[:5]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)