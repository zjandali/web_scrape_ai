# Use Python 3.11
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgstreamer-gl1.0-0 \
    libgstreamer-plugins-bad1.0-0 \
    libenchant-2-2 \
    libsecret-1-0 \
    gir1.2-manette-0.2 \
    libgles2-mesa \
    wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps chromium
RUN playwright install-deps

# Copy application code
COPY . .

# Expose port
EXPOSE 10000

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"] 