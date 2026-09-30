# Use an official lightweight Python image
FROM python:3.14-slim

# Prevent Python from writing .pyc files & enable unbuffered stdout/stderr logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory inside the container
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

    # 1. Create group and user explicitly early in the build
RUN groupadd -g 10001 appuser \
    && useradd -u 10001 -g appuser -s /bin/sh -m appuser

# Install dependencies first (leverages Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code into container
COPY . .

# Ensure the uploads directory exists
RUN mkdir -p uploads

# Switch to the non-root user
USER appuser

# Optional: Run pytest during the image build process
# (Note: If tests fail, the docker build will fail and stop here)
RUN PYTHONPATH=. pytest -o cache_dir=/tmp/.pytest_cache

# Expose port 8000 for FastAPI
EXPOSE 8000

# Target main:app directly since main.py is in the root directory
CMD ["uvicorn", "src.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--loop", "uvloop", \
     "--http", "httptools"]