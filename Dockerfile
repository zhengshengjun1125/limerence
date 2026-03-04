# ===================================================================
# Dockerfile – AI Video Detector
# Build:  docker build -t ai-video-detector .
# Run:    docker run -p 8000:8000 ai-video-detector
# ===================================================================

# Stage 1 – base image with Python + system dependencies
FROM python:3.11-slim AS base

# Install system libs needed by OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    ffmpeg \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Stage 2 – install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3 – copy application code
COPY app/        ./app/
COPY static/     ./static/
COPY templates/  ./templates/

# Create uploads directory (writable at runtime)
RUN mkdir -p static/uploads

# Expose port
EXPOSE 8000

# Non-root user for security
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

# Production start command (Uvicorn with multiple workers)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
