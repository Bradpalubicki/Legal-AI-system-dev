# Celery Worker Container for Legal AI System
# Background task processing for document analysis and AI operations

FROM python:3.11-slim

# Set labels for metadata
LABEL maintainer="Legal AI Development Team" \
      version="1.0" \
      description="Legal AI System Celery Workers" \
      python.version="3.11"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    gcc \
    g++ \
    libpq-dev \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    ffmpeg \
    imagemagick \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r celeryuser && useradd -r -g celeryuser celeryuser

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt requirements-celery.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-celery.txt

# Copy application code
COPY --chown=celeryuser:celeryuser app/ ./app/
COPY --chown=celeryuser:celeryuser celery_app.py ./
COPY --chown=celeryuser:celeryuser tasks/ ./tasks/

# Copy Celery configuration and scripts
COPY --chown=celeryuser:celeryuser celery.conf /etc/celery/
COPY --chown=celeryuser:celeryuser scripts/ /usr/local/bin/
RUN chmod +x /usr/local/bin/*.sh

# Create necessary directories
RUN mkdir -p /app/logs /app/temp /var/run/celery /var/log/celery && \
    chown -R celeryuser:celeryuser /app /var/run/celery /var/log/celery

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    C_FORCE_ROOT=1 \
    CELERY_LOG_LEVEL=info

# Switch to non-root user
USER celeryuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD celery -A celery_app inspect ping || exit 1

# Default command (can be overridden for different worker types)
CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info", "--concurrency=4"]