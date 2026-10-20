# Dockerfile for National Wildlife Conservation Intelligence Platform Backend
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

# Install system dependencies including GDAL, GEOS, PROJ and build utilities for PostGIS & ML
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    g++ \
    curl \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency requirements
COPY backend/requirements.txt ./backend/requirements.txt

# Install python dependencies and PyTorch CPU wheel
RUN pip install --upgrade pip setuptools wheel && \
    pip install torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install -r backend/requirements.txt && \
    python -m spacy download en_core_web_sm

# Copy full application code
COPY . .

# Ensure upload directory exists
RUN mkdir -p uploads ml/models

EXPOSE 8000

# Make render_start executable
RUN chmod +x render_start.sh

CMD ["./render_start.sh"]
