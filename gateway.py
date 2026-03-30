from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import uvicorn
import os

app = FastAPI(title="Automated Library System API Gateway")

CATALOG_URL = "http://localhost:8001"
USER_URL = "http://localhost:8002"
CIRCULATION_URL = "http://localhost:8003"
RECOMMENDATION_URL = "http://localhost:8004"


@app.get("/", response_class=HTMLResponse)
async def root():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Library Management System Gateway</h1>"


@app.get("/search")
async def search_catalog(q: str = ""):
    async with httpx.AsyncClient() as client:
        catalog_response = await client.get(f"{CATALOG_URL}/items", params={"q": q}, timeout=5.0)

        if catalog_response.status_code != 200:
            raise HTTPException(status_code=502, detail="Catalog service unavailable.")

        items = catalog_response.json()
        merged = []

        for item in items:
            avail_response = await client.get(
                f"{CIRCULATION_URL}/availability/{item['id']}",
                timeout=5.0
            )

            if avail_response.status_code == 200:
                availability = avail_response.json()
                merged.append({
                    "id": item["id"],
                    "title": item["title"],
                    "author": item["author"],
                    "genre": item["genre"],
                    "media_type": item["media_type"],
                    "availability": availability["state"]
                })
            else:
                merged.append({
                    "id": item["id"],
                    "title": item["title"],
                    "author": item["author"],
                    "genre": item["genre"],
                    "media_type": item["media_type"],
                    "availability": "UNKNOWN"
                })

    return merged


@app.get("/profile/{user_id}")
async def profile(user_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_URL}/profile/{user_id}", timeout=5.0)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()


@app.get("/availability/{item_id}")
async def availability(item_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{CIRCULATION_URL}/availability/{item_id}", timeout=5.0)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()


@app.post("/borrow")
async def borrow(payload: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{CIRCULATION_URL}/borrow", json=payload, timeout=5.0)

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.json())

    return response.json()


@app.post("/return")
async def return_item(payload: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{CIRCULATION_URL}/return", json=payload, timeout=5.0)

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.json())

    return response.json()


@app.post("/reserve")
async def reserve(payload: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{CIRCULATION_URL}/reserve", json=payload, timeout=5.0)

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.json())

    return response.json()


@app.get("/recommend/{user_id}")
async def recommend(user_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{RECOMMENDATION_URL}/recommend/{user_id}", timeout=5.0)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)