# Use Python 3.12 slim image for smaller size
FROM python:3.8-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install setuptools and wheel first
RUN pip install --no-cache-dir --upgrade pip setuptools>=65.0.0 wheel>=0.37.0

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for database
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8503
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Create cache directory
RUN mkdir -p /app/.cache

# Expose port 8503 (for signal.pemain12.com)
EXPOSE 8503

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8503/_stcore/health || exit 1

# Run the application
CMD ["streamlit", "run", "app.py", "--server.port", "8503", "--server.address", "0.0.0.0"]