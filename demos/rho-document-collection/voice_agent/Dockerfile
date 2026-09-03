# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN uv sync --locked --no-dev
RUN uv run --locked --no-dev python -m livekit.agents download-files

RUN adduser \
    --disabled-password \
    --gecos "" \
    --home /app \
    --shell /sbin/nologin \
    --uid 10001 \
    appuser
RUN chown -R appuser:appuser /app
USER appuser

CMD ["uv", "run", "--locked", "--no-dev", "python", "-m", "rho_document_collection_voice_agent.main", "start"]
