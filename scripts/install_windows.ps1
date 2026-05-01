#Requires -Version 5.1
<#
.SYNOPSIS
    PSC Current Affairs Agent - Windows Installation Script
.DESCRIPTION
    Installs all prerequisites and sets up the application for first use.
    Run in PowerShell as Administrator for full functionality.
.NOTES
    If not running as Administrator, some steps (Redis service) may fail.
    You can still run the app manually afterward.
#>

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$projectDir = Split-Path -Parent $scriptDir

$GREEN = "Green"
$RED = "Red"
$YELLOW = "Yellow"
$BLUE = "Blue"

function Write-Step { param($Number, $Message)
    Write-Host "`n[$Number] $Message" -ForegroundColor $BLUE
}
function Write-Ok { param($Message)
    Write-Host "  $Message" -ForegroundColor $GREEN
}
function Write-Warn { param($Message)
    Write-Host "  WARNING: $Message" -ForegroundColor $YELLOW
}
function Write-Err { param($Message)
    Write-Host "  ERROR: $Message" -ForegroundColor $RED
}

Write-Host "============================================" -ForegroundColor $GREEN
Write-Host "  PSC Current Affairs Agent - Windows Setup" -ForegroundColor $GREEN
Write-Host "============================================" -ForegroundColor $GREEN

Set-Location $projectDir

$installMode = "native"
if ($args -contains "--docker" -or $args -contains "-d") {
    Write-Host "`nDocker mode selected. Run docker-start.ps1 instead." -ForegroundColor $YELLOW
    Write-Host "  .\scripts\docker-start.ps1" -ForegroundColor $YELLOW
    exit 0
}

# --- Step 1: Check Git ---
Write-Step 1 "Checking prerequisites"

if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-Ok "git found: $(git --version)"
} else {
    Write-Err "git is not installed."
    Write-Host "  Download from: https://git-scm.com/download/win" -ForegroundColor $YELLOW
    Write-Host "  Install it, then re-run this script." -ForegroundColor $YELLOW
    exit 1
}

# --- Step 2: Install uv ---
Write-Step 2 "Installing uv (Python package manager)"

if (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Ok "uv already installed: $(uv --version)"
} else {
    Write-Host "  Installing uv..." -ForegroundColor $White
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

    $uvPath = "$env:USERPROFILE\.cargo\bin"
    $uvPath2 = "$env:USERPROFILE\.local\bin"

    if (Test-Path "$uvPath\uv.exe") {
        $env:Path = "$uvPath;$env:Path"
    } elseif (Test-Path "$uvPath2\uv.exe") {
        $env:Path = "$uvPath2;$env:Path"
    }

    if (Get-Command uv -ErrorAction SilentlyContinue) {
        Write-Ok "uv installed: $(uv --version)"
    } else {
        Write-Err "uv installation failed. Install manually from https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    }
}

# --- Step 3: Install Python dependencies ---
Write-Step 3 "Installing Python dependencies"

uv sync --no-dev
Write-Ok "Dependencies installed"

# --- Step 4: Install Ollama ---
Write-Step 4 "Setting up Ollama (local AI)"

if (Get-Command ollama -ErrorAction SilentlyContinue) {
    Write-Ok "Ollama already installed"
} else {
    Write-Host "  Downloading Ollama..." -ForegroundColor $White
    Write-Host "  Please download and install from: https://ollama.com/download" -ForegroundColor $Yellow
    Write-Host "  After installing, re-run this script." -ForegroundColor $Yellow
    Write-Host ""
    $response = Read-Host "  Is Ollama installed now? [y/N]"
    if ($response -ne "y") { exit 1 }
}

try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -ErrorAction Stop
    Write-Ok "Ollama is running"
} catch {
    Write-Host "  Ollama is not running. Starting it..." -ForegroundColor $White
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 5

    try {
        Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -ErrorAction Stop | Out-Null
        Write-Ok "Ollama started"
    } catch {
        Write-Warn "Could not reach Ollama. Start manually: ollama serve"
    }
}

# --- Step 5: Pull AI model ---
Write-Step 5 "Downloading AI model (gemma:2b, ~1.5 GB)"

