FROM python:3.11-slim

WORKDIR /app

# Copy only what's needed
COPY backend_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY backend_api/ .

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]
