from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncpg
import uvicorn

app = FastAPI(title="User Service")

DB_DSN = "postgresql://postgres:postgres@postgres:5432/user_db"
db_pool = None


class RegisterRequest(BaseModel):
    full_name: str
    email: str


class LoginRequest(BaseModel):
    email: str


@app.on_event("startup")
async def startup() -> None:
    global db_pool
    db_pool = await asyncpg.create_pool(dsn=DB_DSN)


@app.on_event("shutdown")
async def shutdown() -> None:
    if db_pool:
        await db_pool.close()


@app.get("/profile/{user_id}")
async def get_profile(user_id: int):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, full_name, email, account_status, max_loans, created_at
            FROM users
            WHERE id = $1
            """,
            user_id,
        )

    if not row:
        raise HTTPException(status_code=404, detail="User not found.")

    return dict(row)


@app.get("/users")
async def get_users():
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, full_name, email, account_status, max_loans, created_at
            FROM users
            ORDER BY id
            """
        )

    return [dict(row) for row in rows]


@app.post("/auth/register")
async def register_user(data: RegisterRequest):
    async with db_pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1",
            data.email
        )

        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")

        row = await conn.fetchrow(
            """
            INSERT INTO users (full_name, email)
            VALUES ($1, $2)
            RETURNING id, full_name, email, account_status, max_loans, created_at
            """,
            data.full_name,
            data.email
        )

    return dict(row)


@app.post("/auth/login")
async def login_user(data: LoginRequest):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, full_name, email, account_status, max_loans, created_at
            FROM users
            WHERE email = $1
            """,
            data.email
        )

    if not row:
        raise HTTPException(status_code=401, detail="User not found")

    return dict(row)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)