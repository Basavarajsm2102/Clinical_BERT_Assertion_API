# Production Dockerfile for Clinical BERT API
FROM python:3.12-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN adduser --disabled-password --gecos '' --shell /bin/bash appuser \
    && chown -R appuser:appuser /code

USER appuser
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Install Python dependencies
COPY --chown=appuser:appuser requirements.txt .
# Install numpy<2 first to avoid compatibility issues
RUN pip install --user --no-cache-dir 'numpy<2'
RUN pip install --user --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=appuser:appuser ./app ./app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
