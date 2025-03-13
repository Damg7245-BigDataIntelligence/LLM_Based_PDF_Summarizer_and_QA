FROM python:3.11.5-slim

ARG SERVICE_TYPE=api
# Convert ARG to ENV so it's available at runtime
ENV SERVICE_TYPE=$SERVICE_TYPE
COPY .env /app/.env

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements-base.txt ./
COPY requirements-api.txt requirements-worker.txt ./

# Install dependencies based on service type
RUN if [ "$SERVICE_TYPE" = "api" ]; then \
        pip install --no-cache-dir -r requirements-api.txt; \
    elif [ "$SERVICE_TYPE" = "summary-worker" ] || [ "$SERVICE_TYPE" = "qa-worker" ]; then \
        pip install --no-cache-dir -r requirements-worker.txt; \
    else \
        echo "Unknown service type: $SERVICE_TYPE"; \
        exit 1; \
    fi

# Copy the application code
COPY app /app/app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV REDIS_HOST=localhost
ENV REDIS_PORT=6379

# Expose the port (only needed for API)
EXPOSE 8000

# Set the command based on service type
CMD if [ "$SERVICE_TYPE" = "api" ]; then \
        uvicorn app.backend.main:app --host 0.0.0.0 --port 8000; \
    elif [ "$SERVICE_TYPE" = "summary-worker" ]; then \
        python -m app.backend.summary_worker; \
    elif [ "$SERVICE_TYPE" = "qa-worker" ]; then \
        python -m app.backend.qa_worker; \
    else \
        echo "Unknown service type: $SERVICE_TYPE"; \
        exit 1; \
    fi