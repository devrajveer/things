# start-all.ps1

$ErrorActionPreference = "Stop"

# 1. Download and Start NATS Server
Write-Host "Checking for NATS Server..."
if (!(Test-Path "nats-server.exe")) {
    Write-Host "Downloading NATS Server..."
    Invoke-WebRequest -Uri "https://github.com/nats-io/nats-server/releases/download/v2.10.14/nats-server-v2.10.14-windows-amd64.zip" -OutFile "nats-server.zip"
    Expand-Archive -Path "nats-server.zip" -DestinationPath "." -Force
    Move-Item -Path "nats-server-v2.10.14-windows-amd64\nats-server.exe" -Destination "nats-server.exe" -Force
    Remove-Item "nats-server.zip"
    Remove-Item "nats-server-v2.10.14-windows-amd64" -Recurse -Force
}

Write-Host "Starting NATS Server with JetStream..."
Start-Process -FilePath ".\nats-server.exe" -ArgumentList "-js"

# Wait a moment for NATS to spin up
Start-Sleep -Seconds 2

# 2. Start Python Services
Write-Host "Starting Core API..."
Start-Process -WorkingDirectory "services\api" -FilePath "python" -ArgumentList "-m uvicorn yp_api.main:app --reload --port 8000"

Write-Host "Starting Ingest API..."
Start-Process -WorkingDirectory "services\ingest" -FilePath "python" -ArgumentList "-m uvicorn yp_ingest.main:app --reload --port 8001"

Write-Host "Starting Background Worker..."
Start-Process -WorkingDirectory "services\worker" -FilePath "python" -ArgumentList "-m yp_worker.main"

# 3. Start Node.js Services
Write-Host "Starting Realtime Service..."
Start-Process -WorkingDirectory "services\realtime" -FilePath "npm.cmd" -ArgumentList "run dev"

Write-Host "Starting Web Dashboard..."
Start-Process -WorkingDirectory "apps\web" -FilePath "npm.cmd" -ArgumentList "run dev"

Write-Host "All services started successfully in the background!"
Write-Host "API: http://localhost:8000"
Write-Host "Ingest: http://localhost:8001"
Write-Host "Web: http://localhost:3001"
