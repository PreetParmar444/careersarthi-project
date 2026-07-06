# ── CareerSarthi container ────────────────────────────────────────────────────
# Multi-stage build: keep the runtime image lean.

FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for PDF/DOCX parsing libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir -e .

# Encrypted local data lives outside the image — mount a volume in prod
RUN mkdir -p /app/.data /app/.secrets

EXPOSE 8080

# Default: run the Career MCP server over HTTP/SSE for Cloud Run.
# Override CMD to run the CLI / agent API instead, e.g.:
#   docker run ... careersarthi careersarthi track
CMD ["python", "-m", "mcp_server.server", "--http"]
