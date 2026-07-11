# Build stage
FROM python:3.14-slim AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.11.28 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project

COPY src ./src
RUN uv sync --locked --no-dev --no-editable

# Runtime stage
FROM python:3.14-slim

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY migrations ./migrations

ENV PATH="/app/.venv/bin:$PATH"
ENV TZ="Asia/Seoul"
ENV SQLITE_PATH="/app/data/telegram-bot.sqlite3"

RUN mkdir -p /app/data

CMD ["telegram-bot"]
