# Use official Python image as base image (same setup as Open Coding Society flask)
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy application code into the container
COPY . /app

# Upgrade pip and install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create non-privileged user; instance/ holds the database and must stay writable
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/instance && \
    chown -R appuser:appuser /app

# Switch to non-privileged user
USER appuser

# One worker because the database is SQLite; threads handle concurrent requests
ENV FLASK_ENV=production \
    GUNICORN_CMD_ARGS="--workers=1 --threads=4 --bind=0.0.0.0:8587 --timeout=30 --access-logfile -"

# Expose application port
EXPOSE 8587

# Start Gunicorn server
CMD ["gunicorn", "main:app"]
