FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Set working directory
WORKDIR /app

# Install dependencies
COPY backend_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend_api/main.py /app/main.py

# Expose the port the app runs on
EXPOSE 8000

# Set metadata
LABEL org.opencontainers.image.title="ArtSensei Image Analysis API" \
      org.opencontainers.image.description="API for analyzing images using ArtSensei Prediction API" \
      org.opencontainers.image.version="1.0.0"

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run the application with production settings
CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2 --log-level info"]
