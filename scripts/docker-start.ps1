#Requires -Version 5.1
<#
.SYNOPSIS
    PSC Current Affairs Agent - Docker Setup (Windows)
.DESCRIPTION
    Manages the full Docker Compose environment for the application.
#>

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$projectDir = Split-Path -Parent $scriptDir

Set-Location $projectDir

$GREEN = "Green"
$RED = "Red"
$YELLOW = "Yellow"
$BLUE = "Blue"

function Write-Step { param($Message) Write-Host "`n$Message" -ForegroundColor $BLUE }
function Write-Ok { param($Message) Write-Host "  $Message" -ForegroundColor $GREEN }
function Write-Warn { param($Message) Write-Host "  WARNING: $Message" -ForegroundColor $YELLOW }
function Write-Err { param($Message) Write-Host "  ERROR: $Message" -ForegroundColor $RED }

Write-Host "============================================" -ForegroundColor $GREEN
Write-Host "  PSC Current Affairs Agent - Docker Setup" -ForegroundColor $GREEN
Write-Host "============================================" -ForegroundColor $GREEN

function Check-Prerequisites {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Err "Docker is not installed."
        Write-Host "  Download from: https://www.docker.com/products/docker-desktop/" -ForegroundColor $Yellow
        exit 1
    }

    try {
        docker info | Out-Null
    } catch {
        Write-Err "Docker is not running. Start Docker Desktop and try again."
        exit 1
    }

    try {
        docker compose version | Out-Null
    } catch {
        Write-Err "docker compose is not available."
        Write-Host "  Make sure Docker Desktop is installed with compose plugin." -ForegroundColor $Yellow
        exit 1
    }

    Write-Ok "Prerequisites OK"
}

function Setup-Env {
    if (-not (Test-Path ".env")) {
        Write-Host "  Creating .env from .env.example..." -ForegroundColor $White
        Copy-Item ".env.example" ".env"
        Write-Ok ".env created"
    } else {
        Write-Ok ".env already exists"
    }
}

function Pull-Model {
    Write-Step "Starting Ollama to download AI model (~1.5 GB)..."

    docker compose up -d ollama

    Write-Host "  Waiting for Ollama to start..." -ForegroundColor $White
    $retries = 0
    while ($retries -lt 30) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -ErrorAction Stop
            break
        } catch {
            Start-Sleep -Seconds 3
            $retries++
            Write-Host "  ." -NoNewline
        }
    }
    Write-Host ""

    if ($retries -ge 30) {
        Write-Err "Ollama failed to start."
        Write-Host "  Check logs: docker compose logs ollama" -ForegroundColor $Yellow
        return
    }

    Write-Host "  Pulling gemma:2b model... (this may take a few minutes)" -ForegroundColor $White
    $ollamaContainer = docker compose ps -q ollama
    docker exec $ollamaContainer ollama pull gemma:2b

    Write-Ok "Model downloaded"
}

function Start-Services {
    Write-Step "Starting all services..."

    docker compose up -d

    Write-Host "  Waiting for services..." -ForegroundColor $White
    Start-Sleep -Seconds 10

    Write-Ok "Services running:"
    docker compose ps

    Write-Host ""
    Write-Host "  App: http://localhost:8000" -ForegroundColor $Green
    Write-Host ""
    Write-Host "  Useful commands:" -ForegroundColor $White
    Write-Host "    View logs:         docker compose logs -f" -ForegroundColor $White
    Write-Host "    Stop:              docker compose down" -ForegroundColor $White
    Write-Host "    Restart:           docker compose restart" -ForegroundColor $White
    Write-Host "    Rebuild:           docker compose up -d --build" -ForegroundColor $White
    Write-Host "    Run pipeline:      docker compose exec worker python scripts/run_pipeline.py" -ForegroundColor $White
}

function Show-Menu {
    Write-Host ""
    Write-Host "  1) Full setup (pull model + start all services)" -ForegroundColor $White
    Write-Host "  2) Start services only" -ForegroundColor $White
    Write-Host "  3) Stop all services" -ForegroundColor $White
    Write-Host "  4) View logs" -ForegroundColor $White
    Write-Host "  5) Rebuild and restart" -ForegroundColor $White
    Write-Host "  6) Trigger pipeline now" -ForegroundColor $White
    Write-Host "  0) Exit" -ForegroundColor $White
    Write-Host ""

    $choice = Read-Host "  Choose an option [0-6]"

    switch ($choice) {
        "1" { Check-Prerequisites; Setup-Env; Pull-Model; Start-Services }
        "2" { Check-Prerequisites; docker compose up -d; Write-Ok "Services started: http://localhost:8000" }
        "3" { docker compose down; Write-Ok "Services stopped." }
        "4" { docker compose logs -f }
        "5" { docker compose up -d --build; Write-Ok "Rebuilt and restarted." }
        "6" { docker compose exec worker python scripts/run_pipeline.py }
        "0" { Write-Host "  Exiting."; exit 0 }
        default { Write-Warn "Invalid option."; Show-Menu }
    }
}

if ($args -contains "--non-interactive" -or $args -contains "-y") {
    Check-Prerequisites
    Setup-Env
    Pull-Model
    Start-Services
} else {
    Check-Prerequisites
    Setup-Env
    Show-Menu
}
