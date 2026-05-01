# PSC Current Affairs Agent

A local-first, AI-powered current affairs system built specifically for **Kerala PSC exam preparation**.

## Features

- **Automated RSS scraping** from trusted news sources (The Hindu, Mathrubhumi, Manorama, Indian Express, Times of India, NDTV)
- **Deduplication** — exact (URL/hash) + semantic (FAISS) to eliminate duplicate articles
- **AI-powered processing** via Ollama (local LLM — no API keys needed)
- **Smart filtering** — Kerala news always kept, India top 70%, International HIGH only
- **Daily MCQ quiz** — 5 questions generated from the day's news
- **Mobile-first web UI** — clean, responsive, no build step
- **Date-range browsing** — today, 7 days, 30 days, 1 year

## Quick Start

```bash
# 1. Install dependencies
uv sync

# 2. Configure
cp .env.example .env

# 3. Download AI model (one-time)
ollama pull gemma:2b

# 4. Initialize database
uv run python scripts/init_db.py

# 5. Start three terminals:
uv run uvicorn app.main:app --reload --port 8000        # Terminal 1
uv run celery -A app.workers.celery_app worker --loglevel=info   # Terminal 2
uv run celery -A app.workers.celery_app beat --loglevel=info     # Terminal 3
```

Then visit **http://localhost:8000**

For detailed setup instructions, see [INSTRUCTIONS.md](INSTRUCTIONS.md).

## Project Structure

```
app/
├── api/routes/          # FastAPI endpoints (news, quiz)
├── core/                # Config, logging
├── db/                  # Database setup, session management
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic response schemas
├── services/
│   ├── scraper/         # RSS + HTML scraping
│   ├── dedup/           # Exact + semantic deduplication
│   ├── llm/             # Ollama client, prompts, validation
│   ├── classifier/      # Category/importance filtering
│   └── quiz/            # Quiz generation
└── workers/             # Celery tasks + scheduling

frontend/                # HTML + Tailwind CSS UI
scripts/                 # Database init, pipeline runner
tests/                   # Unit tests
```

## Tech Stack

| Layer | Tool |
|-------|------|
| API | FastAPI |
| ORM | SQLAlchemy |
| Database | SQLite (MVP) → PostgreSQL (scale) |
| Job Queue | Celery + Redis |
| RSS Parsing | feedparser |
| HTML Parsing | BeautifulSoup4 |
| LLM | Ollama (local) |
| Embeddings | sentence-transformers |
| Vector Search | FAISS |
| Frontend | HTML + Tailwind CSS |

## Configuration

All settings in `.env` (copy from `.env.example`):

```env
DATABASE_URL=sqlite:///./psc_agent.db
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma:2b
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
SEMANTIC_SIMILARITY_THRESHOLD=0.90
```

## Running Tests

```bash
uv run pytest tests/ -v
```

## Docker (Optional)

```bash
docker compose up -d
```

## License

MIT
