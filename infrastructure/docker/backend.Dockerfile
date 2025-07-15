FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.7.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_HOME='/usr/local'

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-root --only main

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/uploads

# Create non-root user
RUN useradd -m -u 1000 prism && \
    chown -R prism:prism /app

# Switch to non-root user
USER prism

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "8000"]