# SwarVox AI

Business voice-agent platform for customer follow-up. This repository currently contains the production-oriented project foundation only: no lead ingestion, authentication, provider webhook, or outbound-call workflow is active yet.

The legacy prototype modules remain in the source tree for reference, but their routers are not registered. Foundation code only serves `GET /health`; it verifies database connectivity and returns HTTP 503 when the database cannot be reached.

## Project Structure

```text
backend/
  app/
    api/                   # HTTP routing boundary
    core/                  # Typed environment configuration
    database/              # SQLAlchemy engine and session utilities
    models/                # Future domain models
    services/              # Future application services
    telephony/             # Future provider adapters
  alembic/                 # Migration environment and version history
  tests/                   # Pytest coverage
frontend/                  # React/Vite shell and Vitest tests
docker-compose.yml         # Local PostgreSQL, backend, and frontend services
.env.example               # Safe configuration template
```

## Local development

Prerequisites: Python 3.12+, Node.js 22+, Docker Desktop, and Docker Compose.

Create a local environment file, then start PostgreSQL:

```powershell
cd "D:\SwarVox AI"
Copy-Item .env.example .env
docker compose up -d postgres
```

### Backend

```bash
cd "D:\SwarVox AI\backend"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item ..\.env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

API docs: `http://127.0.0.1:8000/docs`

## Frontend

```bash
cd "D:\SwarVox AI\frontend"
npm install
npm run dev
```

The frontend uses `VITE_API_BASE_URL`, defaulting to `http://127.0.0.1:8000`.

## Containers

```powershell
cd "D:\SwarVox AI"
docker compose up --build
```

## Tests

```powershell
cd "D:\SwarVox AI\backend"
pytest

cd "D:\SwarVox AI\frontend"
npm test
npm run build
```

## Next increment

Establish business-scoped authentication and authorization, then introduce business and lead tables through an Alembic migration. Consent and opt-out records must exist before any call-creation path is added.
