# CollabTask

[![CI/CD](https://github.com/joselu103/collabtask/actions/workflows/github-actions.yml/badge.svg?branch=master)](https://github.com/joselu103/collabtask/actions/workflows/github-actions.yml)

A **multi-tenant task management API** built with FastAPI. Supports real-time project updates via WebSockets, role-based access control, background email notifications, and async database access throughout.

Deployed on AWS at `https://63.181.132.61.nip.io`.

## Architecture

### Local development

```
HTTP / WS Client
      │
      ▼
 FastAPI App ──────────── PostgreSQL (container)
      │
      └──── Redis (container) ──────► arq Worker
                                          └──── Mailpit (SMTP capture)
```

### Production (AWS)

```
HTTPS Client
      │
      ▼
  Nginx (EC2) ──────► FastAPI App (EC2)
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
        PostgreSQL (RDS)            Valkey (ElastiCache)
                                          │
                                     arq Worker (EC2)
                                          └──── SMTP
```

| Component        | Local                        | Production                        |
| ---------------- | ---------------------------- | --------------------------------- |
| FastAPI app      | Built from source            | Docker image from AWS ECR         |
| PostgreSQL       | Container                    | AWS RDS db.t3.micro               |
| Redis / Valkey   | Container                    | AWS ElastiCache cache.t3.micro    |
| Reverse proxy    | —                            | Nginx container (port 80 → 443)   |
| arq worker       | Container                    | Container (same ECR image)        |
| Mailpit          | Container (SMTP capture)     | —                                 |

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
- **Docker** + **GitHub Actions** — containerisation and CI/CD
- **AWS** (EC2, RDS, ElastiCache, ECR) — production infrastructure

## Local Development

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) with Compose V2
- A `.env` file (see below)
- A `docker-compose.dev.yml` file (not committed — see below)

### Setup

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
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=collabtask
SMTP_HOST=mailpit
SMTP_PORT=1025
SMTP_TLS=false
```

**2. Create `docker-compose.dev.yml`**

This file is gitignored. It adds local-only services and builds the image from source:

```yaml
services:
  db:
    image: postgres:16
    env_file: .env
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    ports:
      - "6379:6379"

  mailpit:
    image: axllent/mailpit
    ports:
      - "1025:1025"
      - "8025:8025"

  migrate:
    build: .
    depends_on:
      db:
        condition: service_healthy

  app:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy

  worker:
    build: .
    depends_on:
      db:
        condition: service_healthy

  db-test:
    profiles:
      - test
    image: postgres:16
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: collabtask_test
    volumes:
      - postgres_data_test:/var/lib/postgresql/data
    ports:
      - "5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d collabtask_test"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  postgres_data_test:
```

**3. Start the stack**

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

| Service    | URL                         |
| ---------- | --------------------------- |
| API docs   | http://localhost:8000/docs  |
| Redoc      | http://localhost:8000/redoc |
| Mailpit UI | http://localhost:8025       |

**4. Tear down**

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml down
```

## Running Tests

Start the test database:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile test up db-test -d
```

Run the suite:

```bash
pytest
```

Coverage is reported automatically. The suite fails if coverage drops below 65%.

## CI/CD

On every push to `master`:

1. **CI** — ruff lint + format check + full test suite (GitHub Actions, Postgres service container)
2. **CD** — Docker image built and pushed to AWS ECR via OIDC (no long-lived credentials)

The production stack pulls the latest image on the next deploy.

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

deploy/
├── nginx.conf              # Nginx reverse proxy config (HTTP→HTTPS, proxy to app)
├── iam-ecr-push-policy.json  # Least-privilege ECR push policy for CI/CD role
└── iam-ecr-pull-policy.json  # Least-privilege ECR pull policy for EC2 role
```

## API Overview

Full interactive documentation is available at `/docs`. Key resource groups:

- `POST /auth/register` — create account
- `POST /auth/login` — obtain access + refresh tokens
- `POST /auth/refresh` — rotate access token
- `GET/POST /organizations/` — manage organizations
- `GET/POST /organizations/{id}/projects/` — manage projects
- `WS /projects/{id}/ws` — real-time project updates
- `GET/POST /projects/{id}/tasks/` — manage tasks
- `PATCH /tasks/{id}/assign` — assign task (triggers email notification)
