## Client Application & API Gateway Setup

The user-facing components consist of a Python CLI client and a FastAPI Gateway. The Gateway ensures that patrons never interact directly with internal databases, satisfying the requirement for proper service isolation.

### Prerequisites
Ensure you have Python 3.8+ installed. Install the required dependencies:
\`\`\`bash
pip install fastapi uvicorn requests httpx
\`\`\`

### Running the System

**1. Start the API Gateway**
The gateway routes client requests to the backend C++ and Python microservices.
\`\`\`bash
python gateway.py
\`\`\`
*Note: The Gateway runs on `http://localhost:8000` by default. Interactive API documentation (Swagger) is automatically available at `http://localhost:8000/docs`.*

**2. Launch the Interactive Client**
Open a new terminal window to start the patron interface. This CLI allows users to search the catalog, view availability, and borrow items.
\`\`\`bash
python client.py
\`\`\`

**3. Run the Concurrency Load Test**
To verify system correctness under concurrency, run the automated load test. This simulates 50 users attempting to check out the exact same resource simultaneously. 
\`\`\`bash
python load_test.py
\`\`\`
The test will output quantitative metrics including request latency, successful transactions, and error frequencies. A successful test will result in exactly 1 successful borrow and 49 rejected conflicts (HTTP 409), proving the Circulation Engine maintains consistent state.

**if errors on sockets, check other connections by entering into terminal:
netstat -ano | findstr :8000

and kill of processes by entering: 
taskkill /PID 12345 /F