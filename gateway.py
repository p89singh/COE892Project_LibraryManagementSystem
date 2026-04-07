from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import httpx
import uvicorn

app = FastAPI(title="Automated Library System API Gateway")

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

CATALOG_URL = "http://catalog-service:8001"
USER_URL = "http://user-service:8002"
CIRCULATION_URL = "http://circulation-service:8003"
RECOMMENDATION_URL = "http://recommendation-service:8004"


@app.get("/")
async def root():
    return FileResponse("frontend/index.html")


@app.get("/login")
async def login_page():
    return FileResponse("frontend/login.html")


@app.get("/register")
async def register_page():
    return FileResponse("frontend/register.html")


@app.get("/catalog")
async def catalog_page():
    return FileResponse("frontend/catalog.html")


@app.get("/my-library")
async def my_library_page():
    return FileResponse("frontend/my-library.html")


@app.get("/recommendations-page")
async def recommendations_page():
    return FileResponse("frontend/recommendations.html")


@app.get("/admin")
async def admin_page():
    return FileResponse("frontend/admin.html")


@app.post("/auth/register")
async def register(payload: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{USER_URL}/auth/register", json=payload, timeout=5.0)

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    try:
        return response.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Invalid response from user service")


@app.post("/auth/login")
async def login(payload: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{USER_URL}/auth/login", json=payload, timeout=5.0)

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    try:
        return response.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Invalid response from user service")


@app.get("/search")
async def search_catalog(q: str = ""):
    async with httpx.AsyncClient() as client:
        catalog_response = await client.get(f"{CATALOG_URL}/items", params={"q": q}, timeout=5.0)

        if catalog_response.status_code != 200:
            raise HTTPException(status_code=502, detail="Catalog service unavailable.")

        try:
            items = catalog_response.json()
        except Exception:
            raise HTTPException(status_code=502, detail="Invalid response from catalog service")

        merged = []

        for item in items:
            avail_response = await client.get(
                f"{CIRCULATION_URL}/availability/{item['id']}",
                timeout=5.0
            )

            if avail_response.status_code == 200:
                try:
                    availability = avail_response.json()
                    merged.append({
                        **item,
                        "availability": availability["state"]
                    })
                except Exception:
                    merged.append({
                        **item,
                        "availability": "UNKNOWN"
                    })
            else:
                merged.append({
                    **item,
                    "availability": "UNKNOWN"
                })

    return merged


@app.get("/items/{item_id}")
async def get_item(item_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{CATALOG_URL}/items/{item_id}", timeout=5.0)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    try:
        return response.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Invalid response from catalog service")


@app.post("/items")
async def create_item(payload: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{CATALOG_URL}/items", json=payload, timeout=5.0)

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    try:
        return response.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Invalid response from catalog service")


@app.put("/items/{item_id}")
async def update_item(item_id: int, payload: dict):
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{CATALOG_URL}/items/{item_id}", json=payload, timeout=5.0)

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    try:
        return response.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Invalid response from catalog service")


@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{CATALOG_URL}/items/{item_id}", timeout=5.0)

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    try:
        return response.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Invalid response from catalog service")


@app.get("/profile/{user_id}")
async def profile(user_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_URL}/profile/{user_id}", timeout=5.0)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    try:
        return response.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Invalid response from user service")


@app.get("/users")
async def users():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_URL}/users", timeout=5.0)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    try:
        return response.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Invalid response from user service")


@app.get("/availability/{item_id}")
async def availability(item_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{CIRCULATION_URL}/availability/{item_id}", timeout=5.0)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    try:
        return response.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Invalid response from circulation service")


@app.post("/borrow")
async def borrow(payload: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{CIRCULATION_URL}/borrow", json=payload, timeout=5.0)

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    try:
        return response.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Invalid response from circulation service")


@app.post("/return")
async def return_item(payload: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{CIRCULATION_URL}/return", json=payload, timeout=5.0)

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    try:
        return response.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Invalid response from circulation service")


@app.post("/reserve")
async def reserve(payload: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{CIRCULATION_URL}/reserve", json=payload, timeout=5.0)

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    try:
        return response.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Invalid response from circulation service")


@app.post("/renew")
async def renew(payload: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{CIRCULATION_URL}/renew", json=payload, timeout=5.0)

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    try:
        return response.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Invalid response from circulation service")


@app.get("/loans/{user_id}")
async def loans(user_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{CIRCULATION_URL}/loans/{user_id}", timeout=5.0)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    try:
        return response.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Invalid response from circulation service")


@app.get("/reservations/{user_id}")
async def reservations(user_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{CIRCULATION_URL}/reservations/{user_id}", timeout=5.0)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    try:
        return response.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Invalid response from circulation service")


@app.get("/recommendations/{user_id}")
async def recommend(user_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{RECOMMENDATION_URL}/recommend/{user_id}", timeout=5.0)

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    try:
        return response.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Invalid response from recommendation service")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)