try {
    $tags = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing | ConvertFrom-Json
    if ($tags.models | Where-Object { $_.name -like "gemma:2b*" }) {
        Write-Ok "gemma:2b model already downloaded"
    } else {
        Write-Host "  Pulling gemma:2b... (this takes a few minutes)" -ForegroundColor $White
        ollama pull gemma:2b
        Write-Ok "Model downloaded"
    }
} catch {
    Write-Host "  Pulling gemma:2b... (this takes a few minutes)" -ForegroundColor $White
    ollama pull gemma:2b
    Write-Ok "Model downloaded"
}

# --- Step 6: Set up Redis ---
Write-Step 6 "Setting up Redis"

if (Get-Service "Redis" -ErrorAction SilentlyContinue) {
    $redisSvc = Get-Service "Redis"
    if ($redisSvc.Status -eq "Running") {
        Write-Ok "Redis service is running"
    } else {
        Write-Host "  Starting Redis service..." -ForegroundColor $White
        Start-Service "Redis"
        Write-Ok "Redis started"
    }
} elseif (Get-Command redis-server -ErrorAction SilentlyContinue) {
    Write-Host "  redis-server found but not installed as a service." -ForegroundColor $White
    Write-Host "  Starting redis-server in background..." -ForegroundColor $White
    Start-Process "redis-server" -WindowStyle Hidden
    Start-Sleep -Seconds 3
    Write-Ok "redis-server started in background"
} else {
    Write-Warn "Redis is not installed."
    Write-Host ""
    Write-Host "  Options:" -ForegroundColor $White
    Write-Host "  1. Install Memurai (Redis for Windows): https://www.memurai.com/get-memurai" -ForegroundColor $White
    Write-Host "  2. Use WSL2 Redis: wsl sudo apt install redis-server && wsl sudo service redis-server start" -ForegroundColor $White
    Write-Host "  3. Use Docker: docker run -d -p 6379:6379 redis:7-alpine" -ForegroundColor $White
    Write-Host ""
    Write-Host "  Without Redis, Celery workers cannot run." -ForegroundColor $Yellow
    Write-Host "  You can still use the app with manual pipeline runs." -ForegroundColor $Yellow

    $response = Read-Host "  Continue without Redis? [y/N]"
    if ($response -ne "y") { exit 1 }
}

# --- Step 7: Initialize database ---
Write-Step 7 "Initializing database"

uv run python scripts/init_db.py
Write-Ok "Database initialized"

# --- Step 8: Create .env ---
Write-Step 8 "Setting up environment"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Ok ".env file created"
} else {
    Write-Ok ".env already exists"
}

# --- Step 9: Create Start script ---
Write-Step 9 "Creating start script"

$startScript = @"
@echo off
echo ============================================
echo   PSC Current Affairs Agent
echo ============================================
echo.
echo Starting services...
echo.

start "PSC Agent - API Server" cmd /k "uv run uvicorn app.main:app --reload --port 8000"
start "PSC Agent - Celery Worker" cmd /k "uv run celery -A app.workers.celery_app worker --loglevel=info"
start "PSC Agent - Celery Beat" cmd /k "uv run celery -A app.workers.celery_app beat --loglevel=info"

echo.
echo Three windows opened. Services are starting...
echo App will be available at: http://localhost:8000
echo.
echo To trigger a scrape now: uv run python scripts/run_pipeline.py
echo.
pause
"@

Set-Content -Path "start.bat" -Value $startScript
Write-Ok "start.bat created in project root"

# --- Done ---
Write-Host "`n============================================" -ForegroundColor $GREEN
Write-Host "  Setup Complete!" -ForegroundColor $GREEN
Write-Host "============================================" -ForegroundColor $GREEN
Write-Host ""
Write-Host "  To start the app:" -ForegroundColor $White
Write-Host "    Double-click: start.bat" -ForegroundColor $White
Write-Host "    Or manually:  uv run uvicorn app.main:app --reload --port 8000" -ForegroundColor $White
Write-Host ""
Write-Host "  App: http://localhost:8000" -ForegroundColor $White
Write-Host "  Docs: Get-Content INSTRUCTIONS.md" -ForegroundColor $White
Write-Host ""
Write-Host "  Quick commands:" -ForegroundColor $White
Write-Host "    Run pipeline now:  uv run python scripts/run_pipeline.py" -ForegroundColor $White
Write-Host "    Run tests:         uv run pytest tests/ -v" -ForegroundColor $White
Write-Host ""
