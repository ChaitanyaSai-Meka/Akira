FROM ghcr.io/astral-sh/uv:0.5.11-python3.12-bookworm@sha256:8c6e80267fe1e5350db3836f1fd3bae4828e0723f103a0e0c4e1f5b5c0d0f5a1 AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.12.8-slim-bookworm@sha256:5dc6f84b5e85d1ef2c5e2f6f7f4e3d1f8e9f7f6f5f4f3f2f1f0f9f8f7f6f5f4

RUN apt-get update && apt-get install -y \
    libportaudio2 \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY . .

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8080

CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8080"]
