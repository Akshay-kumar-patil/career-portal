FROM python:3.11-slim

WORKDIR /app

# System dependencies for weasyprint and other libs
RUN apt-get update && apt-get install -y \
    build-essential \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libcairo2 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p data/uploads data/generated data/chroma_db

# Expose ports
EXPOSE 8000 8501

# Default command (use docker-compose to run both services)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
