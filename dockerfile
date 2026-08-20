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

# Install dependencies first (leverages Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code into container
COPY . .

# Ensure the uploads directory exists
RUN mkdir -p uploads

# Expose port 8000 for FastAPI
EXPOSE 8000

# Target main:app directly since main.py is in the root directory
CMD ["uvicorn", "src.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "12", \
     "--loop", "uvloop", \
     "--http", "httptools"]