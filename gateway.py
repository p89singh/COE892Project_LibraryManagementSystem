from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import uvicorn
import os

app = FastAPI(title="Automated Library System API Gateway")

SERVICES = {
    "catalog":         "http://localhost:8003",   # circulation engine also handles catalog
    "user":            "http://localhost:8002",
    "circulation":     "http://localhost:8003",
    "recommendation":  "http://localhost:8004",
}


@app.get("/")
async def health_check():
    return {"status": "online", "system": "Automated Public Library System"}


@app.get("/search")
async def search_catalog(query: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES['catalog']}/items", params={"q": query})
            return response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Catalog Service unavailable")


@app.post("/borrow")
async def borrow_item(user_id: int, item_id: int):
    async with httpx.AsyncClient(timeout=None) as client:
        try:
            payload  = {"user_id": user_id, "item_id": item_id}
            response = await client.post(f"{SERVICES['circulation']}/borrow", json=payload)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Circulation Engine unavailable")


@app.post("/return")
async def return_item(user_id: int, item_id: int):
    async with httpx.AsyncClient(timeout=None) as client:
        try:
            payload  = {"user_id": user_id, "item_id": item_id}
            response = await client.post(f"{SERVICES['circulation']}/return", json=payload)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Circulation Engine unavailable")


@app.get("/profile/{user_id}")
async def get_user_profile(user_id: int):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES['user']}/profile/{user_id}")
            return response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="User Service unavailable")


@app.get("/recommend/{user_id}")
async def get_recommendations(user_id: int, top_n: int = 5):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{SERVICES['recommendation']}/recommend/{user_id}",
                params={"top_n": top_n}
            )
            return response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Recommendation Service unavailable")


@app.get("/analytics/{user_id}")
async def get_analytics(user_id: int):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES['recommendation']}/analytics/{user_id}")
            return response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Recommendation Service unavailable")


@app.get("/ui", response_class=HTMLResponse)
async def serve_ui():
    with open("index.html", "r") as f:
        return HTMLResponse(content=f.read(), status_code=200)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)