FROM python:3.11-slim

# Prevent Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies (keep minimal)
RUN apt-get update && apt-get install -y gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the backend source
COPY app ./app

# Expose FastAPI port
EXPOSE 8000

# Run with Gunicorn + Uvicorn workers (Azure-safe)
ENV PORT=8000
ENV PYTHONPATH=/app

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --log-level info"]