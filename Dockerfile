# Multi-stage build for optimized Docker image
FROM python:3.11-slim AS builder

# Install system dependencies for building packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Set up uv configuration for better caching
ENV UV_CACHE_DIR=/tmp/uv-cache
ENV UV_PYTHON=/usr/local/bin/python
ENV UV_INDEX_URL=https://pypi.org/simple/

# Copy requirements files first for better layer caching
COPY requirements.txt requirements-dev.txt ./

# Install dependencies using uv with optimized settings
RUN uv pip install --system -r requirements.txt

# Final stage
FROM python:3.11-slim

EXPOSE 8086

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install curl for healthcheck
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["gunicorn", "--bind", "0.0.0.0:8086", "-k", "uvicorn.workers.UvicornWorker", "app.main:app"]
