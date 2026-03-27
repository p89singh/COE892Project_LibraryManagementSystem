from fastapi import FastAPI, HTTPException, Request
import httpx
import uvicorn
from fastapi.responses import HTMLResponse
import os

app = FastAPI(title="Automated Library System API Gateway")

# Service Registry (Update these with your actual local or cloud URLs)
SERVICES = {
    "catalog": "http://localhost:8001",
    "user": "http://localhost:8002",
    "circulation": "http://localhost:8003"
}

@app.get("/")
async def health_check():
    return {"status": "online", "system": "Automated Public Library System"}

# --- Catalog Service Routing ---
@app.get("/search")
async def search_catalog(query: str):
    """Routes search requests to the Catalog Service[cite: 69, 92]."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES['catalog']}/items", params={"q": query})
            return response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Catalog Service unavailable")

# --- Circulation Engine Routing ---
@app.post("/borrow")
async def borrow_item(user_id: int, item_id: int):
    """
    Routes borrowing requests to the Circulation Engine.
    """
    # Add the timeout parameter here as well
    async with httpx.AsyncClient(timeout=None) as client:
        try:
            payload = {"user_id": user_id, "item_id": item_id}
            response = await client.post(f"{SERVICES['circulation']}/borrow", json=payload)
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
            return response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Circulation Engine unavailable")

# --- User Service Routing ---
@app.get("/profile/{user_id}")
async def get_user_profile(user_id: int):
    """Routes account and policy requests to the User Service[cite: 69, 102]."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES['user']}/profile/{user_id}")
            return response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="User Service unavailable")


@app.get("/ui", response_class=HTMLResponse)
async def serve_ui():
    """Serves the LibraryOS Web Interface"""
    # Assuming index.html is in the same folder as gateway.py
    with open("index.html", "r") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content, status_code=200)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)