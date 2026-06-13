# LLMOps - Agent Guide

## Monorepo Structure

- `llmops-api/` — Flask backend (Python 3.13+, uv)
- `llmops-ui/` — Vue 3 frontend (Vite + TypeScript + Tailwind + Arco Design)
- `docker-compose.yml` — PostgreSQL, Redis, Weaviate
- `docs/`, `storage/` — Documentation, logs

## Prerequisites

```bash
docker compose up -d          # PostgreSQL + Redis + Weaviate
# Ollama must be running locally for embeddings (default: http://127.0.0.1:11434)
```

## llmops-api

```bash
cd llmops-api
uv sync                       # Install dependencies
uv run python app/http/app.py # Dev server on :5000
```

### Celery Worker

Use the PowerShell script (cleans .pyc, sets PYTHONPATH, runs with eventlet):

```bash
.\start_celery.ps1
```

Or manually:

```bash
celery -A app.http.app.celery worker -l info --pool eventlet
```

### Database Migrations

```bash
flask --app app.http.app db migrate -m "msg"
flask --app app.http.app db upgrade
flask --app app.http.app db downgrade
```

Migrations directory: `internal/migration/`

### Testing

```bash
cd llmops-api
pytest                        # Uses pytest.ini: -v -s, cache in tmp/
```

### Architecture

- Entry: `app/http/app.py` → creates `Http` (Flask subclass), gets `celery` from extensions
- DI: Uses `injector` library; bindings in `internal/model/module.py`
- Routes: `internal/router/router.py` — all URL rules registered manually via `add_url_rule`
- Extensions: `internal/extension/` — DB, Redis, Celery, Migrate, Login, Logging
- Config: `config/config.py` reads from env vars via `os.getenv`

### Key Directory Layout (internal/)

```
core/         — Agent, tools, workflow engine (LangGraph), memory, retrievers
entity/       — Enums, defaults, constants
model/        — SQLAlchemy ORM models
service/      — Business logic
handler/      — HTTP request handlers (thin layer over services)
schema/       — Request/response validation (WTForms)
router/       — Flask route registration
extension/    — Flask extensions (DB, Redis, Celery)
task/         — Celery async tasks
middleware/   — Auth/request loading
migration/    — Alembic migrations
```

### Gotchas

- **DetachedInstanceError**: In generators/SSE streams, extract ORM IDs *before* yielding (session closes mid-stream)
- **Workflow validation**: Empty workflows auto-create START→END nodes; `workflow_entity.py` validator allows empty nodes/edges
- **Celery eventlet**: Must use `--pool eventlet`; default prefork breaks
- **Windows**: `start_celery.ps1` sets `PYTHONPATH` and cleans `.pyc` before start

## llmops-ui

```bash
cd llmops-ui
npm install
npm run dev                   # Vite dev server, proxies /api → localhost:5000
npm run build                 # type-check + vite build
npm run lint                  # ESLint with auto-fix
npm run format                # Prettier
npm run test:unit             # Vitest
```

### Frontend Stack

- Vue 3 + Vue Router + Pinia
- Arco Design (`@arco-design/web-vue`) as UI component library
- Tailwind CSS + PostCSS
- TypeScript strict mode
- `@` alias → `./src`

### Proxy Config

`/api` requests are proxied to `http://localhost:5000` (Flask backend). Path prefix `/api` is stripped.

## Environment Variables

Create `llmops-api/.env`. Key vars:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY`, `OPENAI_API_BASE_URL` | LLM provider (DashScope compatible) |
| `SQLALCHEMY_DATABASE_URI` | PostgreSQL connection |
| `REDIS_HOST`, `REDIS_PORT` | Redis for Celery + cache |
| `WEAVIATE_HOST`, `WEAVIATE_PORT` | Vector DB |
| `OLLAMA_BASE_URL` | Local embedding model |
| `FLASK_ENV`, `FLASK_DEBUG` | Flask dev mode |

## Code Conventions

- Python 3.13+, type hints required, Pydantic V2
- Flask-WTF for request validation
- `flask --app app.http.app` is the app entry for CLI commands
- Frontend: ESLint + Prettier; run `npm run lint` before committing
