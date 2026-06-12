# LLMOps API - Agent Guide

## Quick Start

```bash
# Install dependencies
uv sync

# Run development server
uv run python app/http/app.py

# Database migrations
flask --app app.http.app db migrate -m "msg"
flask --app app.http.app db upgrade
flask --app app.http.app db downgrade
```

## Architecture

- **Framework**: Flask + SQLAlchemy + LangChain/LangGraph
- **Database**: PostgreSQL
- **Cache**: Redis
- **Task Queue**: Celery
- **Vector DB**: Weaviate

## Key Directories

```
internal/
├── core/           # Core domain logic
│   ├── agent/      # Agent implementations (FunctionCallAgent)
│   ├── tools/      # Tool system (builtin + API tools)
│   ├── workflow/   # Workflow engine (LangGraph)
│   ├── memory/     # TokenBufferMemory
│   └── retrievers/ # Semantic + FullText retrievers
├── entity/         # Enums, defaults, constants
├── model/          # SQLAlchemy ORM models
├── service/        # Business logic
├── handler/        # HTTP request handlers
├── schema/         # Request/response validation (WTForms)
├── router/         # Flask route registration
└── extension/      # Flask extensions (DB, Redis, Celery)
```

## Common Issues & Solutions

### Workflow Validation Errors

When creating empty workflows, the system auto-creates START/END nodes:
- `workflow_entity.py`: Validator allows empty nodes/edges
- `workflow.py`: Auto-creates START→END edge if edges empty

### DetachedInstanceError (SQLAlchemy)

When using generators/SSE streams, extract ORM IDs before yield:
```python
# ❌ Wrong - session closed when generator executes
def stream():
    yield str(user.id)  # DetachedInstanceError

# ✅ Correct - extract ID before generator
user_id = str(user.id)
def stream():
    yield user_id
```

### Pydantic V2 Migration

- `@root_validator` → `@model_validator(mode='before')`
- `allow_population_by_field_name` → `validate_by_name`
- `Optional[field_type]` works with variables

## Environment Variables

Required in `.env`:
- `OPENAI_API_KEY`, `OPENAI_API_BASE_URL`, `LLM_MODEL`
- `SQLALCHEMY_DATABASE_URI`
- `REDIS_HOST`, `REDIS_PORT`
- `WEAVIATE_HOST`, `WEAVIATE_PORT`

## Testing

```bash
pytest
```

## Code Style

- Python 3.13+
- Type hints required
- Pydantic V2 for data validation
- Flask-WTF for request validation
