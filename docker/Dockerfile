# Jukebox – Lidarr Request Portal Dockerfile v0.1.0 – Last updated: 2025-11-23T12:00:00-05:00
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install dependencies from PyPI
RUN pip install --no-cache-dir flask requests

# Copy application files
COPY app/app.py /app/app.py
COPY app/error_parser.py /app/error_parser.py
COPY app/templates /app/templates
COPY app/static /app/static

# DB directory
RUN mkdir -p /app/data
ENV DB_PATH=/app/data/requests.db

EXPOSE 5000

CMD ["python", "app.py"]
