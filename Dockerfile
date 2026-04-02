FROM python:3.12-slim AS base

LABEL maintainer="Softreck <info@softreck.dev>"
LABEL description="prollama — Intelligent LLM Execution Layer"

WORKDIR /app

# Install system deps for tree-sitter compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml README.md ./
COPY src/ src/
RUN pip install --no-cache-dir ".[proxy,ast]"

# Create non-root user
RUN useradd -m -s /bin/bash prollama
USER prollama
WORKDIR /home/prollama

# Default config
RUN prollama init 2>/dev/null || true

EXPOSE 8741

# Default: start proxy server
CMD ["prollama", "start", "--host", "0.0.0.0"]
