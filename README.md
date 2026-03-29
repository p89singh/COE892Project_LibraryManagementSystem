## Client Application & API Gateway Setup

The user-facing components consist of a Python CLI client and a FastAPI Gateway. The Gateway ensures that patrons never interact directly with internal databases, satisfying the requirement for proper service isolation.

### Prerequisites
Ensure you have Python 3.8+ installed. Install the required dependencies:

```bash
pip install fastapi uvicorn requests httpx
```

### Running the System

**1. Start the API Gateway**
The gateway routes client requests to the backend C++ and Python microservices.
```bash
python gateway.py
```
*Note: The Gateway runs on `http://localhost:8000` by default. Interactive API documentation (Swagger) is automatically available at `http://localhost:8000/docs`.*

**2. Launch the Interactive Client**
Open a new terminal window to start the patron interface. This CLI allows users to search the catalog, view availability, and borrow items.
```bash
python client.py
```

**3. Run the Concurrency Load Test**
To verify system correctness under concurrency, run the automated load test. This simulates 50 users attempting to check out the exact same resource simultaneously. 
```bash
python load_test.py
```
The test will output quantitative metrics including request latency, successful transactions, and error frequencies. A successful test will result in exactly 1 successful borrow and 49 rejected conflicts (HTTP 409), proving the Circulation Engine maintains consistent state.

**if errors on sockets, check other connections by entering into terminal:
netstat -ano | findstr :8000

and kill of processes by entering: 
taskkill /PID 12345 /F


## Notification and Recommendation Services

Install the updated dependancies
```bash
pip install fastapi uvicorn requests httpx asyncpg redis aio-pika apscheduler
```

### Notification Services

The Notification Service runs silently in the background and handles all user-facing alerts. It does not expose any HTTP endpoints — it purely listens for events and runs a scheduled job.

It does two things:
1. When a borrow is processed, it immediately sends the user a confirmation message with the item title and due date
2. Every morning at 9:00 AM, it scans the database for any items due within the next 3 days and sends a reminder to the borrowing user

To start it:
```bash
python notification_service.py
```
Note: By default, notifications print to the console. To connect real email or SMS delivery, replace the `send_notification()` function in `notification_service.py` with your preferred delivery method (e.g. SMTP, Twilio).


### Recommendation Service

The Recommendation Service tracks each user's borrowing habits by genre and media type, and uses that history to suggest available items they haven't read yet. It runs on `http://localhost:8004`.

To start it:
```bash
python recommendation_service.py
```

It exposes two endpoints, both accessible through the gateway:
`GET /recommend/{user_id}`

Returns a ranked list of available items personalized to the user's borrowing history. Items are scored based on how closely their genre and media type match the user's past borrows. Genre match is weighted more heavily than media type.
```bash
GET http://localhost:8000/recommend/1
```

You can optionally request more or fewer results using the `top_n` parameter (defaults to 5):

```bash
GET http://localhost:8000/recommend/1?top_n=10
```

Example response:
```json
{
  "user_id": 1,
  "profile": {
    "genre_preferences": { "Fiction": 3, "Technology": 1 },
    "media_preferences": { "Book": 4 }
  },
  "recommended": [
    { "item_id": 3, "title": "Dune", "author": "Herbert", "genre": "Fiction", "media_type": "Book", "score": 7 }
  ]
}
```

Note: If a user has no borrowing history yet, the service falls back to their PostgreSQL borrow history to build an initial profile. Recommendations improve over time as the user borrows more items.
`GET /analytics/{user_id}`

Returns a breakdown of the user's borrowing history by genre and media type, with counts and percentages.
```bash
GET http://localhost:8000/analytics/1
```

Example response:
```json
{
  "user_id": 1,
  "total_borrows": 4,
  "by_genre": [
    { "label": "Fiction",    "count": 3, "percentage": 75.0 },
    { "label": "Technology", "count": 1, "percentage": 25.0 }
  ],
  "by_media": [
    { "label": "Book", "count": 4, "percentage": 100.0 }
  ]
}
```

### Full System Startup Order

Infrastructure must be running before any service is started. Then start each service in its own terminal in this order:

```bash
python circulation.py
python user_service.py
python recommendation_service.py
python notification_service.py
python gateway.py
```

The gateway on port 8000 is the only entry point that should be used. All endpoints listed above are accessed through it, not directly through the individual services.

If errors on sockets, check other connections by entering into terminal:
```bash
netstat -ano | findstr :8000
netstat -ano | findstr :8003
netstat -ano | findstr :8004
```

And kill off processes by entering:
```bash
taskkill /PID 12345 /F
```
