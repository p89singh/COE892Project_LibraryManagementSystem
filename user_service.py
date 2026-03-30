from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncpg
import uvicorn

app = FastAPI(title="User Service")

DB_DSN = "postgresql://postgres:postgres@localhost/user_db"
db_pool = None

@app.on_event("startup")
async def startup():
    global db_pool
    db_pool = await asyncpg.create_pool(dsn=DB_DSN)

@app.on_event("shutdown")
async def shutdown():
    await db_pool.close()

class CreateUserRequest(BaseModel):
    full_name: str
    email: str

@app.get("/profile/{user_id}")
async def get_profile(user_id: int):
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return dict(user)

@app.post("/users")
async def create_user(request: CreateUserRequest):
    async with db_pool.acquire() as conn:
        try:
            user_id = await conn.fetchval(
                "INSERT INTO users (full_name, email) VALUES ($1, $2) RETURNING id",
                request.full_name, request.email
            )
            return {"user_id": user_id, "full_name": request.full_name}
        except asyncpg.exceptions.UniqueViolationError:
            raise HTTPException(status_code=400, detail="Email already registered")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)