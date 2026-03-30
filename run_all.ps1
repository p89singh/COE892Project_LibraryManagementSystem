$repoPath = "C:\Users\singh\Documents\COE892Project_LibraryManagementSystem"
$dbPath = "$repoPath\database"

Write-Host "Starting Library Management System..." -ForegroundColor Green

# Start Docker database services
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$dbPath'; docker compose up -d"

Start-Sleep -Seconds 5

# Start Catalog Service
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$repoPath'; python catalog_service.py"

Start-Sleep -Seconds 2

# Start User Service
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$repoPath'; python user_service.py"

Start-Sleep -Seconds 2

# Start Circulation Service
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$repoPath'; python circulation.py"

Start-Sleep -Seconds 2

# Start Recommendation Service
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$repoPath'; python recommendation_service.py"

Start-Sleep -Seconds 2

# Start Notification Service
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$repoPath'; python notification_service.py"

Start-Sleep -Seconds 2

# Start Gateway
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$repoPath'; python gateway.py"

Start-Sleep -Seconds 3

# Start Client
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$repoPath'; python client.py"

Write-Host "All services launched." -ForegroundColor Cyan
Write-Host "Gateway should be at: http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "Swagger docs should be at: http://127.0.0.1:8000/docs" -ForegroundColor Yellow