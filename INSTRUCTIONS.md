# PSC Current Affairs Agent — Setup Instructions

> Follow the steps for your chosen method. **Docker is recommended** — it installs everything in isolated containers with zero system dependencies.

---

## Option A: Docker (Recommended — Works on Linux & Windows)

> Requires: Docker Desktop (Linux, Windows, or macOS). No other dependencies needed.

### Linux:
```bash
bash scripts/docker-start.sh
```

### Windows (PowerShell):
```powershell
.\scripts\docker-start.ps1
```

This interactive script will:
1. Check Docker is installed and running
2. Create `.env` from template
3. Pull the AI model (`gemma:2b`, ~1.5 GB) into the Ollama container
4. Start all services (Redis, Ollama, API, Worker, Beat)

**Non-interactive (auto yes):**
```bash
# Linux
bash scripts/docker-start.sh --non-interactive

# Windows
.\scripts\docker-start.ps1 -NonInteractive
```

### After Docker setup:

| Action | Command |
|--------|---------|
| Open app | http://localhost:8000 |
| View logs | `docker compose logs -f` |
| Stop all | `docker compose down` |
| Restart | `docker compose restart` |
| Rebuild | `docker compose up -d --build` |
| Run pipeline now | `docker compose exec worker python scripts/run_pipeline.py` |

---

## Option B: Native Install (Linux)

> Installs everything directly on your system. Requires sudo for package installs. Redis and Ollama run as system services.

```bash
bash scripts/install_linux.sh
```

This interactive script will:
1. Detect your OS (Debian/Ubuntu, Fedora, Arch)
2. Install system packages: git, redis, curl, build tools
3. Install `uv` to user scope (`~/.local/bin`) — no sudo needed
4. Install Python dependencies
5. Install Ollama (as a system service)
6. Download the AI model (`gemma:2b`)
7. Initialize the database
8. Optionally set up systemd user services for auto-start

**Non-interactive (auto yes):**
```bash
bash scripts/install_linux.sh --yes
```

**Docker mode from Linux script:**
```bash
bash scripts/install_linux.sh --docker
```

### After native Linux setup:

| Action | Command |
|--------|---------|
| Open app | http://localhost:8000 |
| Start all services | `double-click start.bat` or see below |
| Start API only | `uv run uvicorn app.main:app --reload --port 8000` |
| Start worker | `uv run celery -A app.workers.celery_app worker --loglevel=info` |
| Start scheduler | `uv run celery -A app.workers.celery_app beat --loglevel=info` |
| Run pipeline now | `uv run python scripts/run_pipeline.py` |
| View logs | `journalctl --user -u psc-agent-api -f` |
| Run tests | `uv run pytest tests/ -v` |

---

## Option C: Native Install (Windows)

> Installs everything directly. Requires Ollama and Redis to be set up separately.

### In PowerShell:
```powershell
.\scripts\install_windows.ps1
```

This script will:
1. Check git is installed
2. Install `uv` (Python package manager)
3. Install Python dependencies
4. Check/guide you through Ollama installation
5. Download the AI model (`gemma:2b`)
6. Check Redis status (requires Memurai, WSL Redis, or Docker Redis)
7. Initialize the database
8. Create `start.bat` for easy launching

### Prerequisites for Windows native:

