# Multi-stage Dockerfile for PRISM backend
# Following enterprise best practices for security and efficiency

# Stage 1: Python dependencies builder
FROM python:3.12-slim as python-deps

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry with optimized settings
ENV POETRY_VERSION=1.7.1
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache
# Optimization for Poetry installation issues
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_REQUESTS_TIMEOUT=300

RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

# Add Poetry to PATH
ENV PATH="${PATH}:${POETRY_VENV}/bin"

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY poetry.lock* ./

# Install dependencies with retry logic for EOF error
RUN poetry config virtualenvs.create false \
    && poetry config installer.max-workers 10 \
    && poetry config installer.parallel true \
    && (test -f poetry.lock || poetry lock --no-update) \
    && poetry install --no-interaction --no-ansi --no-root --only main \
    && rm -rf $POETRY_CACHE_DIR

# Stage 2: Frontend builder (for future use)
# FROM node:20-alpine as frontend-builder
# WORKDIR /app
# COPY frontend/package*.json ./
# RUN npm ci --only=production
# COPY frontend/ ./
# RUN npm run build

# Stage 3: Final production image
FROM python:3.12-slim as production

# Security: Create non-root user
RUN groupadd -r prism && useradd -r -g prism prism

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=python-deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=python-deps /usr/local/bin /usr/local/bin

# Copy application code
COPY backend/ ./backend/
COPY alembic.ini ./

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/uploads /home/prism \
    && chown -R prism:prism /app /home/prism

# Security: Switch to non-root user
USER prism

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/app/.local/bin:${PATH}"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Stage 4: Development image
FROM production as development

# Switch back to root for development tools installation
USER root

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    less \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy Poetry files for development
ENV POETRY_VENV=/opt/poetry-venv
COPY --from=python-deps ${POETRY_VENV} ${POETRY_VENV}
ENV PATH="${POETRY_VENV}/bin:${PATH}"

# Install all dependencies including dev
WORKDIR /app
COPY pyproject.toml ./
COPY poetry.lock* ./
# Set Poetry environment variables for development stage
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_REQUESTS_TIMEOUT=300
RUN poetry config virtualenvs.create false \
    && poetry config installer.max-workers 10 \
    && poetry config installer.parallel true \
    && (test -f poetry.lock || poetry lock --no-update) \
    && poetry install --no-interaction --no-ansi --no-root \
    && rm -rf /opt/.cache

# Development volumes will be mounted here
VOLUME ["/app/backend", "/app/logs", "/app/uploads"]

# Create home directory and set permissions
RUN mkdir -p /home/prism && chown -R prism:prism /home/prism /app

# Switch back to prism user
USER prism

# Development command with auto-reload
CMD ["uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]