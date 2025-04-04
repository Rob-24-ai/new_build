FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for caching
COPY backend_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy just the main.py file to /app
COPY backend_api/main.py /app/main.py

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application directly
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
