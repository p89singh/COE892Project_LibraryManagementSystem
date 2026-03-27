from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import uvicorn

app = FastAPI(title="Dummy Circulation Engine")

# Simulated Database
inventory = {
    101: {"title": "Database System Concepts", "available": True, "borrowed_by": None},
    102: {"title": "RabbitMQ in Action", "available": True, "borrowed_by": None}
}

# 1. Declare the lock, but DO NOT create it yet
inventory_lock = None

# 2. Create the lock right as the server starts up
@app.on_event("startup")
async def startup_event():
    global inventory_lock
    inventory_lock = asyncio.Lock()  # Now it safely attaches to the running server!

class BorrowRequest(BaseModel):
    user_id: int
    item_id: int

@app.post("/borrow")
async def process_borrow(request: BorrowRequest):
    global inventory_lock
    
    # The lock now works perfectly to enforce consistency under concurrency
    async with inventory_lock:
        await asyncio.sleep(0.05) # Simulate database processing time
        
        item = inventory.get(request.item_id)
        
        if not item:
            raise HTTPException(status_code=404, detail="Item not found in catalog.")
        
        if not item["available"]:
            raise HTTPException(
                status_code=409, 
                detail=f"Item {request.item_id} is already checked out."
            )
        
        item["available"] = False
        item["borrowed_by"] = request.user_id
        
        print(f"[EVENT] Item {request.item_id} checked out by User {request.user_id}.")
        return {
            "status": "success", 
            "message": f"Item {request.item_id} successfully checked out to user {request.user_id}"
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)