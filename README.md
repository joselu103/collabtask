# CollabTask

A **multi-tenant task management API** built with FastAPI. Supports real-time project updates via WebSockets, role-based access control, background email notifications, and async database access throughout.

## Architecture

```
HTTP / WS Client
      │
      ▼
 FastAPI App ──────────── PostgreSQL
      │                        |
      └──── Redis ──────► arq Worker
                               └──── SMTP (Mailpit in dev)
```

| Component   | Role                                         |
| ----------- | -------------------------------------------- |
| FastAPI app | REST + WebSocket API, auth, RBAC             |
| PostgreSQL  | Primary data store                           |
| Redis       | arq job queue                                |
| arq worker  | Background jobs (e.g. task-assigned email)   |
| Mailpit     | Local SMTP capture (dev only, port 8025)     |
| migrate     | One-shot Alembic migration runner on startup |

## Tech Stack

- **FastAPI** + **Uvicorn** / **Gunicorn** — async HTTP + WebSocket server
- **SQLAlchemy 2 (async)** + **asyncpg** — async ORM
- **Alembic** — database migrations
- **arq** — async background job queue backed by Redis
- **pyjwt** + **pwdlib/bcrypt** — JWT auth, bcrypt password hashing
- **pydantic-settings** — environment-based configuration
- **structlog** — structured logging
- **slowapi** — rate limiting
- **pytest-asyncio** + **httpx** + **factory-boy** — test suite

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) with Compose V2
- A `.env` file (see below)

## Setup

**1. Clone and create your environment file**

```bash
git clone https://github.com/joselu103/collabtask.git
cd collabtask
cp .env.example .env
```

Edit `.env` and fill in the required values:

```
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/collabtask
SECRET_KEY=<random-secret>
REDIS_URL=redis://redis:6379/0
SMTP_HOST=mailpit
SMTP_PORT=1025
SMTP_TLS=false
```

**2. Start the stack**

```bash
docker compose up -d
```

This builds the image, runs migrations, and starts the API, worker, and all backing services.

| Service    | URL                         |
| ---------- | --------------------------- |
| API docs   | http://localhost:8000/docs  |
| Redoc      | http://localhost:8000/redoc |
| Mailpit UI | http://localhost:8025       |

**3. Tear down**

```bash
docker compose down
```

## Running Tests

Tests require a separate test database. Start it with:

```bash
docker compose --profile test up db-test -d
```

Then run the suite:

```bash
pytest
```

Coverage is reported automatically. The suite fails if coverage drops below 65%.

To tear down the test database:

```bash
docker compose --profile test down
```

## Project Structure

```
src/
├── app.py                  # FastAPI app factory, lifespan
├── settings/               # pydantic-settings config, lru_cache
├── shared/                 # BaseModel, BaseRepository, dependencies, logging
├── database/               # Async engine, session factory, transaction helper
├── users/                  # Register, login, refresh token; JWT; bcrypt
├── organizations/          # Org CRUD, membership, RBAC roles
├── projects/               # Project CRUD, WebSocket router
├── tasks/                  # Task CRUD, state machine, assign endpoint
└── workers/                # arq WorkerSettings, background jobs

tests/
├── conftest.py             # Fixtures: app, client, db_session, table setup
├── factories.py            # factory-boy factories (UserFactory, OrgFactory)
├── unit/                   # Mock-based and parametrized unit tests
└── integration/            # Full HTTP flow tests against a real test DB
```

## API Overview

Full interactive documentation is available at `/docs` once the stack is running. Key resource groups:

- `POST /auth/register` — create account
- `POST /auth/login` — obtain access + refresh tokens
- `POST /auth/refresh` — rotate access token
- `GET/POST /organizations/` — manage organizations
- `GET/POST /organizations/{id}/projects/` — manage projects
- `WS /projects/{id}/ws` — real-time project updates
- `GET/POST /projects/{id}/tasks/` — manage tasks
- `PATCH /tasks/{id}/assign` — assign task (triggers email notification)
