FROM python:3.11-slim

# Copy only what's needed
COPY backend_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY backend_api/ /app/backend_api

# Set the working directory to where main.py is located
WORKDIR /app/backend_api

# Expose the port
EXPOSE 8000

# Command to run the application using Python, hardcoding port 8000 for testing
CMD ["python", "-c", "from uvicorn import run; run('main:app', host='0.0.0.0', port=8000)"]
