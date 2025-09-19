# Multi-stage Dockerfile for optimized Clinical BERT API
# Stage 1: Builder - Install dependencies
FROM python:3.12-slim AS builder

WORKDIR /install

# Install system build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# Stage 2: Runtime - Optimized for Cloud Run
FROM python:3.12-slim

WORKDIR /code

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && adduser --disabled-password --gecos '' --shell /bin/bash appuser \
    && chown -R appuser:appuser /code

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Set environment variables before switching user
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/usr/local/bin:$PATH"

# Copy application code
COPY --chown=appuser:appuser ./app ./app
COPY --chown=appuser:appuser entrypoint.sh .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

USER appuser

# Health check for Cloud Run
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080

# Use entrypoint script for proper PORT handling
ENTRYPOINT ["./entrypoint.sh"]
