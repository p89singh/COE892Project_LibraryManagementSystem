from fastapi import FastAPI, HTTPException, Query
import asyncpg
import uvicorn

app = FastAPI(title="Catalog Service")

# Database connection details
DB_DSN = "postgresql://postgres:postgres@localhost/catalog_db"
db_pool = None

@app.on_event("startup")
async def startup():
    global db_pool
    db_pool = await asyncpg.create_pool(dsn=DB_DSN)

@app.on_event("shutdown")
async def shutdown():
    await db_pool.close()

@app.get("/items")
async def search_items(q: str = Query("", alias="q")):
    async with db_pool.acquire() as conn:
        if q:
            # ILIKE provides case-insensitive search
            query = """
                SELECT id, title, author, genre, media_type, total_copies 
                FROM items 
                WHERE title ILIKE $1 OR author ILIKE $1
            """
            rows = await conn.fetch(query, f"%{q}%")
        else:
            query = "SELECT id, title, author, genre, media_type, total_copies FROM items"
            rows = await conn.fetch(query)
            
        return [dict(row) for row in rows]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)