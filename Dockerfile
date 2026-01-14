FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Install Python dependencies
RUN pip install --no-cache-dir .

# Install Playwright browsers (for browser-based scraping)
RUN playwright install chromium && playwright install-deps chromium

# Default command (can be overridden)
CMD ["bash"]
