from fastapi import FastAPI, HTTPException
import uvicorn

app = FastAPI(title="Recommendation Service")

# Dummy catalog (should match your catalog service IDs)
catalog = {
    101: "Database System Concepts",
    102: "RabbitMQ in Action",
    103: "Distributed Systems",
    104: "Operating Systems",
    105: "Computer Networks"
}

# Simple recommendation logic (hardcoded relationships)
recommendations_map = {
    101: [103, 104],
    102: [103],
    103: [101, 105],
    104: [101],
    105: [103]
}


@app.get("/recommend/{user_id}")
async def recommend(user_id: int, borrowed_items: list[int] = []):
    if not borrowed_items:
        return {
            "user_id": user_id,
            "recommendations": list(catalog.keys())[:3]  # default suggestions
        }

    recommended = set()

    for item in borrowed_items:
        if item in recommendations_map:
            recommended.update(recommendations_map[item])

    return {
        "user_id": user_id,
        "recommendations": list(recommended)
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)