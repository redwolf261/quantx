# FutureLens Start Script
# Run this script in PowerShell to launch all services.

Write-Host "=================================================="
Write-Host "   FutureLens - AI Financial Intelligence Platform"
Write-Host "=================================================="

# 1. Start Docker (Optional Fallback)
Write-Host "[1/4] Attempting to start PostgreSQL via Docker..."
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Warning: Docker Compose failed to start. FutureLens will fall back to a local SQLite database (aiosqlite)!"
}


# 2. Setup Backend Virtual Env & Install dependencies
Write-Host "[2/4] Setting up Python backend..."
cd backend
if (-not (Test-Path "venv")) {
    python -m venv venv
}

# Activate virtualenv on Windows PowerShell and install requirements
& .\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

# Setup env file if not exists
if (-not (Test-Path ".env")) {
    copy .env.example .env
    Write-Host "Created .env from template."
}

# 3. Seed database
Write-Host "[3/4] Seeding synthetic Indian banking profiles..."
cd ..
python data/generate_synthetic.py --seed-db

# 4. Install Frontend dependencies
Write-Host "[4/4] Setting up Next.js frontend..."
cd frontend
if (-not (Test-Path ".env.local")) {
    copy .env.local.example .env.local
}
npm install

# 5. Launch everything in background tabs/jobs
Write-Host "Launching services..."

# Start backend in a new window using Windows PowerShell activation
Start-Process powershell -ArgumentList "-ExecutionPolicy", "Bypass", "-NoExit", "-Command", "cd backend; & .\venv\Scripts\Activate.ps1; python main.py" -WindowStyle Normal

# Start frontend in a new window
Start-Process powershell -ArgumentList "-ExecutionPolicy", "Bypass", "-NoExit", "-Command", "cd frontend; npm run dev" -WindowStyle Normal

Write-Host "=================================================="
Write-Host "   FutureLens is starting up!"
Write-Host "   - Backend Docs: http://localhost:8000/docs"
Write-Host "   - Frontend UI:  http://localhost:3000"
Write-Host "=================================================="
