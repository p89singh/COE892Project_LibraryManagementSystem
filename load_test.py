import asyncio
import httpx
import time

# IMPORTANT: If you changed your gateway port to 8080 earlier, change it here too!
GATEWAY_URL = "http://localhost:8000" 
TARGET_ITEM_ID = 101
TOTAL_USERS = 50

async def attempt_borrow(client: httpx.AsyncClient, user_id: int):
    """A single user's attempt to borrow the target item."""
    start_time = time.time()
    try:
        response = await client.post(
            f"{GATEWAY_URL}/borrow",
            params={"user_id": user_id, "item_id": TARGET_ITEM_ID}
        )
        latency = time.time() - start_time
        return {"user_id": user_id, "status": response.status_code, "latency": latency}
    except Exception as e:
        latency = time.time() - start_time
        return {"user_id": user_id, "status": "ERROR", "latency": latency, "detail": str(e), "type": type(e).__name__}

async def run_concurrency_test():
    print("--- Starting Concurrency Test ---")
    print(f"Simulating {TOTAL_USERS} users attempting to borrow Item {TARGET_ITEM_ID} simultaneously...\n")
    
    # timeout=None ensures the client waits patiently for the backend queue
    async with httpx.AsyncClient(timeout=None) as client:
        tasks = [attempt_borrow(client, user_id) for user_id in range(1, TOTAL_USERS + 1)]
        
        overall_start = time.time()
        results = await asyncio.gather(*tasks)
        overall_time = time.time() - overall_start

    # --- Analyze the Results ---
    successes = 0
    conflicts = 0
    errors = 0
    total_latency = 0.0

    for res in results:
        status = res['status']
        total_latency += res['latency']
        
        if status == 200:
            successes += 1
            print(f"[WINNER] User {res['user_id']} successfully borrowed the item!")
        elif status == 409:
            conflicts += 1
        else:
            errors += 1
            print(f"[ERROR] User {res['user_id']} failed | Type: {res.get('type')} | Detail: {res.get('detail')}")
            
    avg_latency = (total_latency / TOTAL_USERS) * 1000

    print("\n--- Test Results ---")
    print(f"Total Requests:     {TOTAL_USERS}")
    print(f"Time Elapsed:       {overall_time:.2f} seconds")
    print(f"Average Latency:    {avg_latency:.2f} ms")
    print(f"Successful Borrows: {successes} (Expected: 1)")
    print(f"Rejected Conflicts: {conflicts} (Expected: {TOTAL_USERS - 1})")
    print(f"System Errors:      {errors} (Expected: 0)")

    if successes == 1 and errors == 0:
        print("\n✅ SUCCESS: The Circulation Engine properly handled concurrency! No double-checkouts.")
    else:
        print("\n❌ FAILED: System encountered errors or failed to process correctly.")

if __name__ == "__main__":
    asyncio.run(run_concurrency_test())