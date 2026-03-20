# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml README.md ./
RUN uv sync --no-dev

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY --from=builder /app/.venv /app/.venv

COPY . .

ENV TELEGRAM_BOT_TOKEN=""
ENV TZ="Asia/Seoul"
ENV SQLITE_PATH="/app/data/telegram-bot.sqlite3"

RUN mkdir -p /app/data

CMD ["uv", "run", "telegram-bot"]
