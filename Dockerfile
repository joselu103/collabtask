# BUILDER

FROM python:3.14-slim-bookworm AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml uv.lock ./

RUN /bin/uv sync --no-dev --frozen --no-install-project

# RUNTIME

FROM python:3.14-slim-bookworm AS runtime

COPY --from=builder /app/.venv /app/.venv

WORKDIR /app

COPY src/ ./src/

COPY alembic/ ./alembic/

COPY alembic.ini ./

EXPOSE 8000

CMD ["/app/.venv/bin/gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "src.app:app", "--bind", "0.0.0.0:8000"]


