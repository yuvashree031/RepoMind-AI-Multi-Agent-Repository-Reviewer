FROM python:3.12-slim

# Prevent python from writing pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (git is required for cloning repos)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY . /app/backend

# Create repositories cache directory
RUN mkdir -p /app/cache/repos

# Expose port 8000
EXPOSE 8000

# Run FastAPI app
CMD ["sh", "-c", "uvicorn backend.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
