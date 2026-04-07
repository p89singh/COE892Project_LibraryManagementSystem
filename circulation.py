from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncpg
import httpx
import uvicorn

app = FastAPI(title="Circulation Service")

DB_DSN = "postgresql://postgres:postgres@postgres:5432/circulation_db"
db_pool = None

NOTIFICATION_URL = "http://notification-service:8005/notify"
RECOMMENDATION_URL = "http://recommendation-service:8004/record-borrow"


class BorrowRequest(BaseModel):
    user_id: int
    item_id: int


class ReturnRequest(BaseModel):
    user_id: int
    item_id: int


class ReserveRequest(BaseModel):
    user_id: int
    item_id: int


class RenewRequest(BaseModel):
    user_id: int
    item_id: int


@app.on_event("startup")
async def startup() -> None:
    global db_pool
    db_pool = await asyncpg.create_pool(dsn=DB_DSN)


@app.on_event("shutdown")
async def shutdown() -> None:
    if db_pool:
        await db_pool.close()


@app.get("/availability/{item_id}")
async def get_availability(item_id: int):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT item_id, state, checked_out_by, reserved_by, updated_at
            FROM item_state
            WHERE item_id = $1
            """,
            item_id,
        )

    if not row:
        raise HTTPException(status_code=404, detail="Item not found in circulation.")

    return dict(row)


@app.post("/borrow")
async def borrow_item(request: BorrowRequest):
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            state_row = await conn.fetchrow(
                """
                SELECT item_id, state, checked_out_by, reserved_by
                FROM item_state
                WHERE item_id = $1
                FOR UPDATE
                """,
                request.item_id,
            )

            if not state_row:
                raise HTTPException(status_code=404, detail="Item not found.")

            if state_row["state"] == "CHECKED_OUT":
                raise HTTPException(status_code=409, detail="Item is already checked out.")

            if state_row["state"] == "RESERVED" and state_row["reserved_by"] != request.user_id:
                raise HTTPException(status_code=409, detail="Item is reserved by another user.")

            due_date = await conn.fetchval(
                "SELECT CURRENT_TIMESTAMP + INTERVAL '14 days'"
            )

            await conn.execute(
                """
                INSERT INTO loans (user_id, item_id, due_date, status)
                VALUES ($1, $2, $3, 'ACTIVE')
                """,
                request.user_id,
                request.item_id,
                due_date,
            )

            await conn.execute(
                """
                UPDATE item_state
                SET state = 'CHECKED_OUT',
                    checked_out_by = $1,
                    reserved_by = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE item_id = $2
                """,
                request.user_id,
                request.item_id,
            )

            await conn.execute(
                """
                UPDATE reservations
                SET status = 'FULFILLED'
                WHERE item_id = $1
                  AND user_id = $2
                  AND status = 'ACTIVE'
                """,
                request.item_id,
                request.user_id,
            )

    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                NOTIFICATION_URL,
                json={
                    "user_id": request.user_id,
                    "message": f"Item {request.item_id} was successfully borrowed."
                },
                timeout=2.0,
            )
        except Exception:
            pass

        try:
            await client.post(
                RECOMMENDATION_URL,
                json={"user_id": request.user_id, "item_id": request.item_id},
                timeout=2.0,
            )
        except Exception:
            pass

    return {
        "status": "success",
        "message": f"Item {request.item_id} successfully checked out to user {request.user_id}"
    }


@app.post("/return")
async def return_item(request: ReturnRequest):
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            state_row = await conn.fetchrow(
                """
                SELECT item_id, state, checked_out_by
                FROM item_state
                WHERE item_id = $1
                FOR UPDATE
                """,
                request.item_id,
            )

            if not state_row:
                raise HTTPException(status_code=404, detail="Item not found.")

            if state_row["state"] != "CHECKED_OUT":
                raise HTTPException(status_code=409, detail="Item is not currently checked out.")

            if state_row["checked_out_by"] != request.user_id:
                raise HTTPException(status_code=403, detail="This user did not borrow the item.")

            await conn.execute(
                """
                UPDATE loans
                SET status = 'RETURNED',
                    returned_at = CURRENT_TIMESTAMP
                WHERE item_id = $1
                  AND user_id = $2
                  AND status = 'ACTIVE'
                """,
                request.item_id,
                request.user_id,
            )

            next_reservation = await conn.fetchrow(
                """
                SELECT user_id
                FROM reservations
                WHERE item_id = $1
                  AND status = 'ACTIVE'
                ORDER BY queue_position ASC NULLS LAST, reserved_at ASC
                LIMIT 1
                """,
                request.item_id,
            )

            if next_reservation:
                await conn.execute(
                    """
                    UPDATE item_state
                    SET state = 'RESERVED',
                        checked_out_by = NULL,
                        reserved_by = $1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE item_id = $2
                    """,
                    next_reservation["user_id"],
                    request.item_id,
                )
            else:
                await conn.execute(
                    """
                    UPDATE item_state
                    SET state = 'AVAILABLE',
                        checked_out_by = NULL,
                        reserved_by = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE item_id = $1
                    """,
                    request.item_id,
                )

    return {
        "status": "success",
        "message": f"Item {request.item_id} successfully returned by user {request.user_id}"
    }


@app.post("/reserve")
async def reserve_item(request: ReserveRequest):
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            state_row = await conn.fetchrow(
                """
                SELECT item_id, state, reserved_by
                FROM item_state
                WHERE item_id = $1
                FOR UPDATE
                """,
                request.item_id,
            )

            if not state_row:
                raise HTTPException(status_code=404, detail="Item not found.")

            existing_active = await conn.fetchrow(
                """
                SELECT id
                FROM reservations
                WHERE item_id = $1
                  AND user_id = $2
                  AND status = 'ACTIVE'
                """,
                request.item_id,
                request.user_id,
            )

            if existing_active:
                raise HTTPException(status_code=409, detail="User already has an active reservation for this item.")

            max_queue = await conn.fetchval(
                """
                SELECT COALESCE(MAX(queue_position), 0)
                FROM reservations
                WHERE item_id = $1
                  AND status = 'ACTIVE'
                """,
                request.item_id,
            )

            queue_position = max_queue + 1

            await conn.execute(
                """
                INSERT INTO reservations (user_id, item_id, queue_position, status)
                VALUES ($1, $2, $3, 'ACTIVE')
                """,
                request.user_id,
                request.item_id,
                queue_position,
            )

            if state_row["state"] == "AVAILABLE" and queue_position == 1:
                await conn.execute(
                    """
                    UPDATE item_state
                    SET state = 'RESERVED',
                        reserved_by = $1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE item_id = $2
                    """,
                    request.user_id,
                    request.item_id,
                )

    return {
        "status": "success",
        "message": f"Reservation created for item {request.item_id} by user {request.user_id}",
        "queue_position": queue_position,
    }


@app.post("/renew")
async def renew_item(request: RenewRequest):
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            state_row = await conn.fetchrow(
                """
                SELECT item_id, state, checked_out_by
                FROM item_state
                WHERE item_id = $1
                FOR UPDATE
                """,
                request.item_id,
            )

            if not state_row:
                raise HTTPException(status_code=404, detail="Item not found.")

            if state_row["state"] != "CHECKED_OUT":
                raise HTTPException(status_code=409, detail="Item is not currently checked out.")

            if state_row["checked_out_by"] != request.user_id:
                raise HTTPException(status_code=403, detail="This user did not borrow the item.")

            active_reservation = await conn.fetchrow(
                """
                SELECT id
                FROM reservations
                WHERE item_id = $1
                  AND status = 'ACTIVE'
                LIMIT 1
                """,
                request.item_id,
            )

            if active_reservation:
                raise HTTPException(status_code=409, detail="Item has an active reservation and cannot be renewed.")

            result = await conn.execute(
                """
                UPDATE loans
                SET due_date = due_date + INTERVAL '14 days'
                WHERE item_id = $1
                  AND user_id = $2
                  AND status = 'ACTIVE'
                """,
                request.item_id,
                request.user_id,
            )

            if result.endswith("0"):
                raise HTTPException(status_code=404, detail="Active loan not found.")

            updated_loan = await conn.fetchrow(
                """
                SELECT id, user_id, item_id, borrowed_at, due_date, returned_at, status
                FROM loans
                WHERE item_id = $1
                  AND user_id = $2
                  AND status = 'ACTIVE'
                ORDER BY borrowed_at DESC
                LIMIT 1
                """,
                request.item_id,
                request.user_id,
            )

    return {
        "status": "success",
        "message": f"Item {request.item_id} successfully renewed for user {request.user_id}",
        "loan": dict(updated_loan),
    }


@app.get("/loans/{user_id}")
async def get_loans(user_id: int):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, user_id, item_id, borrowed_at, due_date, returned_at, status
            FROM loans
            WHERE user_id = $1
            ORDER BY borrowed_at DESC
            """,
            user_id,
        )

    return [dict(row) for row in rows]


@app.get("/reservations/{user_id}")
async def get_reservations(user_id: int):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, user_id, item_id, reserved_at, queue_position, status
            FROM reservations
            WHERE user_id = $1
            ORDER BY reserved_at DESC
            """,
            user_id,
        )

    return [dict(row) for row in rows]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)