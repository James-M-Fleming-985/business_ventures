# Mechanics Update Monitor Service
# Continuously monitors Clash Royale API for balance changes

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY scripts/ ./scripts/
COPY config/ ./config/
COPY enhanced_card_database.json ./

# Create necessary directories
RUN mkdir -p logs data backups

# Set environment variables
ENV PYTHONPATH=/app
ENV CLASH_ROYALE_API_KEY=""

# Create crontab for scheduled checks
RUN echo "0 */6 * * * cd /app && python scripts/mechanics-scheduler.py --mode manual >> logs/cron.log 2>&1" > /etc/cron.d/mechanics-check && \
    chmod 0644 /etc/cron.d/mechanics-check && \
    crontab /etc/cron.d/mechanics-check

# Health check
HEALTHCHECK --interval=30m --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import json; open('data/last_mechanics_scan.json').read()" || exit 1

# Run scheduler in continuous mode
CMD ["python", "scripts/mechanics-scheduler.py", "--mode", "schedule"]