| Dependency | How to get it |
|-----------|---------------|
| **Git** | https://git-scm.com/download/win |
| **Ollama** | https://ollama.com/download |
| **Redis** | Memurai (https://www.memurai.com/get-memurai) OR WSL2 Redis OR Docker Redis |

**Quick Redis options:**
```powershell
# Option 1: Docker (simplest)
docker run -d -p 6379:6379 redis:7-alpine

# Option 2: WSL2
wsl sudo apt install redis-server && wsl sudo service redis-server start

# Option 3: Memurai (native Windows Redis)
# Download installer from memurai.com
```

### After Windows native setup:

| Action | Command |
|--------|---------|
| Open app | http://localhost:8000 |
| Start all | Double-click `start.bat` |
| Start API | `uv run uvicorn app.main:app --reload --port 8000` |
| Start worker | `uv run celery -A app.workers.celery_app worker --loglevel=info` |
| Run pipeline | `uv run python scripts/run_pipeline.py` |
| Run tests | `uv run pytest tests/ -v` |

---

## Option D: Manual Setup (Any OS)

> If the scripts don't work for your system, follow these steps manually.

```bash
# 1. Install dependencies
uv sync

# 2. Configure
cp .env.example .env

# 3. Make sure Redis is running
redis-cli ping  # should return PONG

# 4. Make sure Ollama is running and model is downloaded
ollama serve              # in one terminal (or use system service)
ollama pull gemma:2b      # one-time download

# 5. Initialize database
uv run python scripts/init_db.py

# 6. Start services (3 terminals)
uv run uvicorn app.main:app --reload --port 8000
uv run celery -A app.workers.celery_app worker --loglevel=info
uv run celery -A app.workers.celery_app beat --loglevel=info
```

---

## Using the App

### Home Page (Today's News)
- Shows all processed articles from today
- Each card has category badge (Kerala=green, India=blue, International=orange) and importance badge (HIGH=red, MEDIUM=yellow, LOW=grey)
- Click "Read more" to open the original article

### Quiz Page
- Daily MCQ quiz generated at 6:00 AM
- 5 questions, 4 options each
- Select an answer → Submit → See correct answer + explanation
- Progress bar shows your position
- Score card at the end

### Archive Page
- Filter by date range: Today, 7 Days, 30 Days, 1 Year
- Filter by category and importance using dropdowns

---

## Troubleshooting

### "Ollama connection refused"
```bash
curl http://localhost:11434/api/tags
```
If it fails:
- **Native:** `ollama serve`
- **Docker:** `docker compose restart ollama`

### "Redis connection refused"
```bash
redis-cli ping
```
Should return `PONG`. If not:
- **Linux:** `sudo systemctl start redis-server`
- **Windows (Memurai):** Start the Memurai service
- **Docker:** `docker compose restart redis`

### "Module not found" errors
Use `uv run` prefix for all commands, or activate the virtual environment:
```bash
source .venv/bin/activate    # macOS/Linux
.venv\Scripts\activate       # Windows
```

### No articles showing
Run the pipeline manually:
```bash
# Native
uv run python scripts/run_pipeline.py

# Docker
docker compose exec worker python scripts/run_pipeline.py
```

### Docker: Model pull stuck or slow
```bash
# Check Ollama logs
docker compose logs ollama

# Restart Ollama and retry
docker compose restart ollama
docker compose exec ollama ollama pull gemma:2b
```

### Linux: uv command not found after install
```bash
export PATH="$HOME/.local/bin:$PATH"
# Add this line to ~/.bashrc to make it permanent:
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

## Automatic Scheduling

Once the worker and beat are running (Docker or native):
- **Scraping** runs every 3 hours (12 AM, 3 AM, 6 AM, 9 AM, etc.)
- **Quiz generation** runs daily at 6:00 AM

No manual intervention needed.

---

## Changing the AI Model

Edit `.env` and change the model:
```env
OLLAMA_MODEL=qwen2.5
```

Then pull the new model:
```bash
ollama pull qwen2.5
# or Docker:
docker compose exec ollama ollama pull qwen2.5
```

Then restart:
```bash
# Native: restart all 3 terminals
# Docker:
docker compose restart api worker
```

| Model | Size | Speed | Quality | RAM |
|-------|------|-------|---------|-----|
| `gemma:2b` | ~1.5 GB | Fast | Good | 4 GB+ |
| `qwen2.5` | ~4.7 GB | Medium | Better | 8 GB+ |
| `mistral:7b` | ~4.1 GB | Slow | Best | 16 GB+ |

---

## Docker GPU Support (NVIDIA)

If you have an NVIDIA GPU and want faster AI inference:

1. Install NVIDIA Container Toolkit: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html

2. Uncomment the GPU section in `docker-compose.yml`:
```yaml
# In the ollama service, uncomment:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

3. Restart:
```bash
docker compose down && docker compose up -d
```
