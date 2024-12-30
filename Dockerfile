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
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libxshmfence1 \
    wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Add these lines after the existing apt-get install
RUN apt-get update && apt-get install -y \
    fonts-liberation \
    fonts-noto-color-emoji \
    fonts-noto-cjk \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright with system dependencies
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
ENV NODE_OPTIONS=--max_old_space_size=4096
RUN playwright install --with-deps chromium

# Copy application code
COPY . .

# Expose port
EXPOSE 10000

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]