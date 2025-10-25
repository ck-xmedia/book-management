# FastAPI JSON Book Management Service

A FastAPI service for managing books with JSON file persistence (no database). Includes tests, CI, and Docker deployment.

## Features
- CRUD for books with validation (Pydantic v2)
- JSON file storage with atomic writes and file locking
- In-memory indexing for filtering, search, and pagination
- Structured logging and error handling
- Tests (pytest, httpx) and linting (ruff, black, mypy)
- GitHub Actions CI and Dockerfile

## Quickstart

### Prerequisites
- Python 3.11+ (3.12 recommended)
- pip
- Docker (optional for containerized run)

### Setup
```bash
python -m venv .venv
. ./.venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### Run (dev)
```bash
bash scripts/dev.sh
# or on Windows PowerShell
./scripts/dev.ps1
```

Service runs on http://localhost:8080. Open http://localhost:8080/docs for Swagger.

### Test
```bash
bash scripts/test.sh
```

### Lint & Format
```bash
bash scripts/lint.sh
bash scripts/format.sh
```

### Docker
```bash
docker build -t json-books:latest .
docker run -p 8080:8080 -v $(pwd)/data:/app/data json-books:latest
```

## API
- GET `/api/v1/books`
- POST `/api/v1/books`
- GET `/api/v1/books/{id}`
- PUT `/api/v1/books/{id}`
- DELETE `/api/v1/books/{id}`
- GET `/healthz`

See OpenAPI at `/docs` for full schema.

## Configuration
Use `.env` or environment variables:
- `DATA_DIR` default `./data`
- `DATA_FILE` default `books.json`
- `DATA_LOCK_FILE` default `books.json.lock`
- `ENABLE_BACKUPS` default `true`
- `BACKUP_EVERY_N_WRITES` default `50`
- `PORT` default `8080`

## Notes
- Single-writer enforced; recommended single process (`--workers 1`).
- For persistent data, mount a volume to `/app/data` in Docker.
